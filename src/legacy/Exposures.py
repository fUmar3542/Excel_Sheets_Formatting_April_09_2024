import logging
from typing import Dict
import os
import config
import numpy as np
import pandas as pd
from src.legacy.helper import option_price
from src.handles.exception_handling import MyExceptions

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

RISK_FREE_RATE = config.global_settings.get("risk_free_rate", 0.055)
OPTION_TYPES = config.global_settings.get("option types", [])
NON_OPTION_TYPES = config.global_settings.get("non option types", [])
FUND_NAME_ALIAS = config.global_settings.get("fund name alias", "")


def filter_exposure_calc(
    filter: Dict,
    position: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    strat_df = None
    ector_df = None
    industry_df = None
    country_df = None
    mktcap_df = None
    analyst_df = None
    assettype_df = None
    try:
        # builds exposure_calc_df with all the exposures for different filters
        firm_NAV = AUM_dict[fund_grouping]
        filter_list = list(filter.keys())
        exposure_calc_dict = {}
        for filter_item in filter_list:
            position_grouped = position.groupby([filter_item,'VaRTicker'])

            aggExpo_df = position_grouped['Exposure'].sum().reset_index().drop(columns='VaRTicker')  # XM: Aggregates by VaRTicker
            aggExpo_df['longExpo']=aggExpo_df['Exposure'].apply(lambda x: x if x>0 else 0)
            aggExpo_df['shortExpo']=aggExpo_df['Exposure'].apply(lambda x: x if x<0 else 0)
            aggExpo_df = aggExpo_df.drop(columns='Exposure').groupby(filter_item).sum()
            for name, group in aggExpo_df.iterrows():
                long_exposure_calc = group['longExpo']
                short_exposure_calc = group['shortExpo']
                gross_exposure_calc = long_exposure_calc + abs(short_exposure_calc)
                net_exposure_calc = long_exposure_calc + short_exposure_calc
                exposure_calc_dict[f"{filter_item}_{name}_exposure"] = [
                    long_exposure_calc / firm_NAV,
                    short_exposure_calc / firm_NAV,
                    gross_exposure_calc / firm_NAV,
                    net_exposure_calc / firm_NAV,
                ]
        exposure_calc_df = pd.DataFrame(
            exposure_calc_dict,
            index=[
                "Long",
                "Short",
                "Gross",
                "Net",
            ],
        ).T
        exposure_calc_df = pd.concat([exposure_calc_df], axis=1)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating exposure calculate dataframe\n\n" + str(
                                      ex))
    
    
    # build the output dfs 
    try:
        # strat
        if fund_grouping == "Firm":
            strat_df = exposure_calc_df.loc[exposure_calc_df.index.str.contains("Strat")]
            strat_df.reset_index(inplace=True)
            strat_df.rename(columns={"index": "Strategy Exposure"}, inplace=True)
            strat_df["Strategy Exposure"].replace(
                {"Strat_": ""}, regex=True, inplace=True
            )
            total_df = pd.DataFrame(strat_df.iloc[:, 1:].sum(axis=0).values[None, :],
                                    columns=strat_df.columns[1:], index=["Total"])
            strat_df.set_index(["Strategy Exposure"], inplace=True)
            strat_df = pd.concat([strat_df, total_df], axis=0)
            strat_df.reset_index(inplace=True)
            strat_df.rename(columns={"index": "Strategy Exposure"}, inplace=True)
            strat_df.set_index(["Strategy Exposure"], inplace=True)
        else: # no strat decomp if modeling individual fund
            strat_df = pd.DataFrame()
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building strat dataframe\n\n" + str(
                                      ex))
    try:
        # sector
        sector_df = exposure_calc_df.loc[exposure_calc_df.index.str.contains("Sector")]
        sector_df.reset_index(inplace=True)
        sector_df.rename(columns={"index":"Sector Exposure"},inplace=True)
        sector_df["Sector Exposure"].replace(
            {"Sector_": ""}, regex=True, inplace=True
        )
        sector_df["Sector Exposure"].replace(
            {"_exposure": ""}, regex=True, inplace=True
        )
        total_df = pd.DataFrame(sector_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=sector_df.columns[1:], index=["Total"])
        sector_df.set_index(["Sector Exposure"], inplace=True)
        sector_df = pd.concat([sector_df, total_df],axis=0)
        sector_df.reset_index(inplace=True)
        sector_df.rename(columns={"index": "Sector Exposure"}, inplace=True)
        sector_df.set_index(["Sector Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building sector exposure dataframe\n\n" + str(
                                      ex))
    try:
        # industry
        industry_df = exposure_calc_df.loc[exposure_calc_df.index.str.contains("Industry")]
        industry_df.reset_index(inplace=True)
        industry_df.rename(columns={"index":"Industry Exposure"},inplace=True)
        industry_df["Industry Exposure"].replace(
            {"Industry_": ""}, regex=True, inplace=True
        )
        industry_df["Industry Exposure"].replace(
            {"_exposure": ""}, regex=True, inplace=True
        )
        total_df = pd.DataFrame(industry_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=industry_df.columns[1:], index=["Total"])
        industry_df.set_index(["Industry Exposure"], inplace=True)
        industry_df = pd.concat([industry_df, total_df],axis=0)
        industry_df.reset_index(inplace=True)
        industry_df.rename(columns={"index": "Industry Exposure"}, inplace=True)
        industry_df.set_index(["Industry Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building industry exposure dataframe\n\n" + str(
                                      ex))
    try:
        # country
        country_df = exposure_calc_df.loc[exposure_calc_df.index.str.contains("Country")]
        country_df.reset_index(inplace=True)
        country_df.rename(columns={"index":"Country Exposure"},inplace=True)
        country_df["Country Exposure"].replace(
            {"Country_": ""}, regex=True, inplace=True
        )
        country_df["Country Exposure"].replace(
            {"_exposure": ""}, regex=True, inplace=True
        )
        total_df = pd.DataFrame(country_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=country_df.columns[1:], index=["Total"])
        country_df.set_index(["Country Exposure"], inplace=True)
        country_df = pd.concat([country_df, total_df],axis=0)
        country_df.reset_index(inplace=True)
        country_df.rename(columns={"index": "Country Exposure"}, inplace=True)
        country_df.set_index(["Country Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building country exposure dataframe\n\n" + str(
                                      ex))
    try:
        # market cap
        mktcap_df = exposure_calc_df.loc[exposure_calc_df.index.str.contains("MarketCap")]
        mktcap_df.reset_index(inplace=True)
        mktcap_df.rename(columns={"index":"Market Cap Exposure"},inplace=True)
        mktcap_df["Market Cap Exposure"].replace(
            {"MarketCap_Group_ ": ""}, regex=True, inplace=True
        )
        mktcap_df["Market Cap Exposure"].replace(
            {"_exposure": ""}, regex=True, inplace=True
        )
        total_df = pd.DataFrame(mktcap_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=mktcap_df.columns[1:], index=["Total"])
        mktcap_df.set_index(["Market Cap Exposure"], inplace=True)
        mktcap_df = pd.concat([mktcap_df, total_df],axis=0)
        mktcap_df.reset_index(inplace=True)
        mktcap_df.rename(columns={"index": "Market Cap Exposure"}, inplace=True)
        mktcap_df.set_index(["Market Cap Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building market cap/total exposure dataframe\n\n" + str(
                                      ex))
    try:
        # by analyst
        analyst_df = exposure_calc_df.loc[exposure_calc_df.index.str.contains("Analyst")]
        analyst_df.reset_index(inplace=True)
        indexname= "Analyst Exposure"
        analyst_df.rename(columns={"index":indexname},inplace=True)
        analyst_df[indexname].replace( {"Analyst_ ": ""}, regex=True, inplace=True )
        analyst_df[indexname].replace( {"_exposure": ""}, regex=True, inplace=True )
        total_df = pd.DataFrame(analyst_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=analyst_df.columns[1:], index=["Total"])
        analyst_df.set_index([indexname], inplace=True)
        analyst_df = pd.concat([analyst_df, total_df],axis=0)
        analyst_df.reset_index(inplace=True)
        analyst_df.rename(columns={"index": indexname}, inplace=True)
        analyst_df.set_index([indexname], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building analyst exposure dataframe\n\n" + str(
                                      ex))

    try:
        # by asset type
        assettype_df = exposure_calc_df.loc[exposure_calc_df.index.str.contains("Type")]
        assettype_df.reset_index(inplace=True)
        indexname= "Asset Type Exposure"
        assettype_df.rename(columns={"index":indexname},inplace=True)
        assettype_df[indexname].replace( {"Type_": ""}, regex=True, inplace=True )
        assettype_df[indexname].replace( {"_exposure": ""}, regex=True, inplace=True )
        total_df = pd.DataFrame(assettype_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=assettype_df.columns[1:], index=["Total"])
        assettype_df.set_index([indexname], inplace=True)
        assettype_df = pd.concat([assettype_df, total_df],axis=0)
        assettype_df.reset_index(inplace=True)
        assettype_df.rename(columns={"index": indexname}, inplace=True)
        assettype_df.set_index([indexname], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building asset type exposure dataframe\n\n" + str(
                                      ex))
    finally:
        return strat_df, sector_df, industry_df, country_df, mktcap_df, analyst_df,assettype_df


def filter_beta_adj_exposure_calc(
    filter: Dict,
    position: pd.DataFrame,
    factor_betas: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    strat_df = None
    sector_df = None
    industry_df = None
    country_df = None
    mktcap_df = None
    analyst_df = None
    assettype_df = None
    try:
        firm_NAV = AUM_dict[fund_grouping]
        eq_factor=factor_betas.columns[1] # the equity factor has been put in the first coluimns of factors
        # add BetaExposure to positions
        #position.rename(columns={' BetaExposure':'Exposure'}, inplace=True)
        position.drop([c for c in position.columns if 'beta exposure' in c.lower()],axis=1, inplace=True)  # remove pre existing betaexposure
        equity_mkt_beta = factor_betas[["ID", eq_factor]]
        position = pd.merge(position, equity_mkt_beta, left_on='VaRTicker', right_on = 'ID').drop('ID', axis=1)
        position['BetaExposure'] = position['Exposure']*position[eq_factor]

        filter_list = list(filter.keys())
        exposure_calc_dict = {}
        for filter_item in filter_list:
            position_grouped = position.groupby([filter_item,'VaRTicker'])
            aggExpo_df = position_grouped['BetaExposure'].sum().reset_index().drop(columns='VaRTicker') # XM: Aggregates by VaRTicker
            aggExpo_df['longExpo']=aggExpo_df['BetaExposure'].apply(lambda x: x if x>0 else 0)
            aggExpo_df['shortExpo']=aggExpo_df['BetaExposure'].apply(lambda x: x if x<0 else 0)
            aggExpo_df = aggExpo_df.drop(columns='BetaExposure').groupby(filter_item).sum()
            for name, group in aggExpo_df.iterrows():

                long_exposure_calc = group['longExpo']
                short_exposure_calc = group['shortExpo']
                gross_exposure_calc = long_exposure_calc + abs(short_exposure_calc)
                net_exposure_calc = long_exposure_calc + short_exposure_calc
                exposure_calc_dict[f"{filter_item}_{name}"] = [
                    long_exposure_calc / firm_NAV,
                    short_exposure_calc / firm_NAV,
                    gross_exposure_calc / firm_NAV,
                    net_exposure_calc / firm_NAV,
                ]
        beta_adj_exposure_calc_df = pd.DataFrame(
            exposure_calc_dict,
            index=[
                "Long",
                "Short",
                "Gross",
                "Net",
            ],
        ).T
        beta_adj_exposure_calc_df = pd.concat([beta_adj_exposure_calc_df], axis=1)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating beta exposure dataframe\n\n" + str(
                                      ex))
    try:
        # strat
        if fund_grouping == "Firm":
            strat_df = beta_adj_exposure_calc_df.loc[beta_adj_exposure_calc_df.index.str.contains("Strat")]
            strat_df.reset_index(inplace=True)
            strat_df.rename(columns={"index": "Strategy Beta Exposure"}, inplace=True)
            strat_df["Strategy Beta Exposure"].replace(
                {"Strategy_": ""}, regex=True, inplace=True
            )
            total_df = pd.DataFrame(strat_df.iloc[:, 1:].sum(axis=0).values[None, :],
                                    columns=strat_df.columns[1:], index=["Total"])
            strat_df.set_index(["Strategy Beta Exposure"], inplace=True)
            strat_df = pd.concat([strat_df, total_df], axis=0)
            strat_df.reset_index(inplace=True)
            strat_df.rename(columns={"index": "Strategy Beta Exposure"}, inplace=True)
            strat_df.set_index(["Strategy Beta Exposure"], inplace=True)
        else:
            strat_df = pd.DataFrame()
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building beta strat exposure dataframe\n\n" + str(
                                      ex))
    try:
        # sector
        sector_df = beta_adj_exposure_calc_df.loc[
            beta_adj_exposure_calc_df.index.str.contains("Sector")
        ]
        sector_df.reset_index(inplace=True)
        sector_df.rename(columns={"index":"Sector Beta Exposure"},inplace=True)
        sector_df["Sector Beta Exposure"].replace(
            {"Sector_": ""}, regex=True, inplace=True
        )
        total_df = pd.DataFrame(sector_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=sector_df.columns[1:], index=["Total"])
        sector_df.set_index(["Sector Beta Exposure"], inplace=True)
        sector_df = pd.concat([sector_df, total_df],axis=0)
        sector_df.reset_index(inplace=True)
        sector_df.rename(columns={"index": "Sector Beta Exposure"}, inplace=True)
        sector_df.set_index(["Sector Beta Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building beta sector exposure dataframe\n\n" + str(
                                      ex))
    try:
        # industry
        industry_df = beta_adj_exposure_calc_df.loc[
            beta_adj_exposure_calc_df.index.str.contains("Industry")
        ]
        industry_df.reset_index(inplace=True)
        industry_df.rename(columns={"index":"Industry Beta Exposure"},inplace=True)
        industry_df["Industry Beta Exposure"].replace(
            {"Industry_": ""}, regex=True, inplace=True
        )
        total_df = pd.DataFrame(industry_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=industry_df.columns[1:], index=["Total"])
        industry_df.set_index(["Industry Beta Exposure"], inplace=True)
        industry_df = pd.concat([industry_df, total_df],axis=0)
        industry_df.reset_index(inplace=True)
        industry_df.rename(columns={"index": "Industry Beta Exposure"}, inplace=True)
        industry_df.set_index(["Industry Beta Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building beta industry exposure dataframe\n\n" + str(
                                      ex))
    try:
        # country
        country_df = beta_adj_exposure_calc_df.loc[
            beta_adj_exposure_calc_df.index.str.contains("Country")
        ]
        country_df.reset_index(inplace=True)
        country_df.rename(columns={"index":"Country Beta Exposure"},inplace=True)
        country_df["Country Beta Exposure"].replace(
            {"Country_": ""}, regex=True, inplace=True
        )
        total_df = pd.DataFrame(country_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=country_df.columns[1:], index=["Total"])
        country_df.set_index(["Country Beta Exposure"], inplace=True)
        country_df = pd.concat([country_df, total_df],axis=0)
        country_df.reset_index(inplace=True)
        country_df.rename(columns={"index": "Country Beta Exposure"}, inplace=True)
        country_df.set_index(["Country Beta Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building beta country exposure dataframe\n\n" + str(
                                      ex))
    try:
        # market cap
        mktcap_df = beta_adj_exposure_calc_df.loc[
            beta_adj_exposure_calc_df.index.str.contains("MarketCap")
        ]
        mktcap_df.reset_index(inplace=True)
        mktcap_df.rename(columns={"index":"Market Cap Beta Exposure"},inplace=True)
        mktcap_df["Market Cap Beta Exposure"].replace(
            {"MarketCap_Group_ ": ""}, regex=True, inplace=True
        )
        total_df = pd.DataFrame(mktcap_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=mktcap_df.columns[1:], index=["Total"])
        mktcap_df.set_index(["Market Cap Beta Exposure"], inplace=True)
        mktcap_df = pd.concat([mktcap_df, total_df],axis=0)
        mktcap_df.reset_index(inplace=True)
        mktcap_df.rename(columns={"index": "Market Cap Beta Exposure"}, inplace=True)
        mktcap_df.set_index(["Market Cap Beta Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building market cap beta exposure dataframe\n\n" + str(
                                      ex))
    try:
        # by analyst
        analyst_df = beta_adj_exposure_calc_df.loc[beta_adj_exposure_calc_df.index.str.contains("Analyst")]
        analyst_df.reset_index(inplace=True)
        indexname= "Analyst Beta Exposure"
        analyst_df.rename(columns={"index":indexname},inplace=True)
        analyst_df[indexname].replace( {"Analyst_ ": ""}, regex=True, inplace=True )
        analyst_df[indexname].replace( {"_exposure": ""}, regex=True, inplace=True )
        total_df = pd.DataFrame(analyst_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=analyst_df.columns[1:], index=["Total"])
        analyst_df.set_index([indexname], inplace=True)
        analyst_df = pd.concat([analyst_df, total_df],axis=0)
        analyst_df.reset_index(inplace=True)
        analyst_df.rename(columns={"index": indexname}, inplace=True)
        analyst_df.set_index([indexname], inplace=True)

        # by asset type
        assettype_df = beta_adj_exposure_calc_df.loc[beta_adj_exposure_calc_df.index.str.contains("Type")]
        assettype_df.reset_index(inplace=True)
        indexname= "Asset Type Beta Exposure"
        assettype_df.rename(columns={"index":indexname},inplace=True)
        assettype_df[indexname].replace( {"Type_": ""}, regex=True, inplace=True )
        assettype_df[indexname].replace( {"_exposure": ""}, regex=True, inplace=True )
        total_df = pd.DataFrame(assettype_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=assettype_df.columns[1:], index=["Total"])
        assettype_df.set_index([indexname], inplace=True)
        assettype_df = pd.concat([assettype_df, total_df],axis=0)
        assettype_df.reset_index(inplace=True)
        assettype_df.rename(columns={"index": indexname}, inplace=True)
        assettype_df.set_index([indexname], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building beta industry exposure dataframe\n\n" + str(
                                      ex))
    finally:
        return strat_df, sector_df, industry_df, country_df, mktcap_df, analyst_df,assettype_df


def notional_exposure_calc(
    filter: Dict,
    position: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    firm_NAV = AUM_dict[fund_grouping]
    filter_list = list(filter.keys())
    exposure_calc_dict = {}
    sector_df = None
    try:
        #create column Notional Exposure
        #position.rename(columns={' NotionalExposure':'NotionalExposure'}, inplace=True)  # case of 1623 Capital: data alreadin the input
        position['OptionDir'] = position.apply(lambda x: -1 if 'p' in x['PutCall'].lower() else 1, axis=1)
        position['NotionalExposure'] = position['Quantity'].astype(float)*position['FXRate']*position['UndlPrice']*position['PX_POS_MULT_FACTOR']*position['OptionDir']

        for filter_item in filter_list:
            position_grouped = position.groupby([filter_item])
            for name, group in position_grouped:
                if isinstance(name, tuple):
                    name = name[0]
                long_exposure = group.loc[group["NotionalExposure"] > 0]
                short_exposure = group.loc[group["NotionalExposure"] < 0]
                # aggregate long exposures with same RFID;
                aggregations = {
                    "TradeDate": "first",
                    FUND_NAME_ALIAS: "first",
                    "VaRTicker": "first",
                    "NotionalExposure": "sum",
                }
                long_exposure_tmp = (
                    long_exposure.groupby(["RFID"]).agg(aggregations).reset_index()
                )
                # aggregate short exposures withsame RFID
                short_exposure_tmp = (
                    short_exposure.groupby(["RFID"]).agg(aggregations).reset_index()
                )
                long_exposure_calc = long_exposure_tmp["NotionalExposure"].sum()
                short_exposure_calc = short_exposure_tmp["NotionalExposure"].sum()
                gross_exposure_calc = long_exposure_calc + abs(short_exposure_calc)
                net_exposure_calc = long_exposure_calc + short_exposure_calc
                exposure_calc_dict[f"{filter_item}_{name}"] = [
                    long_exposure_calc / firm_NAV,
                    short_exposure_calc / firm_NAV,
                    gross_exposure_calc / firm_NAV,
                    net_exposure_calc / firm_NAV,
                ]
        notional_calc_df = pd.DataFrame(
            exposure_calc_dict,
            index=[
                "Long",
                "Short",
                "Gross",
                "Net",
            ],
        ).T
        notional_calc_df = pd.concat([notional_calc_df], axis=1)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating notional calculate exposure dataframe\n\n" + str(
                                      ex))
    try:
        # sector
        sector_df = notional_calc_df.loc[
            notional_calc_df.index.str.contains("Sector")
        ]
        sector_df.reset_index(inplace=True)
        sector_df.rename(columns={"index":"Notional Exposure"},inplace=True)
        sector_df["Notional Exposure"].replace(
            {"Sector_": ""}, regex=True, inplace=True
        )
        total_df = pd.DataFrame(sector_df.iloc[:,1:].sum(axis=0).values[None,:],
                                columns=sector_df.columns[1:], index=["Total"])
        sector_df.set_index(["Notional Exposure"], inplace=True)
        sector_df = pd.concat([sector_df, total_df],axis=0)
        sector_df.reset_index(inplace=True)
        sector_df.rename(columns={"index": "Notional Exposure"}, inplace=True)
        sector_df.set_index(["Notional Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during building notional sector exposure dataframe\n\n" + str(
                                      ex))
    finally:
        return sector_df
# industry_df, country_df, mktcap_df


def calculate_short_exposure(equity_mkt_beta, short_exposure_tmp) -> float:
    if short_exposure_tmp.empty:
        return 0
    short_exposure_calc = None
    try:
        unique_tickers = list(short_exposure_tmp["VaRTicker"].unique())
        equity_mkt_beta_group = equity_mkt_beta.loc[
            equity_mkt_beta["ID"].isin(unique_tickers)
        ]
        equity_mkt_beta_group = equity_mkt_beta_group["SPX Index"]
        short_exposure_tmp["beta_adj_exposure"] = (
            equity_mkt_beta_group.values * short_exposure_tmp["Exposure"]
        )
        short_exposure_calc = short_exposure_tmp["beta_adj_exposure"].sum()
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating short exposure dataframe\n\n" + str(
                                      ex))
    finally:
        return short_exposure_calc


def calculate_beta_adjusted_exposure(equity_mkt_beta, exposure_table) -> float:
    """doscstring goes here..."""
    if exposure_table.empty:
        return 0
    return_value = None
    try:
        return_data = exposure_table.reset_index().merge(
            equity_mkt_beta.reset_index().rename(columns={"ID": "VaRTicker"})[
                ["VaRTicker", "SPX Index"]
            ],
            on="VaRTicker",
            how="inner",
        )
        return_data["beta_adj_exposure"] = (
            return_data["Exposure"] * return_data["SPX Index"]
        )
        return_value = return_data["beta_adj_exposure"].sum()
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating beta adjusted exposure return value\n\n" + str(
                                      ex))
    finally:
        return return_value


