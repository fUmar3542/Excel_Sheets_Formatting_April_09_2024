# pylint: disable=C0115
'''
worksheet chart is a container to store information
about a chart that will be inserted into the worksheet.
since we are talking about a chart, the we need to know
the following attributes:
* table_name (the one that ReportTable inserts into excel namespace)
* columns: names of excel table. Will be used to add series to the chart
* page_layout. Required to calculate number of pixels from start to the page end
* initial_number of rows. If the table is not snapped to another table, it is
possible to set up number of lines this chart should take on the sheet
* title. Optional if specified, will override the title of the chart. By
default will be using name of the column used for Axes categories.
* stacked. if yes, the excel utilities will generate a stacked chart.
'''
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from src.report_items.report_item import ReportItem

from .snap_operations import SnapType


@dataclass
class WorksheetChart(ReportItem):
    table_name: Optional[str] = 'some_table'
    columns: Optional[List[str]] = None
    categories_name: str = 'Some table'
    page_layout: Optional[Any] = None
    initial_rows: int = 18
    title: str = None  # type: ignore
    stacked: bool = True
    axis_format: str = 'float'
    custom_height: Optional[int] = None
    custom_width: Optional[int] = None
    custom_padding: Optional[int] = None

    @property
    def size(self) -> Tuple[float, float]:
        # Initial calculations for width and height
        width = self.page_layout.pixels_to_right_edge(self.position[0]) if self.page_layout else self.custom_width
        height = self.page_layout.pixels_to_bottom(self.initial_rows) if self.page_layout else self.custom_height

        if (not self.snap_mode) or (self.snap_mode == SnapType.DOWN):
            # If there is a custom height, use it, otherwise calculate it
            height = self.custom_height if self.custom_height is not None else height
        else:
            # If there's a snap element, calculate height based on its data, otherwise use minimal height
            height = self.page_layout.pixels_to_bottom(len(self.snap_element.data) + 1) if self.snap_element and self.page_layout else 10

        # Adjust for custom padding
        if self.custom_padding is not None:
            width -= 2 * self.custom_padding  # Subtract padding from both sides
            height -= 2 * self.custom_padding  # Subtract padding from top and bottom

        return (width, height)


@dataclass
class WorksheetChart2(ReportItem):
    table_name: Optional[str] = 'some_table'
    columns: Optional[List[str]] = None
    categories_name: str = 'Some table'
    page_layout: Optional[Any] = None
    initial_rows: int = 18
    title: str = None  # type: ignore
    stacked: bool = True
    axis_format: str = 'float'
    custom_height: Optional[int] = None
    custom_width: Optional[int] = None
    custom_padding: Optional[int] = None

    @property
    def size(self) -> Tuple[float, float]:
        # Use custom size if specified
        if self.custom_width and self.custom_height:
            return (self.custom_width, self.custom_height)

        width = self.page_layout.pixels_to_right_edge(self.position[0])

        # Default logic for calculating size
        if (not self.snap_mode) or (self.snap_mode == SnapType.DOWN):
            height = self.page_layout.pixels_to_bottom(self.initial_rows)
        else:
            # Calculation based on the snap item
            height = 18
            if self.snap_element:
                height = self.page_layout.pixels_to_bottom(len(self.snap_element.data) + 1)

        return (width, height)

@dataclass
class WorksheetChart3(ReportItem):
    table_name: Optional[str] = 'some_table'
    columns: Optional[List[str]] = None
    categories_name: str = 'Some table'
    page_layout: Optional[Any] = None
    initial_rows: int = 18
    title: str = None  # type: ignore
    stacked: bool = True
    axis_format: str = 'float'
    custom_height: Optional[int] = None
    custom_width: Optional[int] = None
    top_margin: Optional[int] = None
    bottom_margin: Optional[int] = None
    left_margin: Optional[int] = None
    right_margin: Optional[int] = None

    @property
    def size(self) -> Tuple[float, float]:
        # Use custom size if specified
        if self.custom_width and self.custom_height:
            return (self.custom_width, self.custom_height)

        width = self.page_layout.pixels_to_right_edge(self.position[0]) if self.page_layout else self.custom_width

        # Default logic for calculating size
        if (not self.snap_mode) or (self.snap_mode == SnapType.DOWN):
            height = self.page_layout.pixels_to_bottom(self.initial_rows) if self.page_layout else self.custom_height
        else:
            # Calculation based on the snap item, or use a minimal height
            height = self.page_layout.pixels_to_bottom(len(self.snap_element.data) + 1) if self.snap_element and self.page_layout else 10

        # Adjust width and height based on custom margins
        if self.left_margin and self.right_margin:
            width -= (self.left_margin + self.right_margin)

        if self.top_margin and self.bottom_margin:
            height -= (self.top_margin + self.bottom_margin)

        return (width, height)

@dataclass
class WorksheetChart4(ReportItem):
    table_name: Optional[str] = 'some_table'
    columns: Optional[List[str]] = None
    categories_name: str = 'Some table'
    page_layout: Optional[Any] = None
    initial_rows: int = 18
    title: str = None  # type: ignore
    stacked: bool = True
    axis_format: str = 'float'
    custom_height: Optional[int] = None
    custom_width: Optional[int] = None
    custom_padding: Optional[int] = None

    @property
    def size(self) -> Tuple[float, float]:
        # If custom width is specified, use it; otherwise, calculate it
        width = self.custom_width if self.custom_width else self.page_layout.pixels_to_right_edge(self.position[0])

        # If custom width is specified but custom height is not, use the default height calculation
        if self.custom_width and not self.custom_height:
            if (not self.snap_mode) or (self.snap_mode == SnapType.DOWN):
                height = self.page_layout.pixels_to_bottom(self.initial_rows)
            else:
                # Calculation based on the snap item
                height = 18
                if self.snap_element:
                    height = self.page_layout.pixels_to_bottom(len(self.snap_element.data) + 1)
        else:
            # If custom height is specified, use it
            height = self.custom_height
        if not height:
            height = self.page_layout.pixels_to_bottom(self.initial_rows) if self.page_layout else self.custom_height

        # Adjust for custom padding if specified
        if self.custom_padding:
            width -= self.custom_padding * 2 if width else 0 # Subtract padding from both sides
            height -= self.custom_padding * 2 if height else 0  # Subtract padding from top and bottom if height is calculated

        return (width, height)
