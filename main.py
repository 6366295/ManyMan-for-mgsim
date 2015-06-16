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

from communicator import Communicator
from component import Component
from valueslider import ValueSlider
from infopopup import InfoPopup
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.logger import Logger, LOG_LEVELS
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import WidgetException
from os import _exit as exit
from os.path import exists
from perfgraph import PerfGraph
from task import CoreTask, PendingTask
from time import sleep
from util import is_prime
from widgets import MyTextInput, MyVKeyboard
from kivy.uix.textinput import TextInput
from dotdictify import dotdictify
import config
import kivy
import sys
import task
import math
import json

default_settings = {
    'kivy_version': '1.2.0',
    'keyboards_folder': 'keyboards',
    'logging_level': 'info',
    'address': ['sccsa.science.uva.nl', 11111],
    'framerate': 60.,
    'bufsize': 1024,
    'core_background': 'img/core.png',
    'core_background_active': 'img/core_active.png',
    'core_border': [14, 14, 14, 14],
    'core_padding': 9,
    'core_color_range': [.35, 0.],
    'task_default_color': .7,
    'task_info_image': 'atlas://img/atlas/info',
    'task_dup_image': 'atlas://img/atlas/duplicate',
    'task_start_image': 'atlas://img/atlas/play',
    'task_stop_image': 'atlas://img/atlas/stop_button',
    'task_pause_image': 'atlas://img/atlas/pause_button',
    'task_resume_image': 'atlas://img/atlas/play_button',
    'task_move_image': 'atlas://img/atlas/move_button',
    'logo_image': 'img/uva-logo.jpg',
    'help_image': 'img/help.png',
    'about_image': 'img/about.png',
    'license_image': 'img/license.png',
    'output_buffer_size': 100,
    'output_to_file': True,
    'output_folder': 'output',
    'perfgraph_default_history': '50',
    'voltage_islands': [
        [0, 1, 2, 3, 12, 13, 14, 15],
        [4, 5, 6, 7, 16, 17, 18, 19],
        [8, 9, 10, 11, 20, 21, 22, 23],
        [24, 25, 26, 27, 36, 37, 38, 39],
        [28, 29, 30, 31, 40, 41, 42, 43],
        [32, 33, 34, 35, 44, 45, 46, 47]
    ]
}


