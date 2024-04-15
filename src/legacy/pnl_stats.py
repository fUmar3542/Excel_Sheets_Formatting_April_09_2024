import datetime 
import config
import numpy as np
import pandas as pd

ANNUALIZATION_FACTOR = config.global_settings.get("annualization_factor", 252)


#ANNUALIZATION_FACTOR = 252

def DD_Abs(X):
    r"""
    Calculate the Drawdown (DD) of a returns series
    using uncompounded cumulative returns.

    Parameters
    ----------
    X : 1d-array
        Returns series, must have Tx1 size.

    Raises
    ------
    ValueError
        When the value cannot be calculated.

    Returns
    -------
    value : float
        DD of an uncompounded cumulative returns.

    """

    a = np.array(X, ndmin=2)
    if a.shape[0] == 1 and a.shape[1] > 1:
        a = a.T
    if a.shape[0] > 1 and a.shape[1] > 1:
        raise ValueError("returns must have Tx1 size")

    prices = np.array(a)+1
    NAV = prices.cumprod() # np.cumsum(np.array(prices), axis=0)

    peak = -99999
    n = 0
    DD_list = []

    for v in NAV:
        if v > peak:
            peak = v
        DD = (peak - v)/peak
        if DD > 0:
            # value += DD
            DD_list.append(DD)

    return DD_list[-1] if len(DD_list)>0 else 0 


def MDD_Abs(X):
    r"""
    Calculate the Maximum Drawdown (MDD) of a returns series
    using uncompounded cumulative returns.

    Parameters
    ----------
    X : 1d-array
        Returns series, must have Tx1 size.

    Raises
    ------
    ValueError
        When the value cannot be calculated.

    Returns
    -------
    value : float
        MDD of an uncompounded cumulative returns.

    """

    a = np.array(X, ndmin=2)
    if a.shape[0] == 1 and a.shape[1] > 1:
        a = a.T
    if a.shape[0] > 1 and a.shape[1] > 1:
        raise ValueError("returns must have Tx1 size")

    #prices = np.insert(np.array(a), 0, 1, axis=0)
    prices = np.array(a)+1
    NAV = prices.cumprod()# np.cumsum(np.array(prices), axis=0)
    maxDD = 0
    peak = -99999
    for v in NAV:
        if v > peak:
            peak = v
        DD = (peak - v)/peak
        if DD > maxDD:
            maxDD = DD

    maxDD = np.array(maxDD).item()

    return maxDD

def clean_nav(aum: pd.DataFrame, firm_wide: bool) -> pd.DataFrame:
    clean_aum = convert_aum_columns(aum)
    if firm_wide:
        daily_nav_agg = clean_aum.groupby("PeriodEndDate").agg(
            {"DailyBookPL": "sum", "EndBookNAV": "sum", "PeriodEndDate": "first"}
        )
        daily_nav = daily_nav_agg.copy()
    else:
        daily_nav = aum.copy()

    # calculate returns
    daily_nav["ret"] = daily_nav["DailyBookPL"] / daily_nav["EndBookNAV"].shift(1)

    daily_nav.set_index(["PeriodEndDate"], inplace=True)

    return daily_nav


def clean_nav_extra_filter(daily_nav: pd.DataFrame) -> pd.DataFrame:
    # # keep only days, where abs or ret is lower than 1
    daily_nav = daily_nav.loc[abs(daily_nav["ret"]) < 1]

    return daily_nav

def convert_aum_columns(aum: pd.DataFrame) -> pd.DataFrame:

    """ensure right data types for aum columns"""
    aum["PeriodEndDate"] = pd.to_datetime(aum["PeriodEndDate"]).dt.date
    for col in aum.columns:
        if "PNL" in col or "NAV" in col:
            aum[col].astype(float)
    return aum