def liquidity(
    filter: Dict,
    position: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    exposure_calc_df =None
    try:
        firm_NAV = AUM_dict[fund_grouping]
        filter_list = list(filter.keys())
        bucketNames = ['<1','<2','<5','<10','10+','unknown']
        exposure_calc_dict = dict(zip(bucketNames,[0]*len(bucketNames)))
        position['LiqBucket']=position['DaysLiquid'].apply(set_liq_buckets,args=[bucketNames])
        filter_item = 'LiqBucket'
        #for filter_item in filter_list:
        position_grouped = position.groupby([filter_item])
        for name, group in position_grouped:
            if isinstance(name, tuple):
                name = name[0]
            long_exposure = group.loc[group["Exposure"] > 0]
            short_exposure = group.loc[group["Exposure"] < 0]
            long_exposure_calc = long_exposure["Exposure"].sum()
            short_exposure_calc = short_exposure["Exposure"].sum()
            gross_exposure_calc = long_exposure_calc + abs(short_exposure_calc)
            exposure_calc_dict[f"{name}"] = [
                long_exposure_calc / firm_NAV,
                short_exposure_calc / firm_NAV,
                gross_exposure_calc / firm_NAV,
            ]
        exposure_calc_df = pd.DataFrame(
            exposure_calc_dict,
            index=[
                "Long",
                "Short",
                "Gross",
            ],
        ).T
        exposure_calc_df['%Liquid'] = exposure_calc_df['Gross'].apply(np.cumsum)/exposure_calc_df['Gross'].sum()
        exposure_calc_df = pd.concat([exposure_calc_df], axis=1)
        # add total
        total_df = pd.DataFrame(np.array([exposure_calc_df.sum(axis=0).values]),columns=exposure_calc_df.columns, index=["Total"])
        exposure_calc_df = pd.concat([exposure_calc_df, total_df],axis=0)
        exposure_calc_df.index.name = "Liquidity"
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating liquidity exposure dataframe\n\n" + str(
                                      ex))
    finally:
        return exposure_calc_df


