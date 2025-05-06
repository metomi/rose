
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
"""Integration tests for Rose Arch."""

import pytest
from textwrap import dedent
from types import SimpleNamespace
from typing import Dict


from metomi.rose.task_run import TaskRunner
from metomi.rose.reporter import Reporter


ZIP_METHODS = {
    "nozip": "nozip",
    "gunzipme": "gunzipme.gz",
    "targunzipme": "targunzipme.tar.gz",
    "zstdme": "zstdme.zst",
    "xzme": "xzme.xz"
}


@pytest.fixture
def setup_rose_arch_env(monkeypatch, tmp_path):
    """Mock the environment variables needed for a rose_arch task.
    """
    tmp_path_str = str(tmp_path)
    monkeypatch.setenv("CYLC_WORKFLOW_ID", "foo")
    monkeypatch.setenv("CYLC_TASK_ID", "bar")
    monkeypatch.setenv("CYLC_TASK_NAME", "baz")
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "qux")
    monkeypatch.setenv("CYLC_TASK_LOG_ROOT", tmp_path_str)
    monkeypatch.setenv("ROSE_SUITE_NAME", tmp_path_str)
    monkeypatch.setenv("ROSE_SUITE_DIR", tmp_path_str)
    monkeypatch.setenv("CYLC_RUN_DIR", tmp_path_str)


@pytest.fixture
def setup_rose_arch_task(tmp_path):
    """Set up a rose_arch task with a given config and source files.
    """
    def _inner(
        config: str,
        source_files: Dict[str, str],
    ):
        (tmp_path / 'archive').mkdir()
        (tmp_path / 'source').mkdir()
        for source_file in source_files:
            (tmp_path / 'source' / source_file).write_text(
                source_files[source_file])
        (tmp_path / 'rose-app.conf').write_text(dedent(config))
    return _inner


@pytest.fixture
def run_rose_arch_task(tmp_path, setup_rose_arch_env):
    """Run a rose_arch task."""

    def _inner():
        # Create a crude options object:
        opts = SimpleNamespace()
        for key in TaskRunner.OPTIONS:
            setattr(opts, key, None)
        opts.conf_dir = str(tmp_path)

        # Run our task:
        runner = TaskRunner(event_handler=Reporter())
        runner(opts, [])
    return _inner


@pytest.mark.parametrize(
    "source_file, expected",
    [
        ("nozip", "nozip"),
        ("gunzipme", "gunzipme.gz"),
        ("targunzipme", "targunzipme.tar.gz"),
        ("zstdme", "zstdme.zst"),
        ("xzme", "xzme.xz")
    ]
)
def test_rose_arch(
    tmp_path,
    setup_rose_arch_task,
    run_rose_arch_task,
    source_file,
    expected
):
    """Test the rose_arch app against different compression methods.

    Possible future enhancements:
        - More checks on the compressed files, ensuring that the compression
          has worked as expected.
    """
    setup_rose_arch_task(
        f"""
            mode=rose_arch

            [arch]
            command-format=cp %(sources)s %(target)s
            target-prefix={tmp_path}/archive/
            source-prefix={tmp_path}/source/

            [arch:{expected}]
            source={source_file}
        """,
        ZIP_METHODS,
    )
    run_rose_arch_task()
    assert (tmp_path / 'archive' / expected).exists()


@pytest.mark.parametrize(
    'archiver',
    [
        'gz',
        'tar.gz',
        'xz',
    ]
)
def test_raises_too_many_threads_err(
    tmp_path, setup_rose_arch_task, run_rose_arch_task, archiver
):
    """Test that we get an error if an archiver does not support threads,
    but thread number (other than 1) is passed in.

    """
    setup_rose_arch_task(
        f"""
            mode=rose_arch

            [arch]
            command-format=gzip %(sources)s %(target)s
            target-prefix={tmp_path}/archive/
            source-prefix={tmp_path}/source/

            [arch:zipme.{archiver}]
            source=zipme
            compress-threads=2
        """,
        {"zipme": "Any old text file"},
    )

    with pytest.raises(
        NotImplementedError,
        match="does not support multi-threading"
    ):
        run_rose_arch_task()