def return_analysis(AUM: pd.DataFrame, holdings_date, FirmName) -> pd.DataFrame:
    res1 = single_return_analysis(AUM, holdings_date, FirmName) 
    res = res1
    if FirmName=="CRM": # run thhe return analysis a second time: starting on min(last years last date, inceptiondate)
        firstdtthisyear = datetime.date(pd.to_datetime(holdings_date).year,1,1)
        AUM2 = AUM.copy()
        AUM2.index = pd.to_datetime(AUM2.index)
        #lastyearlastdt = AUM2.loc[:firstdtthisyear,:].sort_index(ascending=False).index[0].date()
        AUM2 = AUM2.loc[firstdtthisyear:,:]
        res2= single_return_analysis(AUM2, holdings_date, FirmName) 
        # arrange both df in a single table
        res2.rename(columns={'Fund':'Fund YTD','SPTR Index':'S&P TR YTD'},inplace=True)
        res1.rename(columns={'Fund':'Fund ITD','SPTR Index':'S&P TR ITD'},inplace=True)
        res=pd.concat([res1,res2],axis=1)
        res = res[['Fund ITD','Fund YTD','S&P TR ITD','S&P TR YTD']]
    return res

def single_return_analysis(AUM: pd.DataFrame, holdings_date, FirmName) -> pd.DataFrame:
    return_analysis_dict = {}
    if FirmName == "IBIS":
        bench_names =["SPX Index", "CCMP Index"]  #adds Nasdaq to list of benchmarks if IBIS 
    elif FirmName == "CRM":
        bench_names = ["SPTR Index"]
    else: # FirmName == "1623 Capital" or other
        bench_names = ["SPX Index"]
        
    asset_cols = ["ret"] + bench_names
        
    # 1. last day ret
    last_day_return = AUM[asset_cols].iloc[-1:, :]
    columns = last_day_return.columns
    index = last_day_return.index
    return_analysis_dict["Last Day Return"] = last_day_return

    # 2.mtd_return
    AUM["month"] = pd.to_datetime(AUM.index).strftime("%Y-%m")
    amon = pd.DatetimeIndex(AUM["month"]).month.tolist()
    ayear = pd.DatetimeIndex(AUM["month"]).year.tolist()
    bmon = [i for i, x in enumerate(amon) if ((x == pd.to_datetime(holdings_date).month ))]
    byear = [i for i, x in enumerate(ayear) if ((x == pd.to_datetime(holdings_date).year))]
    common = [i for i in bmon if i in byear]
    AUM_MTD = AUM.iloc[common][asset_cols]
    MTD_return = pd.DataFrame(
        ((1 + AUM_MTD).cumprod() - 1).iloc[-1, :], index=columns, columns=index).T
    return_analysis_dict["MTD Return"] = MTD_return
    
    # 3. ytd return
    AUM["year"] = pd.to_datetime(AUM.index).strftime("%Y")
    current_year = [i for i, x in enumerate(ayear) if ((x == pd.to_datetime(holdings_date).year))]
    AUM_YTD = AUM.iloc[current_year][asset_cols]
    YTD_return = pd.DataFrame(
        ((1 + AUM_YTD).cumprod() - 1).iloc[-1, :], index=columns, columns=index ).T
    return_analysis_dict["YTD Return"] = YTD_return
    
    # 4. cumul ret
    cumul_ret = pd.DataFrame(
        ((1 + AUM[asset_cols]).cumprod() - 1).iloc[-1, :],
        index=columns,
        columns=index, ).T
    return_analysis_dict["Cumulative Return"] = cumul_ret
    
    # 5. annualized ret
    ann_ret = pd.DataFrame(
        (
            (1 + AUM[asset_cols]).cumprod()
            ** (ANNUALIZATION_FACTOR / len(AUM))
            - 1
        ).iloc[-1, :],
        index=columns,
        columns=index,
    ).T
    return_analysis_dict["Annualized Return"] = ann_ret
    
    # 6. daily volatility
    daily_volatility = pd.DataFrame(
        np.std(AUM[asset_cols]), index=columns, columns=index
    ).T
    return_analysis_dict["Daily Volatility"] = daily_volatility
    # 6. annualized volatility
    annualized_volatility = pd.DataFrame(
        np.std(AUM[asset_cols]) * (np.sqrt(ANNUALIZATION_FACTOR)),
        index=columns,
        columns=index,
    ).T
    return_analysis_dict["Annualized Volatility"] = annualized_volatility
    
    # 7. sharpe ratio
    sharpe_ratio = ann_ret / annualized_volatility
    return_analysis_dict["Sharpe Ratio"] = sharpe_ratio
    
    # 8. downside volatility
    downside_volatility_df_list=[]
    for col in AUM[asset_cols].columns:
        downside_volatility_df = pd.DataFrame(
            np.sqrt((AUM[[col]].loc[AUM[col] < 0]**2).sum() /len(AUM)),
            index=[col],
            columns=index,
        ).T
        downside_volatility_df_list.append(downside_volatility_df)
    downside_volatility = pd.concat(
        downside_volatility_df_list, axis=1
    )
    return_analysis_dict["Downside Deviation"] = downside_volatility
    
    # 9. Annualized downside volatility
    annualized_downside_volatility =  downside_volatility* (np.sqrt(ANNUALIZATION_FACTOR))
    return_analysis_dict["Annualized Downside Deviation"] = annualized_downside_volatility
    
    # 10. sortino ratio
    sortino_ratio = ann_ret / annualized_downside_volatility
    return_analysis_dict["Sortino Ratio"] = sortino_ratio
    
    # 11. up_days
    up_days_df_list = []
    for col in AUM[asset_cols].columns:
        up_days_df = pd.DataFrame(
            len(AUM[col].loc[AUM[col] > 0]), index=[col], columns=index
        ).T
        up_days_df_list.append(up_days_df)
    up_days = pd.concat(up_days_df_list, axis=1)
    return_analysis_dict["Up Days"] = up_days
    
    # 12. down_days
    down_days_df_list = []
    for col in AUM[asset_cols].columns:
        down_days_df = pd.DataFrame(
            len(AUM[col].loc[AUM[col] < 0]), index=[col], columns=index
        ).T
        down_days_df_list.append(down_days_df)
    down_days = pd.concat(down_days_df_list, axis=1)
    return_analysis_dict["Down Days"] = down_days
    
    # 13. largest up day
    largest_up_day = pd.DataFrame(
        AUM[asset_cols].max(), index=columns, columns=index
    ).T
    return_analysis_dict["Largest Up Day"] = largest_up_day
    
    # 14. largest down day
    largest_down_day = pd.DataFrame(
        AUM[asset_cols].min(), index=columns, columns=index
    ).T
    return_analysis_dict["Largest Down Day"] = largest_down_day
    
    # 15. current drawdown
    current_drawdown_df_list = []
    AUM.dropna(inplace=True)
    for col in AUM[asset_cols].columns:
        current_drawdown_df = pd.DataFrame(
            DD_Abs(AUM[col].values), index=[col], columns=index
        ).T
        current_drawdown_df_list.append(current_drawdown_df)
    current_drawdown = pd.concat(current_drawdown_df_list, axis=1)
    current_drawdown.replace(
        {np.nan: "--"}, regex=True, inplace=True
    )
    return_analysis_dict["Current Drawdown"] = current_drawdown
    
    # 16. max drawdown
    max_drawdown_df_list = []
    for col in AUM[asset_cols].columns:
        max_drawdown_df = pd.DataFrame(
            MDD_Abs(AUM[col].values), index=[col], columns=index
        ).T
        max_drawdown_df_list.append(max_drawdown_df)
    max_drawdown = pd.concat(max_drawdown_df_list, axis=1)
    return_analysis_dict["Maximum Drawdown"] = max_drawdown
    
    # 17. CALMAR
    calmar = ann_ret / max_drawdown
    calmar.replace(
        {np.nan: "--", np.inf: "--", -np.inf: "--"}, regex=True, inplace=True
    )
    return_analysis_dict["Return over Drawdown (CALMAR)"] = calmar
    return_analysis_df = (
        pd.concat(return_analysis_dict, axis=0)
        .reset_index(level=0)
        .rename({"level_0": "Return Analysis"}, axis=1)
    )
    return_analysis_df.set_index(["Return Analysis"], inplace=True)
    return_analysis_df.rename(columns={'ret':'Fund','SPX Index':'S&P', 'CCMP Index':'Nasdaq'}, inplace=True)
    
    return return_analysis_df


