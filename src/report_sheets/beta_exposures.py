from typing import Dict

import src.excel_utils.excel_utils as eu
import src.excel_utils.report_group_operations as rgo
from src.excel_utils.header import insert_header
from src.excel_utils.set_up_workbook import set_up_workbook
from src.excel_utils.sheet_format import format_dashboard_worksheet
from src.layouts.layouts import WideDashboardLayout1

from ..report_items.report_table import ReportTable
from ..report_items.snap_operations import SnapType
from ..report_items.worksheet_chart import WorksheetChart
from datetime import datetime

SHEET_NAME = "BetaExposures"


def increase_size(worksheet_chart):
    num_rows = worksheet_chart.snap_element.data.shape[0]
    if num_rows < 4:
        num_rows = num_rows + 1
    worksheet_chart.custom_height = (num_rows+1) * 21
    return worksheet_chart


def generate_beta_exposures_sheet(
    writer,
    fund: str,
    holdings_date: str,
    title: str,
    data: Dict,
) -> None:
    layout = WideDashboardLayout1()
    styles, worksheet = set_up_workbook(writer, sheet_name=SHEET_NAME)
    date_obj = datetime.strptime(holdings_date, "%Y-%m-%d")
    insert_header(worksheet, styles, layout, fund, date_obj, title=title)

    #data.get("macro_beta_decomp_df")
    # #.set_index('Macro Factor Sensitivity', inplace=True)
    
    macro_beta_decomp_df = ReportTable(
        data=data.get("macro_beta_decomp_df"),  # type: ignore
        table_name="macro_beta_decomp_df_fe",
        header_format=styles.get("table_header"), 
        total_format=styles.get("table_total_pct"),        
        values_format=styles.get("percentage"),
        initial_position=(1, 4),
    )
    eu.insert_table(worksheet, macro_beta_decomp_df)

    macro_sensitivity_chart = WorksheetChart(
        table_name="macro_beta_decomp_df_fe",
        columns=[
            "FactorExp",
        ],
        categories_name="Macro Sensitivities",
        snap_element=macro_beta_decomp_df,
        snap_mode=SnapType.RIGHT,
        page_layout=layout,
        margin=1,
        axis_format="percentage",
    )
    macro_sensitivity_chart.custom_width = 1330
    macro_sensitivity_chart = increase_size(macro_sensitivity_chart)
    eu.insert_chart(
        writer,
        worksheet,
        macro_sensitivity_chart,
    )

    sector_beta_decomp_df = ReportTable(
        data=data.get("sector_beta_decomp_df"),  # type: ignore
        table_name="sector_beta_decomp_df_fe",
        values_format=styles.get("percentage"),
        header_format=styles.get("table_header"), 
        total_format=styles.get("table_total_pct"),
        snap_element=macro_beta_decomp_df,
        snap_mode=SnapType.DOWN,
    )
    eu.insert_table(worksheet, sector_beta_decomp_df)
    sector_sensitivity_chart = WorksheetChart(
        table_name="sector_beta_decomp_df_fe",
        columns=[ "FactorExp",],
        categories_name="Sector Sensitivities",
        snap_element=sector_beta_decomp_df,
        snap_mode=SnapType.RIGHT,
        page_layout=layout,
        margin=1,
        axis_format="percentage",
    )
    sector_sensitivity_chart = increase_size(sector_sensitivity_chart)
    eu.insert_chart(writer, worksheet, sector_sensitivity_chart)

    format_dashboard_worksheet(worksheet, layout)

    grouped_top = rgo.group_items(
        data.get("risk_beta_exposure_top_n_list"), 2  # type: ignore
    )
    grouped_bottom = rgo.group_items(
        data.get("risk_beta_exposure_bottom_n_list"), 2  # type: ignore
    )

    report_tables = []
    ancor_element = sector_beta_decomp_df
    row_number = 1
    for top, bottom in zip(grouped_top, grouped_bottom):
        row_group_tables = rgo.init_row(styles, ancor_element, top, bottom, row_number,"beta_exposure")
        report_tables.extend(row_group_tables)
        ancor_element = row_group_tables[0]
        row_number = row_number + 1

    for report_table in report_tables:
        eu.insert_table(worksheet, report_table)
