# Copyright (C) British Crown (Met Office) & Contributors.
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

import _io
import io

ENCODING = "UTF-8"


def write_safely(msg, handle):
    """Wrap handle.write command in logic to deal with change to
    Python3 unicode and byte types.

    Args:
        msg (str or bytes):
            Message to be written - type uncertain.
        handle (file handle):
            Potentially Obscure file or file-like object. May include a variety
            of buffer types.
    """
    # Unforgiving, but fast logic.
    try:
        if isinstance(msg, bytes):
            if isinstance(handle, _io.TextIOWrapper) or isinstance(
                handle, _io.StringIO
            ):
                handle.write(msg.decode())
            elif isinstance(handle, io.BufferedWriter):
                handle.write(msg)
            else:
                handle.write(msg.decode())
        elif isinstance(msg, str):
            if isinstance(handle, io.BufferedWriter):
                handle.write(msg.encode(ENCODING))
            else:
                handle.write(msg)

    # Forgiving, but potentially quite slow logic.
    except TypeError:
        try:
            handle.write(msg)
        except TypeError:
            if isinstance(msg, str):
                handle.write(msg.encode())
            elif isinstance(msg, bytes):
                handle.write(msg.decode())