def comparative_statistics(AUM: pd.DataFrame, return_analysis_df: pd.DataFrame, holdings_date, FirmName):
    if FirmName !="CRM":
        res = single_comparative_statistics(AUM, return_analysis_df, FirmName) 
    else:
        # run for the usual ITD:
        ra2 = return_analysis_df[["Fund ITD",'S&P TR ITD']].rename(columns={"Fund ITD":"Fund",'S&P TR ITD':"SPTR Index"})
        res2 = single_comparative_statistics(AUM, ra2, FirmName) 
        res2.rename(columns={"SPTR Index":"ITD"},inplace=True)
        # run for year to date 
        firstdtthisyear = datetime.date(pd.to_datetime(holdings_date).year,1,1)
        AUM2 = AUM.copy()
        AUM2.index = pd.to_datetime(AUM2.index)
        #lastyearlastdt = AUM2.loc[:firstdtthisyear,:].sort_index(ascending=False).index[0].date()
        AUM2 = AUM2.loc[firstdtthisyear:,:]
        ra1 = return_analysis_df[["Fund YTD",'S&P TR YTD']].rename(columns={"Fund YTD":"Fund",'S&P TR YTD':"SPTR Index"})
        res1 = single_comparative_statistics(AUM2, ra1, FirmName) 
        res1.rename(columns={"SPTR Index":"YTD"},inplace=True)

        res=pd.concat([res2,res1,],axis=1)
    return res

