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

from infopopup import InfoPopup
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from perfgraph import PerfGraph
from util import frange
from valueslider import ValueSlider


class Core(Button):
    """Core object that contains all information about a single core."""

    def __init__(self, index, manyman, **kwargs):
        self.index = index
        self.manyman = manyman

        self.load = 0.0
        self.viz_load = 0.0
        self.move_speed = 0.0

        self.info_built = False
        self.info_showing = False
        self._frequency = 533
        self._voltage = 1.
        self.tasks = dict()
        # Number of tasks RUNNING on the core.
        self.pending_count = 0
        # Always increasing, for determining task color.
        self.task_count = 0

        self.c = None
        self.r = None
        self.info = None
        self.fs = None
        self.frequency_label = None
        self.voltage_label = None
        self.cpu_graph = None
        self.mem_graph = None
        self.task_list = None

        settings = {
            'text': self.info_text(),
            'background_normal': manyman.settings['core_background'],
            'background_down': manyman.settings['core_background_active'],
            'border':  manyman.settings['core_border'],
            'halign': 'center'
        }

        settings.update(kwargs)

        super(Core, self).__init__(**settings)

        self.build()

    def build(self):
        """Render the core widget."""
        with self.canvas:
            # Add the color overlay
            self.c = Color(
                self.manyman.settings['core_color_range'][0], 1, 1, .7,
                mode='hsv'
            )

            p = self.manyman.settings['core_padding']
            self.r = Rectangle(
                pos=[self.pos[0] + p, self.pos[1] + p],
                size=[
                    self.width - 2 * p,
                    max(0, self.height * self.viz_load - 2 * p)
                ]
            )

        # Initialize the popup containing detailed core information
        self.info = InfoPopup(
            title="Core %d" % self.index,
            size_hint=(None, None),
            size=(600, 450)
        )
        self.info.bind(on_show=self.info_show, on_dismiss=self.info_dismiss)

        # Initialize the performance graphs of that popup
        self.cpu_graph = PerfGraph("CPU", container=self)
        self.mem_graph = PerfGraph("MEM", container=self)

    def build_info(self):
        """Render the popup containing detailed core information."""
        layout = BoxLayout(orientation='vertical', spacing=10)

        controls = BoxLayout(spacing=10, size_hint_y=None, height=50)
        #layout.add_widget(controls)

        # Add frequency control slider
        frequency_control = BoxLayout(orientation='vertical', spacing=2)
        controls.add_widget(frequency_control)

        self.frequency_label = Label(text='Frequency: %s MHz' % self.frequency)
        frequency_control.add_widget(self.frequency_label)
        self.fs = ValueSlider(
            min=100,
            max=800,
            value=533,
            values=[800, 533, 400, 320, 267, 200, 100]
        )
        self.fs.bind(on_change=self.frequency_changed)
        self.fs.bind(on_release=self.frequency_set)
        frequency_control.add_widget(self.fs)

        # Add voltage control slider
        voltage_control = BoxLayout(orientation='vertical', spacing=2)
        controls.add_widget(voltage_control)

        self.voltage_label = Label(text='Voltage: %.4fV' % self.voltage)
        voltage_control.add_widget(self.voltage_label)

        content = BoxLayout(spacing=10)
        layout.add_widget(content)

        # Render the performance graphs
        graphs = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=5
        )
        graphs.add_widget(self.cpu_graph)
        graphs.add_widget(self.mem_graph)

        content.add_widget(graphs)

        # Render the task list
        tasks = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=5,
            size_hint_x=None,
            width=300
        )

        scroll = ScrollView(do_scroll_x=False)

        self.task_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.task_list.bind(minimum_height=self.task_list.setter('height'))

        scroll.add_widget(self.task_list)
        tasks.add_widget(scroll)
        content.add_widget(tasks)

        self.info.content = layout

        self.info_built = True

    def frequency_changed(self, ins):
        """Handler when the frequency slider is moved.""" 
        self.frequency_label.text = "Frequency: %d MHz" % ins.val

    def frequency_set(self, ins):
        """Handler when the frequency is set."""
        Logger.info("Core: Set frequency to: %s" % ins.val)
        self._frequency = ins.val
        self.manyman.comm.set_core_frequency(ins.val, self.index)

    def info_show(self, *largs):
        """Handler when the detailed core information popup is opened."""
        if not self.info_built:
            # Render said popup
            self.build_info()
        self.info_showing = True

    def info_dismiss(self, instance):
        """Handler when the detailed core information popup is closed."""
        self.info_showing = False

    def add_task(self, t):
        """Add a task to this core."""
        t.hue = (self.task_count * .15) % 1
        self.tasks[t.tid] = t
        self.task_list.add_widget(t)
        self.task_count += 1

        # Add the task's performance lines
        self.cpu_graph.add_line(t.tid, t.hue)
        self.mem_graph.add_line(t.tid, t.hue)

        Logger.debug("Core: Added task %s to core %d" % (t.tid, self.index))

    def remove_task(self, t):
        """Remove a task from this core."""
        if not t.tid in self.tasks:
            return

        Logger.debug(
            "Core: Removing task %s from core %d" % (t.tid, self.index)
        )
        self.tasks.pop(t.tid)
        self.task_list.remove_widget(t)

        # Remove the task's performance lines
        self.cpu_graph.remove_line(t.tid)
        self.mem_graph.remove_line(t.tid)

    def highlight(self):
        """Highlight this core."""
        self.state = 'down'

    def dehighlight(self):
        """Dehighlight this core."""
        self.state = 'normal'

    def update(self, dt):
        """Update the performance overlay."""

        # Determine the new visible load
        if self.viz_load > self.load + 1e-3:
            self.viz_load -= self.move_speed
        elif self.viz_load < self.load - 1e-3:
            self.viz_load += self.move_speed
        else:
            self.viz_load = self.load

        # Determine the new color
        cr = self.manyman.settings['core_color_range']
        self.c.h = cr[0] + self.viz_load * (cr[1] - cr[0])
        self.c.a = 0.7

        # Determine the new size
        p = self.manyman.settings['core_padding']
        self.r.pos = [self.pos[0] + p, self.pos[1] + p]
        self.r.size = [
            self.width - 2 * p,
            max(0, (self.height - 2 * p) * self.viz_load)
        ]

    def update_load(self, load):
        """Update this core's CPU load."""
        self.load = load

        # Determine the speed at which the overlay will resize
        self.move_speed = abs(self.load - self.viz_load) / \
            self.manyman.settings['framerate'] * 1.2

        self.cpu_graph.update(load * 100)

        self.text = self.info_text()

    def update_mem(self, load):
        """Update this core's memory usage."""
        self.mem_graph.update(load * 100)

    def info_text(self):
        """Retrieve the core's info text."""
        return "Core %d\n(%d tasks)" % (
            self.index,
            self.pending_count
        )

    def on_press(self):
        """Handler when the core is pressed. Opens the detailed info popup."""
        self.info.show()

    def on_release(self):
        """Handler when the core is released. Does nothing."""
        pass

    def get_frequency(self):
        """Getter for the core's frequency."""
        return self._frequency

    def set_frequency(self, value):
        """Setter for the core's frequency."""
        if not self.info_built or self.frequency == value:
            return

        self._frequency = value
        self.fs.val = value

    def get_voltage(self):
        """Getter for the core's voltage."""
        return self._voltage

    def set_voltage(self, value):
        """Setter for the core's voltage."""
        if not self.info_built or self.voltage == value:
            return

        self._voltage = value
        self.voltage_label.text = "Voltage: %.4fV" % value

    # Define getters and setters
    frequency = property(get_frequency, set_frequency)
    voltage = property(get_voltage, set_voltage)
