"""
ManyMan - A Many-core Visualization and Management System
Copyright (C) 2012
University of Amsterdam - Computer Systems Architecture
Jimi van der Woning and Roy Bakker

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from kivy.config import Config
from kivy.graphics import Color, Line
from kivy.logger import Logger
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class PerfGraph(Widget):
    """Widget that shows a performance graph through time."""

    def __init__(self, content, **kwargs):
        self.container = kwargs.get('container', None)
        self.content = content
        self.unit = kwargs.get('unit', '%')
        self.percent_scale = kwargs.get('percent_scale', True)
        self.color = kwargs.get('color', [1, 0, 1])
        self.history = kwargs.get(
            'history',
            Config.getint('settings', 'perfgraph_default_history')
        )

        # Initial load is all zeroes
        self.load = [0] * self.history
        self.label = Label(text=("%s 0%s" % (self.content, self.unit)))

        self.mainline = None
        self.lines = dict()
        self.loads = dict()
        self.colors = dict()
        self.axes_lines = []

        super(PerfGraph, self).__init__(**kwargs)
        self.add_widget(self.label)

        self.bind(pos=self.update_graphics_pos, size=self.update_graphics_size)

    def update_graphics_pos(self, instance, value):
        """Handler when the graph is moved. Redraws graph."""
        self.label.pos = value

        if self.showing():
            # Only redraw when visible
            unit_width = self.width / (self.history - 1.)

            for line in self.axes_lines:
                if self.canvas.indexof(line) >= 0:
                    self.canvas.remove(line)

            self.axes_lines = []
            with self.canvas:
                self.draw_axes()

            if self.canvas.indexof(self.mainline) < 0:
                return

            points = []
            for i in range(self.history):
                points.extend([
                    self.pos[0] + i * unit_width,
                    self.pos[1] + self.load[i] * self.height
                ])
            self.mainline.points = points

            for tid in self.lines.keys():
                points = []
                for i, load in enumerate(self.loads[tid]):
                    points.extend([
                        self.pos[0] + i * unit_width,
                        self.pos[1] + load * self.height
                    ])
                self.lines[tid].points = points

    def update_graphics_size(self, instance, value):
        """Handler when the graph is resized. Redraws graph."""
        self.label.size = value

        if self.showing():
            # Only redraw when visible
            unit_width = self.width / (self.history - 1.)

            for line in self.axes_lines:
                if self.canvas.indexof(line) >= 0:
                    self.canvas.remove(line)

            self.axes_lines = []
            with self.canvas:
                self.draw_axes()

            if self.canvas.indexof(self.mainline) < 0:
                return

            points = []
            for i in range(self.history):
                points.extend([
                    self.pos[0] + i * unit_width,
                    self.pos[1] + self.load[i] * self.height
                ])
            self.mainline.points = points

            for tid in self.lines.keys():
                points = []
                for i, load in enumerate(self.loads[tid]):
                    points.extend([
                        self.pos[0] + i * unit_width,
                        self.pos[1] + load * self.height
                    ])
                self.lines[tid].points = points

    def showing(self):
        """Determine whether the graph is visble or not."""
        return not self.container or self.container.info_showing

    def add_line(self, tid, hue):
        """Add a performance line with hue 'hue' to the graph."""
        Logger.debug("PerfGraph: Adding line for %s" % tid)
        self.loads[tid] = [0] * self.history
        self.colors[tid] = hue

        if self.showing():
            # Only draw the line when visible
            unit_width = self.width / (self.history - 1.)
            points = []
            for i, load in enumerate(self.loads[tid]):
                points.extend([
                    self.pos[0] + i * unit_width,
                    self.pos[1] + load * self.height
                ])

            with self.canvas:
                Color(self.colors[tid], 1, 1, mode='hsv')
                self.lines[tid] = Line(points=points)

    def update_line(self, tid, value):
        """Update the line with given tid to the given value."""
        if not tid in self.loads:
            return

        self.loads[tid].remove(self.loads[tid][0])
        self.loads[tid].append(value)

        if self.showing():
            # Only draw the line when visble
            unit_width = self.width / (self.history - 1.)
            points = []
            for i, load in enumerate(self.loads[tid]):
                if self.percent_scale:
                    y = self.pos[1] + (load / 100.) * self.height
                else:
                    y = self.pos[1] + (load / max(1e-5, *self.load)) * \
                        self.height
                points.extend([
                    self.pos[0] + i * unit_width,
                    y
                ])
            if not tid in self.lines:
                with self.canvas:
                    Color(self.colors[tid], 1, 1, mode='hsv')
                    self.lines[tid] = Line(points=points)
            else:
                self.lines[tid].points = points

    def remove_line(self, tid):
        """Remove the line with given tid from the graph."""
        if not tid in self.loads:
            return

        if tid in self.lines:
            self.canvas.remove(self.lines[tid])
            del self.lines[tid]

        del self.loads[tid]

    def update(self, value):
        """Update the main line to the given value."""
        # Force Kivy to render usage text
        self.label.text = ".........."

        if len(self.load) > 0:
            # Remove the oldest point of the line
            self.load.remove(self.load[0])
        self.load.append(value)

        if self.showing():
            # Only update when visible
            unit_width = self.width / (self.history - 1.)

            with self.canvas:
                for l in self.axes_lines:
                    self.canvas.remove(l)
                self.axes_lines = []
                self.draw_axes()

                Color(*self.color, mode='hsv')
                points = []
                for i in range(self.history):
                    if self.percent_scale:
                        y = self.pos[1] + (self.load[i] / 100.) * self.height
                    else:
                        y = self.pos[1] + \
                            (self.load[i] / float(max(1e-5, *self.load))) * \
                            self.height
                    points.extend([
                        self.pos[0] + i * unit_width,
                        y
                    ])

                if self.canvas.indexof(self.mainline) < 0:
                    self.mainline = Line(points=points)
                else:
                    self.mainline.points = points

            self.label.text = "%s: %f%s" % (self.content, value/100.0, self.unit)

    def draw_axes(self):
        """Draw the axes of the performance graph."""
        Color(0, .3, 0)
        self.axes_lines.append(Line(points=[
            self.pos[0],
            self.pos[1],
            self.pos[0] + self.width,
            self.pos[1]
        ], dash_length=3, dash_offset=6))
        self.axes_lines.append(Line(points=[
            self.pos[0] + self.width,
            self.pos[1],
            self.pos[0] + self.width,
            self.pos[1] + self.height
        ], dash_length=3, dash_offset=6))
        self.axes_lines.append(Line(points=[
            self.pos[0] + self.width,
            self.pos[1] + self.height,
            self.pos[0],
            self.pos[1] + self.height
        ], dash_length=3, dash_offset=6))
        self.axes_lines.append(Line(points=[
            self.pos[0],
            self.pos[1] + self.height,
            self.pos[0],
            self.pos[1]
        ], dash_length=3, dash_offset=6))

        Color(0, .2, 0)
        for i in range(1, 5):
            self.axes_lines.append(Line(points=[
                self.pos[0],
                self.pos[1] + i * self.height / 5,
                self.pos[0] + self.width,
                self.pos[1] + i * self.height / 5
            ], dash_length=1, dash_offset=2))
            self.axes_lines.append(Line(points=[
                self.pos[0] + i * self.width / 5,
                self.pos[1],
                self.pos[0] + i * self.width / 5,
                self.pos[1] + self.height
            ], dash_length=1, dash_offset=2))