def single_comparative_statistics(AUM: pd.DataFrame, return_analysis_df: pd.DataFrame, FirmName):
    comparative_statistics_dict = {}
    if FirmName == "IBIS":
        bench_names =["SPX Index", "CCMP Index"]  #adds Nasdaq to list of benchmarks if IBIS 
    elif FirmName == "CRM":
        bench_names = ["SPTR Index"]
    else:
        bench_names = ["SPX Index"]
    
    # temporarily inverse renaming for accessibility 
    ra_tmp = return_analysis_df.rename(columns={'S&P':'SPX Index', 'Nasdaq':'CCMP Index'})
    
    # 1. beta
    beta_df_list = []
    for col in AUM[bench_names].columns:
        beta_df = pd.DataFrame(
            (AUM[["ret", col]].cov() / np.nanvar(AUM[[col]])).iloc[0, 1],
            columns=[col],
            index=["Beta"],
        )
        beta_df.reset_index(inplace=True, drop=True)
        beta_df_list.append(beta_df)
    beta_df = pd.concat(beta_df_list, axis=1)
    comparative_statistics_dict["Beta"] = beta_df
    
    # 2. correlation
    correlation_df_list = []
    correlation_df = pd.DataFrame(
        AUM[["ret"]+ bench_names].corr().iloc[0, 1:].values,
        #(beta_df.values[0, :] * ra_tmp.loc[ra_tmp.index == "Annualized Volatility" ][bench_names] / ra_tmp.loc[ra_tmp.index == "Annualized Volatility" ]["Fund"].values[0]).values,
        columns=bench_names,
        index=["Correlation"],
    )
    correlation_df.reset_index(inplace=True, drop=True)
    correlation_df_list.append(correlation_df)
    correlation_df = pd.concat(correlation_df_list, axis=1)
    comparative_statistics_dict["Correlation"] = correlation_df
    
    # # 3. up capture
    # # XM:f for loop on cols deleted: up cature of SPX by itself makes no sense 
    # # XM : modified formula accumulation of ln returns instead of simple returns 
    # old code 
    # (
    #     ((1 + AUM[["ret", "SPX Index"]].loc[AUM["SPX Index"] > 0]["ret"]).cumprod() - 1).iloc[-1:]
    #     / ((1 + AUM[["ret", col]].loc[AUM[col] > 0][col]).cumprod() - 1).iloc[
    #         -1:
    #     ]
    # ).values
    up_capture_df_list=[]
    for col in AUM[bench_names].columns:
        up_capture_df = pd.DataFrame( (1 + AUM[["ret", col]].loc[AUM[col] > 0]["ret"]).apply(np.log).sum()/(1 + AUM[["ret", col]].loc[AUM[col] > 0][col]).apply(np.log).sum(),
        columns=[col], 
        index=["Up Capture"],)
        up_capture_df.reset_index(inplace=True, drop=True)
        up_capture_df_list.append(up_capture_df)
    up_capture_df = pd.concat(up_capture_df_list, axis=1)
    comparative_statistics_dict["Up Capture"] = up_capture_df
    # 4. down capture
    # XM : modified same as up capture
    # down_capture_df_list = []
    # for col in AUM[["ret", "SPX Index"]].columns[1:]:
    #     down_capture_df = pd.DataFrame(
    #         (
    #             ((1 + AUM[["ret", col]].loc[AUM[col] < 0]["ret"]).cumprod() - 1).iloc[
    #                 -1:
    #             ]
    #             / ((1 + AUM[["ret", col]].loc[AUM[col] < 0][col]).cumprod() - 1).iloc[
    #                 -1:
    #             ]
    #         ).values,
    #         columns=[col],
    #         index=["Down Capture"],
    #     )
    #     down_capture_df_list.append(down_capture_df)

    down_capture_df_list=[]
    for col in AUM[bench_names].columns:
        down_capture_df = pd.DataFrame( (1 + AUM[["ret", col]].loc[AUM[col] < 0]["ret"]).apply(np.log).sum()/(1 + AUM[["ret", col]].loc[AUM[col] < 0][col]).apply(np.log).sum(),
        columns=[col], 
        index=["Down Capture"],)
        down_capture_df.reset_index(inplace=True, drop=True)
        down_capture_df_list.append(down_capture_df)
    down_capture_df = pd.concat(down_capture_df_list, axis=1)
    comparative_statistics_dict["Down Capture"] = down_capture_df
    
    comparative_statistics_df = (
        pd.concat(comparative_statistics_dict, axis=0)
        .reset_index(level=0)
        .rename({"level_0": "Comparative Statistics"}, axis=1)
    )
    comparative_statistics_df.set_index(["Comparative Statistics"], inplace=True)
    comparative_statistics_df.rename(columns={'SPX Index':'S&P', 'CCMP Index':'Nasdaq'}, inplace=True)
    return comparative_statistics_df


