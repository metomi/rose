# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
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
#-----------------------------------------------------------------------------
"""Implement "rose suite-run"."""

import ast
from datetime import datetime
from fnmatch import fnmatchcase
from glob import glob
import os
import re
from rose.config import ConfigDumper, ConfigLoader, ConfigNode
from rose.config_tree import ConfigTreeLoader
from rose.env import env_var_process
from rose.host_select import HostSelector
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopenError
from rose.reporter import Event, Reporter, ReporterContext
from rose.resource import ResourceLocator
from rose.run import ConfigValueError, NewModeError, Runner
from rose.run_source_vc import write_source_vc_info
from rose.suite_clean import SuiteRunCleaner
from rose.suite_engine_proc import StillRunningError
import socket
import sys
import tarfile
from tempfile import TemporaryFile
from time import sleep, strftime, time
import traceback


class NotRunningError(Exception):

    """An exception raised when a suite is not running."""

    def __str__(self):
        return "%s: is not running" % (self.args)


class VersionMismatchError(Exception):

    """An exception raised when there is a version mismatch."""

    def __str__(self):
        return "Version expected=%s, actual=%s" % self.args


class SuiteHostSelectEvent(Event):

    """An event raised to report the host for running a suite."""

    def __str__(self):
        return "%s: will %s on %s" % self.args


class SuiteLogArchiveEvent(Event):

    """An event raised to report the archiving of a suite log directory."""

    def __str__(self):
        return "%s <= %s" % self.args


