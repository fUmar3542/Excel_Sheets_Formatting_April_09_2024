# pylint: disable=E501,W0621,C0114,C0301
import logging
from itertools import product
from typing import Dict
import os
import numpy as np
import config
import pandas as pd
from tqdm import tqdm
import time
from functools import reduce 

from src.legacy.helper import option_price, option_delta

pd.set_option("mode.chained_assignment", None)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RISK_FREE_RATE = config.global_settings.get("risk_free_rate", '')
QUANTILES = config.global_settings.get("quantiles", {})


AGGREGATIONS = {
    "TradeDate": "first",
    "Strat": "first",
    "UnderlierName": "first",
    "VaRTicker": "first",
    "MarketValue": "sum",
    "Exposure": "sum",
}

GROUP_AGGREGATIONS = {"VaRTicker": "first", "Exposure": "sum"}


SECURITY_TYPES = [
    "fixed", "future", "public", "prefer",
    "common", "reit", "fund", "mlp", "adr", 'etp'
]


def filter_stress_test_price_vol(
    filter_dict: Dict,
    factor_prices: pd.DataFrame,
    position: pd.DataFrame,
    price_vol_shock_range: Dict,
):
    '''add docstring'''
    price_shock_list = price_vol_shock_range["price_shock"]
    vol_shock_list = price_vol_shock_range["vol_shock"]
    shock_params_list = []
    for a, b in product(
        price_shock_list,
        vol_shock_list,
    ):
        params = {"price_shock": a, "vol_shock": b}
        shock_params_list.append(params)
    filter_list = [x for x in list(filter_dict.keys()) if x in position.columns]
    stress_test_price_vol_dict = {}
    stress_test_price_vol_exposure_dict = {}

    #calculations for each position
    
    
    start_time = time.time()
    t1,t2,t3,t4,t5 =0,0,0,0,0
    
    # resulting dataframe for further filtering 
    position_shock = pd.DataFrame(columns = filter_list+['price_shock', 'vol_shock', 'shock_pnl','shock_exposure'])
    
    position_non_option = position.loc[
    position["SECURITY_TYP"].str.contains(
        "|".join(SECURITY_TYPES),
        na=False,case=False, )
    ]
    #print(f'{len(position_non_option)} non options positions')
    position_option = position.loc[
        position["SECURITY_TYP"].str.contains(
            "|".join(["call", "option", "put"]),
            na=False,
            case=False,
        )
    ]
    #print(f'{len(position_option)} options')
    
    for shock in shock_params_list:
        price_shock = shock["price_shock"]
        vol_shock = shock["vol_shock"]

        if not position_non_option.empty:
            position_non_option["shock_value"] = (
                position_non_option["Quantity"].astype(float)
                * position_non_option["FXRate"]
                * position_non_option["MarketPrice"]
                * position_non_option["PX_POS_MULT_FACTOR"]
                * (1 + price_shock)
            )
            position_non_option["shock_pnl"] = (
                position_non_option["shock_value"]
            ) - (
                position_non_option["Quantity"].astype(float)
                * position_non_option["FXRate"]
                * position_non_option["MarketPrice"]
                * position_non_option["PX_POS_MULT_FACTOR"]
            )
            position_non_option["shock_exposure"] = (
                position_non_option["shock_value"] #                - position_non_option["Exposure"]
            )
            position_non_option['price_shock'] = price_shock
            position_non_option['vol_shock'] = vol_shock
            if len(position_shock)==0:
                position_shock =  position_non_option[position_shock.columns]
            else:
                position_shock = pd.concat([position_shock, position_non_option[position_shock.columns]],axis=0)
            
            #position_shock = pd.concat([position_shock, position_non_option[position_shock.columns]],axis=0)

        if not position_option.empty:
            rfrate = RISK_FREE_RATE if 'FinRt' not in position_option.columns else float(list(position_option['FinRt'])[0]) #XM: taking first rate for the moment: TODO : change for pd.series 
            position_option["shock_underlying_price"] = position_option[
                "UndlPrice"
            ] * (1 + price_shock)
            position_option["shock_implied_vol"] = position_option[
                "IVOL_TM"
            ].astype(float) * (1 + vol_shock)
            position_option["shock_option_price"] = option_price(
                S=position_option["shock_underlying_price"],
                X=position_option["Strike"],
                T=position_option["MtyYears"],
                Vol=position_option["shock_implied_vol"].astype(float),
                rf=rfrate,
                type=position_option["PutCall"],
            )
            position_option["shock_option_delta"] = option_delta(
                S=position_option["shock_underlying_price"],
                X=position_option["Strike"],
                T=position_option["MtyYears"],
                Vol=position_option["shock_implied_vol"].astype(float),
                rf=rfrate,
                type=position_option["PutCall"],
            ) 
            position_option["shock_value"] = (
                position_option["shock_option_price"]
                * position_option["PX_POS_MULT_FACTOR"]
                * position_option["Quantity"].astype(float)
                * position_option["FXRate"]
            )
            position_option["shock_exposure"] = (
                position_option["shock_option_delta"]
                * position_option["shock_underlying_price"]
                * position_option["Quantity"].astype(float)
                * position_option["FXRate"]
                * position_option["PX_POS_MULT_FACTOR"]
                #- position_option["Exposure"]
            )
            position_option["shock_pnl"] = (position_option["shock_value"]) - (
                position_option["MarketPrice"]
                * position_option["PX_POS_MULT_FACTOR"]
                * position_option["Quantity"].astype(float)
                * position_option["FXRate"]
            )
            position_option['price_shock'] = price_shock
            position_option['vol_shock'] = vol_shock
            position_shock = pd.concat([position_shock, position_option[position_shock.columns]],axis=0)
            
    dict_filtered={}

    for filter_item in filter_list:
        start_time2 = time.time()
        position_grouped = position_shock.groupby([filter_item,'price_shock','vol_shock'])[['shock_pnl',"shock_exposure"]].sum()
        # record a data frame for the filter with only shock
        dd = position_grouped.reset_index()
        dd = dd.loc[(dd['price_shock']<0) & (dd['vol_shock']==0),[filter_item,'price_shock','shock_pnl']]
        dd = pd.pivot_table(dd, values='shock_pnl', columns='price_shock', index=filter_item)
        dict_filtered[filter_item]=dd

        # make dictionnaries 
        dicseries = position_grouped.reset_index().apply(lambda x: dict([[f"{x.iloc[0]}_price_shock_{x.iloc[1]}_vol_shock_{x.iloc[2]}",x.iloc[3]]]), axis=1)
        stress_test_price_vol_dict = {**stress_test_price_vol_dict, ** reduce(lambda x,y: {**x, **y} ,list(dicseries))}
        dicseries = position_grouped.reset_index().apply(lambda x: dict([[f"{x.iloc[0]}_price_shock_{x.iloc[1]}_vol_shock_{x.iloc[2]}",x.iloc[4]]]), axis=1)
        stress_test_price_vol_exposure_dict = {**stress_test_price_vol_exposure_dict, ** reduce(lambda x,y: {**x, **y} ,list(dicseries))}

    	# record PnL shock as datafrane
        stress_test_price_vol_df = pd.DataFrame(
            stress_test_price_vol_dict, index=["stress_pnl & vol shock"]
        ).T
        date_vector = pd.DataFrame(
            np.repeat(factor_prices.index[-1], len(stress_test_price_vol_df)),
            index=stress_test_price_vol_df.index,
        )
        stress_test_price_vol_df = pd.concat(
            [date_vector, stress_test_price_vol_df], axis=1
        )
        # record Exposure shock as datafrane
        stress_test_price_vol_exposure_df = pd.DataFrame(
            stress_test_price_vol_exposure_dict, index=[
                "stress_exposure & vol shock"]
        ).T
        date_vector = pd.DataFrame(
            np.repeat(factor_prices.index[-1],
                      len(stress_test_price_vol_exposure_df)),
            index=stress_test_price_vol_exposure_df.index,
            columns=[factor_prices.index[-1]],
        )
        stress_test_price_vol_exposure_df = pd.concat(
            [date_vector, stress_test_price_vol_exposure_df], axis=1
        )
        #print("---Filtering --- %s seconds ---" % (time.time() - start_time2))
        
    #print("---Finished --- %s seconds ---" % (time.time() - start_time))
    stress_test_price_vol_df.sort_index(ascending=False,inplace=True)
    stress_test_price_vol_exposure_df.sort_index(ascending=False,inplace=True)
    
    return stress_test_price_vol_df, stress_test_price_vol_exposure_df, dict_filtered


