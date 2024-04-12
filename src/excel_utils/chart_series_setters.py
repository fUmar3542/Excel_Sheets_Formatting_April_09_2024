'''helper functions that create a series objects of a proper type'''


def _add_series(
    chart,
    table_name: str,
    column_name: str,
    categories: str,
    color: str,
    y2_axis: bool
) -> None:
    '''adds a series to the given chart'''
    chart.add_series({
        'values': f'={table_name}[{column_name}]',
        'categories': f'={table_name}[{categories}]',
        'name': column_name,
        'fill': {'color': color},
        'y2_axis': y2_axis
    })


def _add_time_series(
    chart,
    table_name: str,
    column_name: str,
    categories,
    color: str,
    y2_axis: bool
) -> None:
    '''adds time series to the given chart'''
    chart.add_series({
        'values': f'={table_name}[{column_name}]',
        'categories': f'={table_name}[{categories}]',
        'name': column_name,
        'fill': {'color':  color},
        'y2_axis': y2_axis
    })
    chart.set_x_axis({'date_axis': True})


SERIES_SETTERS = {
    'default': _add_series,
    'time_series': _add_time_series,
}
