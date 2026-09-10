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
"""Generic base class shared by the "rose_arch" compression handlers.

Each concrete compressor (e.g. gzip, xz, zstd) lives in its own
"rose_arch_<compressor>.py" module, providing a sub-class of
RoseArchCompressor that applies that compressor with a native Python
library where one is available, falling back to the equivalent command
line tool otherwise. This module contains no compressor-specific logic.

"""

from functools import partial
import os
from shlex import quote


class RoseArchCompressThreadsError(Exception):

    """An exception raised if a compressor cannot use multiple threads."""

    ERROR_FORMAT = "%s: does not support multi-threading"

    def __str__(self):
        return self.ERROR_FORMAT % self.args


def _copy_compressed(new_compressor, chunk_size, f_in, f_out):
    """Compress the content of f_in into f_out, a chunk at a time.

    new_compressor -- a callable returning an incremental compressor, i.e.
                      an object with "compress" and "flush" methods.
    chunk_size -- the amount (in bytes) read from f_in at a time. Sources
                  can be much larger than the available memory, so they
                  are never read in one go.

    """
    compressor = new_compressor()
    for chunk in iter(partial(f_in.read, chunk_size), b""):
        f_out.write(compressor.compress(chunk))
    f_out.write(compressor.flush())


class RoseArchCompressor:

    """Compress each source of an archive target individually.

    Sub-classes should set SCHEMES to the compression schemes they handle
    and COMPRESSOR to the name of the compressor to apply (this name also
    doubles as its command line fallback). A sub-class that can make use
    of more than one thread to compress a single source should set
    MULTI_THREADED = True, and should normally also override
    get_compress_func() (and get_command() if the command line tool
    needs non-default options to make use of the threads).

    """

    # N.B. An empty SCHEMES keeps this base class out of the handlers
    #      discovered by rose.scheme_handler.SchemeHandlersManager.
    SCHEMES: list = []
    COMPRESSOR: str = ""
    MULTI_THREADED = False

    # The amount (in bytes) read from a source at a time by streaming,
    # Python-library-based compression (see get_compress_func()). A
    # moderate value is used here: too small (e.g. 1 MiB) adds
    # unnecessary Python call overhead, and going much bigger gives no
    # benefit while risking memory pressure of its own on constrained
    # systems. Sub-classes may override this if a different chunk size
    # suits their compressor better.
    CHUNK_SIZE = 16 * 1024 * 1024  # 16 MiB

    def __init__(self, app_runner, *args, **kwargs):
        self.app_runner = app_runner

    @classmethod
    def supports_threads(cls, scheme=None):
        """Return True if this compressor can use many threads."""
        return cls.MULTI_THREADED

    @classmethod
    def check_threads(cls, threads):
        """Raise RoseArchCompressThreadsError if "threads" != 1 and this
        compressor cannot use multiple threads.

        A configuration should be rejected by "rose_arch" before it gets
        this far. This is a backstop for any caller which does not check
        first.

        """
        if threads != 1 and not cls.MULTI_THREADED:
            raise RoseArchCompressThreadsError(cls.COMPRESSOR)

    @classmethod
    def get_compress_func(cls, threads):
        """Return a function compressing one file object into another.

        Return None if no Python library is available, which means that
        the "cls.COMPRESSOR" command line tool should be used instead.

        The returned function reads and writes in chunks, so that a
        source much bigger than the available memory can still be
        compressed.

        The base implementation always returns None. Sub-classes for
        which a Python library is available should override this.

        """
        return None

    @classmethod
    def get_command(cls, in_path, out_path, threads):
        """Return a shell command that compresses in_path into out_path."""
        return "%s -c %s >%s" % (
            cls.COMPRESSOR, quote(in_path), quote(out_path)
        )

    @classmethod
    def compress(cls, app_runner, in_path, out_path, threads=1):
        """Compress "in_path" into "out_path" with this compressor.

        threads -- the number of threads to compress with, 0 meaning one
                   per available CPU. Only supported where
                   cls.MULTI_THREADED is True.

        """
        cls.check_threads(threads)
        copy_compressed = cls.get_compress_func(threads)
        if copy_compressed is None:
            app_runner.popen.run_simple(
                cls.get_command(in_path, out_path, threads), shell=True
            )
        else:
            with open(in_path, "rb") as f_in:
                with open(out_path, "wb") as f_out:
                    copy_compressed(f_in, f_out)

    def compress_sources(self, target, work_dir, threads=1):
        """Compress each source in target.

        Use work_dir to dump results.

        """
        type(self).check_threads(threads)
        for source in target.sources.values():
            if source.path.endswith("." + target.compress_scheme):
                continue  # assume already done
            name = source.name + "." + target.compress_scheme
            work_path = os.path.join(work_dir, name)
            self.app_runner.fs_util.makedirs(
                self.app_runner.fs_util.dirname(work_path)
            )
            type(self).compress(
                self.app_runner, source.path, work_path, threads
            )
            source.path = work_path
