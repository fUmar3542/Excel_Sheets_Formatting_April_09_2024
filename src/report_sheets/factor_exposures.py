from typing import Dict

import src.excel_utils.excel_utils as eu
import src.excel_utils.report_group_operations as rgo
from src.excel_utils.header import insert_header
from src.excel_utils.set_up_workbook import set_up_workbook
from src.excel_utils.sheet_format import format_dashboard_worksheet
from src.layouts.layouts import WideDashboardLayout, WideDashboardLayout1
from ..report_items.report_table import ReportTable
from ..report_items.snap_operations import SnapType
from ..report_items.worksheet_chart import WorksheetChart4
from datetime import datetime
from src.handles.exception_handling import MyExceptions

SHEET_NAME = "FactorExposures"


def increase_size(worksheet_chart):
    try:
        num_rows = worksheet_chart.snap_element.data.shape[0]
        if num_rows < 4:
            num_rows = num_rows + 1
        worksheet_chart.custom_height = (num_rows+1) * 21
    except Exception as ex:
        MyExceptions.show_message(tab='factor_exposures.py',
                                  message="Following exception occurred during increasing the chart size\n\n" + str(
                                      ex))
    finally:
        return worksheet_chart


def generate_factor_exposures_sheet(
    writer,
    fund: str,
    holdings_date: str,
    title: str,
    data: Dict,
) -> None:
    # layout = WideDashboardLayout()
    layout = WideDashboardLayout1()
    styles, worksheet = set_up_workbook(writer, sheet_name=SHEET_NAME)
    date_obj = datetime.strptime(holdings_date, "%Y-%m-%d")
    insert_header(worksheet, styles, layout, fund, date_obj, title=title)

    try:
        data.get("macro_factor_decomp_df")
        # #.set_index(
        #     'Macro Factor Sensitivity', inplace=True)
        macro_factor_decomp_df = ReportTable(
            data=data.get("macro_factor_decomp_df"),  # type: ignore
            table_name="macro_factor_decomp_df_fe",
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total_pct"),
            values_format=styles.get("percentage"),
            initial_position=(1, 4),
        )
        eu.insert_table(worksheet, macro_factor_decomp_df)

        macro_sensitivity_chart = WorksheetChart4(
            table_name="macro_factor_decomp_df_fe",
            columns=[
                "FactorRisk",
            ],
            categories_name="Macro Sensitivities",
            snap_element=macro_factor_decomp_df,
            snap_mode=SnapType.RIGHT,
            page_layout=layout,
            margin=1,
            axis_format="percentage",
            custom_padding=1
        )
        macro_sensitivity_chart.custom_width = 1330
        macro_sensitivity_chart = increase_size(macro_sensitivity_chart)
        eu.insert_chart(
            writer,
            worksheet,
            macro_sensitivity_chart,
        )

        data.get("sector_factor_decomp_df").set_index("Sector Sensitivities", inplace=True)
        sector_factor_decomp_df = ReportTable(
            data=data.get("sector_factor_decomp_df"),  # type: ignore
            table_name="sector_factor_decomp_df_fe",
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total_pct"),
            snap_element=macro_factor_decomp_df,
            snap_mode=SnapType.DOWN,
        )
        eu.insert_table(worksheet, sector_factor_decomp_df)

        value_mapping = {
            "Consumer Discretionary": "ConsDisc",
            "Consumer Staples": "ConsStap",
            "Health Care": "HealthCare",
            "Real Estate": "RealEstate",
            "Information Technology": "Tech",
            "Broad Market Index": "BroadMarket",
            "Bond Market Index": "Bonds",
            "Communication Services": "Telecom"
        }

        table_name = "sector_factor_decomp_df2"

        # Assuming 'sector_exposure_df' exists in 'charts'
        df = data.get("sector_factor_decomp_df").copy()  # Create a copy to modify
        df.iloc[:, 0] = df.iloc[:, 0].replace(to_replace=value_mapping)  # Replace values in first values
        sector_exposure = ReportTable(
            data=df,  # type: ignore
            table_name=table_name,
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total_pct"),
            snap_element=sector_factor_decomp_df,
            snap_mode=SnapType.DOWN,
            initial_position=(1000, 1000)
        )

        eu.insert_table(worksheet, sector_exposure)

        sector_sensitivity_chart1 = WorksheetChart4(
            table_name="sector_factor_decomp_df_fe",
            columns=[ "FactorExp",],
            categories_name="Sector Sensitivities",
            snap_element=sector_factor_decomp_df,
            snap_mode=SnapType.RIGHT,
            page_layout=layout,
            margin=1,
            axis_format="percentage",
            custom_padding=1,
            custom_width=1330
        )
        sector_sensitivity_chart = WorksheetChart4(
            table_name=table_name,
            columns=[ "FactorExp",],
            categories_name="Sector Sensitivities",
            snap_element=sector_exposure,
            snap_mode=SnapType.RIGHT,
            page_layout=layout,
            margin=1,
            axis_format="percentage",
            custom_padding=0,
            custom_width=1330
        )
        sector_sensitivity_chart = increase_size(sector_sensitivity_chart)
        sector_sensitivity_chart.position = sector_sensitivity_chart1.position
        eu.insert_chart(writer, worksheet, sector_sensitivity_chart)

        format_dashboard_worksheet(worksheet, layout)

        grouped_top = rgo.group_items(
            data.get("risk_factor_exposure_top_n_list"), 2  # type: ignore
        )
        grouped_bottom = rgo.group_items(
            data.get("risk_factor_exposure_bottom_n_list"), 2  # type: ignore
        )

        report_tables = []
        ancor_element = sector_factor_decomp_df
        row_number = 1
        for top, bottom in zip(grouped_top, grouped_bottom):
            row_group_tables = rgo.init_row(styles, ancor_element, top, bottom, row_number,"factor_exposure")
            report_tables.extend(row_group_tables)
            ancor_element = row_group_tables[0]
            row_number = row_number + 1

        for report_table in report_tables:
            eu.insert_table(worksheet, report_table)
    except Exception as ex:
        MyExceptions.show_message(tab='factor_exposures.py',
                                  message="Following exception occurred during inserting tables and charts into the sheet\n\n" + str(
                                      ex))
