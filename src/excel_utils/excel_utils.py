'''Module for formatting tables in Excel'''
# pylint: disable=W0621

from itertools import cycle
from typing import Callable

import pandas as pd
from xlsxwriter import worksheet

from src.excel_utils.chart_series_setters import SERIES_SETTERS, _add_series
from src.report_items.report_table import ReportTable
from src.report_items.worksheet_chart import WorksheetChart
from src.styles.styles_init import FORMATS
import numpy as np


def insert_text(worksheet, table, text) -> None:
    '''adds text 2 rows above the given cell'''
    col, row = table.position
    row -= 2
    col -= 1
    worksheet.write(row, col, text)

def merge_above(worksheet, table: ReportTable, style, text) -> None:
    '''inserts a text above the given element'''
    (start_col, start_row), (end_col, end_row) = table.range  # type: ignore
    start_row -= 1
    worksheet.merge_range(start_row, start_col-1,
                          start_row, end_col-1, text, style)

def merge_to_left(worksheet, table: ReportTable, style, text) -> None:
    '''inserts merged range to the left'''
    # pylint: disable=W0621
    (start_col, start_row), (end_col, end_row) = table.range  # type: ignore
    worksheet.merge_range(start_row, start_col-1,
                          end_row, start_col-1,
                          text, style
                          )

def apply_leftandup_header_format(worksheet, table: ReportTable, style) -> None:
    (start_col, start_row), (end_col, end_row) = table.range  # type: ignore
    for cnum, val in enumerate(table.data.columns):
        if str(val).replace('.','',1).replace('-','',1).isdigit():
            #worksheet.write(start_row,start_col+cnum, '{:%}'.format(float(val)), style)
            pass
        else:
            worksheet.write(start_row,start_col+cnum, str(val), style)
        #pass
    for rnum, val in enumerate(table.data.iloc[:,0]):
        worksheet.write(start_row+rnum+1,start_col, float(val) if str(val).replace('.','',1).replace('-','',1).isdigit() else str(val), style)

def insert_table(
    worksheet: worksheet,  # type: ignore
    report_table: ReportTable,
    date_index: bool = False
) -> None:
    '''
    writes a given table and formats it as a table

    Args:
        data: data to be inserted
    '''
    nbrows = len(report_table.data)
    if nbrows==0:
        return
    
    # TODO: this should not be here... Need a wrapper
    if report_table.data.index.name not in [None]:
        report_table.data.reset_index(inplace=True)
    
    if date_index:
        report_table.data.iloc[:, 0] = pd.to_datetime(report_table.data.iloc[:, 0],format=r'%Y-%m-%d')
        report_table.data.rename(columns ={report_table.data.columns[0]:report_table.data.columns[0] +'_date'},inplace=True)

    report_table.data.columns = [str(col) for col in report_table.data.columns]

    start_col, start_row = report_table.range[0]
    end_col, end_row = report_table.range[1]  # ztype: ignore
    end_col = end_col - 1
    
    table_has_total = str(report_table.data.iloc[nbrows-1,0]).lower()=='total'
    vals = report_table.data.values
    if table_has_total:
        vals = report_table.data.iloc[:-1,:].values
        end_row -=1

    worksheet.add_table(
        start_row, start_col,
        end_row, end_col,
        {
            'data': vals,
            'name': report_table.table_name,
            'columns': _set_column_types(report_table),
            'autofilter': False,
            'banded_rows': False,
            'style': 'Table Style Medium 16',
        }
    )
    # header_fmt = report_table.header_format
    # bold_fmt
    
    # reformat Header and Total
    for cnum, val in enumerate(report_table.data.columns):
        #print(cnum,val)
        worksheet.write(start_row,start_col+cnum, str(val), report_table.header_format)
        if table_has_total: # Total in bold
            worksheet.write(start_row+nbrows,start_col+cnum, report_table.data.iloc[nbrows-1,cnum],report_table.total_format)
    # reformat specific cells
    if not (report_table.specific_cells_format is None): # there are specific cells to format 
        for f in report_table.specific_cells_format:
            if f[1] in report_table.data.columns:
                cnum = list(report_table.data.columns).index(f[1])
                crow = list(report_table.data.iloc[:,0]).index(f[0])+1
                val = report_table.data.iloc[crow-1,cnum]
                worksheet.write(start_row + crow,start_col + cnum, val, f[2])


        
