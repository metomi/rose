# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
"""Process "file:*" sections in a rose.config.ConfigNode."""

from fnmatch import fnmatch
from hashlib import md5
from multiprocessing import Pool
import os
import re
from rose.checksum import get_checksum
import rose.config
from rose.config_processor import ConfigProcessError, ConfigProcessorBase
from rose.reporter import Event
from rose.resource import ResourceLocator
from rose.scheme_handler import SchemeHandlersManager
import shlex
from shutil import rmtree
import sqlite3
import sys
from tempfile import mkdtemp
from time import sleep
from urlparse import urlparse


class ConfigProcessorForFile(ConfigProcessorBase):
    """Processor for "file:*" sections in a rose.config.ConfigNode."""

    SCHEME = "file"

    def __init__(self, *args, **kwargs):
        ConfigProcessorBase.__init__(self, *args, **kwargs)
        self.loc_handlers_manager = PullableLocHandlersManager(
                event_handler=self.manager.event_handler,
                popen=self.manager.popen,
                fs_util=self.manager.fs_util)
        self.loc_dao = LocDAO()

    def handle_event(self, *args):
        """Invoke event handler with *args, if there is one."""
        self.manager.handle_event(*args)

    def process(self, config, item, orig_keys=None, orig_value=None, **kwargs):
        """Install files according to the file:* sections in "config"."""

        # Find all the "file:*" nodes.
        nodes = {}
        if item == self.SCHEME:
            for key, node in config.value.items():
                if node.is_ignored() or not key.startswith(self.PREFIX):
                    continue
                nodes[key] = node
        else:
            node = config.get([item], no_ignore=True)
            if node is None:
                raise ConfigProcessError(orig_keys, item)
            nodes[item] = node

        if not nodes:
            return

        # Ensure that everything is overwritable
        # Ensure that container directories exist
        for key, node in sorted(nodes.items()):
            name = key[len(self.PREFIX):]
            if os.path.exists(name) and kwargs.get("no_overwrite_mode"):
                e = FileOverwriteError(name)
                raise ConfigProcessError([key], None, e)
            self.manager.fs_util.makedirs(self.manager.fs_util.dirname(name))

        # Create database to store information for incremental updates,
        # if it does not already exist.
        self.loc_dao.create()

        # Gets a list of sources and targets
        sources = {}
        targets = {}
        for key, node in sorted(nodes.items()):
            source_str = node.get_value(["source"])
            name = key[len(self.PREFIX):]
            target_sources = []
            if source_str is not None:
                for source_name in shlex.split(source_str):
                    if not sources.has_key(source_name):
                        sources[source_name] = Loc(source_name)
                    sources[source_name].used_by_names.append(name)
                    target_sources.append(sources[source_name])
            targets[name] = Loc(name)
            targets[name].dep_locs = target_sources
            targets[name].mode = node.get_value(["mode"])

        # Determine the scheme of the location from configuration.
        config_schemes_str = config.get_value(["schemes"])
        config_schemes = [] # [(pattern, scheme), ...]
        if config_schemes_str:
            for line in config_schemes_str.splitlines():
                p, s = line.split("=", 1)
                p = p.strip()
                s = s.strip()
                config_schemes.append((p, s))

        # Where applicable, determine for each source:
        # * Its real name.
        # * The checksums of its paths.
        # * Whether it can be considered unchanged.
        for source in sources.values():
            try:
                for p, s in config_schemes:
                    if fnmatch(source.name, p):
                        source.scheme = s
                        break
                self.loc_handlers_manager.parse(source, config)
            except ValueError as e:
                raise ConfigProcessError([key, "source"], source.name, e)
            prev_source = self.loc_dao.select(source.name)
            source.is_out_of_date = (
                    not prev_source or
                    (not source.key and not source.paths) or
                    prev_source.scheme != source.scheme or
                    prev_source.loc_type != source.loc_type or
                    prev_source.key != source.key or
                    sorted(prev_source.paths) != sorted(source.paths))

        # Inspect each target to see if it is out of date:
        # * Target does not already exist.
        # * Target exists, but does not have a database entry.
        # * Target exists, but does not match settings in database.
        # * Target exists, but a source cannot be considered unchanged.
        for target in targets.values():
            if os.path.islink(target.name):
                target.real_name = os.readlink(target.name)
            elif os.path.exists(target.name):
                for path, checksum in get_checksum(target.name):
                    target.add_path(path, checksum)
                target.paths.sort()
            prev_target = self.loc_dao.select(target.name)
            target.is_out_of_date = (
                    not os.path.exists(target.name) or
                    prev_target is None or
                    prev_target.mode != target.mode or
                    prev_target.real_name != target.real_name or
                    len(prev_target.paths) != len(target.paths))
            if not target.is_out_of_date:
                for prev_path, path in zip(prev_target.paths, target.paths):
                    if prev_path != path:
                        target.is_out_of_date = True
                        break
            if not target.is_out_of_date:
                for dep_loc in target.dep_locs:
                    if dep_loc.is_out_of_date:
                        target.is_out_of_date = True
                        break
            if target.is_out_of_date:
                target.paths = None
                self.loc_dao.delete(target)

        # Set up jobs for rebuilding all out-of-date targets.
        jobs = {}
        for target in targets.values():
            if not target.is_out_of_date:
                continue
            if target.dep_locs:
                if len(target.dep_locs) == 1 and target.mode == "symlink":
                    self.manager.fs_util.symlink(target.dep_locs[0], target.name)
                    self.loc_dao.update(target)
                else:
                    jobs[target.name] = JobProxy(target, JobProxy.INSTALL)
                    for source in target.dep_locs:
                        if not jobs.has_key(source.name):
                            jobs[source.name] = JobProxy(source, JobProxy.PULL)
                        job = jobs[source.name]
                        jobs[target.name].pending_for[source.name] = job
            elif target.mode == "mkdir":
                self.manager.fs_util.makedirs(target.name)
                self.loc_dao.update(target)
                target.loc_type = target.TYPE_TREE
                target.add_path(target.BLOB, None)
            else:
                self.manager.fs_util.install(target.name)
                self.loc_dao.update(target)
                target.loc_type = target.TYPE_BLOB
                for path, checksum in get_checksum(target.name):
                    target.add_path(path, checksum)

        if jobs:
            work_dir = mkdtemp()
            try:
                JobRunner(self)(JobManager(jobs), config, work_dir)
            except ValueError as e:
                if e.args and jobs.has_key(e.args[0]):
                    job = jobs[e.args[0]]
                    if job.action_key == job.PULL:
                        source = job.loc
                        keys = [self.PREFIX + source.used_by_names[0], "source"]
                        raise ConfigProcessError(keys, source.name)
                raise e
            finally:
                rmtree(work_dir)

        # Target checksum compare and report
        for target in targets.values():
            if not target.is_out_of_date or target.loc_type == target.TYPE_TREE:
                continue
            keys = [self.PREFIX + target.name, "checksum"]
            checksum_expected = config.get_value(keys)
            if checksum_expected is None:
                continue
            checksum = target.paths[0].checksum
            if checksum_expected and checksum_expected != checksum:
                e = ChecksumError(checksum_expected, checksum)
                raise ConfigProcessError(keys, checksum_expected, e)
            event = ChecksumEvent(target.name, checksum)
            self.handle_event(event)

    def process_job(self, job, config, work_dir):
        """Process a job, helper for "process"."""
        for key, method in [(job.INSTALL, self._target_install),
                            (job.PULL, self._source_pull)]:
            if job.action_key == key:
                return method(job.loc, config, work_dir)

    def post_process_job(self, job, config, *args):
        """Post-process a successful job, helper for "process"."""
        # TODO: auto decompression of tar, gzip, etc?
        self.loc_dao.update(job.loc)

    def set_event_handler(self, event_handler):
        """Sets the event handler, used by pool workers to capture events."""
        try:
            self.manager.event_handler.event_handler = event_handler
        except AttributeError:
            pass

    def _source_pull(self, source, config, work_dir):
        """Pulls a source to its cache in the work directory."""
        m = md5()
        m.update(source.name)
        source.cache = os.path.join(work_dir, m.hexdigest())
        return self.loc_handlers_manager.pull(source, config)

    def _target_install(self, target, config, work_dir):
        """Install target.

        Build target using its source(s).
        Calculate the checksum(s) of (paths in) target.

        """
        f = None
        is_first = True
        # Install target
        for source in target.dep_locs:
            if target.loc_type is None:
                target.loc_type = source.loc_type
            elif target.loc_type != source.loc_type:
                raise LocTypeError(target.name, source.name, target.loc_type,
                                   source.loc_type)
            if target.loc_type == target.TYPE_BLOB:
                if f is None:
                    if os.path.isdir(target.name):
                        self.manager.fs_util.delete(target.name)
                    f = open(target.name, "wb")
                f.write(open(source.cache).read())
            else: # target.loc_type == target.TYPE_TREE
                args = []
                if is_first:
                    self.manager.fs_util.makedirs(target.name)
                    args.append("--delete-excluded")
                args.extend(["--checksum", source.cache + "/", target.name])
                cmd = self.manager.popen.get_cmd("rsync", *args)
                out, err = self.manager.popen(*cmd)
            is_first = False
        if f is not None:
            f.close()

        # Calculate target checksum(s)
        for path, checksum in get_checksum(target.name):
            target.add_path(path, checksum)


