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

from hashlib import md5
from multiprocessing import Pool
import os
import re
import rose.config
from rose.config_processor import ConfigProcessError, ConfigProcessorBase
from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.fs_util import FileSystemEvent
from rose.reporter import Event
from rose.resource import ResourceLocator
from rose.scheme_handler import SchemeHandlersManager
import shlex
import sqlite3
import shutil
import tempfile
from time import sleep


class FileOverwriteError(Exception):

    """An exception raised in an attempt to overwrite an existing file.

    This will only be raised in non-overwrite mode.

    """

    def __str__(self):
        return ("%s: file already exists (and in no-overwrite mode)" %
                self.args[0])


class UnmatchedChecksumError(Exception):
    """An exception raised on an unmatched checksum."""

    def __str__(self):
        return ("Unmatched checksum, expected=%s, actual=%s" % tuple(self))


class ChecksumEvent(Event):
    """Report the checksum of a file."""

    def __str__(self):
        return "checksum: %s: %s" % self.args


class Loc(object):
    """Represent a location."""

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
        self.cache = None
        self.is_out_of_date = None # boolean

    def __str__(self):
        if self.real_name and self.real_name != self.name:
            return "%s (%s)" % (self.real_name, self.name)
        else:
            return self.name

    def update(self, other):
        self.name = other.name
        self.real_name = other.real_name
        self.scheme = other.scheme
        self.mode = other.mode
        self.paths = other.paths
        self.cache = other.cache
        self.is_out_of_date = other.is_out_of_date


class PathInLoc(object):
    """Represent a sub-path in a location."""

    def __init__(self, name):
        self.name = name
        self.checksum = None

    def __cmp__(self, other):
        return cmp(self.name, other.name) or cmp(self.checksum, other.checksum)

    def __eq__(self, other):
        return (self.name == other.name and self.checksum == other.checksum)

    def __str__(self):
        return self.name


class LocTypeError(Exception):
    """An exception raised when a location type is incorrect.

    The location type is either a file blob or a directory tree.

    """
    def __str__(self):
        return "%s <= %s, expected %s, got %s" % self.args


class LocJobProxy(object):
    """Represent the state of the job for updating a location."""

    ST_DONE = "ST_DONE"
    #ST_FAILED = "ST_FAILED"
    ST_PENDING = "ST_PENDING"
    ST_READY = "ST_READY"
    ST_WORKING = "ST_WORKING"

    def __init__(self, loc, action_key):
        self.loc = loc
        self.action_key = None
        self.name = loc.name
        self.needed_by = {}
        self.pending_for = {}
        self.state = self.ST_READY

    def __str__(self):
        return "%s: %s" % (self.action_key, str(self.loc))

    def update(self, other):
        self.state = other.state
        self.loc.update(other.loc)


class JobManager(object):
    """Manage a set of LocJobProxy objects and their states."""

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
            return [job if job.pending_for for job in self.jobs.values()]
        return (not self.has_jobs and
                any([job.pending_for for job in self.jobs.values()]))

    def has_jobs(self):
        """Return True if there are ready jobs or working jobs."""
        return bool(self.ready_jobs) or bool(self.working_jobs)

    def has_ready_jobs(self):
        """Return True if there are ready jobs."""
        return bool(self.ready_jobs)

    def put_job(self, job_proxy):
        """Tell the manager that a job has completed."""
        job = self.working_jobs.pop(job_proxy.name)
        job.update(job_proxy)
        for up_key, up_job in job.needed_by.items():
            job.needed_by.pop(up_key)
            up_job.pending_for.pop(job.name)
            if not up_job.pending_for:
                self.ready_jobs.append(up_job)
                up_job.state = up_job.ST_READY
        return job


class JobRunner(object):
    """Runs LocJobProxy objects with pool of workers."""

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
            # Add some more jobs into the worker pool, as they are ready
            while job_manager.has_ready_jobs():
                job = job_manager.get_job()
                if job is None:
                    break
                result = pool.apply_async(_loc_job_run,
                                          [self.job_processor, job, *args])
                results[job.name] = result
            if results:
                sleep(self.POLL_DELAY)

        dead_jobs = job_manager.get_dead_jobs()
        if dead_jobs:
            raise UnfinishedJobsError(dead_jobs)

    __call__ = run


class WorkerEventHandler(object):
    """Temporary event handler in a function run by a pool worker process.

    Events are collected in the self.events which is a list of tuples
    representing the arguments the report method in an instance of
    rose.reporter.Reporter.

    """
    def __init__(self):
        self.events = []

    def __call__(self, message, type=None, level=None, prefix=None, clip=None):
        self.events.append((message, type, level, prefix, clip))


def _loc_job_run(job_processor, job_proxy, *args):
    """Helper for JobRunner."""
    event_handler = WorkerEventHandler()
    job_processor.set_event_handler(event_handler)
    job_processor.process_job(job_proxy, *args)
    job_processor.set_event_handler(None)
    return (job_proxy, event_handler.events)


