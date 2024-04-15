from typing import Dict

import src.excel_utils.excel_utils as eu
from src.excel_utils.header import insert_header
from src.excel_utils.set_up_workbook import set_up_workbook
from src.excel_utils.sheet_format import format_dashboard_worksheet
from src.layouts.layouts import DashboardLayout

from ..report_items.report_table import ReportTable
from ..report_items.snap_operations import SnapType
from ..report_items.worksheet_chart import WorksheetChart, WorksheetChart3, WorksheetChart2, WorksheetChart4
from datetime import datetime
from src.handles.exception_handling import MyExceptions


SHEET_NAME = "Dashboard"


def generate_dashboard_sheet(
    writer,
    fund: str,
    holdings_date: str,
    title: str,
    data: Dict,
    nm: str
) -> None:
    """generate elements on the dashboard sheet"""

    layout = DashboardLayout()
    styles, worksheet = set_up_workbook(writer, sheet_name=SHEET_NAME)
    date_obj = datetime.strptime(holdings_date, "%Y-%m-%d")
    # worksheet.set_default_row(30)
    insert_header(worksheet, styles, layout, fund, date_obj, title=title)
    # worksheet.set_default_row(21)
    report_tables = insert_dashboard_tables(data, styles, worksheet)
    _charts = insert_dashboard_charts(writer, layout, worksheet, report_tables, nm=nm)
    format_dashboard_worksheet(worksheet, layout)


