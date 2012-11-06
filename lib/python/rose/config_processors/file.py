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


class Location(object):
    """Represent a (file/directory) location."""

    def __init__(self, name):
        self.name = name
        self.name_orig = name
        self.scheme = None
        self.paths = None
        self.cache = None
        self.refs = None
        self.is_up_to_date = False

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def __eq__(self, other):
        if other is None:
            return False
        if id(self) == id(other):
            return True
        return (self.name == other.name and
                self.paths == other.paths and
                self.refs == other.refs)

    def __str__(self):
        return self.name

    def update(self, other):
        self.name = other.name
        self.name_orig = other.name_orig
        self.scheme = other.scheme
        self.paths = other.paths
        self.cache = other.cache
        self.refs = other.refs
        self.is_up_to_date = other.is_up_to_date


class LocationPath(object):
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


class ConfigProcessorForFile(ConfigProcessorBase):

    SCHEME = "file"
    NPROC = 6
    POLL_DELAY = 0.05
    RE_FCM_SRC = re.compile(r"(?:\A[A-z][\w\+\-\.]*:)|(?:@[^/@]+\Z)")

    def __init__(self, *args, **kwargs):
        ConfigProcessorBase.__init__(self, *args, **kwargs)
        self.file_loc_handlers_manager = FileLocHandlersManager(
                event_handler=self.manager.event_handler,
                popen=self.manager.popen,
                fs_util=self.manager.fs_util)
        self.loc_dao = LocDAO()

    def process(self, config, item, orig_keys=None, orig_value=None, **kwargs):
        """Install files according to the file:* sections in "config"."""
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

        # Parse each location and determine whether they require an update.
        loc_map = {}
        local_loc_map = {}
        for key, node in sorted(nodes.items()):
            locs_str = node.get_value("locations")
            if locs_str is None:
                continue
            local_loc_name = key[len(self.PREFIX):]
            locs = []
            for name in shlex.split(locs_str):
                loc_map[name] = Location(name)
                locs.append(loc_map[name])
            local_loc_map[local_loc_name] = Location(local_loc_name)
            local_loc_map[local_loc_name].refs = sorted(locs)
        pool = self._get_worker_pool(loc_map)
        results = {}
        for name, loc in loc_map.items():
            # TODO: _loc_parse
            result = pool.apply_async(_loc_parse, [self, config, loc])
            results[name] = result
        pool.close()
        while results:
            for name, result in results.items():
                if not result.ready():
                    continue
                results.pop(name)
                loc, args_of_events = result.get()
                loc_map[name].update(loc)
                for args_of_event in args_of_events:
                    self.manager.handle_event(*args_of_event)
            if results:
                sleep(self.POLL_DELAY)

        # Check whether each local "file" needs update.
        for local_loc in local_loc_map.values():
            if os.path.exists(local_loc.name):
                for dirpath, dirnames, filenames in os.walk(local_loc.name):
                    for i in reversed(range(len(dirnames))):
                        dirname = dirnames[i]
                        if dirname.startswith("."):
                            dirnames.pop(i)
                            continue
                        local_loc.paths.append(
                                LocationPath(os.path.join(dirpath, dirname)))
                    for filename in filenames:
                        local_loc.paths.append(
                                LocationPath(os.path.join(dirpath, filename)))
                        m = md5()
                        f = open(filename)
                        m.update(f.read())
                        loc_path.checksum = m.hexdigest()
                # TODO: LocDAO.select
                prev_local_loc = self.loc_dao.select(local_loc.name)
                local_loc.is_up_to_date = (local_loc == prev_local_loc)
            if not local_loc.is_up_to_date:
                # TODO: LocDAO.delete
                self.loc_dao.delete(local_loc.name)

        # Update locations with workers.
        loc_map = {}
        for local_loc in local_loc_map.values():
            if local_loc.is_up_to_date:
                continue
            for loc in local_loc.refs:
                loc_map[loc.name] = loc
        pool = self._get_worker_pool(loc_map)
        results = {}
        for name, loc in loc_map.items():
            # TODO: _loc_pull
            result = pool.apply_async(_loc_pull, [self, config, loc])
            results[name] = result
        pool.close()
        while results:
            for name, result in results.items():
                if not result.ready():
                    continue
                results.pop(name)
                loc, args_of_events = result.get()
                loc_map[name].update(loc)
                # TODO: LocDAO.update
                self.loc_dao.update(loc)
                for args_of_event in args_of_events:
                    self.manager.handle_event(*args_of_event)
            if results:
                sleep(self.POLL_DELAY)

        # Rebuild each "local" file.
        local_locs = [l if not l.is_up_to_date for l in local_loc_map.values()]
        pool = self._get_worker_pool(local_locs)
        results = {}
        for local_loc in local_locs:
            # TODO: _loc_install 
            result = pool.apply_async(_loc_install, [self, config, local_loc]
            results[name] = result
        pool.close()
        while results:
            for name, result in results.items():
                if not result.ready():
                    continue
                results.pop(name)
                local_loc, args_of_events = result.get()
                local_loc_map[name].update(local_loc)
                # TODO: LocDAO.update
                self.loc_dao.update(local_loc)
                for args_of_event in args_of_events:
                    self.manager.handle_event(*args_of_event)
            if results:
                sleep(self.POLL_DELAY)

    def process_target(self, config, key, node):
        """Install a target according to a file:target section."""
        target = key[len(self.PREFIX):]

        content_value = node.get_value(["content"])
        if content_value:
            # Embedded content
            if os.path.isdir(target):
                self.manager.fs_util.delete(target)
            target_file = open(target, 'wb')
            contents = shlex.split(content_value)
            for content in contents:
                target_file.write(self.manager.process(
                        config, content,
                        [key, "content"], content_value))
            target_file.close()
            self.manager.handle_event(
                    FileSystemEvent("content", target, " ".join(contents)))
        else:
            # Free format file
            source_str = node.get_value(["source"], default="")
            sources = []
            for source in shlex.split(source_str):
                try:
                    source = env_var_process(source)
                except UnboundEnvironmentVariableError as e:
                    raise ConfigProcessError(
                            [key, "source"], source_str, e)
                sources.append(os.path.expanduser(source))
            mode = node.get_value(["mode"])
            if len(sources) == 1:
                source = sources[0]
                if mode == "symlink":
                    self.manager.fs_util.symlink(source, target)
                else:
                    #if os.path.exists(target):
                    #    self.manager.fs_util.delete(target)
                    loc = FileLoc(source)
                    self.file_loc_handlers_manager.pull(target, loc)
                    self.manager.handle_event(
                            FileSystemEvent("install", target, source))
            elif len(sources) > 1 or len(sources) == 0 and mode != "mkdir":
                if os.path.isdir(target):
                    self.manager.fs_util.delete(target)
                target_file = open(target, 'wb')
                for source in sources:
                    loc = FileLoc(source)
                    f = self.file_loc_handlers_manager.load(loc)
                    target_file.write(f.read())
                target_file.close()
                self.manager.handle_event(
                        FileSystemEvent("install", target, source_str))
            else:
                if os.path.isdir(target):
                    for name in os.listdir(target):
                        path = os.path.join(target, name)
                        self.manager.fs_util.delete(path)
                else:
                    self.manager.fs_util.delete(target)
                    self.manager.fs_util.makedirs(target)

            # Target MD5 checksum
            checksum_expected = node.get_value(["checksum"])
            if checksum_expected is not None:
                target_file = open(target)
                m = md5()
                m.update(target_file.read())
                checksum = m.hexdigest()
                if checksum_expected and checksum_expected != checksum:
                    e = UnmatchedChecksumError(checksum_expected, checksum)
                    raise ConfigProcessError(
                            [key, "checksum"], checksum_expected, e)
                target_file.close()
                self.manager.handle_event(ChecksumEvent(target, checksum))

    def _get_worker_pool(self, items):
        nproc = int(ResourceLocator.default().get_conf().get_value(
                ["rose.config_processors.file", "nproc"],
                default=self.NPROC))
        if nproc > len(items):
            nproc = len(items)
        return Pool(processes=nproc)

    def _source_export(self, source, target):
        """Export/copy a source file/directory in FS or FCM VC to a target."""
        if source == target:
            return
        elif self._source_is_fcm(source):
            command = ["fcm", "export", "--quiet", source, target]
            return self.manager.popen(*command)
        elif os.path.isdir(source):
            ignore = shutil.ignore_patterns(".*")
            return shutil.copytree(source, target, ignore=ignore)
        else:
            return shutil.copyfile(source, target)


    def _source_is_fcm(self, source):
        """Return true if source is an FCM version controlled resource."""
        return self.RE_FCM_SRC.match(source) is not None


    def _source_load(self, source):
        """Load and return the content of a source file in FS or FCM VC."""
        if self._source_is_fcm(source):
            f = tempfile.TemporaryFile()
            self.manager.popen("fcm", "cat", source, stdout=f)
            f.seek(0)
            return f.read()
        else:
            return open(source).read()


class FileLoc(object):
    """Represent the location of a (remote) file."""

    def __init__(self, name, scheme=None):
        self.name = name
        self.name_invariant = None
        self.scheme = scheme

    def __str__(self):
        if self.name_invariant:
            return self.name_invariant
        else:
            return self.name


class LocDAO(object):
    """DAO for information for incremental updates."""

    DB_FILE_NAME = ".rose-config_processors-file.db"

    def create(self):
        if not os.path.exists(self.DB_FILE_NAME):
            conn = sqlite3.connect(self.DB_FILE_NAME)
            c = conn.cursor()
            c.execute("""CREATE TABLE file(
                          name TEXT,
                          loc TEXT,
                          UNIQUE(name, loc))""")
            c.execute("""CREATE TABLE checksum(
                          root TEXT,
                          path TEXT,
                          value TEXT,
                          UNIQUE(root, path))""")
            conn.commit()


class FileLocHandlerBase(object):
    """Base class for a file location handler."""

    SCHEME = None
    PULL_MODE = "PULL_MODE"
    PUSH_MODE = "PUSH_MODE"

    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler with given arguments if possible."""
        self.manager.handle_event(*args, **kwargs)

    def can_handle(self, file_loc, mode=PULL_MODE):
        """Return True if this handler can handle file_loc."""
        return False

    def load(self, file_loc, **kwargs):
        """Return a temporary file handle to read a remote file_loc."""
        f = tempfile.NamedTemporaryFile()
        self.pull(f.name, file_loc)
        f.seek(0)
        return f

    def pull(self, file_path, file_loc, **kwargs):
        """Pull remote file_loc to local file_path."""
        raise NotImplementedError()

    def push(self, file_path, file_loc, **kwargs):
        """Push local file_path to remote file_loc."""
        raise NotImplementedError()


class FileLocHandlersManager(SchemeHandlersManager):
    """Manage location handlers."""

    PULL_MODE = FileLocHandlerBase.PULL_MODE
    PUSH_MODE = FileLocHandlerBase.PUSH_MODE

    def __init__(self, event_handler=None, popen=None, fs_util=None):
        path = os.path.join(os.path.dirname(__file__), "file_loc_handlers")
        SchemeHandlersManager.__init__(self, path, ["load", "pull", "push"])
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

    def load(self, file_loc, **kwargs):
        if file_loc.scheme:
            p = self.get_handler(file_loc.scheme)
        else:
            p = self.guess_handler(file_loc, mode=self.PULL_MODE)
        return p.load(file_loc, **kwargs)

    def pull(self, file_path, file_loc, **kwargs):
        if file_loc.scheme:
            p = self.get_handler(file_loc.scheme)
        else:
            p = self.guess_handler(file_loc, mode=self.PULL_MODE)
        return p.pull(file_path, file_loc, **kwargs)

    def push(self, file_path, file_loc, **kwargs):
        if file_loc.scheme:
            p = self.get_handler(file_loc.scheme)
        else:
            p = self.guess_handler(file_loc, mode=self.PUSH_MODE)
        return p.push(file_path, file_loc, **kwargs)


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

def _process_target(processor, config, key, node):
    """Pool worker for ConfigProcessorForFile.process."""
    event_handler = WorkerEventHandler()
    processor.manager.event_handler.event_handler = event_handler
    processor.process_target(config, key, node)
    processor.manager.event_handler.event_handler = None
    return event_handler.events
