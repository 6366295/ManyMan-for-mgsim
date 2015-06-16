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


class Component(Button):

    def __init__(self, index, manyman, **kwargs):
        self.index = index
        self.manyman = manyman

        self.load = 0.0
        self.load2 = dict()
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
        
        #EDITED!
        self.data = dict()
        self.buttons_box = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.buttons_box.bind(minimum_height=self.buttons_box.setter('height'))
        self.label = None
        self.current = None
        self.box2 = BoxLayout(orientation='vertical', size_hint_x=None, width=300)
        self.data2 = dict()
        self.scroll2 = None

        settings = {
            'text': self.info_text(),
            'background_normal': manyman.settings['core_background'],
            'background_down': manyman.settings['core_background_active'],
            'border':  manyman.settings['core_border'],
            'halign': 'center',
        }

        settings.update(kwargs)

        super(Component, self).__init__(**settings)

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
            title=self.index,
            size_hint=(None, None),
            size=(650, 450)
        )
        self.info.bind(on_show=self.info_show, on_dismiss=self.info_dismiss)

        # Initialize the performance graphs of that popup
        self.cpu_graph = PerfGraph("Change", container=self)
        self.mem_graph = PerfGraph("MEM", container=self)

    def build_info(self):
        """Render the popup containing detailed core information."""
        layout = BoxLayout(orientation='horizontal', spacing=10)
        
        box = BoxLayout(orientation='vertical', size_hint_x=None, width=300)
        #box2 = BoxLayout(orientation='vertical', size_hint_x=None, width=300)

        
        scroll = ScrollView(do_scroll_x=False)
        
        scroll.add_widget(self.buttons_box)
        box.add_widget(scroll)
        
        self.scroll2 = ScrollView(do_scroll_x=False)
        self.label = Label(text='Nothing selected', halign='left', valign='top', text_size=(250, 150))
        self.label.bind(texture_size=self.label.setter('size'))
        self.scroll2.add_widget(self.label)
        self.box2.add_widget(self.scroll2)
        #self.box2.add_widget(self.cpu_graph)
        layout.add_widget(box)
        layout.add_widget(self.box2)
        
        '''
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
        '''
        # Render the performance graphs

        self.info.content = layout

        self.info_built = True

    def add_acc(self):
        item = AccordionItem(title='Helpssss')
        self.acc.add_widget(item)

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
            
        load3 = 0.0
        for l in self.load2.values():
            load3 += float(l)
            
        load3 = load3/len(self.load2)
        
        # Determine the new color
        cr = self.manyman.settings['core_color_range']
        self.c.h = cr[0] + load3 * (cr[1] - cr[0])
        self.c.a = 0.7
        
        p = self.manyman.settings['core_padding']
        self.r.pos = [self.pos[0] + p, self.pos[1] + p]
        self.r.size = [
            self.width - 2 * p,
            max(0, (self.height - 2 * p) * load3)
        ]

        # Determine the new size
        #for k in self.data.keys():
        #    p = self.manyman.settings['core_padding']
        #    self.r[k].pos = [self.pos[0] + p, self.pos[1] + p]
        #    self.r[k].size = [
        #        self.width - 2 * p,
        #        max(0, (self.height - 2 * p) * self.load2[k]) # was self.viz_load
        #    ]

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
        self.mem_graph.update
        
    def update_data(self, k, v):
        """Update this core's memory usage."""
        if len(self.data[k]) < 1:
            self.data[k].append(v)
        
        if self.data[k]:
            t = self.manyman.current_kernel_cycle - self.manyman.previous_kernel_cycle
            c = 0
            if t != 0:
                c = (v - self.data[k][-1])*(1.0)/t
            self.data2[k][1].update(c * 100)
            
            if v != self.data[k][-1]:
                #self.update_load(1.0)
                self.load2[k] = 1
                self.data[k].append(v)
                self.data2[k][0].background_color = (0,1,0,1)
            else:
                #self.update_load(0.0)
                self.load2[k] = 0
                self.data2[k][0].background_color = (1,1,1,1)
                
        if len(self.data[k]) > 5:
            del self.data[k][0]
            
        self.update(0)
        
        if not self.info_showing:
            return
        
        if self.current in self.data:
            self.label.text = self.current + '\n\n' + '\n'.join(str(x) for x in self.data[unicode(self.current)][-5:])
            
    def set_data(self, k):
        """Update this core's memory usage."""
        self.data[k] = []
        self.load2[k] = 0
        
        #with self.canvas:
        #    p = self.manyman.settings['core_padding']
        #    self.r[k] = Rectangle(
        #        pos=[self.pos[0] + p, self.pos[1] + p],
        #        size=[
        #            self.width - 2 * p,
        #            max(0, self.height * self.load - 2 * p)
        #        ]
        #    )
        
        button = Button(text=k, size_hint=(None,None), size=(300,30))
        button.bind(on_press=self.dostuff)
        self.buttons_box.add_widget(button)
        graph = PerfGraph("", container=self, unit="")
        
        self.data2[k] = [button, graph]
        
    def dostuff(self, *largs):
        self.current = largs[0].text
        self.label.text = self.current + '\n\n' + '\n'.join(str(x) for x in self.data[unicode(self.current)][-5:])
        self.box2.clear_widgets()
        self.box2.add_widget(self.scroll2)
        self.box2.add_widget(self.data2[unicode(self.current)][1])
        
    def get_data(self, k):
        """Update this core's memory usage."""
        #print "WTTTTTTTTTTTTTTTF"
        return self.data[k]

    def info_text(self):
        """Retrieve the core's info text."""
        return self.index.split('.')[-1]

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
