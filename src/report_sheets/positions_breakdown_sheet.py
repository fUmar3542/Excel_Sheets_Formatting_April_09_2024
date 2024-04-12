import pandas as pd

import src.excel_utils.excel_utils as eu
from src.excel_utils.header import insert_header
from src.excel_utils.set_up_workbook import set_up_workbook
from src.excel_utils.sheet_format import format_dashboard_worksheet
from src.layouts.layouts import PositionsBreakdownDashboardLayout
from src.report_items.report_table import ReportTable
from datetime import datetime

SHEET_NAME = "PositionsBreakdown"


def generate_positions_breakdown_sheet(
    writer,
    fund: str,
    holdings_date: str,
    title: str,
    data: pd.DataFrame,
) -> None:
    """generates positions breakdown report"""

    layout = PositionsBreakdownDashboardLayout()
    styles, worksheet = set_up_workbook(writer, sheet_name=SHEET_NAME)
    date_obj = datetime.strptime(holdings_date, "%Y-%m-%d")
    insert_header(worksheet, styles, layout, fund, date_obj, title=title)

    raw_formats = [
        None,
        None,
        "integer",
        "percentage",
        "float",
        "float",
        "percentage",
        *["currency"] * 2,
        "percentage",  # market value + 1% stock
        *["currency"] * 4,  # delta, gamma...
        "currency",
        "percentage",  # 10% stock
    ]
    value_formats = [styles.get(fmt) for fmt in raw_formats]
    report_table = ReportTable(
        initial_position=(1, 4),
        data=data,
        header_format=styles.get("table_header"), 
        total_format=styles.get("table_total"),   
        table_name="position_breakdown",
        values_format=value_formats,
    )

    eu.insert_table(worksheet, report_table)

    format_dashboard_worksheet(worksheet, layout)
