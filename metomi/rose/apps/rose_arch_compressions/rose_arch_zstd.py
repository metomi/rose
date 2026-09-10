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
"""Compress archive sources using zstd."""

from functools import partial
import os
from shlex import quote

from metomi.rose.apps.rose_arch_compressions import (
    RoseArchCompressor,
    _copy_compressed,
)

# The name of the compressor. This is also the name of its command line
# fallback.
ZSTD = "zstd"

# Set this environment variable (to any non-empty value) to always use the
# "zstd" command line tool for zstd compression, bypassing both Python
# libraries, regardless of the number of threads requested or what is
# installed. Useful where a Python zstd library is present but may not
# perform well or to force the same tool to be used everywhere on a site.

ZSTD_FORCE_CLI = "ROSE_ARCH_ZSTD_FORCE_CLI"

class RoseArchZstd(RoseArchCompressor):

    """Compress archive sources in zstd."""

    SCHEMES = ["zst", "zstd"]
    COMPRESSOR = ZSTD
    MULTI_THREADED = True

    @classmethod
    def get_compress_func(cls, threads):
        """Return a streaming zstd compress function, or None if none is
        usable.

        Setting the ZSTD_FORCE_CLI environment variable forces the
        command line tool to be used unconditionally, regardless of
        thread count or what is importable.

        """
        if os.environ.get(ZSTD_FORCE_CLI):
            return None
        if threads == 0:
            threads = os.cpu_count() or 1
        if threads == 1:
            try:
                from compression import zstd  # Python 3.14 and above
            except ImportError:
                pass
            else:
                return partial(
                    _copy_compressed, zstd.ZstdCompressor, cls.CHUNK_SIZE
                )
        try:
            import zstandard  # the "zstandard" distribution
        except ImportError:
            return None
        return zstandard.ZstdCompressor(threads=threads).copy_stream

    @classmethod
    def get_command(cls, in_path, out_path, threads):
        return "%s -T%d -c %s >%s" % (
            cls.COMPRESSOR, threads, quote(in_path), quote(out_path)
        )
