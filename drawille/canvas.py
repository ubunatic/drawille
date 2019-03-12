# -*- coding: utf-8 -*-

# (C) 2014- by Adam Tauber, <asciimoo@gmail.com>
# License: GNU AGPL (see LICENSE file or http://www.gnu.org/licenses)

from __future__ import absolute_import
from builtins import super

import math, os, curses, time, sys
from collections import defaultdict

try:                from shutil import get_terminal_size            # noqa
except ImportError: from shutil_backports import get_terminal_size  # noqa

IS_PY2 = sys.version_info.major < 3

if not IS_PY2: unichr = chr

"""
http://www.alanwood.net/unicode/braille_patterns.html

dots:
   ,___,
   |1 4|
   |2 5|
   |3 6|
   |7 8|
   `````
"""

pixel_map = ((0x01, 0x08),
             (0x02, 0x10),
             (0x04, 0x20),
             (0x40, 0x80))

# braille unicode characters starts at 0x2800
braille_char_offset = 0x2800

def iround(coord):
    T = type(coord)
    if   T is int:   return coord
    elif T is float: return int(round(coord))
    else:            raise TypeError("Unsupported coordinate type <{0}>".format(T))

def colrow(x, y):
    """Convert x, y to column, row in the braille matrix"""
    return iround(x) // 2, iround(y) // 4

def IntDict():   return defaultdict(int)

def IntDict2d(): return defaultdict(IntDict)


class Canvas(object):
    """Canvas implements the pixel surface."""

    def __init__(self, line_ending=os.linesep):
        super().__init__()
        self.clear()
        self.line_ending = line_ending


    def clear(self):
        """Remove all pixels from the :class:`Canvas` object."""
        self.chars = IntDict2d()


    def set(self, x, y):
        """Set a pixel of the :class:`Canvas` object.

        :param x: x coordinate of the pixel
        :param y: y coordinate of the pixel
        """
        x = iround(x)
        y = iround(y)
        col, row = colrow(x, y)

        if type(self.chars[row][col]) is int:
            self.chars[row][col] |= pixel_map[y % 4][x % 2]


    def unset(self, x, y):
        """Unset a pixel of the :class:`Canvas` object.

        :param x: x coordinate of the pixel
        :param y: y coordinate of the pixel
        """
        x = iround(x)
        y = iround(y)
        col, row = colrow(x, y)

        if type(self.chars[row][col]) is int:
            self.chars[row][col] &= ~pixel_map[y % 4][x % 2]

        if type(self.chars[row][col]) is not int or self.chars[row][col] == 0:
            del(self.chars[row][col])

        if not self.chars.get(row):
            del(self.chars[row])


    def toggle(self, x, y):
        """Toggle a pixel of the :class:`Canvas` object.

        :param x: x coordinate of the pixel
        :param y: y coordinate of the pixel
        """
        x = iround(x)
        y = iround(y)
        col, row = colrow(x, y)

        if type(self.chars[row][col]) is not int or self.chars[row][col] & pixel_map[y % 4][x % 2]:
            self.unset(x, y)
        else:
            self.set(x, y)


    def set_text(self, x, y, text):
        """Set text to the given coords.

        :param x: x coordinate of the text start position
        :param y: y coordinate of the text start position
        """
        col, row = colrow(x, y)

        for i,c in enumerate(text):
            self.chars[row][col+i] = c


    def get(self, x, y):
        """Get the state of a pixel. Returns bool.

        :param x: x coordinate of the pixel
        :param y: y coordinate of the pixel
        """
        x = iround(x)
        y = iround(y)
        dot_index = pixel_map[y % 4][x % 2]
        col, row = colrow(x, y)
        char = self.chars.get(row, {}).get(col)

        if   not char:              return False
        elif type(char) is not int: return True
        else:                       return bool(char & dot_index)


    def rows(self, min_x=None, min_y=None, max_x=None, max_y=None):
        """Yields the current :class:`Canvas` object lines.

        :param min_x: (optional) minimum x coordinate of the canvas
        :param min_y: (optional) minimum y coordinate of the canvas
        :param max_x: (optional) maximum x coordinate of the canvas
        :param max_y: (optional) maximum y coordinate of the canvas
        """

        if not self.chars.keys(): return

        minrow =  min_y      // 4 if min_y is not None else min(self.chars.keys())
        maxrow = (max_y - 1) // 4 if max_y is not None else max(self.chars.keys())
        mincol =  min_x      // 2 if min_x is not None else min(min(x.keys()) for x in self.chars.values())
        maxcol = (max_x - 1) // 2 if max_x is not None else max(max(x.keys()) for x in self.chars.values())

        for rownum in range(minrow, maxrow+1):
            if rownum not in self.chars: yield ''; continue

            maxcol = (max_x - 1) // 2 if max_x is not None else max(self.chars[rownum].keys())
            row = []

            for x in range(mincol, maxcol+1):
                char = self.chars[rownum].get(x)

                if not char:            row.append(unichr(braille_char_offset))
                elif type(char) is int: row.append(unichr(braille_char_offset+char))
                else:                   row.append(char)

            yield ''.join(row)


    def frame(self, min_x=None, min_y=None, max_x=None, max_y=None):
        """String representation of the current :class:`Canvas` object pixels.

        :param min_x: (optional) minimum x coordinate of the canvas
        :param min_y: (optional) minimum y coordinate of the canvas
        :param max_x: (optional) maximum x coordinate of the canvas
        :param max_y: (optional) maximum y coordinate of the canvas
        """
        ret = self.line_ending.join(self.rows(min_x, min_y, max_x, max_y))

        if IS_PY2: return ret.encode('utf-8')
        else:      return ret


