from src.styles.styles_init import set_styles


def set_up_workbook(workbook, sheet_name: str, temp=None):

    # for x in workbook.formats:
    #     if not temp:
    #         if x.font_name == 'Calibri' and x.font_size not in [24, 16, 14]:
    #             x.font_name = 'Arial'
    #     if x.font_size not in [24, 16, 14]:
    #         x.font_size = 8
    styles = set_styles(workbook, temp=temp)
    for x in workbook.formats:
        if not temp:
            if x.font_name == 'Calibri' and x.font_size not in [24, 16, 14]:
                x.font_name = 'Arial'
        if x.font_size not in [24, 16, 14]:
            x.font_size = 8
    if sheet_name not in workbook.sheetnames:
        workbook.add_worksheet(sheet_name)

    worksheet = workbook.get_worksheet_by_name(sheet_name)
    worksheet.set_default_row(16)
    worksheet.set_zoom(100)

    return styles, worksheet
