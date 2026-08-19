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
"""Compression helpers shared by the "rose_arch" compression handlers.

Each compressor is applied with a native Python library where one is
available, falling back to the equivalent command line tool otherwise.

"""

from functools import partial
import os
from shlex import quote

# Compressor names. These are also the names of the command line fallbacks.
GZIP = "gzip"
XZ = "xz"
ZSTD = "zstd"

# Only zstd is able to compress a single stream with more than one thread.
MULTI_THREADED = (ZSTD,)

# Set this environment variable (to any non-empty value) to always use the
# "zstd" command line tool for zstd compression, bypassing both Python
# libraries, regardless of the number of threads requested or what is
# installed. Useful where a Python zstd library is present but is known
# not to perform well (see the note in "_get_zstd_compress_func" below),
# or simply to force the same tool to be used everywhere on a site.
ZSTD_FORCE_CLI = "ROSE_ARCH_ZSTD_FORCE_CLI"

# The amount read from a source at a time. Sources can be much larger than
# the available memory, so they are never read in one go.
#
# This only applies to single-threaded compression (xz, or zstd when only
# one thread is requested) - multi-threaded zstd compression uses the
# "zstandard" distribution or the command line tool instead, both of
# which manage their own internal chunking. A moderate value is used
# here: too small (e.g. 1 MiB) adds unnecessary Python call overhead, and
# going much bigger gives no benefit while risking memory pressure of its
# own on constrained systems.
CHUNK_SIZE = 16 * 1024 * 1024


class RoseArchCompressThreadsError(Exception):

    """An exception raised if a compressor cannot use multiple threads."""

    ERROR_FORMAT = "%s: does not support multi-threading"

    def __str__(self):
        return self.ERROR_FORMAT % self.args


def check_threads(name, threads):
    """Raise RoseArchCompressThreadsError if "name" cannot use threads.

    "name" is a compressor or a compression scheme, and is only used to
    build the error message.

    A configuration should be rejected by "rose_arch" before it gets this
    far. This is a backstop for any caller which does not check first.

    """
    if threads != 1 and name not in MULTI_THREADED:
        raise RoseArchCompressThreadsError(name)


def compress(app_runner, compressor, in_path, out_path, threads=1):
    """Compress "in_path" into "out_path" using "compressor".

    compressor -- one of GZIP, XZ or ZSTD.
    threads -- the number of threads to compress with, 0 meaning one per
               available CPU. Only ZSTD supports more than one thread.

    """
    check_threads(compressor, threads)
    copy_compressed = _get_compress_func(compressor, threads)
    if copy_compressed is None:
        app_runner.popen.run_simple(
            _get_command(compressor, in_path, out_path, threads), shell=True
        )
    else:
        with open(in_path, "rb") as f_in:
            with open(out_path, "wb") as f_out:
                copy_compressed(f_in, f_out)


def _get_command(compressor, in_path, out_path, threads):
    """Return a shell command that compresses in_path into out_path."""
    options = ""
    if compressor == ZSTD:
        options = "-T%d " % threads
    return "%s %s-c %s >%s" % (
        compressor, options, quote(in_path), quote(out_path)
    )


def _copy_compressed(new_compressor, f_in, f_out):
    """Compress the content of f_in into f_out, a chunk at a time.

    new_compressor -- a callable returning an incremental compressor, i.e.
                      an object with "compress" and "flush" methods.

    """
    compressor = new_compressor()
    for chunk in iter(partial(f_in.read, CHUNK_SIZE), b""):
        f_out.write(compressor.compress(chunk))
    f_out.write(compressor.flush())


def _get_compress_func(compressor, threads):
    """Return a function compressing one file object into another.

    Return None if no Python library is available, which means that the
    command line tool should be used instead.

    The returned function reads and writes in chunks, so that a source
    much bigger than the available memory can still be compressed.

    """
    if compressor == GZIP:
        return None  # N.B. Python's gzip is slow
    if compressor == XZ:
        try:
            import lzma
        except ImportError:
            return None
        return partial(_copy_compressed, lzma.LZMACompressor)
    if compressor == ZSTD:
        return _get_zstd_compress_func(threads)
    raise KeyError(compressor)


def _get_zstd_compress_func(threads):
    """Return a streaming zstd compress function, or None if none is usable.

    Python 3.14's stdlib "compression.zstd" is only used here for
    single-threaded compression. Testing its multi-threaded "nb_workers"
    option against a real multi-hundred-GB file showed it giving far
    lower throughput than both the "zstd" command line tool and the
    "zstandard" distribution at the same thread count, and using barely
    more than one CPU's worth of work even in a smaller, isolated test -
    i.e. it does not reliably deliver the multi-threaded speedup it is
    asked for. So multi-threaded requests skip straight past it to
    "zstandard" or, failing that, the command line tool, both of which
    have been confirmed to scale with threads on real data.

    Setting the ZSTD_FORCE_CLI environment variable forces the command
    line tool to be used unconditionally, regardless of thread count or
    what is importable, for sites that want that guarantee.

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
            return partial(_copy_compressed, zstd.ZstdCompressor)
    try:
        import zstandard  # the "zstandard" distribution
    except ImportError:
        return None
    return zstandard.ZstdCompressor(threads=threads).copy_stream


class RoseArchCompressor:

    """Compress each source of an archive target individually.

    Sub-classes should set SCHEMES to the compression schemes they handle
    and COMPRESSOR to the compressor to apply.

    """

    # N.B. An empty SCHEMES keeps this base class out of the handlers
    #      discovered by rose.scheme_handler.SchemeHandlersManager.
    SCHEMES: list = []
    COMPRESSOR: str = ""

    def __init__(self, app_runner, *args, **kwargs):
        self.app_runner = app_runner

    @classmethod
    def supports_threads(cls, scheme):
        """Return True if "scheme" can be compressed with many threads."""
        return cls.COMPRESSOR in MULTI_THREADED

    def compress_sources(self, target, work_dir, threads=1):
        """Compress each source in target.

        Use work_dir to dump results.

        """
        check_threads(self.COMPRESSOR, threads)
        for source in target.sources.values():
            if source.path.endswith("." + target.compress_scheme):
                continue  # assume already done
            name = source.name + "." + target.compress_scheme
            work_path = os.path.join(work_dir, name)
            self.app_runner.fs_util.makedirs(
                self.app_runner.fs_util.dirname(work_path)
            )
            compress(
                self.app_runner,
                self.COMPRESSOR,
                source.path,
                work_path,
                threads,
            )
            source.path = work_path
