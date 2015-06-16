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

from infopopup import InfoPopup, swerve_all_popups, swerve_all_popups_back
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from os import mkdir
from os.path import isdir
from perfgraph import PerfGraph
from time import strftime
from widgets import ImageButton


class Task(Widget):
    """Basic task Widget. Contains all information about a task."""

    def __init__(self, name, manyman, **kwargs):
        self.name = name
        self.manyman = manyman
        self._hue = kwargs.get('color', manyman.settings['task_default_color'])

        self.c = None
        self.r = None
        self.layout = None

        self.grabbable = True
        self.coll_core = None

        super(Task, self).__init__(**kwargs)

        self.build()

    def build(self):
        """Render this task object."""
        with self.canvas:
            self.c = Color(self.hue, 1, 1, .7, mode='hsv')
            self.r = Rectangle(pos=self.pos, size=self.size)

        self.layout = BoxLayout(padding=10)
        self.add_widget(self.layout)

    def update_graphics_pos(self, instance, value):
        """
        Handler when the task object moves. Updates its contents' positions.
        """
        self.layout.pos = value
        self.r.pos = value

    def update_graphics_size(self, instance, value):
        """
        Handler when the task object is resized. Updates its contents' sizes.
        """
        self.layout.size = value
        self.r.size = value

    def on_touch_down(self, touch):
        """
        Handler when the task object is touched. Detatches the object from its
        parent so that it can be moved around.
        """
        x, y = touch.x, touch.y

        if not self.collide_point(x, y) or not self.grabbable:
            return False

        # Make sure a task object can not be touched multiple times at once
        self.grabbable = False
        touch.grab(self)

        root_window = self.get_root_window()
        self.from_pos = self.to_window(x, y)
        self.from_parent = self.parent
        self.from_index = self.parent.canvas.indexof(self.canvas)
        self.from_parent.remove_widget(self)

        self.center = self.from_pos
        root_window.add_widget(self)

        swerve_all_popups()

        return True

    def on_touch_move(self, touch):
        """
        Handler when the task object is dragged. Finds the core it is hovering
        above.
        """
        x, y = touch.x, touch.y

        if not touch.grab_current == self:
            return False

        self.center = x, y

        found = False
        for core in self.manyman.cores.values():
            if core.collide_point(x, y):
                if not self.coll_core or core != self.coll_core:
                    if self.coll_core:
                        self.coll_core.dehighlight()
                    core.highlight()

                found = True
                self.coll_core = core
                break

        if not found and self.coll_core:
            self.coll_core.dehighlight()
            self.coll_core = None

        return True

    def on_touch_up(self, touch):
        """
        Handler when the task is released. Moves it back to where it came from.
        """
        if not touch.grab_current == self:
            return False

        if self.coll_core:
            self.coll_core.dehighlight()
            self.reset()
        else:
            anim = Animation(
              center=self.from_pos,
              duration=.2,
              transition='in_out_quad'
            )
            anim.bind(on_complete=self.anim_finish)
            anim.start(self)

        swerve_all_popups_back()

        return True

    def anim_finish(self, anim, instance):
        """Handler when the back-moving animation finishes. Resets the task."""
        self.reset()

    def reset(self):
        """Re-add the task to its former parent."""
        self.parent.remove_widget(self)
        self.add_to(self.from_parent, self.from_index)
        self.grabbable = True

    def add_to(self, widget, index):
        """Add the task to the given widget at the given index."""
        self.parent = widget
        canvas = widget.canvas
        children = widget.children
        if index >= len(children):
            index = len(children)
            next_index = 0
        else:
            next_child = children[index]
            next_index = canvas.indexof(next_child.canvas)
            if next_index == -1:
                next_index = canvas.length()
            else:
                next_index += 1
        l = len(children)
        children.insert(l - index, self)
        canvas.insert(l - next_index, self.canvas)

    def get_hue(self):
        """Getter for the hue value of this task."""
        return self._hue

    def set_hue(self, value):
        """Setter for the hue value of the task."""
        Logger.debug("Task: Setting hue to %.2f" % value)
        self._hue = value
        self.c.h = value
        self.c.a = .7
        self.r.pos = self.r.pos

    # Define getters and setters
    hue = property(get_hue, set_hue)


