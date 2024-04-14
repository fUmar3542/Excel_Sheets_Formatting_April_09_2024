# pylint: disable=E501,W0621,C0114,C0301
import sys
import yaml
import shutil
import os
import logging
import warnings
import config
from argparse import ArgumentParser
from datetime import datetime
from datetime import timedelta
#from typing import List
import pandas as pd
import xlsxwriter


# Global use of YAML file 
yaml_file = f"CRM.yml"
if os.path.exists(yaml_file):
    with open(yaml_file, 'r') as file:
        config_data = yaml.safe_load(file)
        # Assigning global settings from YAML
        global_settings = config_data.get("global_settings", {})
        fund_settings = config_data.get("funds", {})
else:
    print(f"YAML file '{yaml_file}' not found.")
    sys.exit(1)

# Export global and fund variables to config module
config.global_settings = global_settings
config.fund_settings = fund_settings

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
import src.legacy.Exposures as Exposures
import src.legacy.Factors as fac
import src.legacy.pnl_stats as pnl_stats
import src.legacy.VaR as var
import src.legacy.var_utils as var_utils
import src.report_sheets as rsh
from src.calculation_engine.constants import GROUP_LEVELS
from src.calculation_engine.var_calculator import calculate_vars
from src.legacy.helper import calculate_returns, imply_smb_gmv, calculate_log_returns
from src.reporting_engine.var_reports import (generate_group_var_reports, generate_underlier_report)

# import _pydevd_bundle
# _pydevd_bundle.pydevd_constants.PYDEVD_WARN_EVALUATION_TIMEOUT = 30 # seconds


# Filter out the FutureWarning
warnings.filterwarnings(
    "ignore",
    message="The default dtype for empty Series will be 'object' instead"
    " of 'float64' in a future version.",
)

warnings.filterwarnings(
    "ignore",
    message="In a future version of pandas, a length 1 tuple will be returned when iterating over a groupby with a grouper equal to a list of length 1.*",
    category=FutureWarning
)

# Suppress specific UserWarning about Excel sheet names
warnings.filterwarnings(
    "ignore",
    message=".*Sheetname in.*contains spaces but isn't quoted.*",
    category=UserWarning
)


formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logging.getLogger().handlers.clear()

now = datetime.utcnow().strftime("%Y%m%d")


def change_analyst_exposure(df1, df2):
    try:
        df1.index = [index.split("_")[-1].upper() for index in df1.index]
        df2.index = [index.split("_")[-1].upper() for index in df2.index]
    except:
        pass
    finally:
        return df1, df2


