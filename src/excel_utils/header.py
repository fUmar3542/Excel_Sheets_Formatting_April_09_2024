def insert_header(worksheet, styles, layout, fund: str, holdings_date: str, title=None) -> None:
    """inserts header to the worksheet"""
    active_columns = (
        len(layout.CATEGORY_COLUMNS)
        + len(layout.NUMERIC_COLUMNS)
        + len(layout.MIDDLE_COLUMNS)
    )
    worksheet.merge_range(
        0, 1, 0, active_columns, title, styles.get("report_header_title")
    )
    worksheet.merge_range(
        1, 1, 1, active_columns, fund if fund != 'Firm' else "Firm Level", styles.get("report_header_sub_title")
    )
    worksheet.merge_range(
        2,
        1,
        2,
        active_columns,
        holdings_date,
        # datetime.now().strftime(r'%Y-%m-%d'),
        styles.get("report_header_date"),
    )

    worksheet.set_row(0, 30)