def insert_dashboard_tables(data, styles, worksheet) -> Dict[str, ReportTable]:
    return_dict = {}
    try:
        table_name = "var_structured_position_top10"
        var_top_10 = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            initial_position=(1, 4),
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total"),
        )
        eu.insert_table(worksheet, report_table=var_top_10)
        return_dict.update({table_name: var_top_10})

        table_name = "var_structured_position_bottom10"
        var_bottom_10 = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total"),
            snap_element=var_top_10,
            snap_mode=SnapType.RIGHT,
            margin=2,
        )
        eu.insert_table(worksheet, report_table=var_bottom_10)
        return_dict.update({table_name: var_bottom_10})

        table_name = "fund_exp_pct_dashboard"
        data["fund_exp_pct_dashboard"].set_index(["Fund Exposures %"], inplace=True)
        fund_exp_pct = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total"),
            snap_element=var_top_10,
            snap_mode=SnapType.DOWN,
        )
        eu.insert_table(worksheet, report_table=fund_exp_pct)
        return_dict.update({table_name: fund_exp_pct})

        table_name = "fund_exp_usd_dashboard"
        data["fund_exp_usd_dashboard"].set_index(["Fund Exposures $"], inplace=True)
        fund_exp_usd = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            values_format=styles.get("currency"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total"),
            snap_element=fund_exp_pct,
            snap_mode=SnapType.RIGHT,
            margin=3,
        )
        eu.insert_table(worksheet, report_table=fund_exp_usd)
        return_dict.update({table_name: fund_exp_usd})

        table_name = "sector_exposure_df"
        sector_exposure = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total_pct"),
            snap_element=fund_exp_pct,
            snap_mode=SnapType.DOWN,
        )
        eu.insert_table(worksheet, sector_exposure)
        return_dict.update({table_name: sector_exposure})

        table_name = "macro_factor_decomp_df"
        macro_factor_decomp = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total"),
            snap_element=sector_exposure,
            snap_mode=SnapType.DOWN,
        )
        eu.insert_table(worksheet, macro_factor_decomp)
        return_dict.update({table_name: macro_factor_decomp})

        table_name = "sector_factor_decomp_df"
        sector_factor_decomp = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total"),
            snap_element=macro_factor_decomp,
            snap_mode=SnapType.DOWN,
        )
        eu.insert_table(worksheet, sector_factor_decomp)
        return_dict.update({table_name: sector_factor_decomp})

        table_name = "greek_sensitivities_df"
        greek_sensitivities = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            values_format=styles.get("currency"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total"),
            snap_element=sector_factor_decomp,
            snap_mode=SnapType.DOWN,
        )
        eu.insert_table(worksheet, greek_sensitivities)
        return_dict.update({table_name: greek_sensitivities})

        table_name = "options_premium_df"
        options_premium = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            values_format=styles.get("currency"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total"),
            snap_element=greek_sensitivities,
            snap_mode=SnapType.RIGHT,
            margin=3,
        )
        eu.insert_table(worksheet, options_premium)
        return_dict.update({table_name: options_premium})

        table_name = "position_liquidity"
        position_liq = ReportTable(
            data=data.get(table_name),  # type: ignore
            table_name=table_name,
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total_pct"),
            snap_element=greek_sensitivities,
            snap_mode=SnapType.DOWN,
            margin=1,
        )
        eu.insert_table(worksheet, position_liq)
        return_dict.update({table_name: position_liq})

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

        table_name = "sector_exposure_df1"

        # Assuming 'sector_exposure_df' exists in 'charts'
        df = data.get("sector_exposure_df").copy()  # Create a copy to modify
        df.iloc[:, 0] = df.iloc[:, 0].replace(to_replace=value_mapping)  # Replace values in first column
        sector_exposure = ReportTable(
            data=df,  # type: ignore
            table_name=table_name,
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total_pct"),
            snap_element=position_liq,
            snap_mode=SnapType.DOWN,
            initial_position=(1000, 1000)
        )

        eu.insert_table(worksheet, sector_exposure)
        return_dict.update({table_name: sector_exposure})

        table_name = "sector_factor_decomp_df1"

        # Assuming 'sector_exposure_df' exists in 'charts'
        df = data.get("sector_factor_decomp_df").copy()  # Create a copy to modify
        df.iloc[:, 0] = df.iloc[:, 0].replace(to_replace=value_mapping)  # Replace values in the first column
        sector_exposure = ReportTable(
            data=df,  # type: ignore
            table_name=table_name,
            values_format=styles.get("percentage"),
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total_pct"),
            snap_element=sector_exposure,
            snap_mode=SnapType.DOWN,
            initial_position=(2100, 2100)
        )
        eu.insert_table(worksheet, sector_exposure)
        return_dict.update({table_name: sector_exposure})
    except Exception as ex:
        MyExceptions.show_message(tab='dashboard_sheet.py',
                                  message="Following exception occurred during inserting tables into the sheet\n\n" + str(
                                      ex))
    finally:
        return return_dict


def increase_size(worksheet_chart):
    try:
        num_rows = worksheet_chart.snap_element.data.shape[0]
        if num_rows < 4:
            num_rows = num_rows + 1
        worksheet_chart.custom_height = (num_rows+1) * 21
    except Exception as ex:
        MyExceptions.show_message(tab='dashboard_sheet.py',
                                  message="Following exception occurred during increasing the height of the chart\n\n" + str(
                                      ex))
    finally:
        return worksheet_chart


def increase_size_expose(worksheet_chart):
    try:
        num_rows = worksheet_chart.snap_element.shape[0]
        if num_rows <= 4:
            num_rows = num_rows + 1
        worksheet_chart.custom_height = (num_rows+1) * 21
    except Exception as ex:
        MyExceptions.show_message(tab='dashboard_sheet.py',
                                  message="Following exception occurred during increasing the height of the chart\n\n" + str(
                                      ex))
    finally:
        return worksheet_chart


