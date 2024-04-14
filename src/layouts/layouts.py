# pylint: disable=C0115
'''
contains all layouts used to generate reports
In general, each layout defines which columns should:
* be categorical (wide)
* numeric (normal)
* etc...
'''
from typing import Dict

FONT_SIZE = 8
DPI = 92

UNITS_TO_PIXELS = {
    8: 61,
    12: 89,
    26: 187,
}


class DashboardLayout:
    '''class stores information about page layout'''
    NUMERIC_COLUMNS_WIDTH = 12
    CATEGORY_COLUMNS_WIDTH = 26
    SIDE_COLUMNS_WIDTH = 8
    MIDDLE_COLUMNS_WIDTH = 8
    PIXELS_PER_WIDTH = 95 / 12  # FONT_SIZE * DPI / 72
    PIXELS_PER_HEIGHT = 20
    TOTAL_COLS = 15

    CATEGORY_COLUMNS = ['B', 'J', ]
    NUMERIC_COLUMNS = ['C', 'D', 'E', 'F',
                       'G', 'H', 'K','L', 'M', 'N', 'O']
    MIDDLE_COLUMNS = ['I', ]
    SIDE_COLUMNS = ['A', 'Q', ]

    @property
    def widths(self) -> Dict[str, float]:
        '''returns a sorted dictionary of column length'''

        return_dict = {}
        return_dict.update({
            col: self.CATEGORY_COLUMNS_WIDTH for col in self.CATEGORY_COLUMNS
        })

        return_dict.update({
            col: self.SIDE_COLUMNS_WIDTH for col in self.SIDE_COLUMNS
        })

        return_dict.update({
            col: self.MIDDLE_COLUMNS_WIDTH for col in self.MIDDLE_COLUMNS
        })

        return_dict.update({
            col: self.NUMERIC_COLUMNS_WIDTH for col in self.NUMERIC_COLUMNS
        })

        return {
            key: return_dict.get(key) for key in sorted(return_dict.keys())
        }  # type: ignore

    def pixels_to_right_edge(self, start_col: int) -> float:
        '''
        returns number of pixels till the right
        border starting from the n'th column
        '''
        width_in_units = list(self.widths.values())[start_col:-1]
        widths_in_pixels = [
            UNITS_TO_PIXELS.get(x, self.PIXELS_PER_WIDTH)  # type: ignore
            for x in width_in_units
        ]

        return sum(widths_in_pixels)

    def pixels_to_bottom(self, n_row: int) -> float:
        '''returns number of pixels for a given number of rows'''

        return n_row * self.PIXELS_PER_HEIGHT

    @property
    def columns(self) -> str:
        '''returns the name of the last column in the layout'''

        all_values = set(
            self.CATEGORY_COLUMNS +
            self.NUMERIC_COLUMNS +
            self.MIDDLE_COLUMNS +
            self.SIDE_COLUMNS
        )

        return list(all_values)


class NarrowDashboardLayout(DashboardLayout):
    SIDE_COLUMNS = ['A', 'K']
    CATEGORY_COLUMNS = ['B', 'G']
    NUMERIC_COLUMNS = ['C', 'D', 'E', 'H', 'I', 'J']
    MIDDLE_COLUMNS = ['K', ]


class NarrowDashboardLayout1(DashboardLayout):
    SIDE_COLUMNS = ['A', 'K']
    CATEGORY_COLUMNS = ['B']
    NUMERIC_COLUMNS = ['C', 'D', 'E', 'G', 'H', 'I', 'J']
    MIDDLE_COLUMNS = ['K', ]


class PnlReportLayout(DashboardLayout):
    SIDE_COLUMNS = ['A', 'P']
    CATEGORY_COLUMNS = ['B', 'F']
    NUMERIC_COLUMNS = ['C', 'D', 'E', 'G', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
    MIDDLE_COLUMNS = []


class PnlReportLayout1(DashboardLayout):
    SIDE_COLUMNS = ['A', 'P']
    CATEGORY_COLUMNS = ['B', 'H']
    NUMERIC_COLUMNS = ['C', 'D', 'E', 'F', 'G', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
    MIDDLE_COLUMNS = []


class WideDashboardLayout(DashboardLayout):
    '''contains 4 category columns'''
    CATEGORY_COLUMNS = ['B', 'F', 'J', 'N']
    MIDDLE_COLUMNS = ['E', 'I', 'M']
    NUMERIC_COLUMNS = ['C', 'D', 'G', 'H', 'K', 'L', 'O', 'P']


class WideDashboardLayout1(DashboardLayout):
    '''contains 4 category columns'''
    SIDE_COLUMNS = ['A', 'T']
    CATEGORY_COLUMNS = ['B', 'G', 'L', 'Q']
    MIDDLE_COLUMNS = ['E', 'F', 'J', 'K', 'O', 'P']
    NUMERIC_COLUMNS = ['C', 'D', 'H', 'I', 'M', 'N', 'R', 'S']


class ExposureDashboardLayout(DashboardLayout):
    SIDE_COLUMNS = ['A', 'M', ]
    CATEGORY_COLUMNS = ['B', 'H', ]
    MIDDLE_COLUMNS = ['G', ]
    NUMERIC_COLUMNS = ['C', 'D', 'E', 'F', 'I', 'J', 'K', 'L', ]


class StressDashboardLayout(DashboardLayout):
    SIDE_COLUMNS = ['A', 'O', ]
    CATEGORY_COLUMNS = []
    MIDDLE_COLUMNS = []
    NUMERIC_COLUMNS = ['B','C', 'D', 'E', 'F','G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']


class StressDashboardLayout1(DashboardLayout):
    SIDE_COLUMNS = ['A', 'O', ]
    CATEGORY_COLUMNS = ['B',]
    MIDDLE_COLUMNS = []
    NUMERIC_COLUMNS = ['C', 'D', 'E', 'F','G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']


class PositionsDashboardLayout(DashboardLayout):
    SIDE_COLUMNS = ['A', ]
    CATEGORY_COLUMNS = ['B', ]
    MIDDLE_COLUMNS = []
    NUMERIC_COLUMNS = ['C', 'D', 'E', 'F',
                       'G', 'H', 'I', 'J', 'K', 'L', ]


class PositionsBreakdownDashboardLayout(DashboardLayout):
    SIDE_COLUMNS = ['A', 'N']
    CATEGORY_COLUMNS = ['B', 'C', ]
    MIDDLE_COLUMNS = []
    NUMERIC_COLUMNS = ['D', 'E', 'F', 'G', 'H', 'I',
        'J', 'K', 'L', 'M', ]


class CorrelationDashboardLayout(DashboardLayout):
    SIDE_COLUMNS = []
    CATEGORY_COLUMNS = ['A', ]
    MIDDLE_COLUMNS = []
    NUMERIC_COLUMNS = []
