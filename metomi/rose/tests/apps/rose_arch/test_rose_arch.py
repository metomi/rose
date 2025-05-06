from metomi.rose.task_run import main as rose_task_run
from metomi.rose.task_run import TaskRunner
from metomi.rose.reporter import Reporter

import pytest
from textwrap import dedent
from types import SimpleNamespace

ZIP_METHODS = ["nozip", "gunzipme", "targunzipme", "zstdme", "xzme"]


@pytest.fixture
def setup_rose_arch_env(monkeypatch):
    """Mock the environment variables needed for a rose_arch task.
    """
    monkeypatch.setenv("CYLC_WORKFLOW_ID", "foo")
    monkeypatch.setenv("CYLC_TASK_ID", "bar")
    monkeypatch.setenv("CYLC_TASK_NAME", "baz")
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "qux")
    monkeypatch.setenv("CYLC_TASK_LOG_ROOT", "woteva")


def test_rose_arch(tmp_path, setup_rose_arch_env):
    """Test the rose_arch app against different compression methods.

    Possible future enhancements:
        might be nice to abstract the setup so that we can
        test other aspects of rose_arch.
    """
    (tmp_path / 'archive').mkdir()
    (tmp_path / 'source').mkdir(parents=True, exist_ok=True)
    for source in ZIP_METHODS:
        (tmp_path / 'source' / source).write_text(
            "The Quick Brown Fox Jumps Over The Lazy Dog.\n")

    (tmp_path / 'rose-app.conf').write_text(
        dedent(
            f"""
                mode=rose_arch

                [arch]
                command-format=cp %(sources)s %(target)s
                target-prefix={tmp_path}/archive/
                source-prefix={tmp_path}/source/

                [arch:nozip]
                source=nozip

                [arch:gunzipme.gz]
                source=gunzipme

                [arch:targunzipme.tar.gz]
                source=targunzipme

                [arch:zstdme.zst]
                source=zstdme

                [arch:xzme.xz]
                source=xzme
            """
        )
    )

    # Create a crude options object:
    opts = SimpleNamespace()
    for key in TaskRunner.OPTIONS:
        setattr(opts, key, None)
    opts.conf_dir = str(tmp_path)

    # Run our task:
    runner = TaskRunner(event_handler=Reporter())
    runner(opts, [])

    assert (tmp_path / 'archive' / 'nozip').exists()
    assert (tmp_path / 'archive' / 'gunzipme.gz').exists()
    assert (tmp_path / 'archive' / 'targunzipme.tar.gz').exists()
    assert (tmp_path / 'archive' / 'zstdme.zst').exists()
    assert (tmp_path / 'archive' / 'xzme.xz').exists()
