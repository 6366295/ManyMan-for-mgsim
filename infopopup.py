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

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, BorderImage
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from widgets import WRectangle

# Global list of all popups
popups = []


def swerve_all_popups(*largs):
    """Swerve all opened popups out of the way."""
    for popup in popups:
        popup.swerve()


def swerve_all_popups_back(*largs):
    """Swerve all opened popups back to where they came from."""
    for popup in popups:
        popup.swerve_back()


class InfoPopup(Scatter):
    """Widget that contains detailed information in a draggable popup."""

    def __init__(self, **kwargs):
        global popups

        popups.append(self)

        self._built = False
        self._window = None
        self._parent = None
        self._old_center = (0, 0)
        self.layout = None
        self.label = None
        self.container = None

        self.background = kwargs.get(
            'background',
            'atlas://data/images/defaulttheme/modalview-background'
        )
        self.border = kwargs.get('border', [16, 16, 16, 16])

        self._title = kwargs.get('title', 'No title')
        self._content = kwargs.get('content', None)

        self.register_event_type('on_show')
        self.register_event_type('on_dismiss')

        super(InfoPopup, self).__init__(**kwargs)

    def build(self):
        """Render the popup."""
        with self.canvas:
            Color(1, 1, 1)
            BorderImage(
                source=self.background,
                border=self.border,
                pos=self.pos,
                size=self.size
            )

        self.layout = GridLayout(
            cols=1,
            padding=12,
            spacing=5,
            size_hint=(None, None),
            pos=self.pos,
            size=self.size
        )

        header = BoxLayout(size_hint_y=None, height=28)

        # Set the popup's title
        self.label = Label(
            text=self.title,
            size_hint_y=None,
            height=24,
            valign='middle',
            font_size=12,
            padding=(0, 6),
            text_size=(self.width - 124, 24)
        )
        header.add_widget(self.label)

        # Add a close button
        close_btn = Button(
            text='Close',
            size_hint=(None, None),
            size=(100, 28)
        )
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)

        self.layout.add_widget(header)

        separator = WRectangle(
            size_hint_y=None,
            height=2,
            color=[.2, .6, .9, 1.]
        )
        self.layout.add_widget(separator)

        # Add the popup's contents
        self.container = BoxLayout()
        if self._content:
            self.container.add_widget(self._content)
        self.layout.add_widget(self.container)

        self.add_widget(self.layout)

        self._built = True

    def update_textures(self, widget=None, *largs):
        """Update all labels inside the popup."""
        if not isinstance(widget, Widget):
            widget = self
        if isinstance(widget, Label):
            Logger.debug("InfoPopup: Update texture of %s" % widget.__class__)
            widget.texture_update()
        for child in widget.children:
            self.update_textures(child)

    def show(self, *largs):
        """Open the popup."""
        if self._window:
            # Bring to front
            self._window.remove_widget(self)
            self._window.add_widget(self)
            self._align_center()
            return self

        self._window = Window
        if not self._window:
            Logger.warning('InfoPopup: cannot open popup, no window found.')
            return self

        self._window.add_widget(self)
        self._window.bind(on_resize=self._align_center)

        if not self._built:
            # Render the popup when not done so yet
            self.build()
        self.center = self._window.mouse_pos
        self._align_center()

        Clock.schedule_once(self.update_textures, .5)
        self.dispatch('on_show')
        return self

    def dismiss(self, *largs):
        """Close the popup."""
        if self._window:
            self._window.remove_widget(self)
            self._window.unbind(on_resize=self._align_center)
            self._window = None

        self.dispatch('on_dismiss')
        return self

    def swerve(self, *largs):
        """Move the popup to the closest side of the screen."""
        if not self._window:
            return

        self._old_center = self.center

        dx = self._window.center[0] - self.center[0]
        dy = self._window.center[1] - self.center[1]

        # Window dimensions
        ww = self._window.width
        wh = self._window.height

        # Extended sizes
        eww = ww + (self.width - 40)
        ewh = wh + (self.height - 40)

        if abs(dx) / ww >= abs(dy) / wh:
            if dx > 0:
                tx = -(self.width / 2 - 20)
            else:
                tx = ww + (self.width / 2 - 20)

            if dy > 0:
                ty = self.center[1] - eww / 2 * abs(dy) / (abs(dx) + 1e-5) + dy
            else:
                ty = self.center[1] + eww / 2 * abs(dy) / (abs(dx) + 1e-5) + dy
        else:
            if dx > 0:
                tx = self.center[0] - ewh / 2 * abs(dx) / (abs(dy) + 1e-5) + dx
            else:
                tx = self.center[0] + ewh / 2 * abs(dx) / (abs(dy) + 1e-5) + dx

            if dy > 0:
                ty = -(self.height / 2 - 20)
            else:
                ty = wh + (self.height / 2 - 20)

        Animation(
            center=(tx, ty),
            t='in_out_expo',
            d=.3
        ).start(self)

    def swerve_back(self, *largs):
        """Move the popup back to where it came from."""
        if not self._window:
            return

        Animation(
            center=self._old_center,
            t='in_out_expo',
            d=.3
        ).start(self)

    def on_size(self, instance, value):
        """Handler when the popup is resized. Re-align the popup."""
        self._align_center()

    def _align_center(self, *largs):
        """Re-align the popup to the center of the screen."""
        if self._window:
            Animation(
                center=self._window.center,
                t='in_out_expo',
                d=.3
            ).start(self)

    def on_show(self):
        """Handler when the popup is opened. Does nothing."""
        pass

    def on_dismiss(self):
        """Handler when the popup is closed. Does nothing."""
        pass

    def get_title(self):
        """Getter for the popup's title."""
        return self._title

    def set_title(self, value):
        """Setter for the popup's title."""
        self._title = value
        if self.label:
            self.label.text = self._title

    def get_content(self):
        """Getter for the popup's content."""
        return self._content

    def set_content(self, value):
        """Setter for the popup's content."""
        self._content = value
        if self.container:
            self.container.clear_widgets()
            if self._content:
                self.container.add_widget(self._content)
            Clock.schedule_once(self.update_textures, .5)

    # Define getters and setters
    title = property(get_title, set_title)
    content = property(get_content, set_content)
