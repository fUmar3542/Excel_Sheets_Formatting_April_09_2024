'''module contains portfolio var calculator'''

import logging
from dataclasses import dataclass
from functools import cached_property
from typing import Any
import config
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, Any

logger = logging.getLogger(__name__)
QUANTILES = config.global_settings.get("quantiles", {})
DECAY_FACTOR = config.global_settings.get("decay factor", 0.94)

@dataclass
class PortfolioVarCalculator:
    '''
    class is responsible for calculation of different types
    of vars of elements that constiture the portfolio
    It has the following public methods:
        portfolio_var: returns portfolio var for given quantile
        isolated_var: returns isolated var for given quantile
        component_var: returns component var for given quantile
        incremental_var: returns all incremental vars for each asset

    Class attributes:
        prices_table: a dataframe that contains prices of all positions
        positions_table: a dataframe containing all
            positions of a given portfolio
    '''
    prices_table: pd.DataFrame
    positions_table: pd.DataFrame
    nav: float

    def __post_init__(self):
        # make sure that prices table consits only of factors
        # that are relevant for the given positions table
        var_tickers = self.positions_table['VaRTicker'].unique()
        self.prices_table = self.prices_table.loc[:, var_tickers]

    def portfolio_var(self, quantile: float) -> float:
        '''returns portfolio var for given quantile'''
        return self._portfolio_std * quantile

    def isolated_var(self, quantile: float) -> pd.Series:
        '''returns isolated var for given quantile'''
        return self._position_std_filtered * quantile
        #return self._position_std * quantile

    def component_var(self, quantile: float) -> pd.Series:
        '''returns component var for given quantile'''
        return self._position_weights * self.portfolio_var(quantile)

    def incremental_var(self, quantile: float) -> pd.Series:
        '''returns all incremental vars for each asset'''
        return_series = pd.Series(
            {
                ticker: self._ticker_incremental_var(ticker, quantile)
                for ticker in self._var_tickers
            }
        )
        return_series.index.name = 'VaRTicker'
        return return_series

    @cached_property
    def _positions(self) -> pd.DataFrame:
        '''aggregated position exposure for each varTicker'''
        return self.positions_table\
            .groupby('VaRTicker')\
            .agg({'Exposure': 'sum'})

    @cached_property
    def _position_weights(self) -> pd.Series:  
        '''returns position's % Exposure w.r.t NAV '''
        #return self._positions.Exposure / self._positions.Exposure.sum()   #XM: dubious calculation ... 
        return self._positions.Exposure / self.nav

    @cached_property
    def _position_returns(self) -> pd.DataFrame:    #XM: corrected returned value: extra -1 removed 
        '''returns daily returns of the portfolio'''
        # version with na dropped 
        # ( (self.prices_table  - self.prices_table.shift(1))/self.prices_table.shift(1) ).dropna()
        tmp = ( (self.prices_table  - self.prices_table.shift(1))/self.prices_table.shift(1) ).fillna(0)
        tmp[tmp==np.inf]=0  # removes the np.inf values 
        return tmp

    @cached_property
    def _position_log_returns(self) -> pd.DataFrame:   #XM: added this function to return proper log returns as it should be for time series returns 
        '''returns daily log returns of the portfolio'''
        tmp = ( np.log(self.prices_table  / self.prices_table.shift(1)) ).fillna(0)
        tmp[tmp==np.inf]=0
        return tmp # ( np.log(self.prices_table  / self.prices_table.shift(1)) ).fillna(0)

    @cached_property
    def return_covariance(self) -> pd.DataFrame:
        '''returns covariance matrix of the portfolio'''
        return self._position_cov_filtered
        #return self._position_returns.cov()

    @cached_property
    def _portfolio_std(self) -> float:
        '''returns standard deviation of the portfolio'''
        return np.sqrt(
            self._position_weights.T
            @ self.return_covariance
            @ self._position_weights
        )  # type: ignore

    @cached_property
    def _var_tickers(self) -> pd.Series:
        '''returns var tickers '''
        return self._positions.index.to_series()

    @cached_property
    def _position_std_filtered(self) -> pd.Series:
        '''returns EWMA filtered stdev '''
        tmp = self._position_log_returns.copy()
        N= len(tmp)
        tmp = tmp **2
        tmp['decay'] = [(1-DECAY_FACTOR)*(DECAY_FACTOR**(N-i-1)) for i in range(N)]
        for c in tmp.columns[:-1]:
            tmp[c]=tmp[c]*tmp['decay']
        tmp.drop(columns='decay',inplace=True)
        return_series = tmp.sum().apply(lambda x:np.sqrt(x))
        return_series.index.name = 'VaRTicker'
        return return_series

    @cached_property
    def _position_cov_filtered(self) -> pd.DataFrame: #XM created: EWMA covariance
        '''returns EWMA  filtered covariance '''
        tmp = self._position_log_returns.copy()  # replaced from simple returns
        N = len (tmp)
        tmp['decay'] = [((1-DECAY_FACTOR)*(DECAY_FACTOR**(N-i-1)))**0.5 for i in range(N)]
        for c in tmp.columns[:-1]:
            tmp[c]=tmp[c]*tmp['decay']
        tmp.drop(columns='decay',inplace=True)
        return tmp.T.dot(tmp)

    @cached_property
    def _position_std(self) -> pd.Series:
        '''returns standard deviation of the portfolio positions'''
        return_series = self._position_returns.std() 
        return_series.index.name = 'VaRTicker'
        return return_series

    @cached_property
    def _isolated_calculators(self) -> Dict[str, Any]:
        '''returns isolated var calculators for each ticker'''

        return_dict = {}
        for ticker in self._var_tickers:
            incremental_positions = self.positions_table.loc[
                self.positions_table.VaRTicker != ticker, :
            ]
            return_dict[ticker] = PortfolioVarCalculator(
                prices_table=self.prices_table,
                positions_table=incremental_positions,
                nav = self.nav
            )

        return return_dict

    def _ticker_incremental_var(
        self,
        ticker: str,
        quantile: float
    ) -> pd.Series:
        '''returns incremental var for a given ticker for given quantile'''

        return self.portfolio_var(quantile) \
            - self._isolated_calculators[ticker].portfolio_var(quantile)
