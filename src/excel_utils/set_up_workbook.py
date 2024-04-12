from src.styles.styles_init import set_styles
from openpyxl.styles import Font


def set_up_workbook(workbook, sheet_name: str, temp=None):

    styles = set_styles(workbook, temp=temp)
    if sheet_name not in workbook.sheetnames:
        workbook.add_worksheet(sheet_name)

    worksheet = workbook.get_worksheet_by_name(sheet_name)
    worksheet.set_default_row(18)
    # worksheet.default_url_format.font_size = 8
    # worksheet.default_url_format.font_name = "Arial"
    return styles, worksheet
