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

from messageprocessor import MessageProcessor
from kivy.logger import Logger
from threading import Thread
import json
import socket


class Communicator(Thread):
    """Communicator between ManyMan's front- and back-end."""

    def __init__(self, manyman):
        self.manyman = manyman

        self.sock = None
        self.running = True
        self.initialized = False
        self.readbuf = ""

        self.init_processor()
        self.init_connection()

        Thread.__init__(self)

    def init_processor(self):
        """Initialize the messageprocessor."""
        self.processor = MessageProcessor(self)

    def init_connection(self):
        """
        Initialize the connection to the back-end and send the initialization
        message.
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(tuple(self.manyman.settings['address']))
            Logger.info("Communicator: Connected to the server")

            self.send_msg({
                'type': 'client_init',
                'content': {
                    'name': 'PQ Labs Q3'
                }
            })
        except Exception as e:
            Logger.critical(
                "Communicator: Could not connect to the server: %s" % e
            )
            raise e

    def run(self):
        """Continuously check for messages."""
        try:
            while self.running:
                data = self.sock.recv(self.manyman.settings['bufsize'])

                if not data:
                    self.running = False
                    break

                if '\n' in data:
                    # Data is not complete until a newline character has been
                    # received
                    parts = data.split('\n')
                    self.processor.process("%s%s" % (self.readbuf, parts[0]))

                    # Process any adjacent fully received messages
                    for part in parts[1:-1]:
                        self.processor.process(part)

                    self.readbuf = parts[-1]
                else:
                    self.readbuf += data
        except:
            self.running = False
            self.sock.close()

    def send_msg(self, msg):
        """Send a given message to the back-end."""
        Logger.debug("Communicator: Sending: %s" % json.dumps(msg))
        self.sock.send("%s\n" % json.dumps(msg))

    def start_task(self, name, task, core=None):
        """Send a start_task message."""
        msg = {
            'type': 'task_start',
            'content': {
                'name': name,
                'program': task
            }
        }
        if core != None:
            msg['content']['core'] = core
        self.send_msg(msg)

    def move_task(self, task, dest=None):
        """Send a task_move message."""
        msg = {
            'type': 'task_move',
            'content': {
                'id': task.tid
            }
        }
        if dest != None:
            msg['content']['to_core'] = dest
        self.send_msg(msg)

    def pause_task(self, task):
        """Send a task_pause message."""
        self.send_msg({
            'type': 'task_pause',
            'content': {
                'id': task
            }
        })

    def resume_task(self, task, core=None):
        """Send a task_resume message."""
        msg = {
            'type': 'task_resume',
            'content': {
                'id': task
            }
        }
        if core != None:
            msg['content']['core'] = core
        self.send_msg(msg)

    def stop_task(self, task):
        """Send a task_stop message."""
        self.send_msg({
            'type': 'task_stop',
            'content': {
                'id': task
            }
        })

    def duplicate_task(self, task):
        """Send a task_duplicate message."""
        self.send_msg({
            'type': 'task_duplicate',
            'content': {
                'id': task
            }
        })

    def request_output(self, task, offset=0):
        """Send a task_output_request message with given offset."""
        msg = {
            'type': 'task_output_request',
            'content': {
                'id': task
            }
        }
        if offset > 0:
            msg['content']['offset'] = offset
        self.send_msg(msg)

    def set_core_frequency(self, freq, core=None):
        """Send a core_set_frequency message with given frequency."""
        msg = {
            'type': 'core_set_frequency',
            'content': {
                'frequency': freq
            }
        }
        if core != None:
            msg['content']['id'] = core
        self.send_msg(msg)

    # EDITED!
    def selection_new(self, var):
        msg = {
            'type': 'selection_new',
            'content': {
                'sample_vars': var
            }
        }
        self.send_msg(msg)

    def selection_send(self):
        msg = {
            'type': 'selection_send',
            'content': {
            }
        }
        self.send_msg(msg)

    def resume_sim(self):
        msg = {
            'type': 'resume_sim',
            'content': {
            }
        }
        self.send_msg(msg)

    def pause_sim(self):
        msg = {
            'type': 'pause_sim',
            'content': {
            }
        }
        self.send_msg(msg)

    def set_step(self, step):
        msg = {
            'type': 'set_step',
            'content': {
                'step': step
            }
        }
        self.send_msg(msg)

    def change_delay(self, delay):
        msg = {
            'type': 'change_delay',
            'content': {
                'delay': delay
            }
        }
        self.send_msg(msg)