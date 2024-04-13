"""creates pnl report sheet"""
from typing import Dict

import pandas as pd

import src.excel_utils.excel_utils as eu
from src.excel_utils.header import insert_header
from src.excel_utils.set_up_workbook import set_up_workbook
from src.excel_utils.sheet_format import format_dashboard_worksheet
from src.layouts.layouts import DashboardLayout, PnlReportLayout

from ..report_items.report_table import ReportTable
from ..report_items.snap_operations import SnapType
from ..report_items.worksheet_chart import WorksheetChart
from datetime import datetime

PNLDATA_SHEET_NAME = "PNLReport"


def generate_pnlreport_sheet(
    writer,
    fund: str,
    holdings_date: str,
    title: str,
    data_dict: Dict[str, pd.DataFrame],
    FirmName) -> None:
    """generates pnl report sheet"""

    layout = PnlReportLayout()     #DashboardLayout()
    styles, worksheet = set_up_workbook(writer, sheet_name=PNLDATA_SHEET_NAME, temp="PNL")
    date_obj = datetime.strptime(holdings_date, "%Y-%m-%d")
    insert_header(worksheet, styles, layout, holdings_date=date_obj, fund=fund, title=title)

    daily_returns_chart = WorksheetChart(
        initial_position=(1, 4),
        initial_rows=20,
        table_name="aum_clean",
        columns=[
            "Daily Return",
        ],
        categories_name="index_date",
        page_layout=layout,
        title="Daily vs. Cumulative Returns",
        axis_format="percentage",
        custom_height=445,
    )

    cumulative_returns_chart = WorksheetChart(
        initial_position=(1, 5),
        initial_rows=10,
        table_name="aum_clean",
        columns=[
            "Cumulative return",
        ],
        categories_name="index_date",
        page_layout=layout,
        axis_format="percentage",
    )
    eu.insert_dual_axis_chart(
        writer, worksheet, daily_returns_chart, cumulative_returns_chart
    )

    return_analysis_stats = ReportTable(
        data=data_dict.get("return_analysis_stats"),  # type: ignore
        values_format=styles.get("percentage"),
        header_format=styles.get("table_header"), 
        total_format=styles.get("table_total"),
        table_name="return_analysis_stats",
        initial_position=(1, 27),
    )
    eu.insert_table(worksheet, return_analysis_stats)

    dd = data_dict.get("perf_ratio_stats")
    dd.index.name="perf analysis"
    perf_ratio_stats = ReportTable(
        data=dd,  # type: ignore
        values_format=styles.get("float"),
        header_format=styles.get("table_header"), 
        total_format=styles.get("table_total"),   
        table_name="perf_ratio_stats",
        snap_element=return_analysis_stats,
        snap_mode=SnapType.DOWN,
        margin=2,
    )
    eu.insert_table(worksheet, perf_ratio_stats)

    comparative_analysis_stats = ReportTable(
        data=data_dict.get("comparative_analysis_stats"),  # type: ignore
        header_format=styles.get("table_header"), 
        total_format=styles.get("table_total"),   
        values_format=styles.get("percentage"),
        specific_cells_format = [('Beta','S&P',styles.get("float")), ('Correlation','S&P',styles.get("float"))] 
            +[('Beta','Nasdaq',styles.get("float")), ('Correlation','Nasdaq',styles.get("float"))] 
            +[('Beta','YTD',styles.get("float")),('Beta','ITD',styles.get("float")), ('Correlation','YTD',styles.get("float")),('Correlation','ITD',styles.get("float"))],
        table_name="comparative_analysis_stats",
        snap_element=return_analysis_stats,
        snap_mode=SnapType.RIGHT,
        margin=1,
    )
    eu.insert_table(worksheet, comparative_analysis_stats)

    if FirmName != "CRM":
        fund_AUM = ReportTable(
            data=data_dict.get("fund_AUM"),  # type: ignore
            header_format=styles.get("table_header"), 
            total_format=styles.get("table_total"),   
            values_format=styles.get("currency"),
            table_name="fund_AUM",
            snap_element=comparative_analysis_stats,
            snap_mode=SnapType.DOWN,
            margin=2,
        )
        eu.insert_table(worksheet, fund_AUM)

    if  FirmName =="IBIS":
        monthly_pnl_stats = ReportTable(
            data=data_dict.get("monthly_pnl_stats"),  # type: ignore
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"), 
            total_format=styles.get("table_total"),   
            table_name="monthly_returns",
            snap_element=perf_ratio_stats,
            snap_mode=SnapType.DOWN,
            margin=2,
        )
        eu.insert_table(worksheet, monthly_pnl_stats)

    refsnap = monthly_pnl_stats if FirmName =="IBIS" else perf_ratio_stats

    volatility_stats = WorksheetChart(
        snap_element=refsnap,
        snap_mode=SnapType.DOWN,
        margin=2,
        table_name="aum_clean",
        columns=["Volatility", "20D Volatility"],
        categories_name="index_date",
        stacked=False,
        title="Rolling 20 Day Volatility vs. Rolling 1 Year Volatility",
        axis_format="percentage",
        page_layout=layout,
        initial_rows=24,
    )
    eu.insert_chart(
        writer,
        worksheet,
        volatility_stats,
        chart_type="line",
        stacked=False,
    )

    volatility_budget = WorksheetChart(
        snap_element=refsnap,
        snap_mode=SnapType.DOWN,
        margin=28,
        table_name="aum_clean",
        columns=["20D Volatility", "Volatility Budget"],
        categories_name="index_date",
        stacked=False,
        title="Volatility Budget",
        axis_format="percentage",
        page_layout=layout,
        initial_rows=20,
    )
    eu.insert_chart(
        writer,
        worksheet,
        volatility_budget,
        chart_type="line",
        stacked=False,
    )

    format_dashboard_worksheet(worksheet, layout)