if __name__ == "__main__": #Execution of main procedure for laumch in command line

    # Load global variables and file paths from YAML
    ANNUALIZATION_FACTOR = config.global_settings.get("annualization_factor", 252)
    VAR_NBDAYS_AGO = config.global_settings.get("var_nbdays_ago", 182)
    RISK_FREE_RATE = config.global_settings.get("risk_free_rate", 0.055)
    COLNAME_POSITION_GROUPING = config.global_settings.get("column_position_grouping", "UnderlierName")
    DECAY_FACTOR = config.global_settings.get("decay factor", 0.94)
    QUANTILES = config.global_settings.get("quantiles", {})
    OPTION_TYPES = config.global_settings.get("option types", {})
    NON_OPTION_TYPES = config.global_settings.get("non option types", {})
    FUND_NAME_ALIAS = config.global_settings.get("fund name alias", "")
    price_vol_shock_range = config.global_settings.get("stress_test_ranges", {})
    #GROUP_LEVELS = config.global_settings.get("group_levels", {})
    file_paths = config.global_settings.get("file_paths", {})
    INVESTTMENT = config.fund_settings[0].get("investment_advisor")


    # Extract fund-specific information
    for fund_config in config.fund_settings:
        investment_advisor = fund_config.get("investment_advisor", "")
        fund_list = fund_config.get("fundslist", [])
        bench_names = fund_config.get("benchmark", [])
        holdings_date = fund_config.get("holdings_date", "")
        FACTORS_TO_REPORT = fund_config.get("factors_to_report", [])
        custom_outputs = fund_config.get("custom_outputs", [])



    # Before we start write a copy of the config used to the fund directory.

    # Define the new filename
    today = datetime.today().strftime('%Y%m%d')  # Format: YYYYMMDD
    new_file_name = f"{investment_advisor}-run{today}.yml"

    # Define the destination directory
    destination_directory = f"funds/{investment_advisor}/"
    os.makedirs(destination_directory, exist_ok=True)  # Create directory if it doesn't exist

    # Full path for the new file
    new_file_path = os.path.join(destination_directory, new_file_name)

    # Copy the file
    shutil.copy(yaml_file, new_file_path)
  
    

    # deduct first date for history for VaR calculations 
    date_min_var = datetime.date(datetime.strptime(holdings_date,'%Y-%m-%d')+timedelta(days=-VAR_NBDAYS_AGO))
    
    # reads NAV history 
    
    AUM = pd.read_excel(file_paths["historical_pnl_nav"].format(investment_advisor=investment_advisor, holdings_date=pd.to_datetime(holdings_date).strftime('%Y%m%d'))) #read path from yaml file
    AUM = AUM.drop_duplicates()
    AUM_dict = {}
    AUM_clean_df_list = []
    for ix in range(0, len(fund_list)):
        firm = fund_list[ix]
        logger.info(f"loading fund {firm} which is number {ix+1} out of" f" {len(fund_list)}" )
        fund_aum = AUM.loc[AUM["Fund"].str.lower() == firm.lower()]
        AUM_clean = pnl_stats.clean_nav(fund_aum,firm_wide=False)  # model NAVs
        AUM_clean.index = pd.to_datetime(AUM_clean.index).strftime("%Y-%m-%d")
        AUM_clean_df_list.append(AUM_clean)
        AUM_fund = AUM_clean.loc[AUM_clean.index == holdings_date]["EndBookNAV"]
        if len(AUM_fund) > 0:
            AUM_dict[firm] = AUM_fund.values[0]
    AUM_clean = pd.concat(AUM_clean_df_list, axis=0)
    AUM_clean.reset_index(inplace=True)
    
    # firm-wide AUM
    AUM_clean_funds = pnl_stats.clean_nav(AUM_clean, firm_wide=True)
    AUM_clean_funds.index = pd.to_datetime(AUM_clean_funds.index).strftime("%Y-%m-%d")
    AUM_firm = AUM_clean_funds.loc[AUM_clean_funds.index == holdings_date]["EndBookNAV"]
    AUM_dict["Firm"] = AUM_firm.values[0]
    AUM_clean.set_index(["PeriodEndDate"], inplace=True)
    AUM_clean.index = pd.to_datetime(AUM_clean.index).strftime("%Y-%m-%d")

    fund_list_aum = list(AUM_dict.keys())
    
    # reads benchmarks price history 
    df_bench = pd.read_excel(file_paths["benchmarks_histo"].format(investment_advisor=investment_advisor), sheet_name="Sheet1", header=0) #load from yaml
    df_bench.set_index('Dates',inplace=True)
    df_bench.sort_index(inplace=True)
    # calculate benchmark's returns 
    colbenchs = [ x for x in df_bench.columns if x.endswith('Index')]
    bench_rets = df_bench[colbenchs]/df_bench[colbenchs].shift(1)-1
    bench_rets.index = pd.to_datetime(bench_rets.index).strftime("%Y-%m-%d")
    
    for fund in fund_list_aum:
        logger.info(f"--------------------------------> Starting run for {fund} ")
        nav_value = AUM_dict[fund]
        # pd.ExcelWriter
        writer_options = {"constant_memory": False, "nan_inf_to_errors": True}
        file_name = f"funds/{investment_advisor}/{investment_advisor}_{fund}_risk_report_" \
                    f"{pd.to_datetime(holdings_date).strftime('%Y%m%d')}.xlsx"
        writer = xlsxwriter.Workbook(file_name, writer_options)
        writer.set_tab_ratio(75)

        # set AUM_clean_df
        if fund != "Firm":
            AUM_clean_df = AUM_clean.loc[AUM_clean["Fund"].str.lower() == fund.lower()]
        else:
            AUM_clean_df = AUM_clean_funds.copy()
            
        # 1. Read in factors, prices, positions
        factor = pd.read_csv(file_paths["factors"].format(investment_advisor=investment_advisor)) # load from yaml
        eq_factor_name = factor.loc[factor['Factor Names']=='Equity','FactorID'].values[0] # name of the main Equity Factor (benchmark)
        price = pd.read_csv(file_paths["prices"].format(investment_advisor=investment_advisor, holdings_date=pd.to_datetime(holdings_date).strftime('%Y%m%d')))
        price.rename({"Date": "date"}, axis=1, inplace=True) # in case date column is written Date
        price.date = pd.to_datetime(
            price.date,
            format=r"%m/%d/%Y",
        ).dt.date
        
        price.set_index(["date"], inplace=True)
        
        
        # read and process raw positions ------------------------------------
        # # read and process positions
        position = pd.read_csv(file_paths["positions"].format(investment_advisor=investment_advisor, holdings_date=pd.to_datetime(holdings_date).strftime('%Y%m%d')))
        # cleaning of data 
        position.rename(
            {
                'MarketValueInBase':'MarketValue',
                "VaRExposure": "Exposure",
                "MarketCap.1": "MarketCap_Group",
                "VarTicker": "VaRTicker",
                "UnderlierSymbol": "UnderlierName",
                "ProdType": "SECURITY_TYP",
            },
            axis=1,
            inplace=True,
        )
        position["Quantity"].replace(r"[$\+\,\(\)]", "", regex=True, inplace=True)
        position["MarketValue"] = pd.to_numeric( position["MarketValue"], errors="coerce")

        # for now need to process positions and force a
        # distinct RFID for each distinct symbol
        logger.info("process positions and force a distinct RFID for each distinct symbol")
        cols = position.columns[~position.columns.isin(["RFID"])]
        position = position[cols]
        position_group = position.groupby("VaRTicker")
        count = 0
        position_group_df_list = []
        for name, group in position_group:
            count += 1
            group["RFID"] = count
            position_group_df_list.append(group)
        position = pd.concat(position_group_df_list, axis=0)
        position["Exposure"] = position["Exposure"].astype(float)
        position["TradeDate"] = pd.to_datetime(position["TradeDate"]).dt.strftime( "%Y-%m-%d" )

        # structure positions, factor, price data for subsequent
        # estimation of Factor
        # betas, vars, Exposures, and Stress Tests
        
        #restrict factors to reported only ones 
        factor.set_index('Factor Names',inplace=True)
        factor = factor.loc[FACTORS_TO_REPORT,:]
        factor.reset_index(inplace=True)
        
        factor_names = list(factor["Factor Names"])
        factor_names = [name for name in factor_names if str(name) != "nan"]
        
        complete_factor_ids = list(factor["FactorID"])
        factor_ids_price = [col for col in price.columns if not (col.startswith('BBG') or col.startswith('Unnamed')) ]
        factor_prices = price[factor_ids_price]
    
        factors_to_remove = ["RIY Index", "RTY Index", "RAG Index", "RAV Index"]
        factor = factor.loc[~factor["FactorID"].isin(factors_to_remove)]
        factor.set_index('FactorID',inplace=True)
        
        position_ids = list(position["VaRTicker"].unique())
        position_prices = price[position_ids+[eq_factor_name]]

    
        # rename "FundName" as "Strat"
        position.rename(columns={"FundName": "Strat"}, inplace=True)
        # create filters 
        strat_filters = position["Strat"].unique()
        sector_filters = position["Sector"].unique()
        industry_filters = position["Industry"].unique()
        country_filters = position["Country"].unique()
        mcap_filters = position["MarketCap_Group"].unique()
        filters_dict = {
            "Strat": strat_filters,
            "Sector": sector_filters,
            "Industry": industry_filters,
            "Country": country_filters,
            "MarketCap_Group": mcap_filters,
        }
    
        
        # check yaml file for custom outputs``
        if "analyst_exposure" in custom_outputs:
            filters_dict["Analyst"] = position["Analyst"].unique()
        if "type_exposure" in custom_outputs:
            filters_dict["Type"] = position["Type"].unique()

        # 1.a. estimate factor betas, factor vols
        logger.info("Calculating betas to factors")
        factor_returns,_ = calculate_log_returns(factor_prices) 
        factor_returns = imply_smb_gmv(factor_returns,eq_factor_name)
        # restrict factor returns to the reported factors & 6M ago
        factor_returns = factor_returns[factor.index]
        factor_returns = factor_returns.iloc[factor_returns.index>date_min_var,:]
        
        #position_returns = calculate_returns(position_prices)  #XM: replaced by log returns
        position_returns, position_normed_prices = calculate_log_returns(position_prices, eq_factor_name)
        position_returns =position_returns.iloc[position_returns.index>date_min_var,:]
        logger.info("Done with position returns estimation")
        
        # beta estimation 
        factor_betas, factor_returns_ortho, raw_factor_betas = fac.calculate_position_betas(factor_returns, position_returns)


        logger.info("Correlations, Covariances ")
        matrix_correlation = factor_returns_ortho.rename(columns=dict(zip(factor_returns_ortho.columns,factor['Factor Names']))).corr()
        matrix_cov = var_utils.covariance_matrix(factor_returns_ortho)
        raw_matrix_cov = var_utils.covariance_matrix(factor_returns)
        decay_cov = var_utils.decay_covariance_matrix(factor_returns_ortho)  #XM: unused TODO; deprecate

        # filter position on current fund if it's not "Firm"
        if fund != "Firm":  
            position = position.loc[position["Strat"].str.lower() == fund.lower()]
            
        if len(position) == 0:
            LOGGER.info(
                f"no positions for fund {fund} as of holdings_date "
                f"{holdings_date}"
            )
        else:
            filter_items = {
                "position": "VaRTicker",
                "fund": "Strat",
                "sector": "Sector",
                "industry": "Industry",
                "country": "Country",
                "mktcap": "MarketCap_Group",
            }
            # # 1.c Stress Test functions
            # Excel equivalent ["Options&Stress;
            # "Beta & Volatility Stress Test P&L tbl"]
            logger.info("Calculating stress tests")
            stress_test_beta_price_vol_calc = var.filter_stress_test_beta_price_vol(
                filter_items, factor_prices, position,
                factor_betas, price_vol_shock_range
            )
            stress_test_beta_price_vol_results_df = var.stress_test_structuring(
                stress_test_beta_price_vol_calc,
                position, price_vol_shock_range, nav_value
            )
            # Excel equivalent ["Options&Stress;
            # "Price & Volatility Stress Test P&L tbl"]
            (
                stress_test_price_vol_calc,
                stress_test_price_vol_exposure_calc,
                stress_test_filtered_calc
            ) = var.filter_stress_test_price_vol(
                filters_dict, factor_prices, position, price_vol_shock_range
            )
            # Excel equivalent ["Options&Stress;
            # "Price & Volatility Stress Test Net Exposure tbl"]
            stress_test_price_vol_results_df = var.stress_test_structuring(
                stress_test_price_vol_calc, position, price_vol_shock_range, nav_value
            )
            stress_test_price_vol_exposure_results_df = var.stress_test_structuring(
                stress_test_price_vol_exposure_calc, position, price_vol_shock_range, nav_value
            )
            stress_test_filtered_df = var.stress_test_filtered_structuring(
                stress_test_filtered_calc, nav_value
            )

            # 1.e Exposure functions
            
            # Excel equivalent ["ExpReport"]
            logger.info("Calculating Exposures")
            (
                strat_exposure_df,
                sector_exposure_df,
                industry_exposure_df,
                country_exposure_df,
                mktcap_exposure_df,
                analyst_exposure_df,
                assettype_exposure_df,
            ) = Exposures.filter_exposure_calc(filters_dict, position, AUM_dict, fund)
            # Excel equivalent ["ExpReport"]
            (
                strat_beta_adj_exposure_df,
                sector_beta_adj_exposure_df,
                industry_beta_adj_exposure_df,
                country_beta_adj_exposure_df,
                mktcap_beta_adj_exposure_df,
                analyst_beta_adj_exposure_df,
                assettype_beta_adj_exposure_df,
            ) = Exposures.filter_beta_adj_exposure_calc(
                filters_dict, position, factor_betas, AUM_dict, fund
            )
            #notional Exposure (XM: added)
            sector_notional_exposure_df = Exposures.notional_exposure_calc(
                filters_dict, position, AUM_dict, fund
            ) 
            
            logger.info("Calculating Options informations")
            # Excel equivalent ["Options&Stress"; "Option Exposure" tbl]
            options_delta_adj_exposure_df = Exposures.filter_options_delta_adj_exposure(
                position, fund
            )
            # Excel equivalent ["Options&Stress"; "Option Notional" tbl]
            options_delta1_exposure_df = Exposures.filter_options_delta_unadj_exposure(
                position, fund
            )
            # Excel equivalent ["Options&Stress"; "Premium" tbl]
            options_premium_df = Exposures.filter_options_premium(position, fund)
            # Excel equivalent ["Options&Stress"; "Greek Sensitivity" tbl]
            greek_sensitivities_df = Exposures.greek_sensitivities(position, fund)
            
            # Excel equivalent ["OptionsDelta"]
            if  "generate_delta_sheet" in custom_outputs:
                logger.info("Calculating table for Options delta")
                options_delta_df = Exposures.filter_options_delta(position, AUM_dict, fund)
            
            logger.info("Calculating Exposures to Factors")
            # Excel equivalent ["FactorExposures"; "Macro Factor Sensitivity" tbl
            # & "Sector Sensitivities" tbl]
            (
                macro_factor_decomp_df,
                sector_factor_decomp_df,
            ) = Exposures.factor_decomp_filtered(
                position, factor_betas, factor_prices, factor, matrix_cov, AUM_dict, fund
            )
            # Excel equivalent ["FactorExposures"; "Top10" tbls & "Bottom10"
            # tbls by Factor, Exposure by Position]
            (
                risk_factor_exposure_top_N_list,
                risk_factor_exposure_bottom_N_list,
            ) = Exposures.factor_decomp_by_factor_position(
                position, factor_betas, factor, AUM_dict, fund
            )
            
            if "macro_Factor_Top_10_tbls" in custom_outputs:
                # Excel equivalent ["FactorExposures"; "Macro Factor Sensitivity" tbl
                # & "Sector Sensitivities" tbl]
                (
                    macro_beta_decomp_df,
                    sector_beta_decomp_df,
                ) = Exposures.beta_decomp_filtered(
                    position, raw_factor_betas, factor_prices, factor, raw_matrix_cov, AUM_dict, fund
                )
                # Excel equivalent ["FactorExposures"; "Top10" tbls & "Bottom10"
                # tbls by Factor, Exposure by Position]
                (
                    risk_beta_exposure_top_N_list,
                    risk_beta_exposure_bottom_N_list,
                ) = Exposures.beta_decomp_by_factor_position(
                    position, raw_factor_betas, factor, AUM_dict, fund
                )   
            
            logger.info("Calculating Factor Heatmap")
            # Excel equivalents ["FactorHeatMap"]
            factor_heat_map = Exposures.factor_heat_map(
                position, factor_betas, factor, AUM_dict, fund
            )
            d = dict.fromkeys(factor_heat_map.columns, "sum")
            factor_heat_map.reset_index(inplace=True)
            factor_heat_map = factor_heat_map.groupby('Position', as_index=False).agg(d)
            factor_heat_map.set_index(["Position"], inplace=True)
            
            if "betaheatmap" in custom_outputs:
                # Excel equivalents ["BetaHeatMap"]
                beta_heat_map = Exposures.beta_heat_map( position, raw_factor_betas, factor, AUM_dict, fund  )
                d = dict.fromkeys(beta_heat_map.columns, "sum")
                beta_heat_map.reset_index(inplace=True)
                beta_heat_map = beta_heat_map.groupby('Position', as_index=False).agg(d)
                beta_heat_map.set_index(["Position"], inplace=True)


            # Excel equivalents ["PositionsBreakdown"]; ["PositionsSummary"];
            (
                position_breakdown,
                position_summary,
            ) = Exposures.stress_test_beta_price_vol_exposure_by_position(
                position, factor_betas, matrix_cov, position_returns, factor, AUM_dict, fund
            )

            # liquidity breakdown 
            position_liquidity = Exposures.liquidity(filters_dict, position, AUM_dict, fund)

            
            AUM_clean_df.sort_index(inplace=True)
            AUM_clean_df = AUM_clean_df.loc[AUM_clean_df.index <= holdings_date]
            AUM_clean_df = pd.merge(
                AUM_clean_df, bench_rets, right_index=True, left_index=True
            )

            # 1.d. var functions
            
            GROUP_LEVELS["position"]=COLNAME_POSITION_GROUPING
            for x in list(GROUP_LEVELS.keys()):
                if GROUP_LEVELS[x] not in position.columns:
                    GROUP_LEVELS.pop(x)
            # make a name for reporting assets
            var_data = calculate_vars(prices= position_normed_prices, positions=position, nav = nav_value) #price.iloc[price.index>=date_min_var,:]
            var_data.to_excel(f"funds/{investment_advisor}/var_data_{fund}_"
                            f"{pd.to_datetime(holdings_date).strftime('%Y%m%d')}.xlsx")
            top_var_contributors = generate_underlier_report(var_data, ascending=False)
            top_var_diversifiers = generate_underlier_report(var_data, ascending=True)

            keystofilter = (["total"] if fund == "Firm" else []) +list(GROUP_LEVELS.keys())
            group_var_reports = generate_group_var_reports( var_data, keystofilter)

            var_structured_strat = group_var_reports.get("fund")
            var_structured_sector = group_var_reports.get("sector")
            var_structured_industry = group_var_reports.get("industry")
            var_structured_country = group_var_reports.get("country")
            var_structured_mcap = group_var_reports.get("mktcap")
            var_structured_analyst = group_var_reports.get("analyst")
            var_structured_assettype = group_var_reports.get("assettype")

            # 1.g. dashboard
            # Excel equivalents ["Dashboard; "Fund Exposure %" tbl; "Fund Exposures $" tbl]
            # fund exposure % tbl
            position_agg_exposure = (
                position.groupby("RFID")
                .agg(
                    {
                        "TradeDate": "first",
                        "Strat": "first",
                        "UnderlierName": "first",
                        "VaRTicker": "first",
                        "MarketValue": "sum",
                        "Exposure": "sum",
                    }
                )
                .reset_index()
            )
            
            long_mkt_value_pct = tmp = (
                position.loc[position["MarketValue"] > 0]["MarketValue"].sum() / nav_value
            )
            short_mkt_value_pct = tmp = (
                position.loc[position["MarketValue"] < 0]["MarketValue"].sum() / nav_value
            )
            gross_mkt_value_pct = abs(position["MarketValue"]).sum() / nav_value
            net_mkt_value_pct = position["MarketValue"].sum() / nav_value
            long_mkt_value = position.loc[position["MarketValue"] > 0]["MarketValue"].sum()
            short_mkt_value = position.loc[position["MarketValue"] < 0]["MarketValue"].sum()
            gross_mkt_value = abs(position["MarketValue"]).sum()
            net_mkt_value = position["MarketValue"].sum()
            fund_exp_pct_dashboard = pd.DataFrame(
                {
                    "Fund Exposures %": [
                        "Delta Adjusted Exposure",
                        "Beta Adjusted " "Exposure",
                        "Notional Exposure",
                        "Market Value",
                    ],
                    "Long": [
                        sector_exposure_df.loc["Total", "Long"],  # type: ignore
                        sector_beta_adj_exposure_df.loc["Total","Long"],  # type: ignore
                        sector_notional_exposure_df.loc["Total","Long"],
                        long_mkt_value_pct,
                    ],
                    "Short": [
                        sector_exposure_df.loc["Total", "Short"],
                        sector_beta_adj_exposure_df.loc["Total","Short"],  # type: ignore
                        sector_notional_exposure_df.loc["Total","Short"],
                        short_mkt_value_pct,
                    ],
                    "Gross": [
                        sector_exposure_df.loc["Total", "Gross"],
                        sector_beta_adj_exposure_df.loc["Total","Gross"],  # type: ignore
                        sector_notional_exposure_df.loc["Total","Gross"],
                        gross_mkt_value_pct,
                    ],
                    "Net": [
                        sector_exposure_df.loc["Total", "Net"],
                        sector_beta_adj_exposure_df.loc["Total","Net"],  # type: ignore
                        sector_notional_exposure_df.loc["Total","Net"],
                        net_mkt_value_pct,
                    ],
                }
            )
            
            fund_exp_usd_dashboard = pd.DataFrame(
                {
                    "Fund Exposures $": [
                        "Delta Adjusted Exposure",
                        "Beta Adjusted Exposure",
                        "Notional Exposure",
                        "Market Value",
                    ],
                    "Long": [
                        sector_exposure_df.loc["Total","Long"] * nav_value,  # type: ignore
                        sector_beta_adj_exposure_df.loc["Total","Long"]  * nav_value,  # type: ignore
                        sector_notional_exposure_df.loc["Total","Long"] *  nav_value,
                        long_mkt_value,
                    ],
                    "Short": [
                        sector_exposure_df.loc["Total","Short"] * nav_value,  # type: ignore
                        sector_beta_adj_exposure_df.loc["Total","Short"]  # type: ignore
                        * nav_value,  # type: ignore
                        sector_notional_exposure_df.loc["Total","Short"] *  nav_value,
                        short_mkt_value,
                    ],
                    "Gross": [
                        sector_exposure_df.loc["Total","Gross"] * nav_value,  # type: ignore
                        sector_beta_adj_exposure_df.loc["Total","Gross"]  # type: ignore
                        * nav_value,  # type: ignore
                        sector_notional_exposure_df.loc["Total","Gross"] *  nav_value,
                        gross_mkt_value,
                    ],
                    "Net": [
                        sector_exposure_df.loc["Total","Net"] * nav_value,  # type: ignore
                        sector_beta_adj_exposure_df.loc["Total","Net"]  # type: ignore
                        * nav_value,  # type: ignore
                        sector_notional_exposure_df.loc["Total","Net"] *  nav_value,
                        net_mkt_value,
                    ],
                }
            )

            #XM: add exposure to var_contributors: outside of calculate var since var is calculated separately and not keeping positions IDs ...
            #position['pctExposure']=position['MarketValue']/firm_NAV
            curpos = position.copy()
            if fund!="Firm":
                curpos = curpos.loc[curpos['Strat'].str.lower()==fund.lower()]
            curpos.rename(columns={'Exposure':'Exp'},inplace=True)
            curpos['Exposure']=curpos['Exp']/nav_value
            curpos = curpos.groupby(COLNAME_POSITION_GROUPING)['Exposure'].sum()
            top_var_withexpo = top_var_contributors.merge(right=curpos, left_index=True, right_index = True, how='left')
            top_vardiv_withexpo = top_var_diversifiers.merge(right=curpos, left_index=True, right_index = True, how='left')
        


            # ------------------- Generation of excel sheets --------------------------------------------------
            # if isinstance(sector_exposure_df, pd.DataFrame):
            #     sector_exposure_df.iloc[:, 0] = sector_exposure_df.iloc[:, 0].astype(str).str[:5]
            # value_mapping = {
            #     "Consumer Discretionary": "ConsDisc",
            #     "Consumer Staples": "ConsStap",
            #     "Health Care": "HealthCare",
            #     "Real Estate": "RealEstate",
            #     "Information Technology": "Tech",
            #     "Broad Market Index": "BroadMarket",
            #     "Bond Market Index": "Bonds",
            #     "Communication Services": "Telecom"
            # }
            #
            # # Apply the mapping to the index of the DataFrame
            # sector_exposure_df.index = sector_exposure_df.index.to_series().replace(value_mapping, regex=True)
            value_mapping = {
                "ConsDisc": "Consumer Discretionary",
                "ConsStap": "Consumer Staples",
                "HealthCare": "Health Care",
                "RealEstate": "Real Estate",
                "Tech": "Information Technology",
                "BroadMarket": "Broad Market Index",
                "Bonds": "Bond Market Index",
                "Telecom": "Communication Services"
            }
            # Apply the mapping to the index of the DataFrame
            sector_factor_decomp_df.index = sector_factor_decomp_df.index.to_series().replace(value_mapping, regex=True)
            title = "Risk Report"
            rsh.generate_dashboard_sheet(
                writer,
                fund,
                holdings_date,
                title,
                data={
                    "var_structured_position_top10": top_var_withexpo, # top_var_contributors,
                    "var_structured_position_bottom10": top_vardiv_withexpo, # top_var_diversifiers,
                    "sector_exposure_df": sector_exposure_df,
                    "options_premium_df": options_premium_df,
                    "greek_sensitivities_df": greek_sensitivities_df.sort_index(),
                    "macro_factor_decomp_df": macro_factor_decomp_df,  # type: ignore
                    "sector_factor_decomp_df": sector_factor_decomp_df,
                    "fund_exp_pct_dashboard": fund_exp_pct_dashboard,
                    "fund_exp_usd_dashboard": fund_exp_usd_dashboard,
                    "position_liquidity": position_liquidity,
                },
            )
        
            if not options_premium_df.empty: 
                options_premium_df.set_index("Premium", inplace=True)

            # 1.h., build rest of workbook beyond dashboard
            # Excel equivalents ["PNLReport"]
            AUM_clean_df = pnl_stats.clean_nav_extra_filter(AUM_clean_df)
            return_analysis_stats = pnl_stats.return_analysis(AUM_clean_df, holdings_date,investment_advisor)
            
            comparative_analysis_stats = pnl_stats.comparative_statistics(
                AUM_clean_df, return_analysis_stats,holdings_date, investment_advisor)
          
            rsh.generate_pnldata_sheet(
                writer,
                ANNUALIZATION_FACTOR,
                data_dict={
                    "AUM_clean": AUM_clean_df.dropna(),
                },
            )

            perf_ratio_stats = return_analysis_stats.loc[
                (return_analysis_stats.index.str.contains("Up Days"))
                | (return_analysis_stats.index.str.contains("Down Days"))
                | (return_analysis_stats.index.str.contains("Sharpe"))
                | (return_analysis_stats.index.str.contains("Sortino"))
                | (return_analysis_stats.index.str.contains("CALMAR"))
            ]
            return_analysis_stats = return_analysis_stats.loc[
                ~(return_analysis_stats.index.str.contains("Up Days"))
                & ~(return_analysis_stats.index.str.contains("Down Days"))
                & ~(return_analysis_stats.index.str.contains("Sharpe"))
                & ~(return_analysis_stats.index.str.contains("Sortino"))
                & ~(return_analysis_stats.index.str.contains("CALMAR"))
            ]

            monthly_pnl_stats = pnl_stats.monthly_pnl_stats(AUM_clean_df)
            fund_AUM = pd.DataFrame(AUM_clean_df[['EndBookNAV','DailyBookPL']].loc[holdings_date,:]).rename(index={'EndBookNAV':'AUM', 'DailyBookPL':'Daily P&L'}).reset_index()
            fund_AUM.rename(columns={'index':'Fund $',fund_AUM.columns[1]:'Fund'}, inplace=True)
            fund_AUM.set_index('Fund $', inplace=True)
            title = "Risk Report"
            rsh.generate_pnlreport_sheet(
                writer,
                fund,
                holdings_date,
                title,
                data_dict={
                    "comparative_analysis_stats": comparative_analysis_stats,
                    "return_analysis_stats": return_analysis_stats,
                    "perf_ratio_stats": perf_ratio_stats,
                    "monthly_pnl_stats": monthly_pnl_stats,
                    "fund_AUM": fund_AUM,  },
                FirmName=investment_advisor,
            )
            rsh.generate_factor_heatmap_sheet(
                writer,
                data_dict={
                    "factor_heatmap": factor_heat_map[["Exposure","Beta"] + FACTORS_TO_REPORT[1:]].sort_values("Exposure", ascending=False),
                },
            )
            
            if "betaheatmap" in custom_outputs:
                rsh.generate_beta_heatmap_sheet(
                    writer,
                    data_dict={
                        "beta_heatmap": beta_heat_map[["Exposure","Beta"] + FACTORS_TO_REPORT[1:]].sort_values("Exposure", ascending=False),
                    },
                )
            title = INVESTTMENT + " Factor Sensitivity Contributors"
            rsh.generate_factor_exposures_sheet(
                writer,
                fund,
                holdings_date,
                title,
                data={
                    "macro_factor_decomp_df": macro_factor_decomp_df, 
                    "sector_factor_decomp_df": sector_factor_decomp_df,
                    "risk_factor_exposure_top_n_list": risk_factor_exposure_top_N_list,
                    "risk_factor_exposure_bottom_n_list": risk_factor_exposure_bottom_N_list,
                },
            )
            if "beta_exposures_sheet" in custom_outputs:
                title = INVESTTMENT + " Beta Sensitivity Contributors"
                rsh.generate_beta_exposures_sheet(
                    writer,
                    fund,
                    holdings_date,
                    title,
                    data={
                        "macro_beta_decomp_df": macro_beta_decomp_df,
                        "sector_beta_decomp_df": sector_beta_decomp_df,
                        "risk_beta_exposure_top_n_list": risk_beta_exposure_top_N_list,
                        "risk_beta_exposure_bottom_n_list": risk_beta_exposure_bottom_N_list,
                    },
                )
            if INVESTTMENT == "CRM":
                try:
                    values = {}
                    for x in analyst_exposure_df.index.values:
                        if '_' in x:
                            values[x] = x.split("_")[-1].upper()
                    analyst_exposure_df.index = analyst_exposure_df.index.to_series().replace(values, regex=True)
                    values = {}
                    for x in analyst_beta_adj_exposure_df.index.values:
                        if '_' in x:
                            values[x] = x.split("_")[-1].upper()
                    analyst_beta_adj_exposure_df.index = analyst_beta_adj_exposure_df.index.to_series().replace(values, regex=True)
                except:
                    pass
            title = INVESTTMENT + " Exposure Report"
            rsh.generate_exp_report_sheet(
                writer,
                fund,
                holdings_date,
                title,
                data=[
                    {
                        "Strategy exposure": strat_exposure_df,
                        "Strategy Beta Exposure": strat_beta_adj_exposure_df,
                    },
                    {
                        "Analyst Exposure": analyst_exposure_df,
                        "Analyst Beta Exposure": analyst_beta_adj_exposure_df,
                    },
                    {
                        "AssetType Exposure": assettype_exposure_df,
                        "AssetType Beta Exposure": assettype_beta_adj_exposure_df,
                    },
                    {
                        "Sector Exposure": sector_exposure_df,
                        "Sector Beta Exposure": sector_beta_adj_exposure_df,
                    },
                    {
                        "Industry Exposure": industry_exposure_df,
                        "Industry Beta Exposure": industry_beta_adj_exposure_df,
                    },
                    {
                        "Country Exposure": country_exposure_df,
                        "Country Beta Exposure": country_beta_adj_exposure_df,
                    },
                    {
                        "Market Cap Exposure": mktcap_exposure_df,
                        "Market Cap Beta Exposure": mktcap_beta_adj_exposure_df,
                    },
                ],
            )
            
            title = INVESTTMENT + " VaR Report"
            rsh.generate_var_report_sheet(
                writer,
                fund,
                holdings_date,
                title,
                data=[
                    {
                        "var_top10": top_var_contributors,
                        "var_bottom10": top_var_diversifiers,
                    },
                    {
                        "Analyst VaR": None if var_structured_analyst is None else var_structured_analyst.fillna(0), 
                        "Asset Type VaR":None if  var_structured_assettype is None else  var_structured_assettype.fillna(0),
                        "Strat VaR": var_structured_strat.fillna(0),
                        "Sector VaR": var_structured_sector.fillna(0),
                        "Industry VaR": var_structured_industry.fillna(0),
                        "Country VaR": var_structured_country.fillna(0),
                        "MarketCap VaR": var_structured_mcap.fillna(0),
                    },
                ],
            )
            title = INVESTTMENT + " Options Analysis & Stress Tests"
            rsh.generate_options_stress_sheet(
                writer,
                fund,
                holdings_date,
                title,
                data=[
                    {
                        'options_delta_adj_exposure_df':  options_delta_adj_exposure_df,
                        'options_delta1_exposure_df': options_delta1_exposure_df,
                        'greek_sensitivities_df': greek_sensitivities_df,
                        'options_premium_df': options_premium_df,
                    },
                    {
                        'stress_test_price_vol_results_df':
                        stress_test_price_vol_results_df,
                        'stress_test_beta_price_vol_results_df':
                        stress_test_beta_price_vol_results_df,
                        'stress_test_price_vol_exposure_results_df':
                        stress_test_price_vol_exposure_results_df,
                    },
                    {
                        "stress_test_filtered_df": stress_test_filtered_df,
                    }
                ]
            )

            title = INVESTTMENT + " Delta Report"
            if "generate_delta_sheet" in custom_outputs:
                rsh.generate_option_delta_sheet(
                    writer,
                    fund,
                    holdings_date,
                    title,
                    data={
                        "options_delta": options_delta_df,
                    },
                )

            title = INVESTTMENT + " Position Report"
            rsh.generate_positions_summary_sheet(
                writer,
                fund,
                holdings_date,
                title,
                position_summary,
            )
            title = INVESTTMENT + " Position Breakdown Report"
            rsh.generate_positions_breakdown_sheet(
                writer,
                fund,
                holdings_date,
                title,
                position_breakdown.sort_values('Exposure', ascending = False).fillna(0),
            )
            title = INVESTTMENT + " Factor Correlation Report"
            rsh.generate_factor_correlations_sheet(
                writer,
                matrix_correlation,
            )

        writer.close()
        logger.info(f"<--------------------------------  the run for {fund} is complete")