def filter_stress_test_beta_price_vol(
    filter: Dict,
    factor_prices: pd.DataFrame,
    position: pd.DataFrame,
    factor_betas: pd.DataFrame,
    price_vol_shock_range: Dict,):
    eq_factor = factor_betas.columns[1]
    equity_mkt_beta = factor_betas[["ID", eq_factor]]
    equity_mkt_beta.rename(columns={"ID": "VaRTicker"}, inplace=True)
    price_shock_list = price_vol_shock_range["price_shock"]
    vol_shock_list = price_vol_shock_range["vol_shock"]
    shock_params_list = []
    for a, b in product(
        price_shock_list,
        vol_shock_list,
    ):
        params = {"price_shock": a, "vol_shock": b}
        shock_params_list.append(params)
    filter_list = list(filter.keys())
    stress_test_beta_price_vol_dict = {}
    
    #calculations for each position
    position_grouped = position.groupby(filter.get('position'))
    
    start_time = time.time()
    t1,t2,t3,t4,t5 =0,0,0,0,0
    
    # resulting dataframe for further filtering 
    position_shock = pd.DataFrame(columns = list(filter.values())+['price_shock', 'vol_shock', 'shock_pnl'])
    
    position_non_option = position.loc[
    position["SECURITY_TYP"].str.contains(
        "|".join(SECURITY_TYPES),
        na=False,case=False, )
    ]
    #print(f'{len(position_non_option)} non options positions')
    position_option = position.loc[
        position["SECURITY_TYP"].str.contains(
            "|".join(["call", "option", "put"]),
            na=False,
            case=False,
        )
    ]
    #print(f'{len(position_option)} options')
           
    for shock in shock_params_list:
        t0 = time.time()
        shock_pnl = 0
        price_shock = shock["price_shock"]
        vol_shock = shock["vol_shock"]
        t1 += time.time() - t0
        t0 = time.time()
        if not position_non_option.empty:
            equity_mkt_beta_group = pd.merge(
                position_non_option[["VaRTicker"]],
                equity_mkt_beta,
                on=["VaRTicker"],
                how="left",
            )
            t2 += time.time() - t0
            t0 = time.time()
            equity_mkt_beta_group = equity_mkt_beta_group[eq_factor]
            beta_price_shock = equity_mkt_beta_group.values * price_shock
            position_non_option["mkt_value"] = (
                position_non_option["Quantity"].astype(float)
                * position_non_option["FXRate"]
                * position_non_option["MarketPrice"]
                * position_non_option["PX_POS_MULT_FACTOR"]
            )
            # position_non_option["shock_value"] = position_non_option["mkt_value"]* (1 + beta_price_shock)
            position_non_option["shock_pnl"] = position_non_option["mkt_value"]* beta_price_shock
            position_non_option['price_shock'] = price_shock
            position_non_option['vol_shock'] = vol_shock
            if len(position_shock)==0:
                position_shock =  position_non_option[position_shock.columns]
            else:
                position_shock = pd.concat([position_shock, position_non_option[position_shock.columns]],axis=0)
            shock_pnl += position_shock["shock_pnl"].sum()
        t3 += time.time() - t0
        t0 = time.time()
        if not position_option.empty:
            equity_mkt_beta_group = pd.merge(
                position_option[["VaRTicker"]],
                equity_mkt_beta,
                on=["VaRTicker"],
                how="left",
            )
            equity_mkt_beta_group = equity_mkt_beta_group[eq_factor]
            beta_price_shock = equity_mkt_beta_group.values * price_shock
            position_option["shock_underlying_price"] = position_option["UndlPrice"] * (1 + beta_price_shock)
            position_option["shock_implied_vol"] = position_option["IVOL_TM"].astype(float) * (1 + vol_shock)
            position_option["shock_option_price"] = option_price(
                S=position_option["shock_underlying_price"],
                X=position_option["Strike"],
                T=position_option["MtyYears"],
                Vol=position_option["shock_implied_vol"].astype(float),
                rf=RISK_FREE_RATE,
                type=position_option["PutCall"],
            )
            position_option["shock_value"] = (
                position_option["shock_option_price"]
                * position_option["PX_POS_MULT_FACTOR"]
                * position_option["Quantity"].astype(float)
                * position_option["FXRate"]
            )
            position_option["shock_pnl"] = (position_option["shock_value"]) - (
                position_option["MarketPrice"]
                * position_option["PX_POS_MULT_FACTOR"]
                * position_option["Quantity"].astype(float)
                * position_option["FXRate"]
            )
            position_option['price_shock'] = price_shock
            position_option['vol_shock'] = vol_shock
            position_shock = pd.concat([position_shock, position_option[position_shock.columns]],axis=0)
            shock_pnl += position_shock["shock_pnl"].sum()
        t4 += time.time() - t0
        
        
        
    #print("--- %s seconds ---" % (time.time() - start_time))
    start_time = time.time()
    
    for filter_item in filter_list: # [f for f in filter_list if f!='position']:  # position already done as bulk above
        start_time2 = time.time()
        position_grouped = position_shock.groupby([filter.get(filter_item),'price_shock','vol_shock'])['shock_pnl'].sum()
        dicseries = position_grouped.reset_index().apply(lambda x: dict([[f"{x.iloc[0]}_price_shock_{x.iloc[1]}_vol_shock_{x.iloc[2]}",x.iloc[3]]]), axis=1)
        stress_test_beta_price_vol_dict = {**stress_test_beta_price_vol_dict, ** reduce(lambda x,y: {**x, **y} ,list(dicseries))}
        

        stress_test_beta_price_vol_df = pd.DataFrame(
            stress_test_beta_price_vol_dict, index=[
                "stress_pnl_beta*price & vol shock"]
        ).T
        date_vector = pd.DataFrame(
            np.repeat(factor_prices.index[-1],
                        len(stress_test_beta_price_vol_df)),
            index=stress_test_beta_price_vol_df.index,
            columns=[factor_prices.index[-1]],
        )
        stress_test_beta_price_vol_df = pd.concat( [date_vector, stress_test_beta_price_vol_df], axis=1 )

    #print("Finished --- %s seconds ---" % (time.time() - start_time))
    
    
    return stress_test_beta_price_vol_df.sort_index(ascending=False)

