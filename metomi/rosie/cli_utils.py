# Copyright (C) British Crown (Met Office) & Contributors.
# This file is part of Rose, a framework for meteorological suites.
#
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

import textwrap
from typing import Optional, List

# NOTE: Box Drawing characters
# t, b, l, r -> top, bottom, left, right
# h, v -> horizontal, vertical
# l, x -> line, cross (i.e. vertex)

# unicode (U_) chars
U_HL = '─'
U_VL = '│'
U_TL = '┌'
U_TR = '┐'
U_BL = '└'
U_BR = '┘'
U_LX = '├'
U_RX = '┤'
U_TX = '┬'
U_BX = '┴'
U_XX = '┼'

# ASCII (A_) chars
A_HL = '-'
A_VL = '|'
A_TL = '+'
A_TR = '+'
A_BL = '+'
A_BR = '+'
A_LX = '+'
A_RX = '+'
A_TX = '+'
A_BX = '+'
A_XX = '+'


def table(
    rows: List[List[str]],
    header: Optional[List[str]] = None,
    max_width: Optional[int] = None,
    unicode: bool = True,
) -> str:
    """Format text into a table.

    Args:
        rows: 2D table composed of lists.
        header: Optional 1D list to use as the table header.
        max_width: Maximum permitted width for the whole table including
            borders.
        unicode: Use unicode characters if True, else fallback to ascii.

    Examples:
        # simple ASCII table:
        >>> print(table([['a', 'b', 'c']], unicode=False))
        +---+---+---+
        | a | b | c |
        +---+---+---+

        # unicode table with headers and a max-width:
        >>> print(table(
        ...     [['a', 'b', 'c'], ['d', 'e', 'qwertyuiopasdfghjkl']],
        ...     header=['foo', 'bar', 'baz'],
        ...     max_width=27,
        ... ))
        ┌─────┬─────┬─────────────┐
        │ foo │ bar │ baz         │
        ├─────┼─────┼─────────────┤
        ├─────┼─────┼─────────────┤
        │ a   │ b   │ c           │
        ├─────┼─────┼─────────────┤
        │ d   │ e   │ qwertyuiopa │
        │     │     │ sdfghjkl    │
        └─────┴─────┴─────────────┘

        # edge case: table doesn't fit within max_width
        # (columns will use width of 1 and table will exceed max_width)
        >>> print(table([["a", "long"]], max_width=6))
        ┌───┬───┐
        │ a │ l │
        │   │ o │
        │   │ n │
        │   │ g │
        └───┴───┘

        # edge case: no data to display
        >>> table([])
        ''

    """
    if not rows:
        return ''
    # determine character set
    if unicode:
        hl = U_HL
        vl = U_VL
        tl = U_TL
        tr = U_TR
        bl = U_BL
        br = U_BR
        lx = U_LX
        rx = U_RX
        tx = U_TX
        bx = U_BX
        xx = U_XX
    else:
        hl = A_HL
        vl = A_VL
        tl = A_TL
        tr = A_TR
        bl = A_BL
        br = A_BR
        lx = A_LX
        rx = A_RX
        tx = A_TX
        bx = A_BX
        xx = A_XX

    # determine column widths
    widths = [0] * len(rows[0])
    for table_ in (rows, [header or []]):
        for row in (table_):
            for ind, col in enumerate(row):
                widths[ind] = max(widths[ind], len(col))

    def calc_width():
        return (sum(widths) + (len(widths) * 3) + 1)

    # resize cols to make them fix the max_width
    if max_width:
        overhang = max_width - calc_width()
        for _ in range(15):  # limit to 15 itterations
            _max_width = 0
            _max_col = 0
            # find the longest column
            for ind, width in enumerate(widths):
                if width > _max_width:
                    _max_width = width
                    _max_col = ind
            # reduce the longest column by up to 50% until it fits
            widths[_max_col] = max(
                int(widths[_max_col] / 2),
                widths[_max_col] + overhang
            ) or 1  # don't let column width go to 0
            overhang = max_width - calc_width()
            if overhang >= 0:
                break

    # textwrap the table to fit the desired widths
    _rows = [
        [
            textwrap.wrap(col, width=widths[ind])
            for ind, col in enumerate(row)
        ]
        for row in rows
    ]

    # Python f-string for formatting each row of the table
    row_format = vl + vl.join(
        f" {{{ind}:{width}}} " for ind, width in enumerate(widths)
    ) + vl

    # a divider row (i.e. a horizontal line)
    blank_line = lx + xx.join(hl * (width + 2) for width in widths) + rx

    # top border of table
    ret = [tl + tx.join(hl * (width + 2) for width in widths) + tr]

    # table header
    if header:
        ret.append(row_format.format(*header))
        ret.extend([blank_line, blank_line])

    # table body
    for row_ind, row in enumerate(_rows):
        max_height = max(len(col) for col in row)
        for line_ind in range(max_height):
            ret.append(row_format.format(
                *[
                    col[line_ind] if line_ind < len(col) else ''
                    for col in row
                ]
            ))
        if row_ind != len(_rows) - 1:
            # don't add a divider row for the last item
            ret.append(blank_line)

    # bottom border of table
    ret.append(bl + bx.join(hl * (width + 2) for width in widths) + br)

    return '\n'.join(ret)