def set_liq_buckets(x,bucketNames):
    try:
        if isinstance(x,str):
            try: # try to get the numerical value
                x = float(x)
            except:
                return bucketNames[5]
            x= 0
            # '1900' in x:  #manage wrong input format : date like '1/0/1900'  instead of 1
            # x = float(x.split('/')[0])
        if x<1:
            return bucketNames[0]
        elif x>=1 and x<2:
            return bucketNames[1]
        elif x>=2 and x<5:
            return bucketNames[2]
        elif x>=5 and x<10:
            return bucketNames[3]
        elif x>=10:
            return bucketNames[4]
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during setting liquidity buckets\n\n" + str(
                                      ex))


def filter_options_delta_adj_exposure(
    position: pd.DataFrame, fund_grouping: str
) -> pd.DataFrame:
    options_exposure_calc_dict = {}
    options_exposure_calc_df = None
    try:
        position_grouped = position.groupby(FUND_NAME_ALIAS)
        for strat_name, strat_group in position_grouped:
            if (fund_grouping.lower() == strat_name.lower()) or (fund_grouping == "Firm"):
                expiry_grouped = strat_group.groupby(["Expiry"])
                for expiry_date, expiry_group in expiry_grouped:
                    if isinstance(expiry_date, tuple):
                        expiry_date = expiry_date[0]
                    position_option = expiry_group.loc[
                        expiry_group["SECURITY_TYP"].str.contains(
                            "|".join(["call", "option", "put"]),
                            na=False,
                            case=False,
                        )
                    ]
                    if not position_option.empty:
                        long_call_exposure = expiry_group.loc[
                            (expiry_group["Quantity"].astype(float) > 0)
                            & (
                                expiry_group["PutCall"].str.contains(
                                    "call", na=False, case=False
                                )
                            )
                        ]
                        short_call_exposure = expiry_group.loc[
                            (expiry_group["Quantity"].astype(float) < 0)
                            & (
                                expiry_group["PutCall"].str.contains(
                                    "call", na=False, case=False
                                )
                            )
                        ]
                        long_put_exposure = expiry_group.loc[
                            (expiry_group["Quantity"].astype(float) > 0)
                            & (
                                expiry_group["PutCall"].str.contains(
                                    "put", na=False, case=False
                                )
                            )
                        ]
                        short_put_exposure = expiry_group.loc[
                            (expiry_group["Quantity"].astype(float) < 0)
                            & (
                                expiry_group["PutCall"].str.contains(
                                    "put", na=False, case=False
                                )
                            )
                        ]
                        long_call_exposure_calc = long_call_exposure["Exposure"].sum()
                        short_call_exposure_calc = short_call_exposure["Exposure"].sum()
                        long_put_exposure_calc = long_put_exposure["Exposure"].sum()
                        short_put_exposure_calc = short_put_exposure["Exposure"].sum()

                        options_exposure_calc_dict[
                            f"{strat_name}_{expiry_date}_options_exposure"
                        ] = [
                            expiry_date,
                            long_call_exposure_calc,
                            short_call_exposure_calc,
                            long_put_exposure_calc,
                            short_put_exposure_calc,
                        ]

        options_exposure_calc_df = pd.DataFrame(
            options_exposure_calc_dict,
            index=[
                "Option Exposure",
                "Long Calls",
                "Short Calls",
                "Long Puts",
                "Short Puts",
            ],
        ).T
        options_exposure_calc_df["Option Exposure"] = pd.to_datetime(
            options_exposure_calc_df["Option Exposure"]
        ).dt.strftime("%Y-%m-%d")
        options_exposure_calc_df.reset_index(inplace=True, drop=True)
        options_exposure_calc_df.set_index(["Option Exposure"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating options exposure dataframe\n\n" + str(
                                      ex))
    finally:
        return options_exposure_calc_df.sort_index()