def insert_dashboard_charts(writer, layout, worksheet, report_tables, nm):
    charts = {}
    try:
        table_name = "sector_exposure_df"
        sector_exposure_chart1 = WorksheetChart4(
            table_name=table_name,
            columns=["Long", "Short"],
            categories_name="Sector Exposure",
            # initial_rows=6,
            snap_element=report_tables.get(table_name),
            snap_mode=SnapType.RIGHT,
            page_layout=layout,
            axis_format="percentage",
            custom_width=870,
            # custom_height=210,
            margin=1,
        )
        table_name = "sector_exposure_df1"
        sector_exposure_chart = WorksheetChart4(
            table_name=table_name,
            columns=["Long", "Short"],
            categories_name="Sector Exposure",
            # initial_rows=6,
            snap_element=report_tables.get(table_name),
            snap_mode=SnapType.RIGHT,
            page_layout=layout,
            axis_format="percentage",
            custom_width=870,
            # custom_height=210,
            margin=1,
        )

        sector_exposure_chart = increase_size(sector_exposure_chart)
        sector_exposure_chart.position = sector_exposure_chart1.position
        if 'dipsea' in nm.lower():
            if sector_exposure_chart.snap_element.data.shape[0] < 6:
                sector_exposure_chart.custom_height = sector_exposure_chart.custom_height + 75
        eu.insert_chart(writer, worksheet, sector_exposure_chart)
        charts.update({table_name: sector_exposure_chart})

        table_name = "macro_factor_decomp_df"
        macro_factor_sensitivity_chart = WorksheetChart4(
            table_name=table_name,
            columns=["FactorRisk", ],
            categories_name="Macro Sensitivities",
            snap_element=report_tables.get(table_name),
            snap_mode=SnapType.RIGHT,
            page_layout=layout,
            axis_format="percentage",
            custom_width=960,
            #custom_height=250,
            margin=1,
        )
        macro_factor_sensitivity_chart = increase_size(macro_factor_sensitivity_chart)
        if 'dipsea' in nm.lower() and sector_exposure_chart.snap_element.data.shape[0] < 6:
            macro_factor_sensitivity_chart.custom_height = macro_factor_sensitivity_chart.custom_height - 75
            macro_factor_sensitivity_chart.position = (macro_factor_sensitivity_chart.position[0], macro_factor_sensitivity_chart.position[1]+3)
        eu.insert_chart(writer, worksheet, macro_factor_sensitivity_chart)
        charts.update({table_name: macro_factor_sensitivity_chart})

        table_name = "sector_factor_decomp_df"
        sector_sensitivity_chart1 = WorksheetChart4(
            table_name=table_name,
            columns=["FactorRisk"],
            categories_name="Sector Sensitivities",
            snap_element=report_tables.get(table_name),
            snap_mode=SnapType.RIGHT,
            page_layout=layout,
            margin=1,
            axis_format="percentage",
        )
        table_name = "sector_factor_decomp_df1"
        sector_sensitivity_chart = WorksheetChart4(
            table_name=table_name,
            columns=["FactorRisk"],
            categories_name="Sector Sensitivities",
            snap_element=report_tables.get(table_name),
            snap_mode=SnapType.RIGHT,
            page_layout=layout,
            margin=1,
            axis_format="percentage",
            custom_width=960,
        )
        sector_sensitivity_chart = increase_size(sector_sensitivity_chart)
        sector_sensitivity_chart.position = sector_sensitivity_chart1.position
        eu.insert_chart(writer, worksheet, sector_sensitivity_chart)
        charts.update({table_name: sector_sensitivity_chart})

        table_name = "position_liquidity"
        liquidity_chart = WorksheetChart4(
            table_name=table_name,
            columns=["%Liquid"],
            categories_name="Liquidity",
            snap_element=report_tables.get(table_name),
            snap_mode=SnapType.RIGHT,
            page_layout=layout,
            margin=1,
            axis_format="percentage",
            custom_width=870
        )
        liquidity_chart = increase_size(liquidity_chart)
        eu.insert_chart(writer, worksheet, liquidity_chart)
        charts.update({table_name: liquidity_chart})
    except Exception as ex:
        MyExceptions.show_message(tab='dashboard_sheet.py',
                                  message="Following exception occurred during inserting chart\n\n" + str(
                                      ex))
    finally:
        return charts