def line(x1, y1, x2, y2):
    """Yields the pixel coordinates of the line between (x1, y1), (x2, y2)

    :param x1: x coordinate of the startpoint
    :param y1: y coordinate of the startpoint
    :param x2: x coordinate of the endpoint
    :param y2: y coordinate of the endpoint
    """

    x1 = iround(x1)
    y1 = iround(y1)
    x2 = iround(x2)
    y2 = iround(y2)

    xdiff = max(x1, x2) - min(x1, x2)
    ydiff = max(y1, y2) - min(y1, y2)
    xdir = 1 if x1 <= x2 else -1
    ydir = 1 if y1 <= y2 else -1

    if ydiff == 0 and xdiff == 0: return

    r = max(xdiff, ydiff)
    dy = ydiff / float(r) * ydir
    dx = xdiff / float(r) * xdir

    for i in range(r+1):
        i = float(i)
        yield (x1 + i * dx, y1 + i * dy)


def polygon(center_x=0, center_y=0, sides=4, radius=4):
    degree = 360.0 / float(sides)
    dr = float(radius + 1) / 2.0

    for n in range(sides):
        a = n * degree
        b = (n + 1) * degree
        x1 = (center_x + math.cos(math.radians(a))) * dr
        y1 = (center_y + math.sin(math.radians(a))) * dr
        x2 = (center_x + math.cos(math.radians(b))) * dr
        y2 = (center_y + math.sin(math.radians(b))) * dr

        for x, y in line(x1, y1, x2, y2):
            yield x, y


def animate(canvas, fn, delay=1.0/24.0, *args, **kwargs):
    """Animation automation function

    :param canvas: :class:`Canvas` object
    :param fn: Callable. Frame coord generator
    :param delay: Float. Delay between frames.
    :param *args, **kwargs: optional fn parameters
    """

    # python2 unicode curses fix
    if IS_PY2:
        import locale
        locale.setlocale(locale.LC_ALL, "")

    def animation(stdscr):

        for frame in fn(*args, **kwargs):
            for x,y in frame:
                canvas.set(x,y)

            f = canvas.frame()
            stdscr.addstr(0, 0, '{0}\n'.format(f))
            stdscr.refresh()
            if delay:
                time.sleep(delay)
            canvas.clear()

    curses.wrapper(animation)

