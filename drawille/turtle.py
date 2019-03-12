# -*- coding: utf-8 -*-

# (C) 2014- by Adam Tauber, <asciimoo@gmail.com>
# License: GNU AGPL (see LICENSE file or http://www.gnu.org/licenses)

from __future__ import absolute_import
from builtins import super
import math
from drawille.canvas import Canvas, line


class Turtle(Canvas):
    """Turtle graphics interface
    http://en.wikipedia.org/wiki/Turtle_graphics
    """

    def __init__(self, pos_x=0, pos_y=0):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.rotation = 0
        self.brush_on = True
        super().__init__()


    def up(self):
        """Pull the brush up."""
        self.brush_on = False


    def down(self):
        """Push the brush down."""
        self.brush_on = True


    def forward(self, step):
        """Move the turtle forward.

        :param step: Integer. Distance to move forward.
        """
        x = self.pos_x + math.cos(math.radians(self.rotation)) * step
        y = self.pos_y + math.sin(math.radians(self.rotation)) * step
        prev_brush_state = self.brush_on
        self.brush_on = True
        self.move(x, y)
        self.brush_on = prev_brush_state


    def move(self, x, y):
        """Move the turtle to a coordinate.

        :param x: x coordinate
        :param y: y coordinate
        """
        if self.brush_on:
            for lx, ly in line(self.pos_x, self.pos_y, x, y):
                self.set(lx, ly)

        self.pos_x = x
        self.pos_y = y


    def right(self, angle):
        """Rotate the turtle (positive direction).

        :param angle: Integer. Rotation angle in degrees.
        """
        self.rotation += angle


    def left(self, angle):
        """Rotate the turtle (negative direction).

        :param angle: Integer. Rotation angle in degrees.
        """
        self.rotation -= angle


    def back(self, step):
        """Move the turtle backwards.

        :param step: Integer. Distance to move backwards.
        """
        self.forward(-step)


    # 2-letter aliases
    pu = up
    pd = down
    fd = forward
    bk = back
    rt = right
    lt = left
    mv = move

    # 1-letter aliases
    u = up
    d = down
    f = forward
    b = back
    r = right
    l = left  # noqa
    m = move

