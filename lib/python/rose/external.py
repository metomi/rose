# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
#-----------------------------------------------------------------------------
"""This module contains functions to interface with external programs."""

from rose.popen import RosePopener


def _launch(name, event_handler=None, run_fg=False, *args, **kwargs):
    popen = RosePopener(event_handler)
    command = popen.get_cmd(name, *args)
    if run_fg:
        return popen.run(*command, **kwargs)
    popen.run_bg(*command, **kwargs)


def launch_fs_browser(source, event_handler=None, **kwargs):
    """Launch a graphical filesystem browser e.g. nautilus."""
    _launch("fs_browser", event_handler, source, **kwargs)


def launch_geditor(source, event_handler=None, **kwargs):
    """Launch a graphical text editor for a path e.g. gedit."""
    _launch("geditor", event_handler, source, **kwargs)


def launch_image_viewer(source, event_handler=None, run_fg=False,
                        **kwargs):
    """Launch an image viewer for a image file e.g. gimp."""
    _launch("image_viewer", event_handler, run_fg, source, **kwargs)


def launch_terminal(args=None, event_handler=None, **kwargs):
    """Launch a terminal e.g. gnome-terminal."""
    if args is None:
        args = []
    _launch("terminal", event_handler, *args, **kwargs)