class UnfinishedJobsError(Exception):
    """Error raised when there are no ready/working jobs but pending ones."""
    def __str__(self):
        ret = ""
        for job in self.args:
            ret += "[DEAD TASK] %s\n" % str(job)
        return ret


class ConfigProcessorForFile(ConfigProcessorBase):

    SCHEME = "file"
    NPROC = 6
    POLL_DELAY = 0.05
    RE_FCM_SRC = re.compile(r"(?:\A[A-z][\w\+\-\.]*:)|(?:@[^/@]+\Z)")
    T_INSTALL = "install"
    T_PULL = "pull"

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
            content_str = node.get_value("content")
            name = key[len(self.PREFIX):]
            target_sources = []
            if content_str is not None:
                for n in shlex.split(content_str):
                    sources[n] = Loc(n)
                    target_sources.append(sources[n])
            targets[name] = Loc(name)
            targets[name].dep_locs = sorted(target_sources)
            targets[name].mode = node.get_value("mode")

        # Where applicable, determine for each source:
        # * Its invariant name.
        # * Whether it can be considered unchanged.
        for source in sources.values():
            self._source_parse(source, config.get(["loc:" + source.name]))

        # Inspect each target to see if it is out of date:
        # * Target does not already exist.
        # * Target exists, but does not have a database entry.
        # * Target exists, but does not match settings in database.
        # * Target exists, but a source cannot be considered unchanged.
        for target in targets.values():
            if os.path.islink(target.name):
                target.real_name = os.readlink(target.name)
            elif os.path.isfile(target.name):
                m = md5()
                f = open(target.name)
                m.update(f.read())
                target.paths = [PathInLoc("", m.hexdigest())]
            elif os.path.isdir(target.name):
                target.paths = []
                for dirpath, dirnames, filenames in os.walk(target.name):
                    for i in reversed(range(len(dirnames))):
                        dirname = dirnames[i]
                        if dirname.startswith("."):
                            dirnames.pop(i)
                            continue
                        target.paths.append(
                                PathInLoc(os.path.join(dirpath, dirname)))
                    for filename in filenames:
                        m = md5()
                        filepath = os.path.join(dirpath, filename)
                        f = open(filepath)
                        m.update(f.read())
                        target.paths.append(PathInLoc(filepath, m.hexdigest()))
                target.paths.sort()
            prev_target = self.loc_dao.select(target.name)
            target.is_out_of_date = (
                    not os.path.exists(target.name) or
                    prev_target is None or
                    prev_target.mode != target.mode or
                    prev_target.real_name != target.real_name or
                    prev_target.paths != target.paths or
                    any([s.is_out_of_date for s in target.dep_locs]))
            if target.is_out_of_date:
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
                    jobs[target.name] = LocJobProxy(target, self.T_INSTALL)
                    for source in target.dep_locs:
                        jobs[source.name] = LocJobProxy(source, self.T_PULL)
            elif target.mode == "mkdir":
                self.manager.fs_util.makedirs(target.name)
                self.loc_dao.update(target)
                target.loc_type = target.TYPE_TREE
                target.paths = [PathInLoc("", None)]
            else:
                self.manager.fs_util.create(target.name)
                self.loc_dao.update(target)
                target.loc_type = target.TYPE_BLOB
                target.paths = [PathInLoc("", md5().hexdigest())]

        JobRunner(self)(JobManager(jobs), config)

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
                e = UnmatchedChecksumError(checksum_expected, checksum)
                raise ConfigProcessError(keys, checksum_expected, e)
            event = ChecksumEvent(target.name, checksum)
            self.handle_event(event)

    def process_job(self, job, config):
        """Process a job, helper for process."""
        if job.action_key == self.T_INSTALL:
            self._target_install(job.loc, config)
        elif job.action_key == self.T_PULL:
            self._source_pull(job.loc)
        job.state = job.ST_DONE

    def post_process_job(self, job, config):
        self.loc_dao.update(job.loc)

    def _source_parse(self, source, config):
        if config is not None:
            scheme = config.get_value(["scheme"])
            if scheme:
                loc.scheme = scheme
        self.loc_handlers_manager.parse(source)
        prev_source = self.loc_dao.select(source.name)
        source.is_out_of_date = (
                not prev_source or
                (not source.real_name and not source.paths) or
                prev_source.scheme != source.scheme or
                prev_source.loc_type != source.loc_type or
                prev_source.real_name != source.real_name or
                prev_source.paths != source.paths)

    def _source_pull(self, source):
        self.loc_handlers_manager.pull(source)

    def _target_install(self, target, config):
        """Install target.

        Build target using its source(s).
        Calculate the checksum(s) of (paths in) target.

        """
        f = None
        is_first = True
        # Install target
        for source in job.loc.dep_locs:
            if target.loc_type is None:
                target.loc_type = source.loc_type
            elif target.loc_type != source.loc_type
                raise LocTypeError(target.name, source.name, target.loc_type,
                                   source.loc_type)
            if target.loc_type == target.TYPE_BLOB:
                if f is None:
                    f = open(target.name, "wb")
                f.write(open(source.cache).read())
            else: # target.loc_type == target.TYPE_TREE
                args = []
                if is_first:
                    self.manager.fs_util.makedirs(target.name)
                    args.append("--delete-excluded")
                args.extend(["--checksum", source.cache, target.name])
                cmd = self.manager.popen.get_cmd("rsync", *args)
                out, err = self.manager.popen(*cmd)
            is_first = False
        if f is not None:
            f.close()

        # Calculate target checksum(s)
        if target.loc_type == target.TYPE_BLOB:
            m = md5()
            m.update(open(target).read())
            target.paths = [PathInLoc("", m.hexdigest())]
        else:
            target.paths = []
            for dirpath, dirnames, filenames in os.walk(target):
                path = dirpath[len(target) + 1:]
                target.paths.append(PathInLoc(path, None))
                for filename in filenames:
                    filepath = os.path.join(path, filename)
                    m = md5()
                    m.update(open(filepath).read())
                    target.paths.append(PathInLoc(filepath, m.hexdigest()))

    def set_event_handler(self, event_handler):
        """Sets the event handler, used by pool workers to capture events."""
        try:
            self.manager.event_handler.event_handler = event_handler
        except AttributeError:
            pass