def filter_options_delta_unadj_exposure(
    position: pd.DataFrame, fund_grouping: str
) -> pd.DataFrame:
    options_exposure_delta1_calc_dict = {}
    options_exposure_delta1_calc_df = None
    try:
        position["delta_1_exposure"] = (1 / position["Delta"]) * position["Exposure"]
        position_grouped = position.groupby(FUND_NAME_ALIAS)
        for strat_name, strat_group in position_grouped:
            if (fund_grouping.lower() == strat_name.lower()) or (fund_grouping == "Firm"):
                expiry_grouped = strat_group.groupby(["Expiry"])
                for expiry_date, expiry_group in expiry_grouped:
                    if isinstance(expiry_date, tuple):
                        expiry_date = expiry_date[0]
                    position_option = expiry_group.loc[
                        expiry_group["SECURITY_TYP"].str.contains(
                            "|".join(["call", "option", "put"]),
                            na=False,
                            case=False,
                        )
                    ]
                    if not position_option.empty:
                        long_call_exposure = expiry_group.loc[
                            (expiry_group["Quantity"].astype(float) > 0)
                            & (
                                expiry_group["PutCall"].str.contains(
                                    "call", na=False, case=False
                                )
                            )
                        ]
                        short_call_exposure = expiry_group.loc[
                            (expiry_group["Quantity"].astype(float) < 0)
                            & (
                                expiry_group["PutCall"].str.contains(
                                    "call", na=False, case=False
                                )
                            )
                        ]
                        long_put_exposure = expiry_group.loc[
                            (expiry_group["Quantity"].astype(float) > 0)
                            & (
                                expiry_group["PutCall"].str.contains(
                                    "put", na=False, case=False
                                )
                            )
                        ]
                        short_put_exposure = expiry_group.loc[
                            (expiry_group["Quantity"].astype(float) < 0)
                            & (
                                expiry_group["PutCall"].str.contains(
                                    "put", na=False, case=False
                                )
                            )
                        ]
                        long_call_exposure_calc = long_call_exposure["delta_1_exposure"].sum()
                        short_call_exposure_calc = short_call_exposure["delta_1_exposure"].sum()
                        long_put_exposure_calc = long_put_exposure["delta_1_exposure"].sum()
                        short_put_exposure_calc = short_put_exposure["delta_1_exposure"].sum()
                        options_exposure_delta1_calc_dict[
                            f"{strat_name}_{expiry_date}_delta1_options_exposure"
                        ] = [
                            expiry_date,
                            long_call_exposure_calc,
                            short_call_exposure_calc,
                            long_put_exposure_calc,
                            short_put_exposure_calc,
                        ]
                options_exposure_delta1_calc_df = pd.DataFrame(
                    options_exposure_delta1_calc_dict,
                    index=[
                        "Option Notional",
                        "Long Calls",
                        "Short Calls",
                        "Long Puts",
                        "Short Puts",
                    ],
                ).T
                options_exposure_delta1_calc_df["Option Notional"] = pd.to_datetime(
                    options_exposure_delta1_calc_df["Option Notional"]
                ).dt.strftime("%Y-%m-%d")
                options_exposure_delta1_calc_df.reset_index(inplace=True, drop=True)
                options_exposure_delta1_calc_df.set_index(["Option Notional"], inplace=True)
                break
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating options exposure delta dataframe\n\n" + str(
                                      ex))
    finally:
        return options_exposure_delta1_calc_df.sort_index()


def filter_options_delta( position: pd.DataFrame,AUM_dict: Dict, fund_grouping: str) -> pd.DataFrame:
    options_pos_dict = {}
    options_pos_df = None
    try:
        firm_NAV = AUM_dict[fund_grouping]
        # position["delta_1_exposure"] = (1 / position["Delta"]) * position["Exposure"]
        options_positions = position.loc[position["SECURITY_TYP"].str.lower().str.contains("|".join(["call", "option", "put"])),:]
        position_grouped = options_positions.groupby(FUND_NAME_ALIAS)
        for strat_name, strat_group in position_grouped:
            if (fund_grouping.lower() == strat_name.lower()) or (fund_grouping == "Firm"):
                fund_positions_grp = strat_group.groupby(["Description"])
                for option_desc, option_pos_grp in fund_positions_grp:
                    cost = option_pos_grp["Cost"].sum()
                    mv  = option_pos_grp["MarketValue"].sum()
                    pnl  = option_pos_grp["DailyPL"].sum()
                    exp  = option_pos_grp["Exposure"].sum()/firm_NAV
                    delta  = option_pos_grp["Delta"].mean()
                    gamma  = (option_pos_grp["Gamma$"]*option_pos_grp["Quantity"]*option_pos_grp["PX_POS_MULT_FACTOR"]*option_pos_grp["FXRate"]*option_pos_grp["UndlPrice"]**2/10000).sum()
                    vega  = (option_pos_grp["Vega"]*option_pos_grp["Quantity"]*option_pos_grp["PX_POS_MULT_FACTOR"]*option_pos_grp["FXRate"]).sum()
                    theta  = (option_pos_grp["Theta"]*option_pos_grp["Quantity"]*option_pos_grp["PX_POS_MULT_FACTOR"]*option_pos_grp["FXRate"]).sum()

                    options_pos_dict[ f"{option_desc}_option" ] = [ option_desc[0], cost, mv, pnl,exp,  delta, gamma, vega, theta]
                options_pos_df = pd.DataFrame(
                    options_pos_dict,
                    index=['Position','Cost','MV', 'P&L', 'Exposure', 'Delta', 'Gamma 1%', 'Vega 1%', 'Theta 1D'],
                    ).T

                break
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating options delta pos dataframe\n\n" + str(
                                      ex))
    finally:
        return options_pos_df


def filter_options_premium(position: pd.DataFrame, fund_grouping: str) -> pd.DataFrame:
    options_premium_dict = {}
    options_premium_df = None
    try:
        # position["Quantity"].replace(r"[$\+\,\(\)]", "", regex=True, inplace=True)
        position["premium"] = (position["Quantity"].astype(float) * position["MarketPrice"])*(  position["PX_POS_MULT_FACTOR"] if 'PX_POS_MULT_FACTOR' in position.columns else 1)
        position_grouped = position.groupby(FUND_NAME_ALIAS)
        for strat_name, strat_group in position_grouped:
            if (fund_grouping.lower() == strat_name.lower()) or (fund_grouping == "Firm"):
                expiry_grouped = strat_group.groupby(["Expiry"])
                for expiry_date, expiry_group in expiry_grouped:
                    if isinstance(expiry_date, tuple):
                        expiry_date = expiry_date[0]

                    position_option = expiry_group.loc[
                        expiry_group["SECURITY_TYP"].str.contains(
                            "|".join(["call", "option", "put"]),
                            na=False,
                            case=False,
                        )
                    ]
                    if not position_option.empty:
                        call_exposure = expiry_group.loc[
                            (
                                expiry_group["PutCall"].str.contains(
                                    "call", na=False, case=False
                                )
                            )
                        ]
                        call_exposure["intrinsic_value"] = np.where(
                            call_exposure["UndlPrice"].values
                            - call_exposure["Strike"].values
                            < 0,
                            0,
                            (call_exposure["UndlPrice"].values
                            - call_exposure["Strike"].values) *call_exposure["Quantity"].astype(float)*call_exposure["PX_POS_MULT_FACTOR"],
                        )
                        put_exposure = expiry_group.loc[
                            (
                                expiry_group["PutCall"].str.contains(
                                    "put", na=False, case=False
                                )
                            )
                        ]
                        put_exposure["intrinsic_value"] = np.where(
                            put_exposure["Strike"].values - put_exposure["UndlPrice"].values
                            < 0,
                            0,
                            (put_exposure["Strike"].values
                            - put_exposure["UndlPrice"].values)*put_exposure["Quantity"].astype(float)*put_exposure["PX_POS_MULT_FACTOR"],
                        )
                        call_intrinsic_calc = call_exposure["intrinsic_value"].sum()
                        call_premium_calc = call_exposure["premium"].sum()-call_intrinsic_calc
                        put_intrinsic_calc = put_exposure["intrinsic_value"].sum()
                        put_premium_calc = put_exposure["premium"].sum()-put_intrinsic_calc

                        options_premium_dict[f"{strat_name}_{expiry_date}_options_premium"] = [
                            expiry_date,
                            call_premium_calc,
                            call_intrinsic_calc,
                            put_premium_calc,
                            put_intrinsic_calc,
                        ]
                options_premium_df = pd.DataFrame(
                    options_premium_dict,
                    index=[
                        "Premium",
                        "Call Premium",
                        "Call Intrinsic",
                        "Put Premium",
                        "Put Intrinsic",
                    ],
                ).T
                options_premium_df["Premium"] = pd.to_datetime( options_premium_df["Premium"]).dt.strftime("%Y-%m-%d")
                options_premium_df.reset_index(inplace=True, drop=True)
                options_premium_df.set_index(["Premium"], inplace=True)
                break
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating options premium dataframe\n\n" + str(
                                      ex))
    finally:
        return options_premium_df.sort_index()