class PendingTask(Task):
    """Widget for tasks in the pending tasks list."""

    def __init__(self, name, tid, manyman, **kwargs):
        Logger.debug("PendingTask: Inited pendingtask %s" % name)

        self.tid = tid
        self.command = kwargs.get('command', '')

        self.dup_button = None
        self.start_button = None

        super(PendingTask, self).__init__(name, manyman, **kwargs)

        self._build()

    def _build(self):
        """Render the PendingTask."""
        self.dup_button = Image(
            source=self.manyman.settings['task_dup_image'],
            color=(.8, .8, .8, 1),
            size_hint=(None, None),
            size=(40, 40)
        )
        self.layout.add_widget(self.dup_button)

        self.label = Label(
            text="AAAAAAAAAAAAAA",
            halign='center'
        )
        self.layout.add_widget(self.label)

        self.start_button = Image(
            source=self.manyman.settings['task_start_image'],
            color=(.8, .8, .8, 1),
            size_hint=(None, None),
            size=(40, 40)
        )
        self.layout.add_widget(self.start_button)

        self.bind(
            pos=self.update_graphics_pos,
            size=self.update_graphics_size
        )
        self.update_graphics_pos(self, self.pos)
        self.update_graphics_size(self, self.size)

        # Force Kivy to render the labels
        self.label.text = "AAADSldjbdejhvdsaf"

        if self.is_new():
            self.label.text = "%s\nNew" % self.name
        else:
            self.label.text = "%s\nStopped" % self.name

    def is_new(self):
        """Determine whether a task is new or stopped."""
        return self.tid[0] == 'P'

    def on_touch_down(self, touch):
        """Handler when a task is touched. Checks for button touches first."""
        x, y = touch.x, touch.y
        if self.dup_button.collide_point(x, y):
            # Duplicate the task
            self.dup_button.color = (.9, .6, 0, 1)
            Logger.debug("PendingTask: Duplicating task %s" % self.tid)
            if self.is_new():
                self.manyman.new_task(self.command, self.name)
            else:
                self.manyman.comm.duplicate_task(self.tid)
            return False
        if self.start_button.collide_point(x, y):
            # Smart-start the task
            self.start_button.color = (.9, .6, 0, 1)
            if self.is_new():
                self.manyman.comm.start_task(self.name, self.command)
            else:
                self.manyman.comm.move_task(self)
            self.parent.remove_widget(self)
            return False

        if not super(PendingTask, self).on_touch_down(touch):
            return False

        return True

    def on_touch_move(self, touch):
        """Handler when a task is dragged. Reset the button colors."""
        if not super(PendingTask, self).on_touch_move(touch):
            return False

        self.dup_button.color = (.8, .8, .8, 1)
        self.start_button.color = (.8, .8, .8, 1)

        return True

    def on_touch_up(self, touch):
        """
        Handler when a task is released. Starts the task on the core it was
        released on (if any).
        """
        x, y = touch.x, touch.y
        self.dup_button.color = (.8, .8, .8, 1)
        self.start_button.color = (.8, .8, .8, 1)
        if self.dup_button.collide_point(x, y):
            return False
        if self.start_button.collide_point(x, y):
            return False

        if not super(PendingTask, self).on_touch_up(touch):
            return False

        if self.coll_core:
            if self.is_new():
                self.manyman.comm.start_task(
                    self.name,
                    self.command,
                    self.coll_core.index
                )
            else:
                self.manyman.comm.move_task(self, self.coll_core.index)
            self.center = self.from_pos
            self.coll_core = None
            self.parent.remove_widget(self)

        return True


# Text to show when no task output is present yet
NO_OUTPUT_TEXT = 'No output yet...'


