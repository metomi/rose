#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
#-----------------------------------------------------------------------------
"""Invoke a splash screen from the command line."""

import json
import os
from subprocess import Popen, PIPE
import sys
import tempfile
import threading
import time

import pygtk
pygtk.require("2.0")
import gtk
import gobject

import rose.gtk.util
import rose.popen

gobject.threads_init()


class SplashScreenProcess(object):

    """Run a separate process that launches a splash screen.

    Communicate via the update method.

    """

    def __init__(self, *args):
        args = [str(a) for a in args]
        self.args = args
        self._buffer = []
        self._last_buffer_output_time = time.time()
        self.start()

    def update(self, *args, **kwargs):
        """Communicate via stdin to SplashScreenManager.
        
        args and kwargs are the update method args, kwargs.

        """
        if self.process is None:
            self.start()
        if kwargs.get("no_progress"):
            return self._update_buffered(*args, **kwargs)
        self._flush_buffer()
        json_text = json.dumps({"args": args, "kwargs": kwargs})
        self._communicate(json_text)

    def _communicate(self, json_text):
        while True:
            try:
                self.process.stdin.write(json_text + "\n")
            except IOError as e:
                self.start()
            else:
                break

    def _flush_buffer(self):
        if self._buffer:
            self._communicate(self._buffer[-1])
            del self._buffer[:]

    def _update_buffered(self, *args, **kwargs):
        t1 = time.time()
        json_text = json.dumps({"args": args, "kwargs": kwargs})
        if t1 - self._last_buffer_output_time > 0.02:
            self._communicate(json_text)
            del self._buffer[:]
            self._last_buffer_output_time = t1
        else:
            self._buffer.append(json_text)

    __call__ = update

    def start(self):
        file_name = __file__.rsplit(".", 1)[0] + ".py"
        self.process = Popen([file_name] + list(self.args), stdin=PIPE)

    def stop(self):
        self.process.communicate(input=json.dumps("stop") + "\n")
        self.process = None
  

class SplashScreenUpdaterThread(threading.Thread):

    """Update a splash screen using info from the stdin file object."""

    def __init__(self, splash_screen, stop_event, stdin):
        super(SplashScreenUpdaterThread, self).__init__()
        self.splash_screen = splash_screen
        self.stop_event = stop_event
        self.stdin = stdin

    def run(self):
        """Loop over time and wait for stdin lines."""
        gobject.timeout_add(1000, self._check_splash_screen_alive)
        while not self.stop_event.is_set():
            time.sleep(0.005)
            if self.stop_event.is_set():
                return False
            try:
                stdin_line = self.stdin.readline()
            except IOError:
                continue
            try:
                update_input = json.loads(stdin_line.strip())
            except ValueError as e:
                continue
            if update_input == "stop":
                self._stop()
                continue
            gobject.idle_add(self._update_splash_screen, update_input)

    def _stop(self):
        self.stop_event.set()
        try:
            gtk.main_quit()
        except RuntimeError:
            # This can result from gtk having already quit.
            pass

    def _check_splash_screen_alive(self):
        """Check whether the splash screen is finished."""
        if self.splash_screen.stopped or self.stop_event.is_set():
            self._stop()
            return False
        return True

    def _update_splash_screen(self, update_input):
        """Update the splash screen with info extracted from stdin."""
        self.splash_screen.update(*update_input["args"], **update_input["kwargs"])
        return False

if __name__ == "__main__":
    sys.path.append(os.getenv('ROSE_HOME'))
    splash_screen = rose.gtk.util.SplashScreen(*sys.argv[1:])
    stop_event = threading.Event()
    update_thread = SplashScreenUpdaterThread(splash_screen, stop_event, sys.stdin)
    update_thread.start()
    try:
        gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        update_thread.join()
