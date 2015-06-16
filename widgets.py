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
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.widget import Widget


class ImageButton(Button):
    """Button consisting of an image instead of a label."""

    def __init__(self, image_url, **kwargs):
        if 'text' in kwargs:
            del kwargs['text']

        kwargs.update({'color': [1., 0., 0., 1.]})

        self.image_url = image_url

        self.layout = None
        self._image = None

        super(ImageButton, self).__init__(**kwargs)

        self.build()

    def build(self):
        """Render the button."""
        self.layout = BoxLayout(spacing=5, padding=5)

        self._image = Image(
            source=self.image_url,
            color=(.8, .8, .8, 1),
            size_hint_y=None,
            height=40
        )
        self.layout.add_widget(self._image)

        self.add_widget(self.layout)

        self.bind(pos=self.update_graphics_pos, size=self.update_graphics_size)

    def update_graphics_pos(self, instance, value):
        """Handler when the button moves. Move its contents along."""
        self.layout.pos = value

    def update_graphics_size(self, instance, value):
        """Handler when the button resizes. Resize its contents along."""
        self.layout.size = value

    def get_image(self):
        """Getter for the button's image."""
        return self._image.source

    def set_image(self, value):
        """Setter for the button's image."""
        self._image.source = value

    # Define getters and setters
    image = property(get_image, set_image)


class IconButton(Button):
    """Button with an icon on the left."""

    def __init__(self, icon_url, **kwargs):
        self.text = kwargs.get('text', '')
        if self.text:
            del kwargs['text']

        self.icon_url = icon_url

        self.layout = None
        self.icon = None

        super(IconButton, self).__init__(**kwargs)

        self.build()

    def build(self):
        """Render the button."""
        self.layout = BoxLayout(spacing=5, padding=5)

        self.icon = Image(
            source=self.icon_url,
            color=(.8, .8, .8, 1),
            size_hint=(None, None),
            size=(40, 40)
        )
        self.layout.add_widget(self.icon)

        self.label = Label(
            text=self.text,
            size_hint_y=None,
            height=40
        )
        self.layout.add_widget(self.label)

        self.add_widget(self.layout)

        self.bind(pos=self.update_graphics_pos, size=self.update_graphics_size)

    def update_graphics_pos(self, instance, value):
        """Handler when the button moves. Move its contents along."""
        self.layout.pos = value

    def update_graphics_size(self, instance, value):
        """Handler when the button resizes. Resize its contents along."""
        self.layout.size = value

    def get_text(self):
        """Getter for the button's text."""
        return self.label.text

    def set_text(self, value):
        """Setter for the button's text."""
        self.label.text = value

    def get_image(self):
        """Getter for the button's image."""
        return self.icon.source

    def set_image(self, value):
        """Setter for the button's image."""
        self.icon.source = value

    # Define getters and setters
    txt = property(get_text, set_text)
    image = property(get_image, set_image)


class MyVKeyboard(VKeyboard):
    """
    Extended virtual keyboard class of which the keyboards folder can be
    changed.
    """

    def __init__(self, **kwargs):
        self.layout_path = Config.get('settings', 'keyboards_folder')
        super(MyVKeyboard, self).__init__(**kwargs)


class MyTextInput(TextInput):
    """
    Extended text input class which allows for automatic resize and readonly
    text fields.
    """

    def __init__(self, **kwargs):
        self.readonly = kwargs.get('readonly', False)
        self.auto_resize = kwargs.get('auto_resize', False)
        super(MyTextInput, self).__init__(**kwargs)

    def insert_text(self, substring):
        """Insert the given substring when not readonly."""
        if self.readonly:
            return
        super(MyTextInput, self).insert_text(substring)

    def do_backspace(self):
        """Insert a backspace when not readonly."""
        if self.readonly:
            return
        super(MyTextInput, self).do_backspace()

    def delete_selection(self):
        """Delete the selection when not readonly."""
        if self.readonly:
            return
        super(MyTextInput, self).delete_selection()

    def on_touch_down(self, touch):
        """Handle the touch events when not readonly."""
        if self.readonly:
            return False
        super(MyTextInput, self).on_touch_down(touch)

    def on_focus(self, instance, value, *largs):
        """Handle the focus events when not readonly."""
        if self.readonly:
            return
        super(MyTextInput, self).on_focus(instance, value, *largs)

    def append_text(self, text):
        """Append given text to the textfield."""
        self.set_text(self.text + text)

    def set_text(self, text):
        """Set the contents of the textfield to the given text."""
        Logger.debug("MyTextInput: Setting text to %s" % text)
        self.text = text
        if self.auto_resize:
            # Resize the textfield when needed
            self.height = len(self._lines) * (self.line_height +
                self._line_spacing) + self.padding_y * 2


class WRectangle(Widget):
    """Widget version of the Rectangle graphic."""

    def __init__(self, **kwargs):
        self.color = kwargs.get('color', [1., 1., 1., 1.])
        super(WRectangle, self).__init__(**kwargs)

        self.build()

    def build(self):
        """Render the rectangle."""
        with self.canvas:
            self.c = Color()
            self.c.rgba = self.color
            self.r = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_pos, size=self.update_size)

    def update_pos(self, instance, value):
        """Handler when the rectangle's position changes."""
        self.r.pos = value

    def update_size(self, instance, value):
        """Handler when the rectangle's size changes."""
        self.r.size = value
