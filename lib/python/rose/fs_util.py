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
"""File system utilities with event reporting."""

import errno
import os
from rose.reporter import Event
import shutil
import sys

class FileSystemEvent(Event):

    """An event raised on a file system operation."""

    CHDIR = "chdir"
    CREATE = "create"
    DELETE = "delete"
    INSTALL = "install"
    RENAME = "rename"
    SYMLINK = "symlink"
    TOUCH = "touch"

    def __init__(self, action, target, source=None):
        self.action = action
        self.target = target
        self.source = source
        Event.__init__(self, action, target, source)

    def __str__(self):
        target = self.target
        if self.source:
            target = "%s <= %s" % (self.target, self.source)
        return "%s: %s" % (self.action, target)


class FileSystemUtil(object):

    """File system utilities with event reporting."""

    def __init__(self, event_handler=None):
        self.event_handler = event_handler

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""

        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def chdir(self, path):
        """Wrap os.chdir."""

        cwd = os.getcwd()
        os.chdir(path)
        if cwd != os.getcwd():
            event = FileSystemEvent(FileSystemEvent.CHDIR, path + "/")
            self.handle_event(event)

    def delete(self, path):
        """Delete a file or a directory."""

        if os.path.islink(path) or os.path.isfile(path):
            ret = os.unlink(path)
            self.handle_event(FileSystemEvent(FileSystemEvent.DELETE, path))
        elif os.path.isdir(path):
            ret = shutil.rmtree(path, ignore_errors=True)
            event = FileSystemEvent(FileSystemEvent.DELETE, path + "/")
            self.handle_event(event)

    def dirname(self, path):
        """Wrap os.path.dirname.
        
        Unlike os.path.dirname, return "." instead of an empty string if result is
        the current working directory.
 
        """

        d = os.path.dirname(path)
        if d:
            return d
        else:
            return "."

    def install(self, path):
        """Create an empty file in path."""
        if os.path.exists(path):
            self.delete(path)
        open(path, "wb").close()
        event = FileSystemEvent(FileSystemEvent.INSTALL, path)
        self.handle_event(event)

    def makedirs(self, path):
        """Wrap os.makedirs. Does nothing if directory exists."""

        # Attempt to handle race conditions
        while not os.path.isdir(path):
            self.delete(path)
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise e
            else:
                event = FileSystemEvent(FileSystemEvent.CREATE, path)
                self.handle_event(event)

    def rename(self, source, target):
        """Wrap os.rename. Create directory of target if it does not exist."""

        if not os.path.exists(self.dirname(target)):
            self.makedirs(self.dirname(target))
        os.rename(source, target)
        event = FileSystemEvent(FileSystemEvent.RENAME, source, target)
        self.handle_event(event)

    def symlink(self, source, target, no_overwrite_mode=False):
        """Wrap os.symlink.
        
        Create directory of target if it does not exist.
        If no_overwrite_mode is not specified or not True, remove target if it
        exists, and is not a symbolic link pointing to source.

        """

        if not os.path.exists(self.dirname(target)):
            self.makedirs(self.dirname(target))
        if (not no_overwrite_mode and os.path.exists(target) and
            (not os.path.islink(target) or not os.readlink(target) == source)):
            self.delete(target)
        if not os.path.exists(target):
            os.symlink(source, target)
            event = FileSystemEvent(FileSystemEvent.SYMLINK, source, target)
            self.handle_event(event)

    def touch(self, path):
        """Touch a file."""
        open(path, "a").close()
        os.utime(path, None)
        self.handle_event(FileSystemEvent(FileSystemEvent.TOUCH, path))
