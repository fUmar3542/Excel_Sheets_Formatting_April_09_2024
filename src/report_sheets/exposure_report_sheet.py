from typing import Dict, List

import src.excel_utils.excel_utils as eu
import src.excel_utils.report_group_operations as rgo
from src.excel_utils.header import insert_header
from src.excel_utils.set_up_workbook import set_up_workbook
from src.excel_utils.sheet_format import format_dashboard_worksheet
from src.layouts.layouts import ExposureDashboardLayout

from ..report_items.snap_operations import SnapType
from ..report_items.worksheet_chart import WorksheetChart4
from datetime import datetime

SHEET_NAME = "ExpReport"


def generate_exp_report_sheet(
    writer,
    fund: str,
    holdings_date: str,
    title: str,
    data: List[Dict],
) -> None:
    """generates exposure report"""
    layout = ExposureDashboardLayout()
    styles, worksheet = set_up_workbook(writer, sheet_name=SHEET_NAME)
    date_obj = datetime.strptime(holdings_date, "%Y-%m-%d")
    insert_header(worksheet, styles, layout, fund, date_obj, title=title)

    report_tables = []
    report_charts = []

    first_idx = 0 if fund =="Firm" else 1 if len(data[1]['Analyst Exposure'])>1 else 3   #ignore the first "Strategy" tables if this is not firm level 
    
    first_row_tableid1 = list(data[first_idx].keys())[0]
    first_row_tableid2 = list(data[first_idx].keys())[1]
    first_row_tablename1 = first_row_tableid1.replace(' ','_').lower()
    #print(first_row_tablename1)
    first_row_tablename2 = first_row_tableid2.replace(' ','_').lower()
    first_row_tables = rgo.init_report_group(
        styles=styles,
    #    table_names=["strategy_exposure", "strategy_beta_exposure"],
        table_names=[first_row_tablename1, first_row_tablename2],
        tables=[
            data[first_idx].get(first_row_tableid1),
            data[first_idx].get(first_row_tableid2),
        ],  # type: ignore
        inner_snap_mode=SnapType.RIGHT,
        inner_margin=1,
        initial_position=(1, 4),  # type: ignore
    )

    report_tables.extend(first_row_tables)
    
    firstrow_chart = WorksheetChart4(
        snap_element=report_tables[0],
        snap_mode=SnapType.DOWN,
        initial_rows=5,
        page_layout=layout,
        table_name=first_row_tablename1,
        columns=["Long", "Short"],
        #categories_name=first_row_tableid1,
        title=first_row_tableid1,
        categories_name=first_row_tableid1,
        axis_format="percentage",
        custom_height=330,
        margin=2,
        custom_padding=1,
    )
    report_charts.append(firstrow_chart)
    
    ancor_element = report_tables[0]
    for row in data[first_idx+1:]:
        if len(row[list(row.keys())[0]])>1:
            row_tables, row_chart = rgo.init_2_table_row_with_chart(
                styles=styles,
                layout=layout,
                global_snap_to=ancor_element,
                left_name=list(row.keys())[0],
                left_table=list(row.values())[0],
                right_name=list(row.keys())[1],
                right_table=list(row.values())[1],
                chart_columns=["Long", "Short"],
            )
            ancor_element = row_tables[0]
            report_tables.extend(row_tables)
            report_charts.append(row_chart)

    for table in report_tables:
        eu.insert_table(worksheet, table)

    for report_chart in report_charts:
        eu.insert_chart(writer, worksheet, report_chart)

    format_dashboard_worksheet(worksheet, layout)
