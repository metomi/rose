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
import errno
import os
import unittest

from metomi.rose.popen import RosePopener, RosePopenError


class _TestOSErrorFilename(unittest.TestCase):
    """Ensure an OSError has a filename."""

    def test_oserror_has_filename(self):
        """Does what it says."""
        rose_popen = RosePopener()
        name = "bad-command"
        try:
            rose_popen.run(name)
        except RosePopenError as exc:
            ose = FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), name
            )
            try:
                self.assertEqual(str(ose), exc.stderr)
            except AssertionError:
                # This is horrible, but refers to a bug in some versions of
                # Python 2.6 - https://bugs.python.org/issue32490
                err_msg = (
                    "[Errno 2] No such file or directory:"
                    " 'bad-command': 'bad-command'"
                )
                self.assertEqual(err_msg, exc.stderr)
        else:
            self.fail("should return FileNotFoundError")


if __name__ == '__main__':
    unittest.main()