def greek_sensitivities(position: pd.DataFrame, fund_grouping: str) -> pd.DataFrame:
    greek_sensitivities_dict = {}
    greek_sensitivities_df = None
    try:
        position_grouped = position.groupby(FUND_NAME_ALIAS)
        for strat_name, strat_group in position_grouped:
            if (fund_grouping.lower() == strat_name.lower()) or (fund_grouping == "Firm"):
                expiry_grouped = strat_group.groupby(["Expiry"])
                for expiry_date, expiry_group in expiry_grouped:
                    if isinstance(expiry_date, tuple):
                        expiry_date = expiry_date[0]
                    position_option = expiry_group.loc[
                        expiry_group["SECURITY_TYP"].str.contains(
                            "|".join(["call", "option", "put"]),
                            na=False,
                            case=False,
                        )
                    ]
                    if not position_option.empty:
                        position_option["Dollar Gamma 1%"] = (
                            position_option["Gamma$"].astype(float) * position_option["Quantity"].astype(float) * position_option["PX_POS_MULT_FACTOR"] * position_option["FXRate"] * position_option["UndlPrice"]**2 /10000
                        )
                        position_option["Dollar Vega 1%"] = (
                            position_option["Vega"] * position_option["Quantity"].astype(float) * position_option["PX_POS_MULT_FACTOR"] * position_option["FXRate"]
                        )
                        position_option["Dollar Theta 1D"] = (
                            position_option["Theta"]* position_option["Quantity"].astype(float) * position_option["PX_POS_MULT_FACTOR"] * position_option["FXRate"]
                        )
                        delta_exposure_calc = position_option["Exposure"].sum()
                        gamma_exposure_calc = position_option["Dollar Gamma 1%"].sum()
                        vega_exposure_calc = position_option["Dollar Vega 1%"].sum()
                        theta_exposure_calc = position_option["Dollar Theta 1D"].sum()
                        greek_sensitivities_dict[
                            f"{strat_name}_{expiry_date}_greek_sensitivities"
                        ] = [
                            expiry_date,
                            delta_exposure_calc,
                            gamma_exposure_calc,
                            vega_exposure_calc,
                            theta_exposure_calc,
                        ]
                greek_sensitivities_df = pd.DataFrame(
                    greek_sensitivities_dict,
                    index=[
                        "Greek Sensitivity",
                        "Delta Exposure",
                        "Dollar Gamma 1%",
                        "Dollar Vega 1%",
                        "Dollar Theta 1D",
                    ],
                ).T
                greek_sensitivities_df["Greek Sensitivity"] = pd.to_datetime(
                    greek_sensitivities_df["Greek Sensitivity"]
                ).dt.strftime("%Y-%m-%d")
                greek_sensitivities_df.reset_index(inplace=True, drop=True)
                greek_sensitivities_df.set_index(["Greek Sensitivity"], inplace=True)
                break
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating greek sensitivities dataframe\n\n" + str(
                                      ex))
    finally:
        return greek_sensitivities_df.sort_index()


def factor_decomp_filtered(
    position: pd.DataFrame,
    factor_betas: pd.DataFrame,
    factor_prices: pd.DataFrame,
    factor: pd.DataFrame,
    matrix_cov: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    macro_factor_decomp_df = None
    sector_factor_decomp_df = None
    try:
        firm_NAV = AUM_dict[fund_grouping]
        factor_vol = np.sqrt(
            pd.Series(np.diag(matrix_cov), index=factor_betas.drop("ID", axis=1).columns)
        )  # type: ignore
        macro_factor_df = factor.loc[factor["factor_group"] == "macro"][["Factor Names"]]
        sector_factor_df = factor.loc[factor["factor_group"] == "sector"][["Factor Names"]]
        date = factor_prices.index[-1]
        factor_decomp_dict = {}
        position_grouped = position.groupby(FUND_NAME_ALIAS)
        factor_vol_df = pd.DataFrame(
            factor_vol.values, index=factor_vol.index, columns=["FactorVol"]
        )
        for strat_name, strat_group in position_grouped:
            if isinstance(strat_name, tuple):
                strat_name = strat_name[0]
            if fund_grouping.lower() == strat_name.lower():
                temp = (
                    strat_group.groupby("VaRTicker").agg({"Exposure": "sum"}).reset_index()
                )
            elif fund_grouping == "Firm":
                temp = (
                    position.groupby("VaRTicker").agg({"Exposure": "sum"}).reset_index()
                )
            exposure = temp.set_index(temp.VaRTicker).Exposure.values
            # tmp["Exposure"].values
            fund_positions = temp["VaRTicker"].unique()
            fund_factor_betas = factor_betas.loc[
                factor_betas.ID.isin(fund_positions), :
            ].set_index("ID")

            # factor_betas_fund = factor_betas\
            #     .loc[
            #         factor_betas["VaRTicker"].isin(fund_positions)
            #     ]
            strat_factor_exp = exposure[:, None].T @ fund_factor_betas.values
            # @ factor_betas_fund.values[:, 1:]
            factor_decomp_dict[f"{strat_name}"] = strat_factor_exp[0, :]
            factor_decomp_df = pd.DataFrame(factor_decomp_dict, index=factor_vol.index)
            date_vector = pd.DataFrame(
                np.repeat(date, len(factor_decomp_df)),
                index=factor_decomp_df.index,
                columns=["date"],
            )
            factor_decomp_df = pd.concat(
                [date_vector, factor_decomp_df, factor_vol_df], axis=1
            )
            factor_decomp_df["FactorExp"] = (
                factor_decomp_df.iloc[:, 1:-1].sum(axis=1) / firm_NAV
            )
            factor_decomp_df.reset_index(inplace=True)
            factor_decomp_df.rename(columns={"factor": "FactorID"}, inplace=True)
            factor_decomp_df = pd.merge(
                factor_decomp_df,
                factor[["Factor Names"]],
                on=["FactorID"],
                how="left",
            )
            factor_decomp_df.set_index(["Factor Names"], inplace=True)
            factor_decomp_df['FactorRisk'] = factor_decomp_df['FactorVol']*factor_decomp_df['FactorExp'].abs()
            LOGGER.info(f"factor_decomp generated for strat {strat_name}")
            macro_factor_decomp_df = factor_decomp_df.loc[
                factor_decomp_df.index.isin(macro_factor_df["Factor Names"])
            ]
            macro_factor_decomp_df = macro_factor_decomp_df[["FactorExp", "FactorVol","FactorRisk"]]
            macro_factor_decomp_df.reset_index(inplace=True)
            macro_factor_decomp_df.rename(
                columns={"Factor Names": "Macro Sensitivities"}, inplace=True
            )
            macro_factor_decomp_df.set_index(["Macro Sensitivities"], inplace=True)

            sector_factor_decomp_df = factor_decomp_df.loc[
                factor_decomp_df.index.isin(sector_factor_df["Factor Names"])
            ]
            sector_factor_decomp_df = sector_factor_decomp_df[
                ["FactorExp", "FactorVol","FactorRisk"]
            ]
            sector_factor_decomp_df.reset_index(inplace=True)
            sector_factor_decomp_df.rename(
                columns={"Factor Names": "Sector Sensitivities"}, inplace=True
            )
            sector_factor_decomp_df.set_index(["Sector Sensitivities"], inplace=True)
            break

        # macro_factor_decomp_df = macro_factor_decomp_df.loc[factor_betas.drop("ID", axis=1).columns,:]
        # sector_factor_decomp_df = sector_factor_decomp_df.loc[factor_betas.drop("ID", axis=1).columns,:]
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating sector/macro factor decomp dataframe\n\n" + str(
                                      ex))
    finally:
        return macro_factor_decomp_df, sector_factor_decomp_df