class LocDAO(object):
    """DAO for information for incremental updates."""

    DB_FILE_NAME = ".rose-config_processors-file.db"

    def __int__(self):
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
        c.execute("""DELETE FROM locs WHERE name=?""", loc.name)
        c.execute("""DELETE FROM dep_names WHERE name=?""", loc.name)
        c.execute("""DELETE FROM paths WHERE name=?""", loc.name)
        conn.commit()

    def select(self, name):
        """Query database for settings matching name.
        
        Reconstruct setting as a Loc object and return it.
 
        """
        conn = self.get_conn()
        c = conn.cursor()

        c.execute("""SELECT real_name,scheme,mode,loc_type FROM locs""" +
                  """ WHERE name=?""", name)
        row = c.fetchone()
        if row is None:
            return
        loc = Loc(name)
        loc.real_name, loc.scheme, loc.mode, loc.loc_type = row

        c.execute("""SELECT path,checksum FROM paths WHERE name=?""", name)
        for row in c:
            path, checksum = row
            if loc.paths is None:
                loc.paths = []
            loc.paths.append(PathInLoc(path, checksum))

        c.execute("""SELECT dep_name FROM dep_names WHERE name=?""", name)
        for row in c:
            dep_name, = row
            if loc.dep_locs is None:
                loc.dep_locs = []
            loc.dep_locs.append(self.select(dep_name))

    def update(self, loc):
        """Insert or update settings related to loc to the database."""
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO locs VALUES(?,?,?,?,?)""",
                  loc.name, loc.real_name, loc.scheme, loc.mode, loc.loc_type)
        if loc.paths:
            for path in loc.paths:
                c.execute("""INSERT OR REPLACE INTO paths VALUES(?,?,?)""",
                          name, path.name, path.checksum)
        if loc.dep_locs:
            for dep_loc in loc.dep_locs:
                c.execute("""INSERT OR REPLACE INTO dep_names VALUES(?,?)""",
                          name, dep_loc.name)


class PullableLocHandlersManager(SchemeHandlersManager):
    """Manage location handlers.

    Each location handler should have a SCHEME set to a unique string, the
    "can_handle" method, the "parse" method and the "pull" methods.

    """

    def __init__(self, event_handler=None, popen=None, fs_util=None):
        path = os.path.join(os.path.dirname(__file__), "loc_handlers")
        SchemeHandlersManager.__init__(self, [path], ["parse", "pull"])
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        self.popen = popen
        if fs_util is None:
            fs_util = FileSystemUtil(event_handler)
        self.fs_util = fs_util

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler with given arguments if possible."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def parse(self, loc):
        """Parse loc.name, set loc.real_name, loc.scheme where possible."""
        if loc.scheme:
            p = self.get_handler(loc.scheme)
        else:
            p = self.guess_handler(loc)
        return p.parse(loc)

    def pull(self, loc):
        """Pull a location to the local file system.

        If loc.cache is defined, pull to the specified path.
        Otherwise, pull to a temporary directory and set loc.cache.

        Set loc.loc_type where possible.

        """
        if file_loc.scheme:
            p = self.get_handler(loc.scheme)
        else:
            p = self.guess_handler(loc)
        return p.pull(loc)
