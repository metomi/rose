# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
# -----------------------------------------------------------------------------
"""Implement "rose suite-run"."""

import ast
from datetime import datetime
from fnmatch import fnmatchcase
from glob import glob
import os
import pipes
from metomi.rose.config import ConfigDumper, ConfigLoader, ConfigNode
from metomi.rose.env import env_var_process
from metomi.rose.host_select import HostSelector
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopenError
from metomi.rose.reporter import Event, Reporter, ReporterContext
from metomi.rose.resource import ResourceLocator
from metomi.rose.run import ConfigValueError, NewModeError, Runner
from metomi.rose.run_source_vc import write_source_vc_info
from metomi.rose.suite_clean import SuiteRunCleaner
import shutil
import sys
from tempfile import TemporaryFile, mkdtemp
from time import sleep, strftime, time
import traceback


class VersionMismatchError(Exception):

    """An exception raised when there is a version mismatch."""

    def __str__(self):
        return "Version expected=%s, actual=%s" % self.args


class SkipReloadEvent(Event):

    """An event raised to report that suite configuration reload is skipped."""

    def __str__(self):
        return "%s: reload complete. \"%s\" unchanged" % self.args


class SuiteLogArchiveEvent(Event):

    """An event raised to report the archiving of a suite log directory."""

    def __str__(self):
        return "%s <= %s" % self.args