def stress_test_structuring(
    stress_test_df: pd.DataFrame,
    position: pd.DataFrame,
    price_vol_shock_range: Dict,
    firm_NAV: float  
):
    '''dosctring goes here...'''
    position_grouped = position.groupby(["Strat"])
    fund_list = list(position_grouped.groups.keys())
    col = stress_test_df.filter(like="stress_").columns
    stress_test_df = stress_test_df[col] / firm_NAV # position_agg_exposure["MarketValue"].sum()   # XM: wrong denominator 
    price_shock_list = price_vol_shock_range["price_shock"]
    vol_shock_list = price_vol_shock_range["vol_shock"]
    shock_params_list = []
    for a, b in product(
        price_shock_list,
        vol_shock_list,
    ):
        params = {"price_shock": f"price_shock_{a}",
                  "vol_shock": f"vol_shock_{b}"}
        shock_params_list.append(params)

    some_dict = {}
    for shock in shock_params_list:
        price_shock = shock["price_shock"]
        vol_shock = shock["vol_shock"]
        combined_shock_string = f"{price_shock}_{vol_shock}"
        stress_shock_filter = stress_test_df.loc[
            stress_test_df.index.str.contains(combined_shock_string)
        ]
        stress_shock_filter = stress_shock_filter[
            stress_shock_filter.index.str.contains(
                "|".join(fund_list))  # type: ignore
        ]
        some_dict[combined_shock_string] = stress_shock_filter.sum()
    stress_test_arr = np.array(list(some_dict.values()))
    stress_test_arr = np.reshape(
        stress_test_arr,
        (
            int(np.sqrt(len(some_dict))),  # type: ignore
            int(np.sqrt(len(some_dict)))  # type: ignore
        )
    ).T
    logger.info("convert results into summary tbl")
    stress_test_results_df = pd.DataFrame(
        stress_test_arr,
        index=list(vol_shock_list),
        columns=price_shock_list
    )

    stress_test_results_df.rename(columns=dict(zip(stress_test_results_df.columns,[f"{int(100*float(x))}%" for x in stress_test_results_df.columns])),inplace=True)

    return stress_test_results_df.sort_index(ascending=False)
 
 
def stress_test_filtered_structuring(stress_test_filtered_calc, firm_NAV):
    '''format data frames in a dictionnary to have shock in $ and in %'''
    stress_test_dict_struct = {}
    for k in stress_test_filtered_calc.keys():
        dd1 = stress_test_filtered_calc[k]
        dd1 = dd1[sorted(dd1.columns, reverse=True)]
        dd2 = dd1.copy()/firm_NAV
        dd1.rename(columns={x: str(int(-x*100))+"% shock $" for x in dd1.columns }, inplace=True)
        dd2.rename(columns={x: str(int(-x*100))+"% shock %" for x in dd2.columns }, inplace=True)
        stress_test_dict_struct[k]=pd.concat([dd1,dd2],axis=1)[list(sum(list(zip(dd1.columns,dd2.columns)), ()))]
    return stress_test_dict_struct