class ChecksumError(Exception):
    """An exception raised on an unmatched checksum."""
    def __str__(self):
        return ("Unmatched checksum, expected=%s, actual=%s" % tuple(self))


class ChecksumEvent(Event):
    """Report the checksum of a file."""
    def __str__(self):
        return "checksum: %s: %s" % self.args


class FileOverwriteError(Exception):
    """An exception raised in an attempt to overwrite an existing file.

    This will only be raised in non-overwrite mode.

    """
    def __str__(self):
        return ("%s: file already exists (and in no-overwrite mode)" %
                self.args[0])


class JobEvent(Event):
    """Event raised when a job completes."""
    def __init__(self, job):
        Event.__init__(self, job)
        if job.action_key == job.PULL:
            self.level = Event.V

    def __str__(self):
        return str(self.args[0])


class JobManager(object):
    """Manage a set of JobProxy objects and their states."""

    def __init__(self, jobs, names=None):
        """Initiate a location job manager.

        jobs: A dict of all available jobs (job.name, job).
        names: A list of keys in jobs to process.
               If not set or empty, process all jobs.

        """
        self.jobs = jobs
        self.ready_jobs = []
        if not names:
            names = jobs.keys()
        for name in names:
            self.ready_jobs.append(self.jobs[name])
        self.working_jobs = {}

    def get_job(self):
        """Return the next job that requires processing."""
        while self.ready_jobs:
            job = self.ready_jobs.pop()
            for dep_key, dep_job in job.pending_for.items():
                if dep_job.state == dep_job.ST_DONE:
                    job.pending_for.pop(dep_key)
                    if dep_job.needed_by.has_key(job.name):
                        dep_job.needed_by.pop(job.name)
                else:
                    dep_job.needed_by[job.name] = job
                    if dep_job.state is None:
                        dep_job.state = dep_job.ST_READY
                        self.ready_jobs.append(dep_job)
            if job.pending_for:
                job.state = job.ST_PENDING
            else:
                self.working_jobs[job.name] = job
                job.state = job.ST_WORKING
                return job

    def get_dead_jobs(self):
        """Return pending jobs if there are no ready/working ones."""
        if not self.has_jobs:
            jobs = []
            for job in self.jobs.values():
                if job.pending_for:
                    jobs.append(job)
            return jobs

    def has_jobs(self):
        """Return True if there are ready jobs or working jobs."""
        return (bool(self.ready_jobs) or bool(self.working_jobs))

    def has_ready_jobs(self):
        """Return True if there are ready jobs."""
        return bool(self.ready_jobs)

    def put_job(self, job_proxy):
        """Tell the manager that a job has completed."""
        job = self.working_jobs.pop(job_proxy.name)
        job.update(job_proxy)
        job.state = job.ST_DONE
        for up_key, up_job in job.needed_by.items():
            job.needed_by.pop(up_key)
            up_job.pending_for.pop(job.name)
            if not up_job.pending_for:
                self.ready_jobs.append(up_job)
                up_job.state = up_job.ST_READY
        return job


