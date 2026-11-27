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
"""Compress archive sources in gzip."""


from metomi.rose.apps.rose_arch_compressions import RoseArchCompressor

# The name of the compressor. This is also the name of its command line
# fallback.
GZIP = "gzip"


class RoseArchGzip(RoseArchCompressor):

    """Compress archive sources in gzip.

    N.B. Python's gzip library is slow, so this always uses the command
    line tool instead (the base class's default get_compress_func()
    already returns None, so no override is needed here).

    """

    SCHEMES = ["gz", "gzip"]
    COMPRESSOR = GZIP
