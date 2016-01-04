# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
#
# This file is part of Rose, a framework for meteorological suites.
#
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

import Queue
import time
import threading

import gobject
import multiprocessing

from rosie.suite_id import SuiteId


class LocalStatusUpdater(threading.Thread):

    """Update the local suites status in the background."""

    def __init__(self, update_hook):
        super(LocalStatusUpdater, self).__init__()
        self.should_quit = False
        self.should_update_now = False
        self.update_hook = update_hook
        self.local_suites = []
        self.queue = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()
        self.update_event = multiprocessing.Event()
        self.getter = LocalStatusGetter(self.queue, self.update_event,
                                        self.stop_event)
        self.start()

    def run(self):
        """This is the main loop."""
        self.getter.start()
        # Main while loop to fetch and distribute suite info.
        while not self.should_quit:
            self.update()
            time.sleep(0.5)
        # Trigger a stop for the getter process.
        self.stop_event.set()

    def update_now(self):
        """Trigger an update."""
        self.update_event.set()

    def update(self):
        """Check for any new communicated info and if so run a hook."""
        try:
            local_suites = self.queue.get_nowait()
        except Queue.Empty:
            return
        self.local_suites = local_suites
        gobject.idle_add(self.update_hook, local_suites)

    def stop(self):
        """This will break out of the while loop in run."""
        self.stop_event.set()
        self.should_quit = True


class LocalStatusGetter(multiprocessing.Process):

    """Process to retrieve the local suite info."""

    def __init__(self, queue, update_event, stop_event):
        super(LocalStatusGetter, self).__init__()
        self.queue = queue
        self.update_event = update_event
        self.stop_event = stop_event
        self.local_suites = []
        self.daemon = True
        self.update()

    def run(self):
        """This is the main loop."""
        try:
            while not self.stop_event.is_set():
                time.sleep(0.5)
                if self.update_event.is_set():
                    self.update()
                    self.update_event.clear()
        except KeyboardInterrupt:
            pass

    def update(self):
        """Get info and communicate any change."""
        local_suites = SuiteId.get_checked_out_suite_ids()
        if local_suites == self.local_suites:
            return
        self.local_suites = local_suites
        self.queue.put(local_suites)