class JobProxy(object):
    """Represent the state of the job for updating a location."""

    INSTALL = "install"
    PULL = "pull"

    ST_DONE = "ST_DONE"
    #ST_FAILED = "ST_FAILED"
    ST_PENDING = "ST_PENDING"
    ST_READY = "ST_READY"
    ST_WORKING = "ST_WORKING"

    def __init__(self, loc, action_key):
        self.loc = loc
        self.action_key = action_key
        self.name = loc.name
        self.needed_by = {}
        self.pending_for = {}
        self.state = self.ST_READY

    def __str__(self):
        return "%s: %s" % (self.action_key, str(self.loc))

    def update(self, other):
        """Update self.loc and self.state with the values of "other"."""
        self.loc.update(other.loc)


class JobRunner(object):
    """Runs JobProxy objects with pool of workers."""

    NPROC = 6
    POLL_DELAY = 0.05

    def __init__(self, job_processor):
        self.job_processor = job_processor
        conf = ResourceLocator.default().get_conf()
        self.nproc = int(conf.get_value(
                ["rose.config_processors.file", "nproc"],
                default=self.NPROC))

    def run(self, job_manager, *args):
        """Start the job runner with an instance of JobManager."""
        nproc = self.nproc
        if nproc > len(job_manager.jobs):
            nproc = len(job_manager.jobs)
        pool = Pool(processes=nproc)

        results = {}
        while job_manager.has_jobs():
            # Process results, if any is ready
            for name, result in results.items():
                if result.ready():
                    results.pop(name)
                    job_proxy, args_of_events = result.get()
                    for args_of_event in args_of_events:
                        self.job_processor.handle_event(*args_of_event)
                    job = job_manager.put_job(job_proxy)
                    self.job_processor.post_process_job(job, *args)
                    self.job_processor.handle_event(JobEvent(job))
            # Add some more jobs into the worker pool, as they are ready
            while job_manager.has_ready_jobs():
                job = job_manager.get_job()
                if job is None:
                    break
                loc_job_run_args = [self.job_processor, job] + list(args)
                result = pool.apply_async(_job_run, loc_job_run_args)
                results[job.name] = result
            if results:
                sleep(self.POLL_DELAY)

        dead_jobs = job_manager.get_dead_jobs()
        if dead_jobs:
            raise JobRunnerNotCompletedError(dead_jobs)

    __call__ = run


