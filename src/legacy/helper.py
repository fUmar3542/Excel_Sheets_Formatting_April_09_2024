# pylint: disable=uncallable-module
'''helper functions used during calculations'''

import logging
from typing import List
import numpy as np
import pandas as pd
from scipy.stats import norm
import time
from src.handles.exception_handling import MyExceptions

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

INDEX_COLS = ["RIY Index", "RTY Index", "RAG Index", "RAV Index"]
FACTOR_OPERATIONS = {
    'RIY less RTY': ["RIY Index", "RTY Index"],
    'RAG less RAV': ["RAG Index", "RAV Index"],
}
CALL_VALUES = ['Call', 'C', 'c']
PUT_VALUES = ['Put', 'P', 'p']


def imply_smb_gmv(factor_returns: pd.DataFrame,eq_factor_name) -> pd.DataFrame:
    '''
    imply Small - Big, Growth - Value
    adds columns like RIY less RTY
    selects columns in the right order
    '''
    # select columns to return according to the Fund being modelled
    # /!\ The first index is the Equity Factor
    part_b_cols = []
    PART_A_COLS = [eq_factor_name] + ["LD12TRUU Index", "RIY less RTY", "RAG less RAV"]
    try:
        # add factor operation columns
        for target_col, source_cols in FACTOR_OPERATIONS.items():
            col_a, col_b = source_cols
            factor_returns[target_col] = factor_returns[col_a] - \
                factor_returns[col_b]

        stop_cols = INDEX_COLS + PART_A_COLS
        part_b_cols = [
            col for col in factor_returns.columns
            if col not in stop_cols
        ]
    except Exception as ex:
        MyExceptions.show_message(tab='helper.py',
                                  message="Following exception occurred during columns selection\n\n" + str(
                                      ex))
    finally:
        return factor_returns[PART_A_COLS + part_b_cols]


def option_price(
    S: pd.Series,
    X: pd.Series,
    T: pd.Series,
    Vol: pd.Series,
    rf: float,
    type: pd.Series
) -> List[float]:
    '''some black magic happenning here'''
    # TODO: Make it readable

    # start_time = time.time()
    
    price_list = []
    try:
        for idx in range(0, len(S)):
            d1 = (np.log(S.iloc[idx] / X.iloc[idx]) +  # type: ignore
                (rf + Vol.iloc[idx] ** 2 / 2) * T.iloc[idx]
            ) / (Vol.iloc[idx] * np.sqrt(T.iloc[idx]))
            d2 = d1 - Vol.iloc[idx] * np.sqrt(T.iloc[idx])
            if type.iloc[idx] in CALL_VALUES:
                price = S.iloc[idx] * norm.cdf(d1, 0, 1) - X.iloc[idx] * np.exp(
                    -rf * T.iloc[idx]
                ) * norm.cdf(d2, 0, 1)
            elif type.iloc[idx] in PUT_VALUES:
                price = X.iloc[idx] * np.exp(-rf * T.iloc[idx]) * norm.cdf(
                    -d2, 0, 1
                ) - S.iloc[idx] * norm.cdf(-d1, 0, 1)

            price_list.append(price)
    except Exception as ex:
        MyExceptions.show_message(tab='helper.py',
                                  message="Following exception occurred during price calculation\n\n" + str(
                                      ex))
    finally:
        return price_list


def option_delta(
    S: pd.Series,
    X: pd.Series,
    T: pd.Series,
    Vol: pd.Series,
    rf: float,
    type: pd.Series
) -> List[float]:
    delta_list = []
    try:
        for idx in range(0, len(S)):
            d1 = (np.log(S.iloc[idx] / X.iloc[idx]) +  # type: ignore
                (rf + Vol.iloc[idx] ** 2 / 2) * T.iloc[idx]
            ) / (Vol.iloc[idx] * np.sqrt(T.iloc[idx]))
            delta = norm.cdf(d1, 0, 1)
            if type.iloc[idx] in CALL_VALUES:
                pass
            elif type.iloc[idx] in PUT_VALUES:
                delta = delta - 1
            delta_list.append(delta)
    except Exception as ex:
        MyExceptions.show_message(tab='helper.py',
                                  message="Following exception occurred during delta list building\n\n" + str(
                                      ex))
    finally:
        return delta_list


def calculate_returns(data: pd.DataFrame):
    ''' calculates returns of a wide column
        containing only price values per factor
    '''
    return_data = None
    try:
        return_data = data / data.shift(1) - 1
        return_data = return_data.iloc[1:, ]
    except Exception as ex:
        MyExceptions.show_message(tab='helper.py',
                                  message="Following exception occurred during returns data calculation\n\n" + str(
                                      ex))
    finally:
        return return_data


def calculate_log_returns(data: pd.DataFrame, eq_factor_name=None):  #XM: added. returns should be log return for time series.
    ''' calculates log returns of a wide column
        containing only price values per factor
        replaces returns by benchmark return if no price is given 
    '''
    return_data = None
    prices_data = None
    try:
        return_data = np.log(data / data.shift(1))
        return_data = return_data.iloc[1:, ]
        if not eq_factor_name is None:
            for c in return_data.columns:
                return_data.loc[~np.isfinite(return_data[c]),c]= return_data.loc[~np.isfinite(return_data[c]),eq_factor_name]
            return_data.drop(columns=[eq_factor_name],inplace=True)

        # build normed prices
        prices_data = pd.DataFrame(columns = return_data.columns, index= data.index)
        prices_data.iloc[0,:] = 0
        prices_data.iloc[1:,:] = return_data
        prices_data = np.exp(prices_data.astype(float)).cumprod()
    except Exception as ex:
        MyExceptions.show_message(tab='helper.py',
                                  message="Following exception occurred during return data and price data calculation\n\n" + str(
                                      ex))
    finally:
        return return_data, prices_data
