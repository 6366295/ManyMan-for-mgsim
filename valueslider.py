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

from kivy.logger import Logger
from kivy.uix.slider import Slider


class ValueSlider(Slider):
    """
    Extension of the standard Kivy Slider class that fires events and can be
    used to pick a value from a set rather than a range.
    """ 

    def __init__(self, **kwargs):
        self.values = kwargs.get("values", None)
        self.data = kwargs.get("data", None)

        self.register_event_type('on_change')
        self.register_event_type('on_release')

        super(ValueSlider, self).__init__(**kwargs)
        
        self._val = self._nearest_value(self.value)

    def _nearest_pos(self, pos):
        """Retrieve the nearest value position on the slider."""
        if not self.values:
            return pos

        v = self._get_value(pos)
        nv = self._nearest_value(v)
        return self._get_pos(nv)

    def _nearest_value(self, val):
        """Retrieve the nearest value from the given value."""
        if not self.values:
            return val

        nearest = self.values[0]
        for v in self.values:
            if abs(val - v) < abs(val - nearest):
                nearest = v
            elif abs(val - v) > abs(val - nearest):
                break

        self.val = nearest
        return nearest

    def _get_value(self, pos):
        """Get the real value from a given slider position."""
        x = min(self.right, max(pos[0], self.x))
        y = min(self.top, max(pos[1], self.y))
        if self.orientation == 'horizontal':
            if self.width == 0:
                norm = 0.
            else:
                norm = (x - self.x) / float(self.width)
        else:
            if self.height == 0:
                norm = 0.
            else:
                norm = (y - self.y) / float(self.height)
        return norm * (self.max - self.min) + self.min

    def _get_pos(self, val):
        """Get the slider position from a given value."""
        padding = self.padding
        x = self.x
        y = self.y
        d = self.max - self.min
        if d == 0:
            nval = 0
        else:
            nval = (val - self.min) / float(d)
        if self.orientation == 'horizontal':
            return (x + padding + nval * (self.width - 2 * padding), y)
        else:
            return (x, y + padding + nval * (self.height - 2 * padding))

    def on_change(self):
        """Handler when the slider value changes. Does nothing."""
        pass

    def on_release(self):
        """Handler when the slider is released. Does nothing."""
        pass

    def on_touch_down(self, touch):
        """Handler for touch events. Move the slider."""
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.value_pos = self._nearest_pos(touch.pos)
            return True

    def on_touch_move(self, touch):
        """Handler for move events. Move the slider."""
        if touch.grab_current == self:
            self.value_pos = self._nearest_pos(touch.pos)
            return True

    def on_touch_up(self, touch):
        """Handler for release events. Move the slider and fire event."""
        if touch.grab_current == self:
            self.value_pos = self._nearest_pos(touch.pos)
            self.dispatch('on_release')
            return True

    def get_val(self):
        """Getter for the value of the slider."""
        return self._val

    def set_val(self, value):
        """Setter for the slider's value. Fires change event."""
        Logger.debug("ValueSlider: Setting val to %s" % value)
        self._val = value
        self.value_pos = self._get_pos(value)
        self.dispatch('on_change')

    # Define getters and setters
    val = property(get_val, set_val)