def apply_conditional_formatting(
    worksheet,
    report_table,
    include_first_col: bool = True
) -> None:
    '''applies conditional formatting to a specific table'''

    start_col, start_row = report_table.range[0]
    if include_first_col:
        start_col = start_col + 1
    end_col, end_row = report_table.range[1]  # type: ignore

    worksheet.conditional_format(
        start_row, start_col, end_row, end_col,
        {
            'type': '3_color_scale',
            'min_value': -1,
            'max_value': 1,
            'max_type': 'max',
            'min_color': 'red',
            'mid_color': 'white',
            'max_color': 'green',
            'mid_type': 'num',
            'mid_value': 0,
        }
    )

def _set_column_types(report_table):
    '''wrapper for calling the proper collumn type setter'''

    if isinstance(report_table.values_format, list):
        return _set_manual_column_types(report_table)

    return _set_static_column_types(report_table)

def _set_static_column_types(report_table):
    '''generates a dictionary of formats'''
    return_list = []

    data = report_table.data
    data_types = [str(x) for x in list(data.dtypes)]
    for column, column_type in zip(data.columns, data_types):
        column_format = report_table.date_format if ('date' in column_type) or ('date' in column) else report_table.values_format
        return_list.append({
            'header': column,
            'format': column_format,
        })

    return return_list

def _set_manual_column_types(report_table):
    '''sets each column a type specified in a list of values format'''

    return_list = []
    for column, value_format in zip(
        report_table.data.columns,
        report_table.values_format
    ):
        return_list.append({
            'header': column,
            'format': value_format,
        })

    return return_list


def insert_chart(
    workbook, worksheet,
    worksheet_chart: WorksheetChart,
    chart_type: str = 'column',
    stacked: bool = True,
) -> None:
    '''
    Inserts a chart into the worksheet

    Args:
        workbook: active workbook
        worksheet: active worksheet
        worksheet_chart: Instance of worksheet chart
        chart_type: type of the chart (column or line, for example)
        stacked: boolean flag whether to stack the series
        x_axis_labels: list of X-axis labels (optional)
    '''
    chart, position = _set_chart_object(workbook, worksheet_chart, chart_type, stacked)
    # if chart_type not in ['column', 'Line']:  # Check if chart type is not column
    #     chart.set_legend({'position': 'top'})  # If not column, set legend to top
    # else:
    #     chart.set_legend({'position': 'bottom'})  # If column, set legend to bottom
    chart.set_legend({'position': 'bottom'})

    chart.set_x_axis({'label_position': 'low'})
    worksheet.insert_chart(row=position[1], col=position[0], chart=chart)


def insert_dual_axis_chart(    workbook,    worksheet,     worksheet_chart_bars: WorksheetChart,     worksheet_chart_line: WorksheetChart) -> None:
    '''  adds dual axis chart
    Args:
    workbook: excel object
    worksheet: worksheet of the workbook, where the chart should be inserted
    worksheet_chart_bars: WorksheetChart that will contain bars
    worksheet_chart_lines: line chart to be added to the bars chart
    '''
    bar_chart, bar_chart_position = _set_chart_object(
        workbook=workbook,
        worksheet_chart=worksheet_chart_bars,
        chart_type='column',
        stacked=True,
        series_type='time_series',
    )
    series_chart, _ = _set_chart_object(
        workbook=workbook,
        worksheet_chart=worksheet_chart_line,
        chart_type='line',
        stacked=False,
        series_type='time_series',
        y2_axis=True,
    )
    # series_chart.set_y2_axis({'name': worksheet_chart_line.columns[0].capitalize()})
    bar_chart.combine(series_chart)
    bar_chart.set_x_axis({'label_position': 'low'})
    # bar_chart.set_y_axis({'name': worksheet_chart_bars.columns[0].capitalize()})
    # bar_chart.y2_axis['name'] = worksheet_chart_line.columns[0].capitalize()
    # bar_chart.x_axis['defaults']['major_gridlines']['visible'] = 1
    
    worksheet.insert_chart(
        col=bar_chart_position[0],
        row=bar_chart_position[1],
        chart=bar_chart
    )