class CoreTask(Task):
    """Widget for all tasks that are currently on a core."""

    def __init__(self, name, tid, core, status, **kwargs):
        Logger.debug("CoreTask: Inited coretask %s" % tid)

        self.tid = tid
        self._core = core
        self._status = status

        self.info_built = False
        self.info_showing = False

        self.info_button = None
        self.label = None
        self.info = None
        self.stop_button = None
        self.pause_button = None
        self.move_button = None
        self.button_strings = dict()
        self.scroll = None

        self._outfile = None
        self._out = []
        self._cpu = 0.0
        self._mem = 0.0

        super(CoreTask, self).__init__(name, core.manyman, **kwargs)

        self._build()

    def _build(self):
        """Render this task."""
        self.info_button = Image(
            source=self.manyman.settings['task_info_image'],
            color=(.8, .8, .8, 1),
            size_hint=(None, None),
            size=(40, 40)
        )
        self.layout.add_widget(self.info_button)

        self.label = Label(
            text="..........",
            halign='center'
        )
        self.layout.add_widget(self.label)

        # Initialize the detailed task info popup
        self.info = InfoPopup(
            title="%s (%s) - %s on core %d" % \
                (self.name, self.tid, self.status, self.core.index),
            size_hint=(None, None),
            size=(600, 450)
        )
        self.info.bind(on_show=self.info_show, on_dismiss=self.info_dismiss)

        # Initialize the performance graphs located in the popup
        self.cpu_graph = PerfGraph("CPU", container=self)
        self.mem_graph = PerfGraph("MEM", container=self)

        self.bind(pos=self.update_graphics_pos, size=self.update_graphics_size)
        self.update_graphics_pos(self, self.pos)
        self.update_graphics_size(self, self.size)

        self.label.text = '%s\nStatus: %s' % (self.name, self.status)

    def build_info(self):
        """Render the detailed task info popup."""
        layout = BoxLayout(spacing=10)

        # Render the performance graphs
        graphs = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=5
        )
        graphs.add_widget(self.cpu_graph)
        graphs.add_widget(self.mem_graph)

        layout.add_widget(graphs)

        sidebar = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=5,
            size_hint_x=None,
            width=400
        )

        # Render the task control buttons
        controls = BoxLayout(
            spacing=10,
            padding=5,
            size_hint_y=None,
            height=60
        )

        self.stop_button = ImageButton(
            self.manyman.settings['task_stop_image']
        )
        self.bind_button(self.stop_button, self.stop)
        controls.add_widget(self.stop_button)

        self.pause_button = ImageButton(
            self.manyman.settings['task_pause_image']
        )
        self.bind_button(self.pause_button, self.pause)
        controls.add_widget(self.pause_button)

        self.move_button = ImageButton(
            self.manyman.settings['task_move_image']
        )
        self.bind_button(self.move_button, self.move)
        controls.add_widget(self.move_button)

        sidebar.add_widget(controls)

        # Render the output field
        self.scroll = ScrollView(do_scroll_x=False)
        self.output = Label(
            text=NO_OUTPUT_TEXT,
            text_size=(390, None),
            size_hint=(None, None),
            valign='top'
        )
        if len(self._out) > 0:
            self.set_output(self._out)
        self.output.bind(texture_size=self.output.setter('size'))
        self.scroll.add_widget(self.output)

        sidebar.add_widget(self.scroll)
        layout.add_widget(sidebar)

        self.info.content = layout

        self.info_built = True

    def update_graphics_pos(self, instance, value):
        """
        Handler when the task object moves. Updates its contents' positions.
        """
        super(CoreTask, self).update_graphics_pos(instance, value)

    def update_graphics_size(self, instance, value):
        """
        Handler when the task object resizes. Updates its contents' sizes.
        """
        super(CoreTask, self).update_graphics_size(instance, value)

    def bind_button(self, button, string):
        """Bind an action (string) to the given button."""
        self.button_strings[button] = string
        button.bind(on_release=string)

    def unbind_button(self, button):
        """Unbind all actions (strings) from a button."""
        if not button in self.button_strings:
            return

        button.unbind(on_release=self.button_strings[button])

    def unbind_all_buttons(self):
        """Unbind all actions (strings) from all buttons."""
        for button, string in self.button_strings.items():
            button.unbind(on_release=string)
        self._status = "unbound"

    def show_info(self):
        """Show the detailed task info popup."""
        Logger.debug("CoreTask: Showing info")
        self.info.show()

    def info_show(self, *largs):
        """Handler when the detailed task info popup is opened."""
        if not self.info_built:
            # Render the popup if not done yet
            self.build_info()
        self.info_showing = True

        # Request the task output every second
        Clock.schedule_interval(self.request_output, 1.0)

    def info_dismiss(self, *largs):
        """Handler when the detailed task info popup is closed."""
        Logger.debug("CoreTask: Hiding info")
        self.info_showing = False

        # Stop requesting for output
        Clock.unschedule(self.request_output)

    def request_output(self, *largs):
        """Request the output of the task."""
        self.manyman.comm.request_output(self.tid, len(self._out))

    def stop(self, *largs):
        """Stop the task."""
        Logger.debug("CoreTask: Stopping task %s" % self.tid)
        self.manyman.comm.move_task(self, -1)
        self.unbind_all_buttons()

    def pause(self, *largs):
        """Pause the task."""
        Logger.debug("CoreTask: Pausing task %s" % self.tid)
        self.manyman.comm.pause_task(self.tid)
        self.unbind_all_buttons()

    def resume(self, *largs):
        """Resume the task."""
        Logger.debug("CoreTask: Resuming task %s" % self.tid)
        self.manyman.comm.resume_task(self.tid)
        self.unbind_all_buttons()

    def move(self, *largs):
        """Smart-move the task"""
        Logger.debug("CoreTask: Smart-moving task %s" % self.tid)
        self.manyman.comm.move_task(self)
        self.unbind_all_buttons()

    def set_output(self, output):
        """Append the new output to the previous output."""
        self._out += output

        if self.manyman.settings['output_to_file']:
            # Write output to a file
            if not isdir(self.manyman.settings['output_folder']):
                mkdir(self.manyman.settings['output_folder'])
            f = open(self.outfile, "a")
            f.write("".join(output))
            f.close()

        if not self.info_showing:
            # Do not render output when the info popup is hidden
            return

        # Determine if the output window should scroll down or not
        scroll_down = self.scroll.scroll_y == 0 or \
            self.output.text == NO_OUTPUT_TEXT

        # Show the last lines of the output
        self.output.text = "".join(
            self._out[-self.manyman.settings['output_buffer_size']:]
        )
        if scroll_down:
            self.scroll.scroll_y = 0

    def on_touch_down(self, touch):
        """Handler when a task is touched. Checks for button presses first."""
        x, y = touch.x, touch.y
        if self.info_button.collide_point(x, y):
            self.info_button.color = (.9, .6, 0, 1)
            self.show_info()
            return False

        if not self.status == "Running":
            return False

        if not super(CoreTask, self).on_touch_down(touch):
            return False

        return True

    def on_touch_move(self, touch):
        """Handler when a task is moved."""
        if not self.status == "Running":
            return False

        if not super(CoreTask, self).on_touch_move(touch):
            return False

        self.info_button.color = (.8, .8, .8, 1)

        return True

    def on_touch_up(self, touch):
        """
        Handler when a task is released. Moves the task if released on a core,
        stops it otherwise.
        """
        x, y = touch.x, touch.y
        self.info_button.color = (.8, .8, .8, 1)
        if self.info_button.collide_point(x, y):
            return False

        if not super(CoreTask, self).on_touch_up(touch):
            return False

        if not self.status == "Running":
            return False

        if self.coll_core:
            self.manyman.comm.move_task(self, self.coll_core.index)
            self.coll_core = None
        else:
            self.manyman.comm.move_task(self, -1)

        return True

    def update_title(self):
        """Update the title of the detailed popup."""
        if self.core and not self.status in ["Finished", "Failed"]:
            self.info.title = "%s (%s) - %s on core %d" % \
                (self.name, self.tid, self.status, self.core.index)
        else:
            self.info.title = "%s (%s) - %s" % \
                (self.name, self.tid, self.status)

    def get_core(self):
        """Retrieve the core the task is running on."""
        return self._core

    def set_core(self, value):
        """Set the core the task is running on."""
        self._core = value
        self.update_title()
        if not self.core:
            self.info.dismiss()

    def get_status(self):
        """Getter for the task's status."""
        return self._status

    def set_status(self, value):
        """Setter for the task's status. Binds and unbinds buttons."""
        if self._status == value:
            return

        Logger.debug("CoreTask: Set status to %s" % value)
        self._status = value
        self.label.text = '%s\nStatus: %s' % (self.name, value)
        self.update_title()
        if not self.info_built:
            return

        if value == "Running":
            self.pause_button.image = self.manyman.settings['task_pause_image']
            self.bind_button(self.stop_button, self.stop)
            self.bind_button(self.pause_button, self.pause)
            self.bind_button(self.move_button, self.move)

        elif value == "Stopped":
            self.pause_button.image = \
                self.manyman.settings['task_resume_image']
            self.bind_button(self.pause_button, self.resume)

        elif value == "Finished":
            Clock.unschedule(self.request_output)

    def get_cpu(self):
        """Getter for the current CPU usage."""
        return self._cpu

    def set_cpu(self, value):
        """Setter for the current CPU usage. Updates the performance graphs."""
        self._cpu = value * .01
        self.core.cpu_graph.update_line(self.tid, value)
        self.cpu_graph.update(value)

    def get_mem(self):
        """Getter for the current memory usage."""
        return self._mem

    def set_mem(self, value):
        """Setter for the current mem usage. Updates the performance graphs."""
        self._mem = value * .01
        self.core.mem_graph.update_line(self.tid, value)
        self.mem_graph.update(value)

    def get_outfile(self):
        """Getter for the output file. Generates one when not present."""
        if not self._outfile:
            self._outfile = self.manyman.settings['output_folder'] + "/" + \
                strftime("%Y%m%d-%H%M%S-") + "%s-%s.txt" % \
                (self.name, self.tid)
        return self._outfile

    # Define getters and setters
    core = property(get_core, set_core)
    status = property(get_status, set_status)
    load_cpu = property(get_cpu, set_cpu)
    load_mem = property(get_mem, set_mem)
    outfile = property(get_outfile)
