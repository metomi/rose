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
"""Unit tests for the "rose_arch" compression handlers."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from metomi.rose.apps.rose_arch_compressions import compression_util
from metomi.rose.apps.rose_arch_compressions.compression_util import (
    GZIP,
    XZ,
    ZSTD,
    RoseArchCompressThreadsError,
)
from metomi.rose.apps.rose_arch_compressions.rose_arch_gzip import RoseArchGzip
from metomi.rose.apps.rose_arch_compressions.rose_arch_tar import (
    RoseArchTarGzip,
)
from metomi.rose.apps.rose_arch_compressions.rose_arch_xz import RoseArchXz
from metomi.rose.apps.rose_arch_compressions.rose_arch_zstd import RoseArchZstd


HANDLERS = {
    "gz": RoseArchGzip,
    "gzip": RoseArchGzip,
    "xz": RoseArchXz,
    "zst": RoseArchZstd,
    "zstd": RoseArchZstd,
}


@pytest.fixture
def app_runner(tmp_path):
    """A mock AppRunner which records the commands it is asked to run."""
    runner = MagicMock()
    runner.fs_util.dirname = lambda path: str(tmp_path)
    return runner


@pytest.fixture
def target(tmp_path):
    """Return a minimal stand in for a RoseArchTarget."""

    def _inner(compress_scheme, name="hello.txt", text="Hello World"):
        path = tmp_path / name
        path.write_text(text)
        source = SimpleNamespace(name=name, path=str(path))
        return SimpleNamespace(
            name="dummy",
            sources={"checksum": source},
            compress_scheme=compress_scheme,
            work_source_path=None,
        )

    return _inner


@pytest.fixture
def no_python_libraries(monkeypatch):
    """Force the handlers onto their command line fallbacks."""
    monkeypatch.setattr(
        compression_util, "_get_compress_func", lambda *args: None
    )


@pytest.mark.parametrize(
    "scheme, tool",
    [
        ("gz", "gzip"),
        ("gzip", "gzip"),
        ("xz", "xz"),
        ("zst", "zstd"),
        ("zstd", "zstd"),
    ],
)
def test_compress_sources_command(
    app_runner, target, tmp_path, no_python_libraries, scheme, tool
):
    """Each source is compressed by the expected command line tool."""
    a_target = target(scheme)
    HANDLERS[scheme](app_runner).compress_sources(a_target, str(tmp_path))

    command = app_runner.popen.run_simple.call_args[0][0]
    assert command.startswith(tool + " ")
    assert a_target.sources["checksum"].path.endswith("hello.txt." + scheme)


@pytest.mark.parametrize("scheme", ["xz", "zst", "zstd"])
def test_compress_sources_library(app_runner, target, tmp_path, scheme):
    """Each source is compressed in process where a library is available."""
    compressor = XZ if scheme == "xz" else ZSTD
    if compression_util._get_compress_func(compressor, 1) is None:
        pytest.skip("no Python library for %s" % compressor)

    a_target = target(scheme)
    HANDLERS[scheme](app_runner).compress_sources(a_target, str(tmp_path))

    app_runner.popen.run_simple.assert_not_called()
    path = a_target.sources["checksum"].path
    assert path.endswith("hello.txt." + scheme)
    with open(path, "rb") as handle:
        assert handle.read()  # some compressed bytes were written


def test_compress_sources_skips_compressed(app_runner, target, tmp_path):
    """A source which is already compressed is left alone."""
    a_target = target("gz", name="hello.txt.gz")
    orig_path = a_target.sources["checksum"].path

    RoseArchGzip(app_runner).compress_sources(a_target, str(tmp_path))

    app_runner.popen.run_simple.assert_not_called()
    assert a_target.sources["checksum"].path == orig_path


@pytest.mark.parametrize("scheme", ["xz", "zst"])
def test_compress_sources_streams(
    app_runner, target, tmp_path, monkeypatch, scheme
):
    """A source is compressed in chunks, so it need not fit in memory."""
    compressor = XZ if scheme == "xz" else ZSTD
    if compression_util._get_compress_func(compressor, 1) is None:
        pytest.skip("no Python library for %s" % compressor)
    monkeypatch.setattr(compression_util, "CHUNK_SIZE", 8)

    text = "Hello World " * 100  # many chunks of 8 bytes
    a_target = target(scheme, text=text)
    HANDLERS[scheme](app_runner).compress_sources(a_target, str(tmp_path))

    with open(a_target.sources["checksum"].path, "rb") as handle:
        assert _decompress(compressor, handle.read()) == text.encode()


def _decompress(compressor, data):
    """Decompress "data" with whichever library the tests can import.

    N.B. A streamed frame does not record the decompressed size, so the
    "zstandard" one shot decompress cannot be used here.

    """
    if compressor == XZ:
        import lzma

        return lzma.decompress(data)
    try:
        from compression import zstd
    except ImportError:
        import zstandard

        return zstandard.ZstdDecompressor().decompressobj().decompress(data)
    return zstd.decompress(data)


@pytest.mark.parametrize(
    "scheme, tool",
    [
        ("tar.gz", "gzip"),
        ("tgz", "gzip"),
        ("pax.gz", "gzip"),
        ("tar.xz", "xz"),
        ("txz", "xz"),
        ("pax.xz", "xz"),
        ("tar.zst", "zstd"),
        ("tzst", "zstd"),
        ("pax.zst", "zstd"),
    ],
)
def test_tar_compress_sources_command(
    app_runner, target, tmp_path, no_python_libraries, scheme, tool
):
    """The tar file is compressed by the expected command line tool."""
    a_target = target(scheme)
    RoseArchTarGzip(app_runner).compress_sources(a_target, str(tmp_path))

    command = app_runner.popen.run_simple.call_args[0][0]
    assert command.startswith(tool + " ")
    assert a_target.work_source_path.endswith("." + scheme)


@pytest.mark.parametrize("scheme", ["tar", "pax"])
def test_tar_compress_sources_uncompressed(
    app_runner, target, tmp_path, scheme
):
    """A plain tar/pax target is not passed to a compressor."""
    a_target = target(scheme)
    RoseArchTarGzip(app_runner).compress_sources(a_target, str(tmp_path))

    app_runner.popen.run_simple.assert_not_called()
    assert a_target.work_source_path.endswith(".tar")


@pytest.mark.parametrize("threads", [0, 2, 8])
def test_zstd_command_threads(
    app_runner, target, tmp_path, no_python_libraries, threads
):
    """The number of threads is passed on to the zstd command."""
    a_target = target("zst")
    RoseArchZstd(app_runner).compress_sources(
        a_target, str(tmp_path), threads=threads
    )

    command = app_runner.popen.run_simple.call_args[0][0]
    assert "-T%d " % threads in command


@pytest.mark.parametrize(
    "scheme", ["gz", "gzip", "xz", "tar.gz", "tar", "txz"]
)
def test_multi_threading_not_supported(app_runner, target, tmp_path, scheme):
    """Only zstd may be asked for more than one thread."""
    handler = HANDLERS.get(scheme, RoseArchTarGzip)(app_runner)

    assert not handler.supports_threads(scheme)
    with pytest.raises(
        RoseArchCompressThreadsError, match="does not support multi-threading"
    ):
        handler.compress_sources(target(scheme), str(tmp_path), threads=4)


@pytest.mark.parametrize("scheme", ["zst", "zstd", "tar.zst", "tzst"])
def test_multi_threading_supported(app_runner, target, tmp_path, scheme):
    """zstd schemes accept more than one thread."""
    handler = HANDLERS.get(scheme, RoseArchTarGzip)(app_runner)

    assert handler.supports_threads(scheme)
    handler.compress_sources(target(scheme), str(tmp_path), threads=2)


def test_gzip_always_uses_the_command_line():
    """Python's gzip is slow, so the command line tool is preferred."""
    assert compression_util._get_compress_func(GZIP, 1) is None


def test_get_command_quotes_paths():
    """Paths are quoted so that a shell cannot act on their contents."""
    command = compression_util._get_command(
        ZSTD, "in file; rm -rf /", "out file", 4
    )
    assert command == "zstd -T4 -c 'in file; rm -rf /' >'out file'"