def factor_decomp_by_factor_position(
    position: pd.DataFrame,
    factor_betas: pd.DataFrame,
    factor: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    risk_factor_exposure_top_N_list = None
    risk_factor_exposure_bottom_N_list = None
    try:
        firm_NAV = np.array([AUM_dict[fund_grouping]])
        # --------- aggregate exposure of positions and their beta
        # align factor index to columns of factors_betas and change index for Factor Names and columns of factor_beta for the same
        #--> This should not be done here : modifications of factor_beta are impacting the rest of the code elsewhere

        factor = factor.reindex(index=factor_betas.columns[1:])
        factor.reset_index(inplace=True)
        factor.rename(columns={"index": "FactorID"}, inplace=True)
        factor.set_index(["Factor Names"], inplace=True)
        factor_betas.columns = [factor_betas.columns[0]] + list(factor.index)

        # agg positions by exposure across fund strats
        position_agg_exposure = (
            position.groupby(
                [  "RFID",   ]
            )
            .agg(
                {
                    "TradeDate": "first",
                    FUND_NAME_ALIAS: "first",
                    "UnderlierName": "first",
                    "VaRTicker": "first",
                    "MarketValue": "sum",
                    "Exposure": "sum",
                }
            )
            .reset_index()
        )
        position_agg_exposure.rename(columns={"VaRTicker": "ID"}, inplace=True)

        factor_beta_exposure = pd.merge(
            factor_betas, position_agg_exposure, on=["ID"], how="inner"
        )
        # ------- loop through column by column
        risk_factor_exposure_top_N_list = []
        risk_factor_exposure_bottom_N_list = []
        for col in factor_beta_exposure.columns[1 : len(factor_betas.columns)]:
            risk_factor_exposure = pd.DataFrame(
                np.concatenate(
                    (
                        factor_beta_exposure["UnderlierName"].values[:, None],
                        (
                            factor_beta_exposure[col] * factor_beta_exposure["Exposure"]
                        ).values[:, None]
                        / firm_NAV[:, None],
                        factor_beta_exposure["Exposure"].values[:, None]
                        / firm_NAV[:, None],
                    ),
                    axis=1,
                ),
                columns=[f"{col} - Top 10", "Exposure", "FactorExp"],
                index=factor_beta_exposure.index,  # factor_betas.index,
            )

            # get the top 10
            risk_factor_exposure_sorted = risk_factor_exposure.sort_values(
                ["Exposure"], ascending=[False]
            )
            risk_factor_exposure_sorted_top_10 = risk_factor_exposure_sorted.iloc[:10, :]
            risk_factor_exposure_sorted_top_10.reset_index(inplace=True, drop=True)
            risk_factor_exposure_sorted_top_10.set_index([f"{col} - Top 10"], inplace=True)
            risk_factor_exposure_top_N_list.append(risk_factor_exposure_sorted_top_10)

            # get the Bottom 10
            risk_factor_exposure_sorted = risk_factor_exposure.sort_values(
                ["Exposure"], ascending=[True]
            )
            risk_factor_exposure_sorted_bottom_10 = risk_factor_exposure_sorted.iloc[:10, :]
            risk_factor_exposure_sorted_bottom_10.reset_index(inplace=True, drop=True)
            risk_factor_exposure_sorted_bottom_10.rename(
                columns={f"{col} - Top 10": f"{col} - Bottom 10"}, inplace=True
            )
            risk_factor_exposure_sorted_bottom_10.set_index(
                [f"{col} - Bottom 10"], inplace=True
            )
            risk_factor_exposure_bottom_N_list.append(risk_factor_exposure_sorted_bottom_10)
        LOGGER.info(
            "apply position agg data against factor betas to build the factor by "
            "factor top N risk contributors by position"
        )
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating rsk factor exposure top list\n\n" + str(
                                      ex))
    finally:
        return risk_factor_exposure_top_N_list, risk_factor_exposure_bottom_N_list


def beta_decomp_filtered(
    position: pd.DataFrame,
    factor_betas: pd.DataFrame,
    factor_prices: pd.DataFrame,
    factor: pd.DataFrame,
    matrix_cov: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    macro_factor_decomp_df = None
    sector_factor_decomp_df = None
    try:
        firm_NAV = AUM_dict[fund_grouping]
        factor_vol = np.sqrt(pd.Series(np.diag(matrix_cov), index=factor_betas.drop("ID", axis=1).columns))  # type: ignore
        macro_factor_df = factor.loc[factor["factor_group"] == "macro"][["Factor Names"]]
        sector_factor_df = factor.loc[factor["factor_group"] == "sector"][["Factor Names"]]
        date = factor_prices.index[-1]
        factor_decomp_dict = {}
        position_grouped = position.groupby(FUND_NAME_ALIAS)
        factor_vol_df = pd.DataFrame(
            factor_vol.values, index=factor_vol.index, columns=["FactorVol"]
        )
        for strat_name, strat_group in position_grouped:
            # sums up exposures per position --> to exposure
            if isinstance(strat_name, tuple):
                strat_name = strat_name[0]
            if fund_grouping.lower() == strat_name.lower():
                temp = (strat_group.groupby("VaRTicker").agg({"Exposure": "sum"}).reset_index())
            elif fund_grouping == "Firm":
                temp = (position.groupby("VaRTicker").agg({"Exposure": "sum"}).reset_index())
            exposure = temp.set_index(temp.VaRTicker).Exposure.values
            # tmp["Exposure"].values

            # calculate the decomposition of exposure per beta: factor_decomp_df
            fund_positions = temp["VaRTicker"].unique()
            fund_factor_betas = factor_betas.loc[factor_betas.ID.isin(fund_positions), :].set_index("ID")
            # factor_betas_fund = factor_betas\
            #     .loc[
            #         factor_betas["VaRTicker"].isin(fund_positions)
            #     ]
            strat_factor_exp = exposure[:, None].T @ fund_factor_betas.values
            # @ factor_betas_fund.values[:, 1:]
            factor_decomp_dict[f"{strat_name}"] = strat_factor_exp[0, :]
            factor_decomp_df = pd.DataFrame(factor_decomp_dict, index=factor_vol.index)


            date_vector = pd.DataFrame(
                np.repeat(date, len(factor_decomp_df)),
                index=factor_decomp_df.index,
                columns=["date"],
            )
            factor_decomp_df = pd.concat(
                [date_vector, factor_decomp_df, factor_vol_df], axis=1
            )
            factor_decomp_df["FactorExp"] = (
                factor_decomp_df.iloc[:, 1:-1].sum(axis=1) / firm_NAV
            )
            factor_decomp_df.reset_index(inplace=True)
            factor_decomp_df.rename(columns={"factor": "FactorID"}, inplace=True)
            factor_decomp_df.rename(columns={'index':'Factor Names'}, inplace=True)
            factor_decomp_df = pd.merge(
                factor_decomp_df,
                factor[["Factor Names"]],
                on=["FactorID"],
                how="left",
            )
            factor_decomp_df.set_index(["Factor Names"], inplace=True)
            factor_decomp_df['FactorRisk'] = factor_decomp_df['FactorVol']*factor_decomp_df['FactorExp'].abs()
            LOGGER.info(f"factor_decomp generated for strat {strat_name}")

            # filter factor_decomp_df for macro factors only
            macro_factor_decomp_df = factor_decomp_df.loc[
                factor_decomp_df.index.isin(macro_factor_df["Factor Names"])
            ]
            macro_factor_decomp_df = macro_factor_decomp_df[["FactorExp", "FactorVol","FactorRisk"]]
            macro_factor_decomp_df.reset_index(inplace=True)
            macro_factor_decomp_df.rename(
                columns={"Factor Names": "Macro Sensitivities"}, inplace=True
            )
            macro_factor_decomp_df.set_index(["Macro Sensitivities"], inplace=True)

            # filter factor_decomp_df for sector factors only
            sector_factor_decomp_df = factor_decomp_df.loc[
                factor_decomp_df.index.isin(sector_factor_df["Factor Names"])
            ]
            sector_factor_decomp_df = sector_factor_decomp_df[
                ["FactorExp", "FactorVol","FactorRisk"]
            ]
            sector_factor_decomp_df.reset_index(inplace=True)
            sector_factor_decomp_df.rename(
                columns={"Factor Names": "Sector Sensitivities"}, inplace=True
            )
            sector_factor_decomp_df.set_index(["Sector Sensitivities"], inplace=True)
            #break

        # macro_factor_decomp_df = macro_factor_decomp_df.loc[factor_betas.drop("ID", axis=1).columns,:]
        # sector_factor_decomp_df = sector_factor_decomp_df.loc[factor_betas.drop("ID", axis=1).columns,:]
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating macro/sector factor decomp dataframe\n\n" + str(
                                      ex))
    finally:
        return macro_factor_decomp_df, sector_factor_decomp_df