def _job_run(job_processor, job_proxy, *args):
    """Helper for JobRunner."""
    event_handler = JobRunnerWorkerEventHandler()
    job_processor.set_event_handler(event_handler)
    try:
        job_processor.process_job(job_proxy, *args)
    except Exception as e:
        #import traceback
        #traceback.print_exc(e)
        raise e
    finally:
        job_processor.set_event_handler(None)
    return (job_proxy, event_handler.events)


class JobRunnerWorkerEventHandler(object):
    """Temporary event handler in a function run by a pool worker process.

    Events are collected in the self.events which is a list of tuples
    representing the arguments the report method in an instance of
    rose.reporter.Reporter.

    """
    def __init__(self):
        self.events = []

    def __call__(self, message, type=None, level=None, prefix=None, clip=None):
        self.events.append((message, type, level, prefix, clip))


class JobRunnerNotCompletedError(Exception):
    """Error raised when there are no ready/working jobs but pending ones."""
    def __str__(self):
        ret = ""
        for job in self.args:
            ret += "[DEAD TASK] %s\n" % str(job)
        return ret


class Loc(object):
    """Represent a location."""

    BLOB = ""
    TYPE_TREE = "tree"
    TYPE_BLOB = "blob"

    def __init__(self, name, scheme=None, dep_locs=None):
        self.name = name
        self.real_name = None
        self.scheme = scheme
        self.dep_locs = dep_locs
        self.mode = None
        self.loc_type = None
        self.paths = None
        self.key = None
        self.cache = None
        self.used_by_names = []
        self.is_out_of_date = None # boolean

    def __str__(self):
        ret = self.name
        if self.real_name and self.real_name != self.name:
            ret = "%s (%s)" % (self.real_name, self.name)
        if self.dep_locs:
            for dep_loc in self.dep_locs:
                ret += "\n    source: %s" % str(dep_loc)
        return ret

    def add_path(self, *args):
        """Create and append a LocSubPath(*args) to this location."""
        if self.paths is None:
            self.paths = []
        self.paths.append(LocSubPath(*args))

    def update(self, other):
        """Update the values of this location with the values of "other"."""
        self.name = other.name
        self.real_name = other.real_name
        self.scheme = other.scheme
        self.mode = other.mode
        self.paths = other.paths
        self.key = other.key
        self.cache = other.cache
        self.is_out_of_date = other.is_out_of_date


class LocTypeError(Exception):
    """An exception raised when a location type is incorrect.

    The location type is either a file blob or a directory tree.

    """
    def __str__(self):
        return "%s <= %s, expected %s, got %s" % self.args


class LocSubPath(object):
    """Represent a sub-path in a location."""

    def __init__(self, name, checksum=None):
        self.name = name
        self.checksum = checksum

    def __cmp__(self, other):
        return cmp(self.name, other.name) or cmp(self.checksum, other.checksum)

    def __eq__(self, other):
        return (self.name == other.name and self.checksum == other.checksum)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.name