class ManyMan(App):
    """
    Application window. Contains all visualization and sets up the entire
    front-end system.
    """

    def __init__(self, **kwargs):
        self.settings_file = 'settings.cfg'
        if len(sys.argv) > 1:
            self.settings_file = sys.argv[1]

        self.settings = default_settings.copy()
        self.comm = None
        self.cores = dict()
        self.tasks = dict()
        self.pending_tasks = dict()
        self.pending_count = 0
        self.finished_tasks = dict()
        self.chip_name = ""
        self.chip_cores = ""
        self.chip_orientation = None
        self.started = False

        # EDITED
        self.selections_file = 'selections.txt'
        self.core_grid = None
        self.sample_vars = []
        self.current_vars = []
        self.current_vars2 = []
        self.components = dict()
        self.l1_components_grid_list = dict()
        self.components_list = dict()
        self.vars_input = None
        self.change_selection = None
        self.saved_selection_list = None
        self.current_kernel_cycle = 0
        self.previous_kernel_cycle = 0

        self.status_label = None
        self.kernel_label = None
        self.delay_label = None
        self.step_label = None

        self.save_selection_popup = None
        self.save_selection_name = None
        self.save_selection_dict = dict()

        self.delay_input = None
        self.change_delay_popup = None

        self.step_input = None
        self.set_step_popup = None

        self.layout = None
        self.sidebar = None
        self.leftbar = None
        self.rightbar = None
        self.task_list = None
        self.finished_list = None
        self.task_create = None
        self.name_input = None
        self.command_input = None
        self.cpu_graph = None
        self.power_graph = None
        self.help_window = None
        self.frequencies_window = None
        self.frequency_labels = []
        self.frequency_sliders = []

        self.load_settings()
        self.load_selections()
        self.config_kivy()
        self.config_logger()
        self.init_communicator()

        super(ManyMan, self).__init__(**kwargs)

    def load_settings(self):
        """Load settings from settings file."""
        try:
            self.settings.update(config.Config(file(self.settings_file)))
        except Exception, err:
            print 'Settings could not be loaded: %s' % err
            exit(1)

    # EDITED!
    def load_selections(self):
        """Load selection from selection file."""
        try:
            file_object = open(self.selections_file, 'r')
            self.save_selection_dict = json.loads(file_object.read())
            file_object.close()
        except Exception, err:
            print 'Selection could not be loaded: %s' % err
            exit(1)

    def config_kivy(self):
        """Configure kivy."""
        kivy.require(self.settings['kivy_version'])
        if not exists(self.settings['keyboards_folder']):
            raise WidgetException(
                "Keyboards folder (%s) could not be found." % \
                self.settings['keyboards_folder']
            )
        if Config.get('kivy', 'keyboard_mode') != 'multi' or \
            Config.get('kivy', 'keyboard_layout') != 'qwerty':
            Config.set('kivy', 'keyboard_mode', 'multi')
            Config.set('kivy', 'keyboard_layout', 'qwerty')
            Config.write()
            raise WidgetException(
                "Keyboard mode was not set properly. Need to restart."
            )

    def config_logger(self):
        """Configure the kivy logger."""
        Logger.setLevel(LOG_LEVELS[self.settings['logging_level']])

    def init_communicator(self):
        """Initialize the communicator."""
        try:
            self.comm = Communicator(self)
            self.comm.start()
            while not self.comm.initialized:
                sleep(.1)
        except:
            if self.comm:
                self.comm.running = False
                self.comm.join()
            exit(0)

    def build_config(self, *largs):
        """Copy the settings to the Kivy Config module."""
        Config.setdefaults('settings', self.settings)

    def build(self):
        """Build the main window."""
        Clock.max_iteration = 100
        self.layout = BoxLayout()
        return self.layout

    def on_start(self):
        """Handler when the tool is started."""
        self.set_vkeyboard()
        self.init_leftbar()
        self.init_core_grid()
        self.init_rightbar()
        self.init_new_selection()
        self.init_change_delay()
        self.init_set_step()
        self.init_save_selection_popup()
        self.started = True

    def on_stop(self):
        """Handler when the tool is stopped."""
        #self.comm.sock.shutdown(0)
        self.comm.sock.close()
        self.comm.running = False
        self.comm.join()

    def set_vkeyboard(self):
        """Setup the virtual keyboard."""
        win = self.layout.get_root_window()
        if not win:
            raise WidgetException("Could not access the root window")

        win.set_vkeyboard_class(MyVKeyboard)

    def init_leftbar(self):
        """Initialize the left sidebar."""
        self.leftbar = BoxLayout(
            orientation='vertical',
            padding=5,
            spacing=10,
            size_hint_x=None,
            width=300
        )
        self.init_chip_info()
        self.init_left_controls()

        #EDITED!
        self.init_saved_selection()
        self.init_save_current_selection()

        self.layout.add_widget(self.leftbar)

    # EDITED
    def layout_cols(self, ncomponents):
        """Determine how many colums a GridLayout gets."""
        elems = ncomponents

        if is_prime(elems) and elems > 2:
            elems += 1

        rows = 1
        cols = elems

        for i in xrange(1, elems):
            if elems % i == 0 and rows < cols:
                rows = i
                cols = elems / i

        return cols

    # EDITED
    def layout_components(self, vars):
        """Create layout of components from selected vars."""
        components_dict = dotdictify()

        for i in sorted(vars):
            components = i.split(":")
            if components[0] in components_dict:
                continue

            components_dict[components[0]] = None

        return components_dict

    # EDITED
    def layout_traverse(self, d, s=""):
        temp = dict()
        for k, v in sorted(d.iteritems()):
            if isinstance(v, dict):
                rlayout = self.layout_traverse(v, s+k+'.')
                c = Component(s+k, self, size_hint=(1,0.5))
                self.components_list[s+k] = c
                temp_layout = BoxLayout(orientation='vertical')
                temp_layout.add_widget(c)
                temp_layout.add_widget(rlayout)
                temp[k] = temp_layout
                #print k, s+k

                # Clock.schedule_interval(
                #     c.update,
                #     1.0 / self.settings['framerate']
                # )
            else:
                c = Component(s+k, self)
                self.components_list[s+k] = c
                temp[k] = c
                #print k, s+k
                # Clock.schedule_interval(
                #     c.update,
                #     1.0 / self.settings['framerate']
                # )

        cols = self.layout_cols(len(d))

        layout = GridLayout(cols=cols, spacing=0)

        for k, v in sorted(temp.iteritems()):
            #print s+":"+k
            layout.add_widget(v)
        return layout

    # EDITED
    def init_core_grid(self):
        """Initialize the core grid on the left side of the window."""

        # Create components structure in a dictionary
        components_dict = self.layout_components(self.sample_vars)

        cols = self.layout_cols(len(components_dict))
        self.core_grid = GridLayout(cols=cols, spacing=10)

        for component1 in sorted(components_dict):
            layout = BoxLayout(orientation='vertical')
            c = Component(component1, self, size_hint=(1,0.2))
            self.components_list[component1] = c
            layout.add_widget(c)
            if components_dict[component1] != None:
                layout.add_widget(self.layout_traverse(components_dict[component1], component1+'.'))
            self.l1_components_grid_list[component1] = layout
            self.core_grid.add_widget(layout)
            # Clock.schedule_interval(
            #     c.update,
            #     1.0 / self.settings['framerate']
            # )

        #popup buttons
        for k in self.sample_vars:
            components = k.split(':')
            if components[0] in self.components_list:
                if len(components) < 2:
                    self.components_list[components[0]].set_data(components[0])
                elif len(components) > 2:
                    self.components_list[components[0]].set_data(':'.join(components[1:]))
                else:
                    self.components_list[components[0]].set_data(components[1])

        self.layout.add_widget(self.core_grid)
        

    def init_rightbar(self):
        """Initialize the right sidebar."""
        self.rightbar = BoxLayout(
            orientation='vertical',
            padding=5,
            spacing=10,
            size_hint_x=None,
            width=300
        )
        self.init_program_info()
        self.init_right_controls()

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=False)

        self.finished_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.finished_list.bind(
            minimum_height=self.finished_list.setter('height')
        )

        #scroll.add_widget(self.finished_list)
        self.rightbar.add_widget(self.finished_list)
        self.rightbar.add_widget(scroll)

        b = Button(
            text='Resume',
            size_hint_y=None,
            height=40
        )
        b.bind(on_press=self.resume_sim)
        self.finished_list.add_widget(b)

        b = Button(
            text='Pause',
            size_hint_y=None,
            height=40
        )
        b.bind(on_press=self.pause_sim)
        self.finished_list.add_widget(b)

        b = Button(
            text='Change Send Delay',
            size_hint_y=None,
            height=40
        )
        b.bind(on_press=self.change_delay_open)
        self.finished_list.add_widget(b)

        b = Button(
            text='Set Steps',
            size_hint_y=None,
            height=40
        )
        b.bind(on_press=self.set_step_open)
        self.finished_list.add_widget(b)

        self.status_label = Label(text="simulator status\n\npauzed", halign='center', valign='top', text_size=(200,None))
        self.kernel_label = Label(text="kernel cycle\n\n0000", halign='center', valign='top', text_size=(200,None))
        self.delay_label = Label(text="current send delay\n\n0000", halign='center', valign='top', text_size=(200,None))
        self.step_label = Label(text="current steps\n\n0000", halign='center', valign='top', text_size=(200,None))

        self.rightbar.add_widget(self.status_label)
        self.rightbar.add_widget(self.kernel_label)
        self.rightbar.add_widget(self.delay_label)
        self.rightbar.add_widget(self.step_label)

        self.layout.add_widget(self.rightbar)

    def pause_sim(self, *largs):
        self.comm.pause_sim()

    def resume_sim(self, *largs):
        self.comm.resume_sim()

    def change_delay(self, delay):
        try:
            delay = float(delay)
            self.comm.change_delay(delay)
        except ValueError:
            print "Not a float"

    def change_delay_open(self, *largs):
        """Handler when the 'Add task' button is pressed."""
        self.change_delay_popup.open()

    def init_change_delay(self):
        """Initialize the 'Change Selection' popup."""
        self.change_delay_popup = Popup(
            title="Change delay",
            size_hint=(None, None),
            size=(600, 160)
        )

        content = GridLayout(cols=1, spacing=20)

        inputs = FloatLayout(orientation='horizontal')
        inputs.add_widget(
            Label(
                text='Delay:\n(0.1-10.0)',
                text_size=(150, None),
                padding_x=5,
                size_hint=(.25, None),
                height=40,
                pos_hint={'x': 0, 'y': 0}
            )
        )
        self.delay_input = TextInput(
            multiline=False,
            size_hint=(.75, None),
            height=40,
            pos_hint={'x': .25, 'y': 0}
        )
        inputs.add_widget(self.delay_input)
        content.add_widget(inputs)

        submit = Button(text='Send Delay', size_hint=(1, None), height=30)
        submit.bind(on_press=self.process_change_delay)
        content.add_widget(submit)
        self.change_delay_popup.content = content

    def set_step(self, steps):
        try:
            steps = int(steps)
            self.comm.set_step(steps)
        except ValueError:
            print "Not a int"

    def set_step_open(self, *largs):
        """Handler when the 'Add task' button is pressed."""
        self.set_step_popup.open()

    def init_set_step(self):
        """Initialize the 'Change Selection' popup."""
        self.set_step_popup = Popup(
            title="Set simulation steps (Set to 0, for running until the end)",
            size_hint=(None, None),
            size=(600, 160)
        )

        content = GridLayout(cols=1, spacing=20)

        inputs = FloatLayout(orientation='horizontal')
        inputs.add_widget(
            Label(
                text='Steps:',
                text_size=(150, None),
                padding_x=5,
                size_hint=(.25, None),
                height=40,
                pos_hint={'x': 0, 'y': 0}
            )
        )
        self.step_input = TextInput(
            multiline=False,
            size_hint=(.75, None),
            height=40,
            pos_hint={'x': .25, 'y': 0}
        )
        inputs.add_widget(self.step_input)
        content.add_widget(inputs)

        submit = Button(text='Send Steps', size_hint=(1, None), height=30)
        submit.bind(on_press=self.process_set_step)
        content.add_widget(submit)
        self.set_step_popup.content = content

    def process_change_delay(self, *largs):
        if self.delay_input.text:
            self.change_delay(self.delay_input.text)
        self.change_delay_popup.dismiss()
        self.delay_input.text = ''

    def process_set_step(self, *largs):
        if self.step_input.text:
            self.set_step(self.step_input.text)
        self.set_step_popup.dismiss()
        self.step_input.text = ''

    def init_chip_info(self):
        """Initialize the chip information text on the left top corner."""
        chip_info = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=60
        )

        chip_info.add_widget(Label(text=self.chip_name, font_size=(20)))
        chip_info.add_widget(Label(
            text=("%d-core chip" % self.chip_cores),
            size_hint=(1, .3)
        ))

        self.leftbar.add_widget(chip_info)

    def init_left_controls(self):
        """Initialize the control buttons below the chip info."""
        controls = GridLayout(
            cols=1,
            spacing=5,
            size_hint_y=None,
            height=40
        )

        # EDITED! TEMP task_button2
        selection_button = Button(text='New Selection')
        selection_button.bind(on_press=self.new_selection)
        controls.add_widget(selection_button)

        self.leftbar.add_widget(controls)

    #EDITED!
    def init_saved_selection(self):
        label = Label(
            text="Saved Selections:",
            size_hint_y=None,
            height=20
        )
        self.leftbar.add_widget(label)

        scroll = ScrollView(do_scroll_x=False)

        self.saved_selection_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.saved_selection_list.bind(minimum_height=self.saved_selection_list.setter('height'))

        scroll.add_widget(self.saved_selection_list)
        self.leftbar.add_widget(scroll)

    def init_save_current_selection(self):
        button_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=50
        )

        button = Button(text='Save Selection')
        button.bind(on_press=self.save_selection)

        button_container.add_widget(button)
        self.leftbar.add_widget(button_container)

    def init_program_info(self):
        """Initialize the program information text on the right top corner."""
        logo = FloatLayout(size_hint=(None, None), size=(290, 60))
        logo.add_widget(
            Image(
                source=self.settings['logo_image'],
                size_hint=(60. / 290., 1),
                pos_hint={'x': .8, 'y': 0}
            )
        )
        self.rightbar.add_widget(logo)

        program_info = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )

        program_info.add_widget(Label(text="ManyMan", font_size=(20)))
        program_info.add_widget(Label(
            text="Many-core Manager",
            size_hint=(1, .3)
        ))

        logo.add_widget(program_info)

    def init_right_controls(self):
        """Initialize the control buttons below the program info."""
        controls = GridLayout(
            cols=2,
            spacing=5,
            size_hint_y=None,
            height=40
        )

        help_button = Button(text='Help')
        help_button.bind(on_press=self.show_help)
        controls.add_widget(help_button)

        exit_button = Button(text='Exit')
        exit_button.bind(on_press=self.stop)
        controls.add_widget(exit_button)

        self.rightbar.add_widget(controls)

    #EDITED!
    def init_new_selection(self):
        """Initialize the 'Change Selection' popup."""
        self.change_selection = Popup(
            title="New Selection",
            size_hint=(None, None),
            size=(600, 230)
        )

        content = GridLayout(cols=1, spacing=20)

        inputs = FloatLayout(orientation='horizontal')
        inputs.add_widget(
            Label(
                text='Vars:',
                text_size=(150, None),
                padding_x=5,
                size_hint=(.25, None),
                height=100,
                pos_hint={'x': 0, 'y': 0}
            )
        )
        self.vars_input = TextInput(
            multiline=True,
            size_hint=(.75, None),
            height=100,
            pos_hint={'x': .25, 'y': 0}
        )
        inputs.add_widget(self.vars_input)
        content.add_widget(inputs)


        submit = Button(text='Send Selection', size_hint=(1, None), height=30)
        submit.bind(on_press=self.process_new_selection)
        content.add_widget(submit)
        self.change_selection.content = content

    #EDITED!
    def init_save_selection_popup(self):
        """Initialize the 'Add task' popup."""
        self.save_selection_popup = Popup(
            title="Save selection",
            size_hint=(None, None),
            size=(600, 150)
        )

        content = GridLayout(cols=1, spacing=20)

        inputs = FloatLayout(orientation='horizontal')
        inputs.add_widget(
            Label(
                text='Name (required):',
                text_size=(150, None),
                padding_x=5,
                size_hint=(.25, None),
                height=30,
                pos_hint={'x': 0, 'y': 0}
            )
        )
        self.save_selection_name = TextInput(
            multiline=False,
            size_hint=(.75, None),
            height=30,
            pos_hint={'x': .25, 'y': 0}
        )
        inputs.add_widget(self.save_selection_name)
        content.add_widget(inputs)

        submit = Button(text='Save', size_hint=(1, None), height=30)
        submit.bind(on_press=self.process_save_selection)
        content.add_widget(submit)
        self.save_selection_popup.content = content

        for k, v in self.save_selection_dict.items():
            button = Button(text=k, size_hint=(None, None), size=(290, 30), background_color=(0,0,1,1))
            button.bind(on_press=self.selection_new2)
            self.saved_selection_list.add_widget(button)

    # EDITED! TEMP
    def new_selection(self, *largs):
        """Handler when the 'Add task' button is pressed."""
        self.change_selection.open()

    #EDITED!
    def save_selection(self, *largs):
        """Handler when the 'Add task' button is pressed."""
        self.save_selection_popup.open()

    #EDITED!
    def process_new_selection(self, *largs):
        """
        Handler when the 'Create task' button in the 'Add task' popup is
        pressed.
        """
        if self.vars_input.text:
            self.selection_new(self.vars_input.text)
        self.change_selection.dismiss()
        self.vars_input.text = ''

    #EDITED!
    def process_save_selection(self, *largs):
        """
        Handler when the 'Create task' button in the 'Add task' popup is
        pressed.
        """
        if self.save_selection_name.text:
            if self.save_selection_name.text in self.save_selection_dict:
                print 'already exists'
            else:
                button = Button(text=self.save_selection_name.text, size_hint=(None, None), size=(290, 30), background_color=(0,0,1,1))
                button.bind(on_press=self.selection_new2)
                self.saved_selection_list.add_widget(button)

                self.save_selection_dict[button.text] = self.current_vars
        self.save_selection_popup.dismiss()
        self.save_selection_name.text = ''

    #EDITED!
    def selection_new(self, new_vars):
        new_vars = new_vars.split('\n')
        self.current_vars2 = new_vars
        self.comm.selection_new(new_vars)

    #EDITED!
    def selection_new2(self, *largs):
        new_vars = self.save_selection_dict[largs[0].text]
        if set(new_vars) == set(self.current_vars):
            print "same selection"
        else:
            self.current_vars2 = new_vars
            self.comm.selection_new(new_vars)

    def show_help(self, *largs):
        """Show the help popup."""
        if not self.help_window:
            # Build the help window when this has not been done yet.
            self.help_window = Popup(
                title="Help",
                size_hint=(None, None),
                size=(600, 600)
            )

            acc = Accordion()
            self.help_window.content = acc

            item = AccordionItem(title='Help')
            item.add_widget(Image(source=self.settings['help_image']))
            acc.add_widget(item)

            item2 = AccordionItem(title='About')
            item2.add_widget(Image(source=self.settings['about_image']))
            acc.add_widget(item2)

            item3 = AccordionItem(title='License')
            item3.add_widget(Image(source=self.settings['license_image']))
            acc.add_widget(item3)

        self.help_window.open()

    def show_frequencies(self, *largs):
        """Show the frequencies popup."""
        if not self.frequencies_window:
            # Build the help window when this has not been done yet.
            self.frequencies_window = InfoPopup(
                title="Tile frequencies",
                size_hint=(None, None),
                size=(600, 450)
            )

            b = BoxLayout(orientation='vertical')
            self.frequencies_window.content = b

            for i in xrange(len(self.settings['voltage_islands'])):
                r = BoxLayout(size_hint_y=None, height=50)
                l = Label(
                    text='Power domain %d:\nFrequency: %dMHz' % (i, 533),
                    size_hint_x=None,
                    width=150
                )
                self.frequency_labels += [l] 
                r.add_widget(l)
                
                vs = ValueSlider(
                    min=100,
                    max=800,
                    value=533,
                    values=[800, 533, 400, 320, 267, 200, 100],
                    data=i
                )
                vs.val = 533
                vs.bind(on_change=self.frequency_changed)
                vs.bind(on_release=self.frequency_set)
                self.frequency_sliders += [vs]
                r.add_widget(vs)
                b.add_widget(r)

            r = BoxLayout(size_hint_y=None, height=50)
            l = Label(
                text='All power domains:\nFrequency: %dMHz' % (533),
                size_hint_x=None,
                width=150
            )
            self.frequency_labels += [l] 
            r.add_widget(l)
            
            vs = ValueSlider(
                min=100,
                max=800,
                value=533,
                values=[800, 533, 400, 320, 267, 200, 100]
            )
            vs.val = 533
            vs.bind(on_change=self.frequency_changed)
            vs.bind(on_release=self.frequency_set)
            self.frequency_sliders += [vs]
            r.add_widget(vs)
            b.add_widget(r)

        self.frequencies_window.show()

    def frequency_changed(self, ins):
        Logger.debug("ManyMan: slider %s changed" % ins.data)
        if ins.data != None:
            l = self.frequency_labels[ins.data]
            l.text = 'Power domain %d:\nFrequency: %dMHz' % (ins.data, ins.val)
        else:
            l = self.frequency_labels[len(self.settings['voltage_islands'])]
            l.text = 'All power domains:\nFrequency: %dMHz' % (ins.val)
            for i in xrange(len(self.settings['voltage_islands'])):
                s = self.frequency_sliders[i]
                s.val = ins.val

    def frequency_set(self, ins):
        Logger.debug("ManyMan: slider %s set" % ins.data)
        if ins.data != None:
            self.comm.set_core_frequency(
                ins.val,
                self.settings['voltage_islands'][ins.data][0]
            )
        else:
            Logger.info("ManyMan: ssaasdsslider %s set" % ins.data)
            self.comm.set_core_frequency(ins.val)

    def get_cpu_load(self):
        """Getter for the current CPU load. MAY NOT BE CALLED."""
        raise Exception("Can not access the current CPU load.")

    def set_cpu_load(self, value):
        """Setter for the current CPU load. Updates the performance graph."""
        self.cpu_graph.update(value * 100)

    def get_cpu_power(self):
        """Getter for the current CPU power. MAY NOT BE CALLED."""
        raise Exception("Can not access the current CPU power.")

    def set_cpu_power(self, value):
        """Setter for the current CPU power. Updates the performance graph."""
        self.power_graph.update(value)

    # Define getters and setters.
    cpu_load = property(get_cpu_load, set_cpu_load)
    cpu_power = property(get_cpu_power, set_cpu_power)


if __name__ in ('__android__', '__main__'):
    # Run the program.
    manyman = ManyMan()
    try:
        manyman.run()
    except Exception, e:
        Logger.critical("Main: %s" % e)
    finally:
        file_object = open('selections.txt', 'w')
        file_object.write(json.dumps(manyman.save_selection_dict))
        file_object.close()
        exit(0)