def beta_decomp_by_factor_position(
    position: pd.DataFrame,
    factor_betas: pd.DataFrame,
    factor: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    risk_factor_exposure_top_N_list = None
    risk_factor_exposure_bottom_N_list = None
    try:
        firm_NAV = np.array([AUM_dict[fund_grouping]])
        factor.reset_index(inplace=True)
        #factor.rename(columns={"index": "FactorID"}, inplace=True)
        factor.set_index(["Factor Names"], inplace=True)
        factor = factor.reindex(index=factor_betas.columns[1:])
        factor_betas.columns = [factor_betas.columns[0]] + list(factor.index)
        # agg positions by exposure across fund strats
        position_agg_exposure = (
            position.groupby(["RFID",])
            .agg(
                {
                    "TradeDate": "first",
                    FUND_NAME_ALIAS: "first",
                    "UnderlierName": "first",
                    "VaRTicker": "first",
                    "MarketValue": "sum",
                    "Exposure": "sum",
                }
            )
            .reset_index()
        )
        position_agg_exposure.rename(columns={"VaRTicker": "ID"}, inplace=True)
        factor_beta_exposure = pd.merge(
            factor_betas, position_agg_exposure, on=["ID"], how="inner"
        )
        # loop through column by column
        risk_factor_exposure_top_N_list = []
        risk_factor_exposure_bottom_N_list = []
        for col in factor_beta_exposure.columns[1 : len(factor_betas.columns)]:
            risk_factor_exposure = pd.DataFrame(
                np.concatenate(
                    (
                        factor_beta_exposure["UnderlierName"].values[:, None],
                        (
                            factor_beta_exposure[col] * factor_beta_exposure["Exposure"]
                        ).values[:, None]
                        / firm_NAV[:, None],
                        factor_beta_exposure["Exposure"].values[:, None]
                        / firm_NAV[:, None],
                    ),
                    axis=1,
                ),
                columns=[f"{col} - Top 10", "Exposure", "FactorExp"],
                index=factor_beta_exposure.index,  # factor_betas.index,
            )
            risk_factor_exposure_sorted = risk_factor_exposure.sort_values(["Exposure"], ascending=[False])
            risk_factor_exposure_sorted_top_10 = risk_factor_exposure_sorted.iloc[:10, :]
            risk_factor_exposure_sorted_top_10.reset_index(inplace=True, drop=True)
            risk_factor_exposure_sorted_top_10.set_index([f"{col} - Top 10"], inplace=True)
            risk_factor_exposure_top_N_list.append(risk_factor_exposure_sorted_top_10)

            risk_factor_exposure_sorted = risk_factor_exposure.sort_values(["Exposure"], ascending=[True])
            risk_factor_exposure_sorted_bottom_10 = risk_factor_exposure_sorted.iloc[:10, :]
            risk_factor_exposure_sorted_bottom_10.reset_index(inplace=True, drop=True)
            risk_factor_exposure_sorted_bottom_10.rename(
                columns={f"{col} - Top 10": f"{col} - Bottom 10"}, inplace=True
            )
            risk_factor_exposure_sorted_bottom_10.set_index(
                [f"{col} - Bottom 10"], inplace=True
            )
            risk_factor_exposure_bottom_N_list.append(risk_factor_exposure_sorted_bottom_10)
        LOGGER.info(
            "apply position agg data against factor betas to build the factor by "
            "factor top N risk contributors by position"
        )
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating beta risk factor exposure top list\n\n" + str(
                                      ex))
    return risk_factor_exposure_top_N_list, risk_factor_exposure_bottom_N_list



def factor_heat_map(
    position: pd.DataFrame,
    factor_betas: pd.DataFrame,
    factor: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    risk_factor_exposure_df = None
    try:
        firm_NAV = AUM_dict[fund_grouping]
        factor.reset_index(inplace=True)
        factor.set_index(["Factor Names"], inplace=True)
        factor = factor.reindex(index=factor_betas.columns[1:])
        factor_betas.columns = [factor_betas.columns[0]] + list(factor.index)
        # agg positions by exposure across fund strats
        position_agg_exposure = (
            position.groupby(
                [
                    "RFID",
                ]
            )
            .agg(
                {
                    "TradeDate": "first",
                    FUND_NAME_ALIAS: "first",
                    "UnderlierName": "first",
                    "VaRTicker": "first",
                    "MarketValue": "sum",
                    "Exposure": "sum",
                }
            )
            .reset_index()
        )
        position_agg_exposure.rename(columns={"VaRTicker": "ID"}, inplace=True)
        factor_beta_exposure = pd.merge(
            factor_betas, position_agg_exposure, on=["ID"], how="inner"
        )
        # loop through column by column
        risk_factor_exposure_df_list = []
        for col in factor_beta_exposure.columns[1 : len(factor_betas.columns)]:
            underlier_names = factor_beta_exposure["UnderlierName"]
            beta_exposures = (
                factor_beta_exposure[col] * factor_beta_exposure["Exposure"] / firm_NAV
            )
            exposures = factor_beta_exposure["Exposure"] / firm_NAV

            risk_factor_exposure = pd.DataFrame(
                {
                    "Position": underlier_names,
                    f"{col}": beta_exposures,
                    "Exposure": exposures,
                }
            )
            risk_factor_exposure_df_list.append(risk_factor_exposure)
        LOGGER.info(
            "apply position agg data against factor betas to build the factor by "
            "factor top N risk contributors by position"
        )
        risk_factor_exposure_df = pd.concat(risk_factor_exposure_df_list, axis=1)
        risk_factor_exposure_df = risk_factor_exposure_df.loc[
            :, ~risk_factor_exposure_df.columns.duplicated()
        ]
        risk_factor_exposure_df.rename(columns={"Equity": "Beta"}, inplace=True)
        risk_factor_exposure_df = risk_factor_exposure_df[
            [
                "Position",
                "Exposure",
            ]
            + [
                col
                for col in risk_factor_exposure_df.columns
                if col
                not in [
                       "Position",
                       "Exposure",
                ]
            ]
        ]
        risk_factor_exposure_df.reset_index(inplace=True, drop=True)
        risk_factor_exposure_df.set_index(["Position"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating beta risk factor heat map\n\n" + str(
                                      ex))
    finally:
        return risk_factor_exposure_df


def beta_heat_map(
    position: pd.DataFrame,
    factor_betas: pd.DataFrame,
    factor: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    risk_factor_exposure_df = None
    try:
        firm_NAV = AUM_dict[fund_grouping]
        # replace Bloomberg tickers for factors by factor names in factor_betas
        factor= factor.reset_index().set_index(["FactorID"]).reindex(index=factor_betas.columns[1:])
        factor_betas.columns = [factor_betas.columns[0]] + list(factor['Factor Names'])

        # agg positions by exposure across fund strats
        position_agg_exposure = (
            position.groupby(
                [
                    "RFID",
                ]
            )
            .agg(
                {
                    "TradeDate": "first",
                    FUND_NAME_ALIAS: "first",
                    "UnderlierName": "first",
                    "VaRTicker": "first",
                    "MarketValue": "sum",
                    "Exposure": "sum",
                }
            )
            .reset_index()
        )
        position_agg_exposure.rename(columns={"VaRTicker": "ID"}, inplace=True)
        factor_beta_exposure = pd.merge(factor_betas, position_agg_exposure, on=["ID"], how="inner")

        # loop through column by column to calculate Exposure% * beta
        risk_factor_exposure_df_list = []
        for col in factor_beta_exposure.columns[1 : len(factor_betas.columns)]:
            underlier_names = factor_beta_exposure["UnderlierName"]
            beta_exposures = (
                factor_beta_exposure[col] * factor_beta_exposure["Exposure"] / firm_NAV
            )
            exposures = factor_beta_exposure["Exposure"] / firm_NAV

            risk_factor_exposure = pd.DataFrame(
                {
                    "Position": underlier_names,
                    f"{col}": beta_exposures,
                    "Exposure": exposures,
                }
            )
            risk_factor_exposure_df_list.append(risk_factor_exposure)
        LOGGER.info(
            "apply position agg data against factor betas to build the factor by "
            "factor top N risk contributors by position"
        )
        risk_factor_exposure_df = pd.concat(risk_factor_exposure_df_list, axis=1)
        risk_factor_exposure_df = risk_factor_exposure_df.loc[
            :, ~risk_factor_exposure_df.columns.duplicated()
        ]
        risk_factor_exposure_df.rename(columns={"Equity": "Beta"}, inplace=True)
        risk_factor_exposure_df = risk_factor_exposure_df[
            [
                "Position",
                "Exposure",
            ]
            + [
                col
                for col in risk_factor_exposure_df.columns
                if col
                not in [
                       "Position",
                       "Exposure",
                ]
            ]
        ]
        risk_factor_exposure_df.reset_index(inplace=True, drop=True)
        risk_factor_exposure_df.set_index(["Position"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating beta heat map risk factor exposure\n\n" + str(
                                      ex))
    finally:
        return risk_factor_exposure_df


def stress_test_beta_price_vol_exposure_by_position(
    position: pd.DataFrame,
    factor_betas: pd.DataFrame,
    matrix_cov: pd.DataFrame,
    position_returns: pd.DataFrame,
    factor: pd.DataFrame,
    AUM_dict: Dict,
    fund_grouping: str,
) -> pd.DataFrame:
    position_breakdown = None
    position_summary = None
    try:
        firm_NAV = AUM_dict[fund_grouping]
        factor = factor.reindex(index=factor_betas.columns[1:])
        factor.reset_index(inplace=True)
        factor.rename(columns={"index": "Factor Names"}, inplace=True)
        factor.set_index(["Factor Names"], inplace=True)
        factor_betas.columns = [factor_betas.columns[0]] + list(factor.index)

        eq_factor = factor.loc['Equity','FactorID']
        # agg positions by exposure across fund strats
        price_shock_list = [-0.01, -0.1]

        position_non_option = position.loc[
            position["SECURITY_TYP"].str.contains(
                "|".join(NON_OPTION_TYPES),
                na=False,
                case=False,
            )
        ]
        position_option = position.loc[
            position["SECURITY_TYP"].str.contains(
                "|".join(OPTION_TYPES),
                na=False,
                case=False,
            )
        ]
        price_shock_df_list = []
        for price_shock in price_shock_list:
            combined_price_shock_list = []
            if not position_non_option.empty:
                position_non_option_brief = parse_non_option_position(
                    firm_NAV, position_non_option, price_shock
                )
                combined_price_shock_list.append(position_non_option_brief)
            if not position_option.empty:
                position_option_brief = parse_option_position(
                    firm_NAV, position_option, price_shock
                )
                combined_price_shock_list.append(position_option_brief)
            price_shock_df_list.append(pd.concat(combined_price_shock_list, axis=0))
        price_shock_df = pd.concat(price_shock_df_list, axis=1)
        price_shock_df = price_shock_df.loc[:, ~price_shock_df.columns.duplicated()]
        LOGGER.info("estimate RFID vol")
        position_cov = position_returns.cov()
        position_vols = pd.DataFrame(
            np.sqrt(pd.Series(np.diag(position_cov))).values,
            index=position_cov.index,
            columns=["stdev"],
        )
        position_vols.reset_index(inplace=True)
        position_vols.rename(columns={"index": "ID"}, inplace=True)
        price_shock_df.rename(columns={"VaRTicker": "ID"}, inplace=True)
        beta_spx = factor_betas[["ID", "Equity"]]
        price_shock_df = pd.merge(price_shock_df, beta_spx, on=["ID"], how="left")
        price_shock_df = pd.merge(price_shock_df, position_vols, on=["ID"], how="left")
        spx_vol = np.sqrt(matrix_cov.loc[matrix_cov.index == eq_factor][eq_factor])
        price_shock_df["Correl"] = (
            price_shock_df["Equity"].values * spx_vol.values
        ) / price_shock_df["stdev"].values
        price_shock_df.rename(
            columns={
                "UnderlierName": "Underlier",
                "Description": "Position",
                "Quantity": "Shares/Contracts",
                "Equity": "Beta",
                "stdev": "Volatility",
            },
            inplace=True,
        )
        price_shock_df["Exposure"] = price_shock_df["Exposure"] / firm_NAV
        price_shock_df = price_shock_df[
            [
                "Underlier",
                "Position",
                "Shares/Contracts",
                "Exposure",
                "Beta",
                "Correl",
                "Volatility",
            ]
            + [
                col
                for col in price_shock_df.columns
                if col
                not in [
                    "Underlier",
                    "Position",
                    "Shares/Contracts",
                    "Exposure",
                    "Beta",
                    "Correl",
                    "Volatility",
                    "ID",
                    "RFID",
                ]
            ]
        ]
        position_breakdown = price_shock_df
        position_breakdown.reset_index(inplace=True, drop=True)
        position_breakdown.set_index(["Underlier"], inplace=True)
        position_breakdown = position_breakdown.sort_values(["Exposure"], ascending=False)
        cols = [
            col
            for col in position_breakdown.columns
            if col
            not in [
                "UnderlierName",
                "Dollar Delta",
                "Dollar Gamma 1%",
                "Dollar Vega 1%",
                "Dollar Theta 1D",
            ]
        ]
        position_breakdown.reset_index(inplace=True)
        colNames = position_breakdown.columns[position_breakdown.columns.str.contains(pat='Dollar Delta')]
        if len(colNames) > 0:
            position_breakdown_agg = position_breakdown.groupby(
                [
                    "Position",
                ]
            ).agg(
                {
                    "Underlier": "sum",
                    "Shares/Contracts": "sum",
                    "Exposure": "sum",
                    "Beta": "first",
                    "Correl": "first",
                    "Volatility": "first",
                    "MarketValue": "sum",
                    "1% Shock $": "sum",
                    "1% Shock %": "sum",
                    "Dollar Delta": "sum",
                    "Dollar Gamma 1%": "sum",
                    "Dollar Vega 1%": "sum",
                    "Dollar Theta 1D": "sum",
                    "10% Shock $": "sum",
                    "10% Shock %": "sum",
                }
            )
        else:
            position_breakdown_agg = position_breakdown.groupby(
                [
                    "Position",
                ]
            ).agg(
                {
                    "Underlier": "sum",
                    "Shares/Contracts": "sum",
                    "Exposure": "sum",
                    "Beta": "first",
                    "Correl": "first",
                    "Volatility": "first",
                    "MarketValue": "sum",
                    "1% Shock $": "sum",
                    "1% Shock %": "sum",
                    "10% Shock $": "sum",
                    "10% Shock %": "sum",
                }
            )
        position_breakdown = position_breakdown_agg.copy()
        position_breakdown.reset_index(inplace=True)
        position_breakdown.set_index(["Underlier"], inplace=True)
        position_summary = position_breakdown[cols]
        position_summary.reset_index(inplace=True, drop=True)
        position_summary.set_index(["Position"], inplace=True)
        position_summary = position_summary.sort_values(["Exposure"], ascending=False)
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during calculating stress test position breakdown/summary dataframe\n\n" + str(
                                      ex))
    finally:
        return position_breakdown, position_summary