# # Create a new column chart. This will use this as the primary chart.
# column_chart2 = workbook.add_chart({"type": "column"})

# # Configure the data series for the primary chart.
# column_chart2.add_series(
#     {
#         "name": "=Sheet1!$B$1",
#         "categories": "=Sheet1!$A$2:$A$7",
#         "values": "=Sheet1!$B$2:$B$7",
#     }
# )

# # Create a new column chart. This will use this as the secondary chart.
# line_chart2 = workbook.add_chart({"type": "line"})

# # Configure the data series for the secondary chart. We also set a
# # secondary Y axis via (y2_axis). This is the only difference between
# # this and the first example, apart from the axis label below.
# line_chart2.add_series(
#     {
#         "name": "=Sheet1!$C$1",
#         "categories": "=Sheet1!$A$2:$A$7",
#         "values": "=Sheet1!$C$2:$C$7",
#         "y2_axis": True,
#     }
# )

# # Combine the charts.
# column_chart2.combine(line_chart2)

# # Add a chart title and some axis labels.
# column_chart2.set_title({"name": "Combine chart - secondary Y axis"})
# column_chart2.set_x_axis({"name": "Test number"})
# column_chart2.set_y_axis({"name": "Sample length (mm)"})

# # Note: the y2 properties are on the secondary chart.
# line_chart2.set_y2_axis({"name": "Target length (mm)"})

# # Insert the chart into the worksheet
# worksheet.insert_chart("E18", column_chart2)


def _set_chart_object(
    workbook,
    worksheet_chart,
    chart_type: str = 'column',
    stacked=True,
    series_type: str = 'default',
    y2_axis=False,
):
    '''
    function is responsible for correct setting of the chart object itself:
    Proper chart type, proper axis format, add series
    returns a chart object and its position
    '''
    chart = _create_chart(workbook, chart_type, stacked)
    _set_chart_title(worksheet_chart, chart)
    _set_axis_format(
        chart,
        FORMATS.get(f'{worksheet_chart.axis_format}_text')  # type: ignore
    )
    position = _format_chart(worksheet_chart, chart)
    _add_column_series(
        worksheet_chart,
        chart,
        SERIES_SETTERS.get(series_type, _add_series), 
        y2_axis
    )
    if y2_axis:
        _set_y2_axis_format(
            chart,
            FORMATS.get(f'{worksheet_chart.axis_format}_text')  # type: ignore
        )
        # chart.set_y2_axis({'num_format': FORMATS.get(f'{worksheet_chart.axis_format}_text')})
    # if True:
    #     chart.y_axis.defaults['num_format'] = '# ##0.00%'
    # chart.set_y_axis_title(worksheet_chart.columns[0])
    return chart, position


def _create_chart(workbook, chart_type: str = 'column', stacked=True):
    chart_options = {'type': chart_type, }
    if stacked:
        chart_options.update({'subtype': 'stacked', })  # type: ignore
    chart = workbook.add_chart(chart_options)

    return chart

def _set_axis_format(chart, axis_format: str):
    chart.set_y_axis({'num_format': axis_format})

def _set_y2_axis_format(chart, axis_format: str):
    chart.set_y2_axis({'num_format': axis_format})

def _set_chart_title(worksheet_chart, chart):
    chart_title = worksheet_chart.title \
        if worksheet_chart.title else worksheet_chart.categories_name
    chart.set_title({
        'name': chart_title,
        'overlay': False,
    })


def _add_column_series(worksheet_chart, chart, series_setter: Callable, y2_axis):
    '''adds series defined in worksheet_chart to the chart object'''
    color_generator = cycle(['#4472C4','#ED7D31'])
    for column in worksheet_chart.columns:
        series_setter(
            chart, worksheet_chart.table_name,  # type: ignore
            column, worksheet_chart.categories_name,
            next(color_generator), 
            y2_axis
        )

def _format_chart(worksheet_chart, chart):
    '''formats axis'''
    position = worksheet_chart.position
    size = worksheet_chart.size
    chart.set_legend({'position': 'bottom'})
    chart.set_size({'width': size[0], 'height': size[1]})
    return position
