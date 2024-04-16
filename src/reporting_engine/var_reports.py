"""
module contains functions required to generate
output tables for the final report
"""
import pandas as pd
from typing import Dict, List
from src.handles.exception_handling import MyExceptions

COLUMN_MAPPING = {
    "isolated": "IsoVaR",
    "component": "CompVaR",
    "incremental": "IncVaR",
}

N_ROWS = 10


def generate_underlier_report(
    var_data: pd.DataFrame,
    ascending: bool = False,
) -> pd.DataFrame:
    """
    funtion generates top or bottom var underlier contrinutions
    Args:
        positions: list of positions
        var_data: global dataset with calculated var values
        ascending: a bool flag indicating whether we want to get
            bottom or top rows. If ascending, the bottom rows will
            be returned
    """
    return_data = None
    try:
        selected_var_data = var_data.loc[
            (var_data.group == "position") & (var_data.var_type.isin(COLUMN_MAPPING))
        ]

        return_data = _format_var_data(selected_var_data)
        return_data = _format_output_columns(return_data)
        return_data = (
            return_data.reset_index()
            .sort_values("Inc95", ascending=ascending, axis=0)
            .set_index("Positions")
        )

        axis_name = "Top10 VaR Diversifiers" if ascending else "Top10 VaR Contributors"

        return_data = return_data.rename_axis(axis_name)
        cols = return_data[return_data.columns[return_data.columns.str.contains("Inc")].to_list() + return_data.columns[return_data.columns.str.contains("Iso")].to_list()].columns
        return_data = return_data[cols]
        #return_data.columns = return_data.columns.str.replace("Comp", "")
        return_data = return_data.add_suffix("VaR")
    except Exception as ex:
        MyExceptions.show_message(tab='var_reports.py',
                                  message="Following exception occurred during generating underlier report\n\n" + str(
                                      ex))
    finally:
        return return_data.head(N_ROWS)


def _format_var_data(selected_var_data: pd.DataFrame) -> pd.DataFrame:
    """wrapper function that pivots the var data and renames column names"""
    return_data = None
    try:
        return_data = pd.pivot_table(
            selected_var_data,
            index="attribute",
            values="var",
            columns=["var_type", "var_confidence"],
        )

        return_data = (
            _flattern_column_names(return_data)
            .reset_index()
            .rename(columns={"attribute": "Positions"})
            .set_index("Positions")
        )

    except Exception as ex:
        MyExceptions.show_message(tab='var_reports.py',
                                  message="Following exception occurred during formatting dataframe\n\n" + str(
                                      ex))
    finally:
        return return_data


def _format_output_columns(data: pd.DataFrame) -> pd.DataFrame:
    """formats column_names"""
    # select columns in the right order
    return_data = None
    try:
        return_data = data[
            [
                *[col for col in data.columns if "Inc" in col],
                *[col for col in data.columns if "Iso" in col],
                *[col for col in data.columns if "Comp" in col],
            ]
        ]

        # rename columns to give them the output values
        for key, value in COLUMN_MAPPING.items():
            return_data = return_data.rename(
                columns={col: col.replace(key, value) for col in return_data.columns}
            )
    except Exception as ex:
        MyExceptions.show_message(tab='var_reports.py',
                                  message="Following exception occurred during formatting output dataframe\n\n" + str(
                                      ex))
    finally:
        return return_data


def _flattern_column_names(data: pd.DataFrame) -> pd.DataFrame:
    """function flatterns column names after pivoting"""
    try:
        return_columns = []
        for col in data.columns:

            combined_column_name = "".join(col)
            if ("incremental" in combined_column_name) or (
                "isolated" in combined_column_name
            ):
                combined_column_name = combined_column_name[:3] + combined_column_name[-2:]
                combined_column_name = combined_column_name.capitalize()
            elif "component" in combined_column_name:
                combined_column_name = combined_column_name[:4] + combined_column_name[-2:]
                combined_column_name = combined_column_name.capitalize()

            return_columns.append(combined_column_name)
        data.columns = return_columns
    except Exception as ex:
        MyExceptions.show_message(tab='var_reports.py',
                                  message="Following exception occurred during flattern column names\n\n" + str(
                                      ex))
    finally:
        return data


def generate_group_var_report(var_data: pd.DataFrame, group: str) -> pd.DataFrame:
    """generates a var report for a given group"""
    return_data = None
    try:
        selected_var_data = var_data.loc[
            (var_data.group == group) & (var_data.var_type.isin(COLUMN_MAPPING))
        ]

        return_data = pd.pivot_table(
            selected_var_data,
            index="attribute",
            values="var",
            columns=["var_type", "var_confidence"],
        )

        return_data = (
            _flattern_column_names(return_data)
            .reset_index()
            .rename(columns={"attribute": group.capitalize()})
            .set_index(group.capitalize())
        )

        return_data = _format_output_columns(return_data)
    except Exception as ex:
        MyExceptions.show_message(tab='var_reports.py',
                                  message="Following exception occurred during generating group var report\n\n" + str(
                                      ex))
    finally:
        return return_data


def generate_group_var_reports(
    var_data: pd.DataFrame, groups: List[str]
) -> Dict[str, pd.DataFrame]:
    """generates a var report for a given group"""

    return_data = {}
    try:
        for group in groups:
            if group in ["sector","industry","country","mktcap", "analyst", "assettype"]:
                tmp = generate_group_var_report(var_data, group)
                # adds total
                total_df = pd.DataFrame(tmp.iloc[:, :].sum(axis=0).values[None, :],
                                        columns=tmp.columns, index=["Total"])
                tmp = pd.concat([tmp, total_df], axis=0)
                tmp.reset_index(inplace=True)
                colcatname = f"{group}".capitalize() + " VaR" if group!="mktcap" else "MarketCap VaR"
                tmp.rename(columns={"index":colcatname }, inplace=True)
                tmp.set_index([colcatname], inplace=True)
                return_data[group] = tmp
            else:
                return_data[group] = generate_group_var_report(var_data, group)
    except Exception as ex:
        MyExceptions.show_message(tab='var_reports.py',
                                  message="Following exception occurred during generating group var report\n\n" + str(
                                      ex))
    finally:
        return return_data