def parse_option_position(
    firm_NAV: float, position_option: pd.DataFrame, price_shock: float
):
    position_option_brief = None
    try:
        position_option["shock_underlying_price"] = position_option["UndlPrice"] * (
            1 + price_shock
        )
        position_option["shock_option_price"] = option_price(
            S=position_option["shock_underlying_price"],
            X=position_option["Strike"],
            T=position_option["MtyYears"],
            Vol=position_option["IVOL_TM"].astype(float),
            rf=RISK_FREE_RATE,
            type=position_option["PutCall"],
        )
        if ("PX_POS_MULT_FACTOR" in position_option.columns) and ("FXRate" in position_option.columns):
            position_option[f"{100*abs(price_shock):.0f}$ shock value"] = (
                position_option["shock_option_price"]
                * position_option["PX_POS_MULT_FACTOR"]
                * position_option["Quantity"].astype(float)
                * position_option["FXRate"]
            )
        else:
            position_option[f"{100*abs(price_shock):.0f}$ shock value"] = (
                position_option["shock_option_price"]
                * position_option["Quantity"].astype(float)
            )
        if ("PX_POS_MULT_FACTOR" in position_option.columns) and ("FXRate" in position_option.columns):
            position_option[f"{100*abs(price_shock):.0f}% Shock $"] = (
                position_option[f"{100*abs(price_shock):.0f}$ shock value"]
            ) - (
                position_option["MarketPrice"]
                * position_option["PX_POS_MULT_FACTOR"]
                * position_option["Quantity"].astype(float)
                * position_option["FXRate"]
            )
        else:
            position_option[f"{100*abs(price_shock):.0f}% Shock $"] = (
                position_option[f"{100*abs(price_shock):.0f}$ shock value"]
            ) - (
                position_option["MarketPrice"]
                * position_option["Quantity"].astype(float)
            )
        position_option[f"{100*abs(price_shock):.0f}% Shock %"] = position_option[
            f"{100*abs(price_shock):.0f}% Shock $"
        ].divide(firm_NAV)
        position_option["Dollar Delta"] = position_option["Exposure"]
        position_option["Dollar Gamma 1%"] = (
            position_option["Gamma$"].astype(float) * position_option["Exposure"]
        )
        position_option["Dollar Vega 1%"] = (
            position_option["Vega"] * position_option["Exposure"]
        )
        position_option["Dollar Theta 1D"] = (
            position_option["Theta"] * position_option["Exposure"]
        )
        position_option_brief = position_option[
            [
                "UnderlierName",
                "Description",
                "VaRTicker",
                "RFID",
                "Quantity",
                "Dollar Delta",
                "Dollar Gamma 1%",
                "Dollar Vega 1%",
                "Dollar Theta 1D",
                "MarketValue",
                "Exposure",
                f"{100*abs(price_shock):.0f}% Shock $",
                f"{100*abs(price_shock):.0f}% Shock %",
            ]
        ]
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during parsing positions options brief\n\n" + str(
                                      ex))
    finally:
        return position_option_brief


def parse_non_option_position(
    firm_NAV: float, position_non_option: pd.DataFrame, price_shock: float
):
    position_non_option_brief = None
    try:
        if ("PX_POS_MULT_FACTOR" in position_non_option.columns) and ("FXRate" in position_non_option.columns):
            position_non_option[f"{100*abs(price_shock):.0f}$ shock value"] = (
                position_non_option["Quantity"].astype(float)
                * position_non_option["FXRate"]
                * position_non_option["MarketPrice"]
                * position_non_option["PX_POS_MULT_FACTOR"]
                * (1 + price_shock)
            )
        else:
            position_non_option[f"{100*abs(price_shock):.0f}$ shock value"] = (
                position_non_option["Quantity"].astype(float)
                * position_non_option["MarketPrice"]
                * (1 + price_shock)
            )
        if ("PX_POS_MULT_FACTOR" in position_non_option.columns) and ("FXRate" in position_non_option.columns):
            position_non_option[f"{100*abs(price_shock):.0f}% Shock $"] = (
                position_non_option[f"{100*abs(price_shock):.0f}$ shock value"]
            ) - (
                position_non_option["Quantity"].astype(float)
                * position_non_option["FXRate"]
                * position_non_option["MarketPrice"]
                * position_non_option["PX_POS_MULT_FACTOR"]
            )
        else:
            position_non_option[f"{100*abs(price_shock):.0f}% Shock $"] = (
                position_non_option[f"{100*abs(price_shock):.0f}$ shock value"]
            ) - (
                position_non_option["Quantity"].astype(float)
                * position_non_option["MarketPrice"]
            )
        position_non_option[f"{100*abs(price_shock):.0f}% Shock %"] = position_non_option[
            f"{100*abs(price_shock):.0f}% Shock $"
        ].divide(firm_NAV)
        position_non_option_brief = position_non_option[
            [
                "UnderlierName",
                "Description",
                "VaRTicker",
                "RFID",
                "Quantity",
                "MarketValue",
                "Exposure",
                f"{100*abs(price_shock):.0f}% Shock $",
                f"{100*abs(price_shock):.0f}% Shock %",
            ]
        ]
    except Exception as ex:
        MyExceptions.show_message(tab='Exposure.py',
                                  message="Following exception occurred during parsing factor positions\n\n" + str(
                                      ex))
    finally:
        return position_non_option_brief
