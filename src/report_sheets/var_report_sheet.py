from typing import Dict, List

import src.excel_utils.excel_utils as eu
import src.excel_utils.report_group_operations as rgo
from src.excel_utils.header import insert_header
from src.excel_utils.set_up_workbook import set_up_workbook
from src.excel_utils.sheet_format import format_dashboard_worksheet
from src.layouts.layouts import NarrowDashboardLayout

from ..report_items.snap_operations import SnapType
from datetime import datetime

SHEET_NAME = "VaRReport"

def set_column_widths(worksheet, start_col, end_col, width):
    # Set the column widths. Assuming 0-index based (A=0, B=1, etc.)
    worksheet.set_column(start_col, end_col, width)

def generate_var_report_sheet(
    writer,
    fund,
    holdings_date: str,
    title: str,
    data: List[Dict],
) -> None:
    """Generates var report"""

    layout = NarrowDashboardLayout()
    styles, worksheet = set_up_workbook(writer, sheet_name=SHEET_NAME)
    date_obj = datetime.strptime(holdings_date, "%Y-%m-%d")
    insert_header(worksheet, styles, layout, fund, date_obj, title=title)

    # Define the column width for the second table here (adjust as needed)
    # This will set the width for columns B to H to 20 units.
    set_column_widths(worksheet, 1, 7, 20)

    report_tables = []
    report_charts = []

    first_row_tables = rgo.init_report_group(
        styles=styles,
        table_names=["var_top10", "var_bottom10"],
        tables=[data[0].get("var_top10")[['Inc95VaR','Inc99VaR']], data[0].get("var_bottom10")[['Inc95VaR','Inc99VaR']]],  # type: ignore
        inner_snap_mode=SnapType.RIGHT,
        inner_margin=1,
        initial_position=(1, 5),  # type: ignore
    )
    report_tables.extend(first_row_tables)

    ancor_item = report_tables[0]
    next_row_margin = 5
    for table_name, table_data in data[1].items():
        if table_data is not None:
            row_table, row_chart = rgo.init_table_with_chart(
                styles=styles,
                layout=layout,
                global_snap_to=ancor_item,
                table_name=table_name,
                table_data=table_data,
                chart_columns=["Iso95", "Iso99"],
                next_row_margin=next_row_margin,
            )
            next_row_margin = 18
            ancor_item = row_table
            report_tables.append(row_table)
            report_charts.append(row_chart)

    for table in report_tables:
        eu.insert_table(worksheet, table)

    for report_chart in report_charts:
        eu.insert_chart(writer, worksheet, report_chart, stacked=False)

    format_dashboard_worksheet(worksheet, layout)
