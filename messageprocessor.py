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
import json


# List of valid message types.
known_msg_types = (
    'server_init',
    'status',
    'task_output',
    'sim_data',
    'selection_set',
    'invalid_message'
)


class InvalidMessage(Exception):
    """Define the InvalidMessage exception. Only for naming conventions."""
    pass


class MessageProcessor:
    """Processor for all messages that arrive in ManyMan's front-end."""

    def __init__(self, comm):
        self.comm = comm

    def process(self, msg):
        """Process the given message 'msg'."""
        try:
            data = json.loads(msg)
            #print(data)

            if not data['type'] in known_msg_types:
                raise InvalidMessage('Unknown message type: %s' % data['type'])
            elif not self.comm.initialized and data['type'] != 'server_init':
                raise InvalidMessage(
                    'Did not receive initialization message first.'
                )
            elif self.comm.manyman.started or not self.comm.initialized:
                getattr(self, "process_" + data['type'])(data['content'])
        except Exception, e:
            import traceback
            Logger.error(
                'MsgProcessor: Received invalid message:\n - %s\n - %s\n' \
                ' - %s\n - %s' % (e, type(e), msg, traceback.format_exc())
            )

    # EDITED!
    def process_server_init(self, msg):
        """Process the server_init message."""
        self.comm.manyman.chip_name = msg['name']
        self.comm.manyman.chip_cores = msg['cores']
        self.comm.manyman.sample_vars = msg['sample_vars']
        self.comm.manyman.current_vars = msg['default_vars']
        if 'orientation' in msg:
            self.comm.manyman.chip_orientation = msg['orientation']

        Logger.info("MsgProcessor: Initialized %s, a %d-core chip" %
            (msg['name'], msg['cores']))

        self.comm.initialized = True

    def process_status(self, msg):
        """Process a status message."""
        mm = self.comm.manyman
        total_load = 0

        # Update the loads of the cores
        for i in mm.cores.keys():
            core = mm.cores[i]
            load = msg['chip']['Cores'][i]['CPU'] / 100.0
            core.update_load(load)
            total_load += load
            mem = msg['chip']['Cores'][i]['MEM'] / 100.0
            core.update_mem(mem)
            core.frequency = msg['chip']['Cores'][i]['Frequency']
            core.voltage = msg['chip']['Cores'][i]['Voltage']

        task_ids = []
        new_count = dict()

        # Update all task information
        for task in msg['chip']['Tasks']:
            if mm.has_task(task['ID']):
                t = mm.tasks[task['ID']]
                if task["Status"] in ["Finished", "Failed"] and \
                    not t.status in ["Finished", "Failed"]:
                    mm.finish_task(task['ID'], task['Status'])
                elif not task['Status'] in ["Finished", "Failed"] and \
                    ((not t.core and task['Core'] >= 0) or \
                    (t.core and t.core.index != task['Core'])):
                    if task['Core'] < 0:
                        mm.move_task(t)
                    else:
                        mm.move_task(t, mm.cores[task['Core']])
            else:
                t = mm.add_task(
                    task['ID'],
                    task['Name'],
                    task['Core'],
                    task['Status']
                )

            # Count the number of tasks per core
            if not task['Status'] in ["Finished", "Failed", "Stopped"]:
                if task['Core'] in new_count:
                    new_count[task['Core']] += 1
                else:
                    new_count[task['Core']] = 1

            if t:
                task_ids.append(task['ID'])
                t.status = task['Status']
                if t.core:
                    t.load_cpu = task['CPU']
                    t.load_mem = task['MEM']

        # Update the number of running tasks per core
        for core in range(len(mm.cores)):
            count = 0
            if core in new_count:
                count = new_count[core]
            mm.cores[core].pending_count = count

        # Remove all stopped tasks from the system
        for task in filter(lambda x: x not in task_ids, mm.tasks):
            Logger.debug("MsgProcessor: %s no longer running" % task)
            mm.remove_task(task)

        # Calculate the total load
        total_load /= len(mm.cores)
        Logger.debug("MsgProcessor: Total load: %.1f%%" % (total_load * 100.))
        mm.cpu_load = total_load
        mm.cpu_power = msg['chip']['Power']

    def process_task_output(self, msg):
        """Process a task_output message."""
        if not self.comm.manyman.has_task(msg['id']):
            return

        t = self.comm.manyman.tasks[msg['id']]
        t.set_output(msg['output'])

    def process_sim_data(self, msg):
        mm = self.comm.manyman
        #mm.components_list['cpu0'].update_load(0.5)
        mm.previous_kernel_cycle = mm.current_kernel_cycle
        mm.current_kernel_cycle = msg['data']['kernel.cycle']
        delay = msg['status']['delay']
        status = msg['status']['sim']
        step = msg['status']['step']

        if status == 0:
            mm.status_label.text = "simulator status\n\npaused"
        else:
            mm.status_label.text = "simulator status\n\nrunning"
        mm.kernel_label.text = "kernel cycle\n\n" + str(mm.current_kernel_cycle)
        mm.delay_label.text = "current send delay\n\n" + str(delay)
        mm.step_label.text = "current steps\n\n" + str(step)

        for k, v in msg['data'].items():
            #print k
            components = k.split(':')
            if components[0] in mm.components_list:
                if len(components) < 2:
                    mm.components_list[components[0]].update_data(components[0], v)
                elif len(components) > 2:
                    mm.components_list[components[0]].update_data(':'.join(components[1:]), v)
                else:
                    mm.components_list[components[0]].update_data(components[1], v)
                #print components[0], mm.components_list[components[0]].get_data(components[0])
                #if v != 0:
                #    mm.components_list[components[0]].update_load(0.5)
                #print components[0] + ': ' + str(v)

    def process_selection_set(self, msg):
        mm = self.comm.manyman

        mm.sample_vars = msg['sample_vars']
        mm.current_vars = mm.current_vars2

        mm.layout.remove_widget(mm.rightbar)
        mm.layout.remove_widget(mm.core_grid)

        mm.init_core_grid()
        mm.layout.add_widget(mm.rightbar)

        mm.comm.selection_send()


    def process_invalid_message(self, msg):
        """Process an invalid_message message."""
        Logger.warning(
            "MsgProcessor: Sent an invalid message to the server:\n %s" % \
            msg['message']
        )
