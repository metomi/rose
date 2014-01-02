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
"""A handler of locations on remote hosts."""

import os
from rose.checksum import get_checksum
import socket
from tempfile import TemporaryFile

class RsyncLocHandler(object):
    """Handler of locations on remote hosts."""

    def __init__(self, manager):
        self.manager = manager
        self.rsync = self.manager.popen.which("rsync")
        self.bad_address = None
        try:
            self.bad_address = socket.gethostbyname("no-such-host")
        except IOError:
            pass

    def can_pull(self, loc):
        if self.rsync is None:
            return False
        host, path = loc.name.split(":", 1)
        try:
            address = socket.gethostbyname(host)
        except IOError:
            return False
        else:
            return self.bad_address is None or address != self.bad_address

    def parse(self, loc, conf_tree):
        """Set loc.scheme, loc.loc_type, loc.paths."""
        loc.scheme = "rsync"
        # Attempt to obtain the checksum(s) via "ssh"
        host, path = loc.name.split(":", 1)
        cmd = self.manager.popen.get_cmd("ssh", host, "bash")
        f = TemporaryFile()
        f.write("""
        set -eu
        if [[ -d %(path)s ]]; then
            echo '%(tree)s'
            cd %(path)s
            find . -type d | sed '/^\.$/d; /\/\./d; s/^\.\/*/- /'
            md5sum $(find . -type f | sed '/\/\./d; s/^\.\///')
        elif [[ -f %(path)s ]]; then
            echo '%(blob)s'
            md5sum %(path)s
        fi
        """ % {"path": path, "blob": loc.TYPE_BLOB, "tree": loc.TYPE_TREE})
        f.seek(0)
        out, err = self.manager.popen(*cmd, stdin=f)
        lines = out.splitlines()
        if not lines or lines[0] not in [loc.TYPE_BLOB, loc.TYPE_TREE]:
            raise ValueError(loc.name)
        loc.loc_type = lines.pop(0)
        if loc.loc_type == loc.TYPE_BLOB:
            line = lines.pop(0)
            checksum, name = line.split(None, 1)
            loc.add_path(loc.BLOB, checksum)
        for line in lines:
            checksum, name = line.split(None, 1)
            if checksum == "-":
                checksum = None
            loc.add_path(name, checksum)

    def pull(self, loc, conf_tree):
        """Run "rsync" to pull files or directories of loc to its cache."""
        name = loc.name
        if loc.loc_type == loc.TYPE_TREE:
            name = loc.name + "/"
        cmd = self.manager.popen.get_cmd("rsync", name, loc.cache)
        self.manager.popen(*cmd)