class LocDAO(object):
    """DAO for information for incremental updates."""

    DB_FILE_NAME = ".rose-config_processors-file.db"

    def __init__(self):
        self.conn = None

    def get_conn(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.DB_FILE_NAME)
        return self.conn

    def create(self):
        """Create the database file if it does not exist."""
        if not os.path.exists(self.DB_FILE_NAME):
            conn = self.get_conn()
            c = conn.cursor()
            c.execute("""CREATE TABLE locs(
                          name TEXT,
                          real_name TEXT,
                          scheme TEXT,
                          mode TEXT,
                          loc_type TEXT,
                          key TEXT,
                          PRIMARY KEY(name))""")
            c.execute("""CREATE TABLE paths(
                          name TEXT,
                          path TEXT,
                          checksum TEXT,
                          UNIQUE(name, path))""")
            c.execute("""CREATE TABLE dep_names(
                          name TEXT,
                          dep_name TEXT,
                          UNIQUE(name, dep_name))""")
            conn.commit()

    def delete(self, loc):
        """Remove settings related to loc from the database."""
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("""DELETE FROM locs WHERE name=?""", [loc.name])
        c.execute("""DELETE FROM dep_names WHERE name=?""", [loc.name])
        c.execute("""DELETE FROM paths WHERE name=?""", [loc.name])
        conn.commit()

    def select(self, name):
        """Query database for settings matching name.
        
        Reconstruct setting as a Loc object and return it.
 
        """
        conn = self.get_conn()
        c = conn.cursor()

        c.execute("""SELECT real_name,scheme,mode,loc_type,key FROM locs""" +
                  """ WHERE name=?""", [name])
        row = c.fetchone()
        if row is None:
            return
        loc = Loc(name)
        loc.real_name, loc.scheme, loc.mode, loc.loc_type, loc.key = row

        c.execute("""SELECT path,checksum FROM paths WHERE name=?""", [name])
        for row in c:
            path, checksum = row
            if loc.paths is None:
                loc.paths = []
            loc.add_path(path, checksum)

        c.execute("""SELECT dep_name FROM dep_names WHERE name=?""", [name])
        for row in c:
            dep_name, = row
            if loc.dep_locs is None:
                loc.dep_locs = []
            loc.dep_locs.append(self.select(dep_name))

        return loc

    def update(self, loc):
        """Insert or update settings related to loc to the database."""
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO locs VALUES(?,?,?,?,?,?)""",
                  [loc.name, loc.real_name, loc.scheme, loc.mode, loc.loc_type,
                   loc.key])
        if loc.paths:
            for path in loc.paths:
                c.execute("""INSERT OR REPLACE INTO paths VALUES(?,?,?)""",
                          [loc.name, path.name, path.checksum])
        if loc.dep_locs:
            for dep_loc in loc.dep_locs:
                c.execute("""INSERT OR REPLACE INTO dep_names VALUES(?,?)""",
                          [loc.name, dep_loc.name])
        conn.commit()


class PullableLocHandlersManager(SchemeHandlersManager):
    """Manage location handlers.

    Each location handler should have a SCHEME set to a unique string, the
    "can_handle" method, the "parse" method and the "pull" methods.

    """

    DEFAULT_SCHEME = "fs"

    def __init__(self, event_handler=None, popen=None, fs_util=None):
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        if fs_util is None:
            fs_util = FileSystemUtil(event_handler)
        rose_lib_path = fs_util.dirname(fs_util.dirname(__file__))
        lib_path = os.path.join(rose_lib_path, "loc_handlers")
        self.popen = popen
        self.fs_util = fs_util
        SchemeHandlersManager.__init__(self, [lib_path], attrs=["parse", "pull"],
                                       can_handle="can_pull")

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler with given arguments if possible."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def parse(self, loc, config):
        """Parse loc.name.
        
        Set loc.real_name, loc.scheme, loc.loc_type, loc.key, loc.paths, etc.
        if relevant.

        """
        if loc.scheme:
            # Scheme specified in the configuration.
            handler = self.get_handler(loc.scheme)
            if handler is None:
                raise ValueError(loc.name)
        else:
            # Scheme not specified in the configuration.
            scheme = urlparse(loc.name).scheme
            if scheme:
                handler = self.get_handler(scheme)
                if handler is None:
                    handler = self.guess_handler(loc)
                if handler is None:
                    raise ValueError(loc.name)
            else:
                handler = self.get_handler(self.DEFAULT_SCHEME)
        return handler.parse(loc, config)

    def pull(self, loc, config):
        """Pull loc to its cache."""
        if loc.scheme is None:
            self.parse(loc, config)
        return self.get_handler(loc.scheme).pull(loc, config)
