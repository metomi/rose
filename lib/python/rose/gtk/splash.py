#!/usr/bin/env python
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
import pango

import rose.gtk.util
import rose.popen

gobject.threads_init()


class SplashScreen(gtk.Window):

    """Run a splash screen that receives update information."""

    BACKGROUND_COLOUR = "white"  # Same as logo background.
    PADDING = 10
    SUB_PADDING = 5
    FONT_DESC = "8"
    PULSE_FRACTION = 0.05
    TIME_WAIT_FINISH = 500  # Milliseconds.
    TIME_IDLE_BEFORE_PULSE = 3000  # Milliseconds.
    TIME_INTERVAL_PULSE = 50  # Milliseconds.

    def __init__(self, logo_path, title, total_number_of_events):
        super(SplashScreen, self).__init__()
        self.set_title(title)
        self.set_decorated(False)
        self.stopped = False
        self.set_icon(rose.gtk.util.get_icon())
        self.modify_bg(gtk.STATE_NORMAL,
                       rose.gtk.util.color_parse(self.BACKGROUND_COLOUR))
        self.set_gravity(gtk.gdk.GRAVITY_CENTER)
        self.set_position(gtk.WIN_POS_CENTER)
        main_vbox = gtk.VBox()
        main_vbox.show()
        image = gtk.image_new_from_file(logo_path)
        image.show()
        image_hbox = gtk.HBox()
        image_hbox.show()
        image_hbox.pack_start(image, expand=False, fill=True)
        main_vbox.pack_start(image_hbox, expand=False, fill=True)
        self._is_progress_bar_pulsing = False
        self._progress_fraction = 0.0
        self.progress_bar = gtk.ProgressBar()
        self.progress_bar.set_pulse_step(self.PULSE_FRACTION)
        self.progress_bar.show()
        self.progress_bar.modify_font(pango.FontDescription(self.FONT_DESC))
        self.progress_bar.set_ellipsize(pango.ELLIPSIZE_END)
        self._progress_message = None
        self.event_count = 0.0
        self.total_number_of_events = float(total_number_of_events)
        progress_hbox = gtk.HBox(spacing=self.SUB_PADDING)
        progress_hbox.show()
        progress_hbox.pack_start(self.progress_bar, expand=True, fill=True,
                                 padding=self.SUB_PADDING)
        main_vbox.pack_start(progress_hbox, expand=False, fill=False,
                             padding=self.PADDING)
        self.add(main_vbox)
        if self.total_number_of_events > 0:
            self.show()
        while gtk.events_pending():
            gtk.main_iteration()

    def update(self, event, no_progress=False, new_total_events=None):
        """Show text corresponding to an event."""
        text = str(event)
        if new_total_events is not None:
            self.total_number_of_events = new_total_events
            self.event_count = 0.0

        if not no_progress:
            self.event_count += 1.0

        if self.total_number_of_events == 0:
            fraction = 1.0
        else:
            fraction = min(
                [1.0, self.event_count / self.total_number_of_events])
        self._stop_pulse()

        if not no_progress:
            gobject.idle_add(self.progress_bar.set_fraction, fraction)
            self._progress_fraction = fraction

        self.progress_bar.set_text(text)
        self._progress_message = text
        gobject.timeout_add(self.TIME_IDLE_BEFORE_PULSE,
                            self._start_pulse, fraction, text)

        if fraction == 1.0 and not no_progress:
            gobject.timeout_add(self.TIME_WAIT_FINISH,
                                lambda: self.finish())

        while gtk.events_pending():
            gtk.main_iteration()

    def _start_pulse(self, idle_fraction, idle_message):
        """Start the progress bar pulsing (moving side-to-side)."""
        if (self._progress_message != idle_message or
                self._progress_fraction != idle_fraction):
            return False
        self._is_progress_bar_pulsing = True
        gobject.timeout_add(self.TIME_INTERVAL_PULSE,
                            self._pulse)
        return False

    def _stop_pulse(self):
        self._is_progress_bar_pulsing = False

    def _pulse(self):
        if self._is_progress_bar_pulsing:
            self.progress_bar.pulse()
        while gtk.events_pending():
            gtk.main_iteration()
        return self._is_progress_bar_pulsing

    def finish(self):
        """Delete the splash screen."""
        self.stopped = True
        gobject.idle_add(self.destroy)
        return False


class NullSplashScreenProcess(object):

    """Implement a null interface similar to SplashScreenProcess."""

    def __init__(self, *args):
        pass

    def update(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass


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
                self.process.stdin.write(json_text + "\n")
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
        if self.process is not None and not self.process.stdin.closed:
            try:
                self.process.communicate(input=json.dumps("stop") + "\n")
            except IOError:
                pass
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
        self.splash_screen.update(
            *update_input["args"], **update_input["kwargs"])
        return False

if __name__ == "__main__":
    sys.path.append(os.getenv('ROSE_HOME'))
    splash_screen = SplashScreen(*sys.argv[1:])
    stop_event = threading.Event()
    update_thread = SplashScreenUpdaterThread(
        splash_screen, stop_event, sys.stdin)
    update_thread.start()
    try:
        gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        update_thread.join()