class SuiteRunner(Runner):

    """Invoke a Rose suite."""

    SLEEP_PIPE = 0.05
    NAME = "suite"
    OPTIONS = ["conf_dir", "defines", "defines_suite", "gcontrol_mode", "host",
               "install_only_mode", "local_install_only_mode",
               "log_archive_mode", "log_keep", "log_name", "name", "new_mode",
               "no_overwrite_mode", "opt_conf_keys", "reload_mode", "remote",
               "restart_mode", "run_mode", "strict_mode"]

    REC_DONT_SYNC = re.compile(
            r"\A(?:\..*|cylc-suite\.db.*|log(?:\..*)*|state|share|work)\Z")

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
            f = TemporaryFile()
            log_context = ReporterContext(None, self.event_handler.VV, f)
            self.event_handler.contexts[uuid] = log_context

        # Check suite engine specific compatibility
        self.suite_engine_proc.check_global_conf_compat()

        # Suite name from the current working directory
        if opts.conf_dir:
            self.fs_util.chdir(opts.conf_dir)
        opts.conf_dir = os.getcwd()

        if opts.defines_suite:
            suite_section = "jinja2:" + self.suite_engine_proc.SUITE_CONF
            if not opts.defines:
                opts.defines = []
            for define in opts.defines_suite:
                opts.defines.append("[" + suite_section + "]" + define)

        # --remote=KEY=VALUE,...
        if opts.remote:
            # opts.name always set for remote.
            return self._run_remote(opts, opts.name)

        conf_tree = self.config_load(opts)
        self.fs_util.chdir(conf_tree.conf_dirs[0])

        suite_name = opts.name
        if not opts.name:
            suite_name = os.path.basename(os.getcwd())

        # Automatic Rose constants
        # ROSE_ORIG_HOST: originating host
        # ROSE_VERSION: Rose version (not retained in run_mode=="reload")
        # Suite engine version
        jinja2_section = "jinja2:" + self.suite_engine_proc.SUITE_CONF
        my_rose_version = ResourceLocator.default().get_version()
        suite_engine_key = self.suite_engine_proc.get_version_env_name()
        if opts.run_mode == "reload":
            prev_config_path = self.suite_engine_proc.get_suite_dir(
                    suite_name, "log", "rose-suite-run.conf")
            prev_config = ConfigLoader()(prev_config_path)
            suite_engine_version = prev_config.get_value(
                    ["env", suite_engine_key])
        else:
            suite_engine_version = self.suite_engine_proc.get_version()
        auto_items = {"ROSE_ORIG_HOST": socket.gethostname(),
                      "ROSE_VERSION": ResourceLocator.default().get_version(),
                      suite_engine_key: suite_engine_version}
        for k, v in auto_items.items():
            requested_value = conf_tree.node.get_value(["env", k])
            if requested_value:
                if k == "ROSE_VERSION" and v != requested_value:
                    e = VersionMismatchError(requested_value, v)
                    raise ConfigValueError(["env", k], requested_value, e)
                v = requested_value
            else:
                conf_tree.node.set(["env", k], v)
            conf_tree.node.set([jinja2_section, k], '"' + v + '"')

        # See if suite is running or not
        hosts = []
        if opts.host:
            hosts.append(opts.host)
        conf = ResourceLocator.default().get_conf()

        known_hosts = self.host_selector.expand(
              conf.get_value(["rose-suite-run", "hosts"], "").split() +
              conf.get_value(["rose-suite-run", "scan-hosts"], "").split() +
              ["localhost"])[0]
        known_hosts = list(set(known_hosts))

        for known_host in known_hosts:
            if known_host not in hosts:
                hosts.append(known_host)
        if opts.run_mode == "reload":
            suite_run_hosts = self.suite_engine_proc.ping(suite_name, hosts)
            if not suite_run_hosts:
                raise NotRunningError(suite_name)
            hosts = suite_run_hosts
        else:
            reason = self.suite_engine_proc.is_suite_running(
                        None, suite_name, hosts)
            if reason:
                raise StillRunningError(suite_name, reason)

        # Install the suite to its run location
        # TODO: files from inherited locations
        suite_dir_rel = self._suite_dir_rel(suite_name)
        suite_dir = os.path.join(os.path.expanduser("~"), suite_dir_rel)

        suite_conf_dir = os.getcwd()
        locs_conf = ConfigNode()
        if opts.new_mode:
            if os.getcwd() == suite_dir:
                raise NewModeError("PWD", os.getcwd())
            elif opts.run_mode in ["reload", "restart"]:
                raise NewModeError("--run", opts.run_mode)
            self.suite_run_cleaner.clean(suite_name)
        if os.getcwd() != suite_dir:
            self._run_init_dir(opts, suite_name, conf_tree,
                               locs_conf=locs_conf)
            os.chdir(suite_dir)
        cwd = os.getcwd()
        for rel_path, conf_dir in conf_tree.files.items():
            if conf_dir == cwd or self.REC_DONT_SYNC.match(rel_path):
                continue
            self.fs_util.copy2(os.path.join(conf_dir, rel_path), rel_path)

        # Housekeep log files
        if not opts.install_only_mode and not opts.local_install_only_mode:
            self._run_init_dir_log(opts, suite_name, conf_tree)
        self.fs_util.makedirs("log/suite")

        # Rose configuration and version logs
        self.fs_util.makedirs("log/rose-conf")
        run_mode = opts.run_mode
        if run_mode not in ["reload", "restart", "run"]:
            run_mode = "run"
        mode = run_mode
        if opts.install_only_mode:
            mode = "install-only"
        elif opts.local_install_only_mode:
            mode = "local-install-only"
        prefix = "rose-conf/%s-%s" % (strftime("%Y%m%dT%H%M%S"), mode)

        # Dump the actual configuration as rose-suite-run.conf
        ConfigDumper()(conf_tree.node, "log/" + prefix + ".conf")

        # Install version information file
        write_source_vc_info(
                suite_conf_dir, "log/" + prefix + ".version", self.popen)

        # If run through rose-stem, install version information files for
        # each source tree if they're a working copy
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

        # Create the suite log view
        self.suite_engine_proc.job_logs_db_create(suite_name, close=True)

        # Install share/work directories (local)
        for name in ["share", "work"]:
            self._run_init_dir_work(opts, suite_name, name, conf_tree,
                                    locs_conf=locs_conf)
            # TODO: locs_conf.set(["localhost", ])

        # Process Environment Variables
        environ = self.config_pm(conf_tree, "env")

        # Process Files
        self.config_pm(conf_tree, "file",
                       no_overwrite_mode=opts.no_overwrite_mode)

        # Process Jinja2 configuration
        self.config_pm(conf_tree, "jinja2")

        # Register the suite
        self.suite_engine_proc.validate(suite_name, opts.strict_mode,
                                        opts.debug_mode)

        if opts.local_install_only_mode:
            return

        # Install suite files to each remote [user@]host
        for name in ["", "log/", "share/", "work/"]:
            uuid_file = os.path.abspath(name + uuid)
            open(uuid_file, "w").close()
            work_files.append(uuid_file)

        # Install items to user@host
        auths = self.suite_engine_proc.get_tasks_auths(suite_name)
        queue = [] # [[pipe, command, "ssh"|"rsync", auth], ...]
        for auth in sorted(auths):
            host = auth
            if "@" in auth:
                host = auth.split("@", 1)[1]
            command = self.popen.get_cmd("ssh", auth, "bash", "--login", "-c")
            rose_bin = "rose"
            for h in [host, "*"]:
                rose_home_node = conf.get(["rose-home-at", h],
                                          no_ignore=True)
                if rose_home_node is not None:
                    rose_bin = "%s/bin/rose" % (rose_home_node.value)
                    break
            # Build remote "rose suite-run" command
            rose_sr = "ROSE_VERSION=%s %s" % (my_rose_version, rose_bin)
            rose_sr += " suite-run -v -v --name=%s" % suite_name
            for key in ["new", "debug", "install-only"]:
                attr = key.replace("-", "_") + "_mode"
                if getattr(opts, attr, None) is not None:
                    rose_sr += " --" + key
            if opts.log_keep:
                rose_sr += " --log-keep=" + opts.log_keep
            if opts.log_name:
                rose_sr += " --log-name=" + opts.log_name
            if not opts.log_archive_mode:
                rose_sr += " --no-log-archive"
            rose_sr += " --run=" + opts.run_mode
            host_confs = ["root-dir", "root-dir-share", "root-dir-work"]
            rose_sr += " --remote=uuid=" + uuid
            locs_conf.set([auth])
            for key in host_confs:
                value = self._run_conf(key, host=host, conf_tree=conf_tree)
                if value is not None:
                    v = self.popen.list_to_shell_str([str(value)])
                    rose_sr += "," + key + "=" + v
                    locs_conf.set([auth, key], value)
            command += ["'" + rose_sr + "'"]
            pipe = self.popen.run_bg(*command)
            queue.append([pipe, command, "ssh", auth])

        while queue:
            sleep(self.SLEEP_PIPE)
            pipe, command, command_name, auth = queue.pop(0)
            if pipe.poll() is None:
                queue.append([pipe, command, command_name, auth]) # put it back
                continue
            rc = pipe.wait()
            out, err = pipe.communicate()
            if rc:
                raise RosePopenError(command, rc, out, err)
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
                for name in ["", "log/", "share/", "work/"]:
                    filters["excludes"].append(name + uuid)
                target = auth + ":" + suite_dir_rel
                cmd = self._get_cmd_rsync(target, **filters)
                queue.append([self.popen.run_bg(*cmd), cmd, "rsync", auth])

        # Install ends
        ConfigDumper()(locs_conf, os.path.join("log", "rose-suite-run.locs"))
        if opts.install_only_mode:
            return

        # Start the suite
        self.fs_util.chdir("log")
        ret = 0
        host = hosts[0]
        # FIXME: should sync files to suite host?
        if opts.host:
            hosts = [host]

        # For run and restart, get host for running the suite
        if opts.run_mode != "reload" and not opts.host:
            hosts = []
            v = conf.get_value(["rose-suite-run", "hosts"], "localhost")
            known_hosts = self.host_selector.expand(v.split())[0]
            for known_host in known_hosts:
                if known_host not in hosts:
                    hosts.append(known_host)

        if hosts == ["localhost"]:
            host = hosts[0]
        else:
            host = self.host_selector(hosts)[0][0]
        self.handle_event(SuiteHostSelectEvent(suite_name, run_mode, host))
        # FIXME: values in environ were expanded in the localhost
        self.suite_engine_proc.run(
                suite_name, host, environ, opts.run_mode, args)
        open("rose-suite-run.host", "w").write(host + "\n")

        # Launch the monitoring tool
        # Note: maybe use os.ttyname(sys.stdout.fileno())?
        if os.getenv("DISPLAY") and host and opts.gcontrol_mode:
            self.suite_engine_proc.gcontrol(suite_name, host)

        return ret

    def _run_conf(
            self, key, default=None, host=None, conf_tree=None, r_opts=None):
        """Return the value of a setting given by a key for a given host. If
        r_opts is defined, we are alerady in a remote host, so there is no need
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
                if pattern.startswith("jinja2:"):
                    section, key = pattern.rsplit(":", 1)
                    p_node = conf.get([section, key], no_ignore=True)
                    # Values in "jinja2:*" section are quoted.
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

    def _run_init_dir_log(self, opts, suite_name, conf_tree=None, r_opts=None):
        """Create the suite's log/ directory. Housekeep, archive old ones."""
        # Do nothing in log append mode if log directory already exists
        if opts.run_mode in ["reload", "restart"] and os.path.isdir("log"):
            return

        # Log directory of this run
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
            t = time() - abs(float(log_keep)) * 86400.0
            for log in list(logs):
                if os.path.isfile(log):
                    if t > os.stat(log).st_mtime:
                        self.fs_util.delete(log)
                        logs.remove(log)
                else:
                    for root, dirs, files in os.walk(log):
                        keep = False
                        for file in files:
                            path = os.path.join(root, file)
                            if (os.path.exists(path) and
                                os.stat(path).st_mtime >= t):
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
                log_tar = log + ".tar"
                f_bsize = os.statvfs(log).f_bsize
                f = tarfile.open(log_tar, "w", bufsize=f_bsize)
                f.add(log)
                f.close()
                # N.B. Python's gzip is slow
                self.popen.run_simple("gzip", log_tar)
                self.handle_event(SuiteLogArchiveEvent(log_tar + ".gz", log))
                self.fs_util.delete(log)

    def _run_init_dir_work(self, opts, suite_name, name, conf_tree=None,
                           r_opts=None, locs_conf=None):
        """Create a named suite's directory."""
        item_path = os.path.realpath(name)
        item_path_source = item_path
        key = "root-dir-" + name
        item_root = self._run_conf(key, conf_tree=conf_tree, r_opts=r_opts)
        if item_root is not None:
            if locs_conf is not None:
                locs_conf.set(["localhost", key], item_root)
            item_root = env_var_process(item_root)
            suite_dir_rel = self._suite_dir_rel(suite_name)
            item_path_source = os.path.join(item_root, suite_dir_rel, name)
            item_path_source = os.path.realpath(item_path_source)
        if item_path == item_path_source:
            if opts.new_mode:
                self.fs_util.delete(name)
            self.fs_util.makedirs(name)
        else:
            if opts.new_mode:
                self.fs_util.delete(item_path_source)
            self.fs_util.makedirs(item_path_source)
            self.fs_util.symlink(item_path_source, name, opts.no_overwrite_mode)

    def _run_remote(self, opts, suite_name):
        """rose suite-run --remote=KEY=VALUE,..."""
        suite_dir_rel = self._suite_dir_rel(suite_name)
        r_opts = {}
        for item in opts.remote.split(","):
            k, v = item.split("=", 1)
            r_opts[k] = v
        uuid_file = os.path.join(suite_dir_rel, r_opts["uuid"])
        if os.path.exists(uuid_file):
            self.handle_event("/" + r_opts["uuid"] + "\n", level=0)
        elif opts.new_mode:
            self.fs_util.delete(suite_dir_rel)
        self._run_init_dir(opts, suite_name, r_opts=r_opts)
        os.chdir(suite_dir_rel)
        for name in ["share", "work"]:
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
                self._run_init_dir_log(opts, suite_name, r_opts=r_opts)
        self.fs_util.makedirs("log/suite")

    def _get_cmd_rsync(self, target, excludes=None, includes=None):
        """rsync relevant suite items to target."""
        if excludes is None:
            excludes = []
        if includes is None:
            includes = []
        c = self.popen.get_cmd("rsync", "--delete-excluded")
        for exclude in excludes:
            c.append("--exclude=" + exclude)
        for include in includes:
            c.append("--include=" + include)
        for item in os.listdir("."):
            if not self.REC_DONT_SYNC.match(item) or item in excludes:
                c.append(item)
        c.append(target)
        return c

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
    except Exception as e:
        runner.handle_event(e)
        if opts.debug_mode:
            traceback.print_exc(e)
        if isinstance(e, RosePopenError):
            sys.exit(e.rc)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
