from typing import Any

ALIGN_CENTER = 'center'
VALIGN_CENTER = 'vcenter'
DARK_BLUE_COLOR = '#44546A'
WHIE_COLOR = '#FFFFFF'
TABLE_HEADER_FILL_COLOR = '#44546A'
TEXT_FONT = 'Arial'
TEXT_SIZE = 8

SOLID_BORDER_INDEX = 1
DASHED_BORDER_INDEX = 4

CURRENCY_FORMAT = '"$"#,##0_);[Red]("$"#,##0)'
PERCENTAGE_FORMAT = '# ##0.00%_);[Red](# ##0.00%)'
PERCENTAGE_NO_COLOR_FORMAT = '0.00%'
PERCENTAGE_ROUND_FORMAT = '##0%'
FLOAT_NO_COLOR_FORMAT = '0.00'
FLOAT_FORMAT = '0.00;[Red]-0.00'
INTEGER_FORMAT = '#,##0'
DATE_FORMAT = 'mm/dd/yy'


def add_header_style(workbook, temp=None) -> Any:
    '''adds table style for a header for a given workbook'''
    style = workbook.add_format()
    # style.set_align(ALIGN_CENTER)
    style.set_valign(VALIGN_CENTER)
    style.set_bg_color(DARK_BLUE_COLOR)
    style.set_bold(True)
    style.set_font_name(TEXT_FONT)
    style.set_font_color(WHIE_COLOR)
    style.set_size(TEXT_SIZE)
    style.set_num_format(PERCENTAGE_ROUND_FORMAT)
    style.set_border(SOLID_BORDER_INDEX)
    style.set_border_color(DARK_BLUE_COLOR)
    return style


def add_total_style(workbook) -> Any:
    '''adds table style for the total '''
    style = workbook.add_format()
    style.set_bold(True)
    # style.set_align(ALIGN_CENTER)
    style.set_valign(VALIGN_CENTER)
    #style.set_font_name(TEXT_FONT)
    #style.set_font_color(WHIE_COLOR)
    #style.set_size(TEXT_SIZE)
    #style.set_border(SOLID_BORDER_INDEX)
    style.set_top(SOLID_BORDER_INDEX)
    style.set_bottom(SOLID_BORDER_INDEX)
    #style.set_border_color(DARK_BLUE_COLOR)

    return style


def add_total_pct_style(workbook) -> Any:
    '''adds table style for the total '''
    style = workbook.add_format()
    style.set_bold(True)
    style.set_num_format(PERCENTAGE_FORMAT)
    style.set_font_name(TEXT_FONT)
    # style.set_align(ALIGN_CENTER)
    style.set_valign(VALIGN_CENTER)
    #style.set_font_color(WHIE_COLOR)
    style.set_size(TEXT_SIZE)
    #style.set_border(SOLID_BORDER_INDEX)
    style.set_top(SOLID_BORDER_INDEX)
    style.set_bottom(SOLID_BORDER_INDEX)
    #style.set_border_color(DARK_BLUE_COLOR)
    return style


def add_table_body_format(workbook) -> Any:
    '''adds table body format'''
    style = workbook.add_format()
    style.set_font_name = TEXT_FONT
    style.set_size(TEXT_SIZE)
    style.set_border(DASHED_BORDER_INDEX)
    style.set_border_color(DARK_BLUE_COLOR)
    style.set_valign(VALIGN_CENTER)
    # style.set_align(ALIGN_CENTER)
    return style


def add_body_frame_format(workbook) -> Any:
    '''adds solid frame to outer'''

    style = workbook.add_format()
    style.set_top(SOLID_BORDER_INDEX)
    style.set_top_color(DARK_BLUE_COLOR)
    style.set_bottom(SOLID_BORDER_INDEX)
    style.set_bottom_color(DARK_BLUE_COLOR)
    style.set_left(SOLID_BORDER_INDEX)
    style.set_left_color(DARK_BLUE_COLOR)
    style.set_right(SOLID_BORDER_INDEX)
    style.set_right_color(DARK_BLUE_COLOR)
    style.set_font_name = TEXT_FONT
    style.set_size(TEXT_SIZE)
    style.set_valign(VALIGN_CENTER)


def add_merged_vertical(workbook) -> Any:
    style = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'font_color': 'white',
        'bg_color': TABLE_HEADER_FILL_COLOR,
        'rotation': 90,
    })
    return style


def add_merged_horizontal(workbook) -> Any:
    style = workbook.add_format({
        'align': 'center',
        'valign': 'center',
        'font_color': 'white',
        'bg_color': TABLE_HEADER_FILL_COLOR
    })
    return style


def _add_num_format(workbook, format) -> Any:
    '''adds number format'''

    style = workbook.add_format()
    style.set_num_format(format)
    style.set_border(DASHED_BORDER_INDEX)
    style.set_valign(VALIGN_CENTER)
    return style


def my_value_format(workbook, format) -> Any:
    '''adds number format'''

    style = workbook.add_format()
    style.set_border(DASHED_BORDER_INDEX)
    style.set_valign(VALIGN_CENTER)
    return style


def add_currency_format(workbook) -> Any:
    '''adds currency format'''

    return _add_num_format(workbook, CURRENCY_FORMAT)


def add_integer_format(workbook) -> Any:
    '''adds integer format'''

    return _add_num_format(workbook, INTEGER_FORMAT)


def add_percentage_format(workbook) -> Any:
    '''adds currency format'''
    return _add_num_format(workbook, PERCENTAGE_FORMAT)


def add_percentage_round_format(workbook) -> Any:
    '''adds currency format'''
    return _add_num_format(workbook, PERCENTAGE_ROUND_FORMAT)


def add_float_format(workbook) -> Any:
    '''adds float format'''

    return _add_num_format(workbook, FLOAT_FORMAT)


def add_black_font_percentage_format(workbook):
    '''percentage format for conditional formatting'''

    return _add_num_format(workbook, PERCENTAGE_NO_COLOR_FORMAT)


def add_black_float_format(workbook):
    '''add black floats for conditional formatting'''

    return _add_num_format(workbook, FLOAT_NO_COLOR_FORMAT)


def add_date_format(workbook) -> Any:
    '''adds date format'''

    return _add_num_format(workbook, DATE_FORMAT)
