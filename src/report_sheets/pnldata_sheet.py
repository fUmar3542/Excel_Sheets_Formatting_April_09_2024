"""data sheet with pnl data"""
from typing import Dict
import numpy as np
import pandas as pd
import src.excel_utils.excel_utils as eu
from src.excel_utils.set_up_workbook import set_up_workbook
from ..report_items.report_table import ReportTable
from src.handles.exception_handling import MyExceptions

PNLDATA_SHEET_NAME = "PNLData"


def generate_pnldata_sheet(
    writer,
    ANNUALIZATION_FACTOR: int,
    data_dict: Dict[str, pd.DataFrame],
) -> None:
    """generates pnl report sheet that is used later for dashboards"""
    try:
        styles, worksheet = set_up_workbook(writer, PNLDATA_SHEET_NAME)

        # TODO: this part should be a part of data generation
        table_name = "AUM_clean"
        table = _adjust_table(data_dict.get(table_name))
        table["Volatility"] = np.sqrt(ANNUALIZATION_FACTOR) * table["Volatility"]
        table["20D Volatility"] = np.sqrt(ANNUALIZATION_FACTOR) * table["20D Volatility"]
        table["Volatility Budget"] = (
            np.sqrt(ANNUALIZATION_FACTOR) * table["Volatility Budget"]
        )
        table.dropna(inplace=True)  # type: ignore
        aum_clean = ReportTable(
            data=table,
            table_name=table_name,
            values_format=None,
            header_format=styles.get("table_header"),
            total_format=styles.get("table_total"),
            date_format=styles.get("date"),
            initial_position=(0, 0),
        )
        eu.insert_table(worksheet, aum_clean, date_index=True)
    except Exception as ex:
        MyExceptions.show_message(tab='pnldata_sheet.py',
                                  message="Following exception occurred during inserting a table into the sheet\n\n" + str(
                                      ex))


def _adjust_table(table: pd.DataFrame) -> pd.DataFrame:
    try:
        """formats table for the output"""
        table = _add_cumulative_return_column(table, "Cumulative return")
        table = _add_window_std(table, "Volatility", 252)
        table = _add_window_std(table, "20D Volatility", 20)
        table = _add_volatility_budget(table, "Volatility Budget")
        table.rename({"ret": "Daily Return"}, axis=1, inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='pnldata_sheet.py',
                                  message="Following exception occurred during adjusting a table in the sheet\n\n" + str(
                                      ex))
    return table


def _add_cumulative_return_column(data: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """adds cummulative return to the data"""
    data[col_name] = data.ret.cumsum()
    return data


def _add_window_std(
    data: pd.DataFrame, col_name: str, window_size: int
) -> pd.DataFrame:
    try:
        """adds a column with a rolling window std"""

        data[col_name] = data.ret.rolling(window=window_size).std()
        data.reset_index(inplace=True)
        for i in range(window_size):
            data.loc[i, col_name] = data.ret[: i + 1].std()

        data[col_name].fillna(0, inplace=True)
        data.set_index(["index"], inplace=True)
    except Exception as ex:
        MyExceptions.show_message(tab='pnldata_sheet.py',
                                  message="Following exception occurred during adding a in the sheet\n\n" + str(
                                      ex))
    return data


def _add_volatility_budget(data: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """adds volatility budget to the table"""
    data[col_name] = data["20D Volatility"] / 10
    return data