def monthly_pnl_stats(AUM: pd.DataFrame) -> pd.DataFrame:
    # estimate monthly rets
    AUM.index = pd.to_datetime(AUM.index)
    monthly_rets = AUM["ret"].resample("M").agg(lambda x: (x + 1).prod() - 1)
    monthly_rets = pd.DataFrame(
        monthly_rets.values, index=monthly_rets.index, columns=["monthly_rets"]
    )
    years = list(monthly_rets.index.strftime("%Y").unique())
    monthly_rets.index = monthly_rets.index.strftime("%Y-%m-%d")
    monthly_rets.reset_index(inplace=True)
    monthly_rets.rename(columns={"index": "date"}, inplace=True)
    df_list = []
    for year in years:
        df = monthly_rets.loc[monthly_rets["date"].str.contains(year)]
        start_month = pd.to_datetime(df["date"].iloc[0]).strftime("%m")
        if start_month > "01":
            start = f"{year}-{'01'}-{'31'}"
            pre_date_range = pd.date_range(
                start=start,
                end=(
                    pd.to_datetime(df["date"].iloc[0]) - pd.offsets.MonthEnd()
                ).strftime("%Y-%m-%d"),
                freq="M",
            )
            pre_date_range = pre_date_range.strftime("%Y-%m-%d")
            pre_date_range = pd.DataFrame(
                np.concatenate(
                    (
                        pre_date_range.values[:, None],
                        np.array(["--"] * len(pre_date_range))[:, None],
                    ),
                    axis=1,
                ),
                columns=["date", "Fund"],
                index=range(0, len(pre_date_range)),
            )
            df = pd.concat([pre_date_range, df], axis=0)
        end_month = pd.to_datetime(df["date"].iloc[-1]).strftime("%m")
        if start_month < "12":
            start = pd.to_datetime(df["date"].iloc[-1]) + pd.offsets.MonthEnd()
            post_date_range = pd.date_range(
                start=start,
                end=f"{year}-{'12'}-{'31'}",
                freq="M",
            )
            post_date_range = post_date_range.strftime("%Y-%m-%d")
            post_date_range = pd.DataFrame(
                np.concatenate(
                    (
                        post_date_range.values[:, None],
                        np.array(["--"] * len(post_date_range))[:, None],
                    ),
                    axis=1,
                ),
                columns=["date", "Fund"],
                index=range(0, len(post_date_range)),
            )
        df = pd.concat([df, post_date_range], axis=0)
        df_list.append(df)
    monthly_rets = pd.concat(df_list, axis=0)
    monthly_rets.replace(
        {np.nan: "--"}, regex=True, inplace=True
    )
    monthly_rets_arr = np.array(monthly_rets["monthly_rets"])[:, None]
    modulo_remainder = monthly_rets_arr.shape[0] % 12
    if modulo_remainder == 0:
        num_rows = int(monthly_rets_arr.shape[0] / 12)
    else:
        num_rows = int(monthly_rets_arr.shape[0] / 12)
    monthly_rets = pd.DataFrame(
        monthly_rets_arr.reshape((num_rows, 12)),
        columns=[
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
        index=years,
    )
    return monthly_rets