class SuiteRunner(Runner):

    """Invoke a Rose suite."""

    SLEEP_PIPE = 0.05
    NAME = "suite"
    OPTIONS = [
        "conf_dir",
        "defines",
        "defines_suite",
        "host",
        "install_only_mode",
        "local_install_only_mode",
        "log_archive_mode",
        "log_keep",
        "log_name",
        "name",
        "new_mode",
        "no_overwrite_mode",
        "opt_conf_keys",
        "reload_mode",
        "remote",
        "restart_mode",
        "run_mode",
        "strict_mode",
        "validate_suite_only"]

    # Lists of rsync (always) exclude globs
    SYNC_EXCLUDES = (
        "/.*",
        "/cylc-suite.db",
        "/log",
        "/log.*",
        "/state",
        "/share",
        "/work",
    )

    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        self.host_selector = HostSelector(self.event_handler, self.popen)
        self.suite_run_cleaner = SuiteRunCleaner(
            event_handler=self.event_handler,
            host_selector=self.host_selector,
            suite_engine_proc=self.suite_engine_proc)

    def run_impl(self, opts, args, uuid, work_files):
        # Log file, temporary
        if hasattr(self.event_handler, "contexts"):
            t_file = TemporaryFile()
            log_context = ReporterContext(None, self.event_handler.VV, t_file)
            self.event_handler.contexts[uuid] = log_context

        # Check suite engine specific compatibility
        self.suite_engine_proc.check_global_conf_compat()

        # Suite name from the current working directory
        if opts.conf_dir:
            self.fs_util.chdir(opts.conf_dir)
        opts.conf_dir = os.getcwd()

        # --remote=KEY=VALUE,...
        if opts.remote:
            # opts.name always set for remote.
            return self._run_remote(opts, opts.name)

        conf_tree = self.config_load(opts)
        self.fs_util.chdir(conf_tree.conf_dirs[0])

        suite_name = opts.name
        if not opts.name:
            suite_name = os.path.basename(os.getcwd())

        # Check suite.rc #! line for template scheme
        templ_scheme = "jinja2"
        if self.suite_engine_proc.SUITE_CONF in conf_tree.files:
            suiterc_path = os.path.join(
                conf_tree.files[self.suite_engine_proc.SUITE_CONF],
                self.suite_engine_proc.SUITE_CONF)
            with open(suiterc_path) as fh:
                line = fh.readline()
                if line.startswith("#!"):
                    templ_scheme = line[2:].strip().lower()
        suite_section = (templ_scheme + ':' +
                         self.suite_engine_proc.SUITE_CONF)

        extra_defines = []
        if opts.defines_suite:
            for define in opts.defines_suite:
                extra_defines.append("[" + suite_section + "]" + define)

        # Automatic Rose constants
        # ROSE_ORIG_HOST: originating host
        # ROSE_VERSION: Rose version (not retained in run_mode=="reload")
        # Suite engine version
        my_rose_version = ResourceLocator.default().get_version()
        suite_engine_key = self.suite_engine_proc.get_version_env_name()
        if opts.run_mode in ["reload", "restart"]:
            prev_config_path = self.suite_engine_proc.get_suite_dir(
                suite_name, "log", "rose-suite-run.conf")
            prev_config = ConfigLoader()(prev_config_path)
            suite_engine_version = prev_config.get_value(
                ["env", suite_engine_key])
        else:
            suite_engine_version =\
                self.suite_engine_proc.get_version().decode()
        resloc = ResourceLocator.default()
        auto_items = [
            (suite_engine_key, suite_engine_version),
            ("ROSE_ORIG_HOST", self.host_selector.get_local_host()),
            ("ROSE_SITE", resloc.get_conf().get_value(['site'], '')),
            ("ROSE_VERSION", resloc.get_version())]
        for key, val in auto_items:
            requested_value = conf_tree.node.get_value(["env", key])
            if requested_value:
                if key == "ROSE_VERSION" and val != requested_value:
                    exc = VersionMismatchError(requested_value, val)
                    raise ConfigValueError(["env", key], requested_value, exc)
                val = requested_value
            else:
                conf_tree.node.set(["env", key], val,
                                   state=conf_tree.node.STATE_NORMAL)
            extra_defines.append('[%s]%s="%s"' % (suite_section, key, val))

        # Pass automatic Rose constants as suite defines
        self.conf_tree_loader.node_loader.load(extra_defines, conf_tree.node)

        # See if suite is running or not
        if opts.run_mode == "reload":
            # Check suite is running
            self.suite_engine_proc.get_suite_contact(suite_name)
        else:
            self.suite_engine_proc.check_suite_not_running(suite_name)

        # Install the suite to its run location
        suite_dir_rel = self._suite_dir_rel(suite_name)

        # Unfortunately a large try/finally block to ensure a temporary folder
        # created in validate only mode is cleaned up. Exceptions are not
        # caught here
        try:
            # Process Environment Variables
            environ = self.config_pm(conf_tree, "env")

            if opts.validate_suite_only_mode:
                temp_dir = mkdtemp()
                suite_dir = os.path.join(temp_dir, suite_dir_rel)
                os.makedirs(suite_dir, 0o0700)
            else:
                suite_dir = os.path.join(
                    os.path.expanduser("~"), suite_dir_rel)

            suite_conf_dir = os.getcwd()
            locs_conf = ConfigNode()
            if opts.new_mode:
                if os.getcwd() == suite_dir:
                    raise NewModeError("PWD", os.getcwd())
                elif opts.run_mode in ["reload", "restart"]:
                    raise NewModeError("--run", opts.run_mode)
                self.suite_run_cleaner.clean(suite_name)
            if os.getcwd() != suite_dir:
                if opts.run_mode == "run":
                    self._run_init_dir(opts, suite_name, conf_tree,
                                       locs_conf=locs_conf)
                os.chdir(suite_dir)

            # Housekeep log files
            now_str = None
            if not opts.install_only_mode and not opts.local_install_only_mode:
                now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                self._run_init_dir_log(opts, now_str)
            self.fs_util.makedirs("log/suite")

            # Rose configuration and version logs
            self.fs_util.makedirs("log/rose-conf")
            run_mode = opts.run_mode
            if run_mode not in ["reload", "restart", "run"]:
                run_mode = "run"
            mode = run_mode
            if opts.validate_suite_only_mode:
                mode = "validate-suite-only"
            elif opts.install_only_mode:
                mode = "install-only"
            elif opts.local_install_only_mode:
                mode = "local-install-only"
            prefix = "rose-conf/%s-%s" % (strftime("%Y%m%dT%H%M%S"), mode)

            # Dump the actual configuration as rose-suite-run.conf
            ConfigDumper()(conf_tree.node, "log/" + prefix + ".conf")

            # Install version information file
            write_source_vc_info(
                suite_conf_dir, "log/" + prefix + ".version", self.popen)

            # If run through rose-stem, install version information
            # files for each source tree if they're a working copy
            if hasattr(opts, 'source') and hasattr(opts, 'project'):
                for i, url in enumerate(opts.source):
                    if os.path.isdir(url):
                        write_source_vc_info(
                            url, "log/" + opts.project[i] + "-" + str(i) +
                            ".version", self.popen)

            for ext in [".conf", ".version"]:
                self.fs_util.symlink(prefix + ext, "log/rose-suite-run" + ext)

            # Move temporary log to permanent log
            if hasattr(self.event_handler, "contexts"):
                log_file_path = os.path.abspath(
                    os.path.join("log", "rose-suite-run.log"))
                log_file = open(log_file_path, "ab")
                temp_log_file = self.event_handler.contexts[uuid].handle
                temp_log_file.seek(0)
                log_file.write(temp_log_file.read())
                self.event_handler.contexts[uuid].handle = log_file
                temp_log_file.close()

            # Process Files
            cwd = os.getcwd()
            for rel_path, conf_dir in conf_tree.files.items():
                if (conf_dir == cwd or
                        any(fnmatchcase(os.sep + rel_path, exclude)
                            for exclude in self.SYNC_EXCLUDES) or
                        conf_tree.node.get(
                            [templ_scheme + ":" + rel_path]) is not None):
                    continue
                # No sub-directories, very slow otherwise
                if os.sep in rel_path:
                    rel_path = rel_path.split(os.sep, 1)[0]
                target_key = self.config_pm.get_handler(
                    "file").PREFIX + rel_path
                target_node = conf_tree.node.get([target_key])
                if target_node is None:
                    conf_tree.node.set([target_key])
                    target_node = conf_tree.node.get([target_key])
                elif target_node.is_ignored():
                    continue
                source_node = target_node.get("source")
                if source_node is None:
                    target_node.set(
                        ["source"], os.path.join(
                            conf_dir, rel_path))
                elif source_node.is_ignored():
                    continue
            self.config_pm(conf_tree, "file",
                           no_overwrite_mode=opts.no_overwrite_mode)

            # Process suite configuration template header
            # (e.g. Jinja2:suite.rc, EmPy:suite.rc)
            self.config_pm(conf_tree, templ_scheme, environ=environ)

            # Ask suite engine to parse suite configuration
            # and determine if it is up to date (unchanged)
            if opts.validate_suite_only_mode:
                suite_conf_unchanged = self.suite_engine_proc.cmp_suite_conf(
                    suite_dir, None, opts.strict_mode,
                    debug_mode=True)
            else:
                suite_conf_unchanged = self.suite_engine_proc.cmp_suite_conf(
                    suite_name, opts.run_mode, opts.strict_mode,
                    opts.debug_mode)
        finally:
            # Ensure the temporary directory created is cleaned up regardless
            # of success or failure
            if opts.validate_suite_only_mode and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        # Only validating so finish now
        if opts.validate_suite_only_mode:
            return

        # Install share/work directories (local)
        for name in ["share", "share/cycle", "work"]:
            self._run_init_dir_work(
                opts, suite_name, name, conf_tree, locs_conf=locs_conf)

        if opts.local_install_only_mode:
            return

        # Install suite files to each remote [user@]host
        for name in ["", "log/", "share/", "share/cycle/", "work/"]:
            uuid_file = os.path.abspath(name + uuid)
            open(uuid_file, "w").close()
            work_files.append(uuid_file)

        # Install items to user@host
        auths = self.suite_engine_proc.get_tasks_auths(suite_name)
        proc_queue = []  # [[proc, command, "ssh"|"rsync", auth], ...]
        for auth in sorted(auths):
            host = auth
            if "@" in auth:
                host = auth.split("@", 1)[1]
            # Remote shell
            command = self.popen.get_cmd("ssh", "-n", auth)
            # Provide ROSE_VERSION and CYLC_VERSION in the environment
            shcommand = "env ROSE_VERSION=%s %s=%s" % (
                my_rose_version, suite_engine_key, suite_engine_version)
            # Use login shell?
            no_login_shell = self._run_conf(
                "remote-no-login-shell", host=host, conf_tree=conf_tree)
            if not no_login_shell or no_login_shell.lower() != "true":
                shcommand += r""" bash -l -c '"$0" "$@"'"""
            # Path to "rose" command, if applicable
            rose_bin = self._run_conf(
                "remote-rose-bin", host=host, conf_tree=conf_tree,
                default="rose")
            # Build remote "rose suite-run" command
            shcommand += " %s suite-run -vv -n %s" % (
                rose_bin, suite_name)
            for key in ["new", "debug", "install-only"]:
                attr = key.replace("-", "_") + "_mode"
                if getattr(opts, attr, None) is not None:
                    shcommand += " --%s" % key
            if opts.log_keep:
                shcommand += " --log-keep=%s" % opts.log_keep
            if opts.log_name:
                shcommand += " --log-name=%s" % opts.log_name
            if not opts.log_archive_mode:
                shcommand += " --no-log-archive"
            shcommand += " --run=%s" % opts.run_mode
            # Build --remote= option
            shcommand += " --remote=uuid=%s" % uuid
            if now_str is not None:
                shcommand += ",now-str=%s" % now_str
            host_confs = [
                "root-dir",
                "root-dir{share}",
                "root-dir{share/cycle}",
                "root-dir{work}"]
            locs_conf.set([auth])
            for key in host_confs:
                value = self._run_conf(key, host=host, conf_tree=conf_tree)
                if value is not None:
                    val = self.popen.list_to_shell_str([str(value)])
                    shcommand += ",%s=%s" % (key, pipes.quote(val))
                    locs_conf.set([auth, key], value)
            command.append(shcommand)
            proc = self.popen.run_bg(*command)
            proc_queue.append([proc, command, "ssh", auth])

        while proc_queue:
            sleep(self.SLEEP_PIPE)
            proc, command, command_name, auth = proc_queue.pop(0)
            if proc.poll() is None:  # put it back in proc_queue
                proc_queue.append([proc, command, command_name, auth])
                continue
            ret_code = proc.wait()
            out, err = proc.communicate()
            ret_code, out, err = [
                i.decode() if isinstance(i, bytes) else i for i in [
                    ret_code, out, err]]
            if ret_code:
                raise RosePopenError(command, ret_code, out, err)
            if command_name == "rsync":
                self.handle_event(out, level=Event.VV)
                continue
            else:
                self.handle_event(out, level=Event.VV, prefix="[%s] " % auth)
            for line in out.split("\n"):
                if "/" + uuid == line.strip():
                    locs_conf.unset([auth])
                    break
            else:
                filters = {"excludes": [], "includes": []}
                for name in ["", "log/", "share/", "share/cycle/", "work/"]:
                    filters["excludes"].append(name + uuid)
                target = auth + ":" + suite_dir_rel
                cmd = self._get_cmd_rsync(target, **filters)
                proc_queue.append(
                    [self.popen.run_bg(*cmd), cmd, "rsync", auth])

        # Install ends
        ConfigDumper()(locs_conf, os.path.join("log", "rose-suite-run.locs"))
        if opts.install_only_mode:
            return
        elif opts.run_mode == "reload" and suite_conf_unchanged:
            conf_name = self.suite_engine_proc.SUITE_CONF
            self.handle_event(SkipReloadEvent(suite_name, conf_name))
            return

        # Start the suite
        self.fs_util.chdir("log")
        self.suite_engine_proc.run(suite_name, opts.host, opts.run_mode, args)

        # Disconnect log file handle, so monitoring tool command will no longer
        # be associated with the log file.
        self.event_handler.contexts[uuid].handle.close()
        self.event_handler.contexts.pop(uuid)

        return 0

    @classmethod
    def _run_conf(
            cls, key, default=None, host=None, conf_tree=None, r_opts=None):
        """Return the value of a setting given by a key for a given host. If
        r_opts is defined, we are already in a remote host, so there is no need
        to do a host match. Otherwise, the setting may be found in the run time
        configuration, or the default (i.e. site/user configuration). The value
        of each setting in the configuration would be in a line delimited list
        of PATTERN=VALUE pairs.
        """
        if r_opts is not None:
            return r_opts.get(key, default)
        if host is None:
            host = "localhost"
        for conf, keys in [
                (conf_tree.node, []),
                (ResourceLocator.default().get_conf(), ["rose-suite-run"])]:
            if conf is None:
                continue
            node_value = conf.get_value(keys + [key])
            if node_value is None:
                continue
            for line in node_value.strip().splitlines():
                pattern, value = line.strip().split("=", 1)
                if (pattern.startswith("jinja2:") or
                        pattern.startswith("empy:")):
                    section, name = pattern.rsplit(":", 1)
                    p_node = conf.get([section, name], no_ignore=True)
                    # Values in "jinja2:*" and "empy:*" sections are quoted.
                    pattern = ast.literal_eval(p_node.value)
                if fnmatchcase(host, pattern):
                    return value.strip()
        return default

    def _run_init_dir(self, opts, suite_name, conf_tree=None, r_opts=None,
                      locs_conf=None):
        """Create the suite's directory."""
        suite_dir_rel = self._suite_dir_rel(suite_name)
        home = os.path.expanduser("~")
        suite_dir_root = self._run_conf("root-dir", conf_tree=conf_tree,
                                        r_opts=r_opts)
        if suite_dir_root:
            if locs_conf is not None:
                locs_conf.set(["localhost", "root-dir"], suite_dir_root)
            suite_dir_root = env_var_process(suite_dir_root)
        suite_dir_home = os.path.join(home, suite_dir_rel)
        if (suite_dir_root and
                os.path.realpath(home) != os.path.realpath(suite_dir_root)):
            suite_dir_real = os.path.join(suite_dir_root, suite_dir_rel)
            self.fs_util.makedirs(suite_dir_real)
            self.fs_util.symlink(suite_dir_real, suite_dir_home,
                                 opts.no_overwrite_mode)
        else:
            self.fs_util.makedirs(suite_dir_home)

    def _run_init_dir_log(self, opts, now_str=None):
        """Create the suite's log/ directory. Housekeep, archive old ones."""
        # Do nothing in log append mode if log directory already exists
        if opts.run_mode in ["reload", "restart"] and os.path.isdir("log"):
            return

        # Log directory of this run
        if now_str is None:
            now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        now_log = "log." + now_str
        self.fs_util.makedirs(now_log)
        self.fs_util.symlink(now_log, "log")
        now_log_name = getattr(opts, "log_name", None)
        if now_log_name:
            self.fs_util.symlink(now_log, "log." + now_log_name)

        # Keep log for this run and named logs
        logs = set(glob("log.*") + ["log"])
        for log in list(logs):
            if os.path.islink(log):
                logs.remove(log)
                log_link = os.readlink(log)
                if log_link in logs:
                    logs.remove(log_link)

        # Housekeep old logs, if necessary
        log_keep = getattr(opts, "log_keep", None)
        if log_keep:
            t_threshold = time() - abs(float(log_keep)) * 86400.0
            for log in list(logs):
                if os.path.isfile(log):
                    if t_threshold > os.stat(log).st_mtime:
                        self.fs_util.delete(log)
                        logs.remove(log)
                else:
                    for root, _, files in os.walk(log):
                        keep = False
                        for file_ in files:
                            path = os.path.join(root, file_)
                            if (os.path.exists(path) and
                                    os.stat(path).st_mtime >= t_threshold):
                                keep = True
                                break
                        if keep:
                            break
                    else:
                        self.fs_util.delete(log)
                        logs.remove(log)

        # Archive old logs, if necessary
        if getattr(opts, "log_archive_mode", True):
            for log in list(logs):
                if os.path.isfile(log):
                    continue
                log_tar_gz = log + ".tar.gz"
                try:
                    self.popen.run_simple("tar", "-czf", log_tar_gz, log)
                except RosePopenError:
                    try:
                        self.fs_util.delete(log_tar_gz)
                    except OSError:
                        pass
                    raise
                else:
                    self.handle_event(SuiteLogArchiveEvent(log_tar_gz, log))
                    self.fs_util.delete(log)

    def _run_init_dir_work(self, opts, suite_name, name, conf_tree=None,
                           r_opts=None, locs_conf=None):
        """Create a named suite's directory."""
        item_path = os.path.realpath(name)
        item_path_source = item_path
        key = "root-dir{" + name + "}"
        item_root = self._run_conf(key, conf_tree=conf_tree, r_opts=r_opts)
        if item_root is None:  # backward compat
            item_root = self._run_conf(
                "root-dir-" + name, conf_tree=conf_tree, r_opts=r_opts)
        if item_root:
            if locs_conf is not None:
                locs_conf.set(["localhost", key], item_root)
            item_root = env_var_process(item_root)
            suite_dir_rel = self._suite_dir_rel(suite_name)
            if os.path.isabs(item_root):
                item_path_source = os.path.join(item_root, suite_dir_rel, name)
            else:
                item_path_source = item_root
            item_path_source = os.path.realpath(item_path_source)
        if item_path == item_path_source:
            if opts.new_mode:
                self.fs_util.delete(name)
            self.fs_util.makedirs(name)
        else:
            if opts.new_mode:
                self.fs_util.delete(item_path_source)
            self.fs_util.makedirs(item_path_source)
            if os.sep in name:
                dirname_of_name = os.path.dirname(name)
                self.fs_util.makedirs(dirname_of_name)
                item_path_source_rel = os.path.relpath(
                    item_path_source, os.path.realpath(dirname_of_name))
            else:
                item_path_source_rel = os.path.relpath(item_path_source)
            if len(item_path_source_rel) < len(item_path_source):
                self.fs_util.symlink(
                    item_path_source_rel, name, opts.no_overwrite_mode)
            else:
                self.fs_util.symlink(
                    item_path_source, name, opts.no_overwrite_mode)

    def _run_remote(self, opts, suite_name):
        """rose suite-run --remote=KEY=VALUE,..."""
        suite_dir_rel = self._suite_dir_rel(suite_name)
        r_opts = {}
        for item in opts.remote.split(","):
            key, val = item.split("=", 1)
            r_opts[key] = val
        uuid_file = os.path.join(suite_dir_rel, r_opts["uuid"])
        if os.path.exists(uuid_file):
            self.handle_event("/" + r_opts["uuid"] + "\n", level=0)
        elif opts.new_mode:
            self.fs_util.delete(suite_dir_rel)
        if opts.run_mode == "run" or not os.path.exists(suite_dir_rel):
            self._run_init_dir(opts, suite_name, r_opts=r_opts)
        os.chdir(suite_dir_rel)
        for name in ["share", "share/cycle", "work"]:
            uuid_file = os.path.join(name, r_opts["uuid"])
            if os.path.exists(uuid_file):
                self.handle_event(name + "/" + r_opts["uuid"] + "\n", level=0)
            else:
                self._run_init_dir_work(opts, suite_name, name, r_opts=r_opts)
        if not opts.install_only_mode:
            uuid_file = os.path.join("log", r_opts["uuid"])
            if os.path.exists(uuid_file):
                self.handle_event("log/" + r_opts["uuid"] + "\n", level=0)
            else:
                self._run_init_dir_log(opts, r_opts.get("now-str"))
        self.fs_util.makedirs("log/suite")

    def _get_cmd_rsync(self, target, excludes=None, includes=None):
        """rsync relevant suite items to target."""
        if excludes is None:
            excludes = []
        if includes is None:
            includes = []
        cmd = self.popen.get_cmd("rsync")
        for exclude in excludes + list(self.SYNC_EXCLUDES):
            cmd.append("--exclude=" + exclude)
        for include in includes:
            cmd.append("--include=" + include)
        cmd.append("./")
        cmd.append(target)
        return cmd

    def _suite_dir_rel(self, suite_name):
        """Return the relative path to the suite running directory."""
        return self.suite_engine_proc.get_suite_dir_rel(suite_name)


def main():
    """Launcher for the CLI."""
    opt_parser = RoseOptionParser()
    option_keys = SuiteRunner.OPTIONS
    opt_parser.add_my_options(*option_keys)
    opts, args = opt_parser.parse_args(sys.argv[1:])
    event_handler = Reporter(opts.verbosity - opts.quietness)
    runner = SuiteRunner(event_handler)
    try:
        sys.exit(runner(opts, args))
    except Exception as exc:
        runner.handle_event(exc)
        if opts.debug_mode:
            traceback.print_exc()
        if isinstance(exc, RosePopenError):
            sys.exit(exc.ret_code)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
