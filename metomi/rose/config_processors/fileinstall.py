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
# ----------------------------------------------------------------------------
"""Process "file:*" sections in node of a metomi.rose.config_tree.ConfigTree.
"""

from fnmatch import fnmatch
from glob import glob
from io import BytesIO
import os
import shlex
from shutil import rmtree
import sqlite3
from tempfile import mkdtemp
from typing import Any, Optional
from urllib.parse import urlparse

import aiofiles
from metomi.rose.checksum import (
    get_checksum,
    get_checksum_func,
    guess_checksum_algorithm,
)
from metomi.rose.config_processor import (
    ConfigProcessError,
    ConfigProcessorBase,
)
from metomi.rose.env import UnboundEnvironmentVariableError, env_var_process
from metomi.rose.fs_util import FileSystemUtil
from metomi.rose.job_runner import JobManager, JobProxy, JobRunner
from metomi.rose.popen import RosePopener
from metomi.rose.reporter import Event
from metomi.rose.scheme_handler import SchemeHandlersManager


class ConfigProcessorForFile(ConfigProcessorBase):
    """Processor for [file:*] in node of a ConfigTree."""

    SCHEME = "file"

    def __init__(self, *args, **kwargs):
        ConfigProcessorBase.__init__(self, *args, **kwargs)
        self.loc_handlers_manager = PullableLocHandlersManager(
            event_handler=self.manager.event_handler,
            popen=self.manager.popen,
            fs_util=self.manager.fs_util,
        )

    def handle_event(self, *args):
        """Invoke event handler with *args, if there is one."""
        self.manager.handle_event(*args)

    def process(
        self, conf_tree, item, orig_keys=None, orig_value=None, **kwargs
    ):
        """Install files according to [file:*] in conf_tree.

        kwargs["no_overwrite_mode"]: fail if a target file already exists.

        """

        # Find all the "file:*" nodes.
        nodes = {}
        if item == self.SCHEME:
            for key, node in list(conf_tree.node.value.items()):
                if node.is_ignored() or not key.startswith(self.PREFIX):
                    continue
                nodes[key] = node
        else:
            node = conf_tree.node.get([item], no_ignore=True)
            if node is None:
                raise ConfigProcessError(orig_keys, item)
            nodes[item] = node

        if not nodes:
            return

        # Create database to store information for incremental updates,
        # if it does not already exist.
        loc_dao = LocDAO()
        loc_dao.create()

        cwd = os.getcwd()
        file_install_root = conf_tree.node.get_value(
            ["file-install-root"], os.getenv("ROSE_FILE_INSTALL_ROOT", None)
        )
        if file_install_root:
            file_install_root = env_var_process(file_install_root)
            self.manager.fs_util.makedirs(file_install_root)
            self.manager.fs_util.chdir(file_install_root)
        try:
            self._process(conf_tree, nodes, loc_dao, **kwargs)
        finally:
            if cwd != os.getcwd():
                self.manager.fs_util.chdir(cwd)

    def _process(self, conf_tree, nodes, loc_dao, **kwargs):
        """Helper for self.process."""
        # Ensure that everything is overwritable
        # Ensure that container directories exist
        for key, node in sorted(nodes.items()):
            try:
                name = env_var_process(key[len(self.PREFIX) :])
            except UnboundEnvironmentVariableError as exc:
                raise ConfigProcessError([key], key, exc)
            if os.path.exists(name) and kwargs.get("no_overwrite_mode"):
                raise ConfigProcessError([key], None, FileOverwriteError(name))
            self.manager.fs_util.makedirs(self.manager.fs_util.dirname(name))
        # Gets a list of sources and targets
        sources = {}
        targets = {}
        for key, node in sorted(nodes.items()):
            # N.B. no need to catch UnboundEnvironmentVariableError here
            #      because any exception should been caught earlier.
            name = env_var_process(key[len(self.PREFIX) :])
            targets[name] = Loc(name)
            targets[name].action_key = Loc.A_INSTALL
            targets[name].mode = node.get_value(["mode"])
            if targets[name].mode and targets[name].mode not in Loc.MODES:
                raise ConfigProcessError([key, "mode"], targets[name].mode)
            target_sources = []
            for k in ["content", "source"]:  # "content" for back compat
                source_str = node.get_value([k])
                if source_str is None:
                    continue
                try:
                    source_str = env_var_process(source_str)
                except UnboundEnvironmentVariableError as exc:
                    raise ConfigProcessError([key, k], source_str, exc)
                source_names = []
                for raw_source_glob in shlex.split(source_str):
                    source_glob = raw_source_glob
                    if raw_source_glob.startswith(
                        "("
                    ) and raw_source_glob.endswith(")"):
                        source_glob = raw_source_glob[1:-1]
                    names = glob(source_glob)
                    if names:
                        source_names += sorted(names)
                    else:
                        source_names.append(raw_source_glob)
                for raw_source_name in source_names:
                    source_name = raw_source_name
                    is_optional = raw_source_name.startswith(
                        "("
                    ) and raw_source_name.endswith(")")
                    if is_optional:
                        source_name = raw_source_name[1:-1]
                    if source_name.startswith("~"):
                        source_name = os.path.expanduser(source_name)
                    if targets[name].mode in [
                        targets[name].MODE_SYMLINK,
                        targets[name].MODE_SYMLINK_PLUS,
                    ]:
                        if targets[name].real_name:
                            # Symlink mode can only have 1 source
                            raise ConfigProcessError([key, k], source_str)
                        targets[name].real_name = source_name
                    else:
                        if source_name not in sources:
                            sources[source_name] = Loc(source_name)
                            sources[source_name].action_key = Loc.A_SOURCE
                            sources[source_name].is_optional = is_optional
                        sources[source_name].used_by_names.append(name)
                        target_sources.append(sources[source_name])
            targets[name].dep_locs = target_sources
            if not targets[name].real_name and targets[name].mode in [
                targets[name].MODE_SYMLINK,
                targets[name].MODE_SYMLINK_PLUS,
            ]:
                raise ConfigProcessError([key, "source"], None)

        # Determine the scheme of the location from configuration.
        config_schemes_str = conf_tree.node.get_value(["schemes"])
        config_schemes = []  # [(pattern, scheme), ...]
        if config_schemes_str:
            for line in config_schemes_str.splitlines():
                pattern, scheme = line.split("=", 1)
                pattern = pattern.strip()
                scheme = scheme.strip()
                config_schemes.append((pattern, scheme))

        # Where applicable, determine for each source:
        # * Its real name.
        # * The checksums of its paths.
        # * Whether it can be considered unchanged.
        for source in list(sources.values()):
            try:
                for pattern, scheme in config_schemes:
                    if fnmatch(source.name, pattern):
                        source.scheme = scheme
                        break
                self.loc_handlers_manager.parse(source, conf_tree)
            except ValueError:
                if source.is_optional:
                    sources.pop(source.name)
                    for name in source.used_by_names:
                        targets[name].dep_locs.remove(source)
                        event = SourceSkipEvent(name, source.name)
                        self.handle_event(event)
                    continue
                else:
                    raise ConfigProcessError(
                        ["file:" + source.used_by_names[0], "source"],
                        source.name,
                    )
            prev_source = loc_dao.select(source.name)
            source.is_out_of_date = (
                not prev_source
                or (not source.key and not source.paths)
                or prev_source.scheme != source.scheme
                or prev_source.loc_type != source.loc_type
                or prev_source.key != source.key
                or sorted(prev_source.paths) != sorted(source.paths)
            )

        # Inspect each target to see if it is out of date:
        # * Target does not already exist.
        # * Target exists, but does not have a database entry.
        # * Target exists, but does not match settings in database.
        # * Target exists, but a source cannot be considered unchanged.
        for target in list(targets.values()):
            if target.real_name:
                target.is_out_of_date = not os.path.islink(
                    target.name
                ) or target.real_name != os.readlink(target.name)
            elif target.mode == target.MODE_MKDIR:
                target.is_out_of_date = os.path.islink(
                    target.name
                ) or not os.path.isdir(target.name)
            else:
                if os.path.exists(target.name) and not os.path.islink(
                    target.name
                ):
                    for path, checksum, access_mode in get_checksum(
                        target.name
                    ):
                        target.add_path(path, checksum, access_mode)
                    target.paths.sort()
                prev_target = loc_dao.select(target.name)
                target.is_out_of_date = (
                    os.path.islink(target.name)
                    or not os.path.exists(target.name)
                    or prev_target is None
                    or prev_target.mode != target.mode
                    or len(prev_target.paths) != len(target.paths)
                )
                if not target.is_out_of_date:
                    prev_target.paths.sort()
                    for prev_path, path in zip(
                        prev_target.paths, target.paths
                    ):
                        if prev_path != path:
                            target.is_out_of_date = True
                            break
                # See if any sources have changed names.
                if not target.is_out_of_date:
                    conn = loc_dao.get_conn()
                    prev_dep_locs = conn.execute(
                        """
                            SELECT *
                            FROM dep_names
                            WHERE name=?
                            ORDER BY ROWID
                        """,
                        [target.name],
                    ).fetchall()
                    prev_dep_locs = [i[1] for i in prev_dep_locs]
                    prev_dep_locs = [loc_dao.select(i) for i in prev_dep_locs]
                    if [i.name for i in prev_dep_locs] != [
                        i.name for i in target.dep_locs
                    ]:
                        target.is_out_of_date = True
                # See if any sources out of date
                if not target.is_out_of_date:
                    for dep_loc in target.dep_locs:
                        if dep_loc.is_out_of_date:
                            target.is_out_of_date = True
                            break
            if target.is_out_of_date:
                target.paths = None
                loc_dao.delete_locs.append(target)

        # Set up jobs for rebuilding all out-of-date targets.
        jobs = {}
        for name, target in sorted(targets.items()):
            if not target.is_out_of_date:
                self.handle_event(FileUnchangedEvent(target, level=Event.V))
                continue
            if target.mode in [target.MODE_SYMLINK, target.MODE_SYMLINK_PLUS]:
                if target.mode == target.MODE_SYMLINK_PLUS:
                    try:
                        os.stat(target.real_name)
                    except OSError as exc:
                        raise ConfigProcessError(
                            [self.PREFIX + target.name, "source"],
                            target.real_name,
                            exc,
                        )
                self.manager.fs_util.symlink(target.real_name, target.name)
                loc_dao.update_locs.append(target)
            elif target.mode == target.MODE_MKDIR:
                if os.path.islink(target.name):
                    self.manager.fs_util.delete(target.name)
                self.manager.fs_util.makedirs(target.name)
                loc_dao.update_locs.append(target)
                target.loc_type = target.TYPE_TREE
                target.add_path(target.BLOB, None, None)
            elif target.dep_locs:
                if os.path.islink(target.name):
                    self.manager.fs_util.delete(target.name)
                jobs[target.name] = JobProxy(target)
                for source in target.dep_locs:
                    if source.name not in jobs:
                        jobs[source.name] = JobProxy(source)
                        jobs[source.name].event_level = Event.V
                    job = jobs[source.name]
                    jobs[target.name].pending_for[source.name] = job
                p_name = target.name
                while (
                    os.path.dirname(p_name)
                    and os.path.dirname(p_name) != p_name
                ):
                    p_name = os.path.dirname(p_name)
                    if p_name in jobs:
                        jobs[target.name].pending_for[p_name] = jobs[p_name]
            else:
                self.manager.fs_util.install(target.name)
                target.loc_type = target.TYPE_BLOB
                for path, checksum, access_mode in get_checksum(target.name):
                    target.add_path(path, checksum, access_mode)
                loc_dao.update_locs.append(target)
        loc_dao.execute_queued_items()

        # If relevant, use job runner to get sources and build targets
        if jobs:
            work_dir = mkdtemp()
            try:
                nproc_keys = ["rose.config_processors.fileinstall", "nproc"]
                nproc_str = conf_tree.node.get_value(nproc_keys)
                nproc = None
                if nproc_str is not None:
                    nproc = int(nproc_str)
                job_runner = JobRunner(self, nproc)
                job_runner(JobManager(jobs), conf_tree, loc_dao, work_dir)
            except ValueError as exc:
                if exc.args and exc.args[0] in jobs:
                    job = jobs[exc.args[0]]
                    if job.context.action_key == Loc.A_SOURCE:
                        source = job.context
                        keys = [
                            self.PREFIX + source.used_by_names[0],
                            "source",
                        ]
                        raise ConfigProcessError(keys, source.name)
                raise exc
            finally:
                loc_dao.execute_queued_items()
                rmtree(work_dir)

        # Target checksum compare and report
        for target in list(targets.values()):
            if (
                not target.is_out_of_date
                or target.loc_type == target.TYPE_TREE
            ):
                continue
            keys = [self.PREFIX + target.name, "checksum"]
            checksum_expected = conf_tree.node.get_value(keys)
            if checksum_expected is None:
                continue
            checksum = target.paths[0].checksum
            if checksum_expected:
                if len(checksum_expected) != len(checksum):
                    algorithm = guess_checksum_algorithm(checksum_expected)
                    if algorithm:
                        checksum = get_checksum_func(algorithm)(target.name)
                if checksum_expected != checksum:
                    raise ConfigProcessError(
                        keys,
                        checksum_expected,
                        ChecksumError(checksum_expected, checksum),
                    )
            event = ChecksumEvent(target.name, target.paths[0].checksum)
            self.handle_event(event)

    async def process_job(self, job, conf_tree, loc_dao, work_dir):
        """Process a job, helper for "process"."""
        for key, method in [
            (Loc.A_INSTALL, self._target_install),
            (Loc.A_SOURCE, self._source_pull),
        ]:
            if job.context.action_key == key:
                return await method(job.context, conf_tree, work_dir)

    @classmethod
    def post_process_job(cls, job, conf_tree, loc_dao, work_dir):
        """Post-process a successful job, helper for "process"."""
        loc_dao.update_locs.append(job.context)

    def set_event_handler(self, event_handler):
        """Sets the event handler, used by pool workers to capture events."""
        try:
            self.manager.event_handler.event_handler = event_handler
        except AttributeError:
            pass

    async def _source_pull(self, source, conf_tree, work_dir):
        """Pulls a source to its cache in the work directory."""
        source.cache = os.path.join(
            work_dir,
            # checksum the source name (not it's contents).
            # this is a cheap solution to provide a unique, repeatable
            # and filesystem safe identifier for a source name (which could be
            # a url).
            get_checksum_func()(BytesIO(source.name.encode())),
        )
        return await self.loc_handlers_manager.pull(source, conf_tree)

    async def _target_install(self, target, conf_tree, work_dir):
        """Install target.

        Build target using its source(s).
        Calculate the checksum(s) of (paths in) target.

        """
        CHUNK_SIZE = 1024 * 4
        tgt_handle = None
        mod_bits = None
        is_first = True
        # Install target
        for source in target.dep_locs:
            if target.loc_type is None:
                target.loc_type = source.loc_type
            elif target.loc_type != source.loc_type:
                raise LocTypeError(
                    target.name, source.name, target.loc_type, source.loc_type
                )
            if target.loc_type == target.TYPE_BLOB:
                if tgt_handle is None:
                    if not os.path.isfile(target.name):
                        self.manager.fs_util.delete(target.name)
                    tgt_handle = await aiofiles.open(target.name, "wb")

                async with aiofiles.open(
                    source.cache, mode='rb'
                ) as source_handle:
                    while True:
                        bytes_ = await source_handle.read(CHUNK_SIZE)
                        if not bytes_:
                            break
                        await tgt_handle.write(bytes_)
                if mod_bits is None:
                    mod_bits = os.stat(source.cache).st_mode
                else:
                    mod_bits |= os.stat(source.cache).st_mode
            else:  # target.loc_type == target.TYPE_TREE
                args = []
                if is_first:
                    self.manager.fs_util.makedirs(target.name)
                args.extend(["--checksum", source.cache + "/", target.name])
                cmd = self.manager.popen.get_cmd("rsync", *args)
                self.manager.popen(*cmd)
            is_first = False
        if tgt_handle is not None:
            await tgt_handle.close()
        if mod_bits:
            os.chmod(target.name, mod_bits)

        # TODO: auto decompression of tar, gzip, etc?

        # Calculate target checksum(s)
        for path, checksum, access_mode in get_checksum(target.name):
            target.add_path(path, checksum, access_mode)


class ChecksumError(Exception):
    """An exception raised on an unmatched checksum."""

    def __str__(self):
        return "Unmatched checksum, expected=%s, actual=%s" % self.args


class ChecksumEvent(Event):
    """Report the checksum of a file."""

    def __str__(self):
        return "checksum: %s: %s" % self.args


class FileOverwriteError(Exception):
    """An exception raised in an attempt to overwrite an existing file.

    This will only be raised in non-overwrite mode.

    """

    def __str__(self):
        return (
            "%s: file already exists (and in no-overwrite mode)" % self.args[0]
        )


class FileUnchangedEvent(Event):
    """Report an unchanged file."""

    def __str__(self):
        return str(self.args[0])


class Loc:

    """Represent a location.

    A Loc object has the following attributes:
    loc.name - The name of the location
    loc.real_name - This loc is a symbolic link pointing to this value
    loc.action_key - Either loc.A_SOURCE (a source) or loc.A_INSTALL (a target)
    loc.scheme - The location scheme, e.g. "svn" for Subversion location
    loc.dep_locs - A list of sources (Loc objects) of this target
    loc.mode - Target installation mode, "auto", "symlink", "mkdir", etc
    loc.loc_type - Either loc.TYPE_TREE (directory) or loc.TYPE_BLOB (file)
    loc.paths - A list of sub-paths of this loc
    loc.key - An key to indicate if this source is modified or not
              (e.g. a SVN revision)
    loc.cache - A cache for this source
    loc.used_by_names - This source is used by this list of target names
    loc.is_out_of_date - This loc is out of date
    loc.is_optional - A boolean to indicate if a source is optional or not

    """

    A_SOURCE = "source"
    A_INSTALL = "install"
    A_INSTALL_UNC = "unchanged"
    BLOB = ""
    MODE_AUTO = "auto"
    MODE_MKDIR = "mkdir"
    MODE_SYMLINK = "symlink"
    MODE_SYMLINK_PLUS = "symlink+"
    MODES = (MODE_AUTO, MODE_MKDIR, MODE_SYMLINK, MODE_SYMLINK_PLUS)
    TYPE_TREE = "tree"
    TYPE_BLOB = "blob"

    def __init__(self, name, scheme=None, dep_locs=None):
        self.name = name
        self.real_name = None
        self.action_key = None
        self.scheme = scheme
        self.dep_locs = dep_locs
        self.mode = None
        self.loc_type = None
        self.paths = []
        self.key = None
        self.cache = None
        self.used_by_names = []
        self.is_out_of_date = None  # boolean
        self.is_optional = False

    def __str__(self):
        ret = self.name
        if self.real_name and self.real_name != self.name:
            ret = "%s (%s)" % (self.real_name, self.name)
        if self.dep_locs:
            for dep_loc in self.dep_locs:
                ret += "\n    %s" % str(dep_loc)
        if self.action_key == self.A_INSTALL and not self.is_out_of_date:
            ret = "%s: %s" % (self.A_INSTALL_UNC, ret)
        elif self.action_key is not None:
            ret = "%s: %s" % (self.action_key, ret)
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


class LocSubPath:
    """Represent a sub-path in a location.

    Attrs:
        name:
            Path name.
        checksum:
            Computed checksum value.
        access_mode:
            File type and mode bits (see os.stat_result:st_mode).
    """

    def __init__(
        self,
        name: str,
        checksum: Any = None,
        access_mode: Optional[int] = None
    ):
        self.name = name
        self.checksum = checksum
        self.access_mode = access_mode

    def __lt__(self, other):
        return (self.name, self.checksum, self.access_mode) < (
            other.name,
            other.checksum,
            other.access_mode,
        )

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.checksum == other.checksum
            and self.access_mode == other.access_mode
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.name


class LocDAO:
    """DAO for information for incremental updates."""

    FILE_NAME = ".rose-config_processors-file.db"
    SCHEMA_LOCS = (
        "name TEXT, "
        + "real_name TEXT, "
        + "scheme TEXT, "
        + "mode TEXT, "
        + "loc_type TEXT, "
        + "key TEXT, "
        + "PRIMARY KEY(name)"
    )
    SCHEMA_PATHS = "name TEXT, path TEXT,checksum TEXT, UNIQUE(name, path)"
    SCHEMA_DEP_NAMES = "name TEXT, dep_name TEXT, UNIQUE(name, dep_name)"

    def __init__(self):
        self.file_name = os.path.abspath(self.FILE_NAME)
        self.conn = None
        self.delete_locs = []
        self.update_locs = []

    def get_conn(self):
        """Return a Connection object to the database."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.file_name)
        return self.conn

    def create(self):
        """Create the database file if it does not exist."""
        conn = self.get_conn()
        cur = conn.execute(
            """SELECT name FROM sqlite_master WHERE type="table"
               ORDER BY name"""
        )
        names = [str(row[0]) for row in cur.fetchall()]
        for name, schema in [
            ("locs", self.SCHEMA_LOCS),
            ("paths", self.SCHEMA_PATHS),
            ("dep_names", self.SCHEMA_DEP_NAMES),
        ]:
            if name not in names:
                conn.execute("CREATE TABLE " + name + "(" + schema + ")")
        conn.commit()

    def execute_queued_items(self):
        """Execute queued delete_locs and updates."""
        if not self.delete_locs and not self.update_locs:
            return
        try:
            conn = self.get_conn()
            # Locations to delete
            if self.delete_locs:
                for table in ["locs", "dep_names", "paths"]:
                    conn.executemany(
                        (r"DELETE FROM %s WHERE name=?" % table),
                        [[loc.name] for loc in self.delete_locs],
                    )
            # Locations to update
            if self.update_locs:
                data = {
                    "locs": {"n_args": 6, "args_list": []},
                    "paths": {"n_args": 3, "args_list": []},
                    "dep_names": {"n_args": 2, "args_list": []},
                }
                for loc in self.update_locs:
                    data["locs"]["args_list"].append(
                        [
                            loc.name,
                            loc.real_name,
                            loc.scheme,
                            loc.mode,
                            loc.loc_type,
                            loc.key,
                        ]
                    )
                    if loc.paths:
                        for path in loc.paths:
                            if path.checksum and path.access_mode:
                                checksum_str = ":".join(
                                    [path.checksum, str(path.access_mode)]
                                )
                            else:
                                checksum_str = None
                            data["paths"]["args_list"].append(
                                [loc.name, path.name, checksum_str]
                            )
                    if loc.dep_locs:
                        for dep_loc in loc.dep_locs:
                            data["dep_names"]["args_list"].append(
                                [loc.name, dep_loc.name]
                            )
                for table, datum in list(data.items()):
                    if datum["args_list"]:
                        conn.executemany(
                            (
                                "INSERT OR REPLACE INTO %s VALUES(%s)"
                                % (table, ",".join("?" * datum["n_args"]))
                            ),
                            datum["args_list"],
                        )
            conn.commit()
        except sqlite3.Error:
            try:
                self.conn.rollback()
            except sqlite3.Error:
                pass
            raise
        else:
            del self.delete_locs[:]
            del self.update_locs[:]

    def select(self, name):
        """Query database for settings matching name.

        Reconstruct setting as a Loc object and return it.

        """
        conn = self.get_conn()
        row = conn.execute(
            """SELECT real_name,scheme,mode,loc_type,key"""
            + """ FROM locs WHERE name=?""",
            [name],
        ).fetchone()
        if row is None:
            return
        loc = Loc(name)
        loc.real_name, loc.scheme, loc.mode, loc.loc_type, loc.key = row

        for row in conn.execute(
            """SELECT path,checksum FROM paths WHERE name=?""", [name]
        ):
            path, checksum_str = row
            checksum = None
            access_mode = None
            if checksum_str:
                checksum_items = checksum_str.rsplit(":", 1)
                checksum = checksum_items.pop(0)
                access_mode = None
                if checksum_items:
                    access_mode = int(checksum_items.pop(0))
            if loc.paths is None:
                loc.paths = []
            loc.add_path(path, checksum, access_mode)

        for row in conn.execute(
            """SELECT dep_name FROM dep_names WHERE name=?""", [name]
        ):
            (dep_name,) = row
            if loc.dep_locs is None:
                loc.dep_locs = []
            loc.dep_locs.append(self.select(dep_name))
        return loc


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
        self.popen = popen
        if fs_util is None:
            fs_util = FileSystemUtil(event_handler)
        self.fs_util = fs_util
        SchemeHandlersManager.__init__(
            self,
            [self.get_rose_path()],
            ns="metomi.rose.loc_handlers",
            attrs=["parse", "pull"],
            can_handle="can_pull",
        )

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler with given arguments if possible."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def parse(self, loc, conf_tree):
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
        return handler.parse(loc, conf_tree)

    def pull(self, loc, conf_tree):
        """Pull loc to its cache."""
        if loc.scheme is None:
            self.parse(loc, conf_tree)
        return self.get_handler(loc.scheme).pull(loc, conf_tree)


class SourceSkipEvent(Event):

    """Report skipping of a missing optional source."""

    KIND = Event.KIND_ERR

    def __str__(self):
        return "file:%s: skip missing optional source: %s" % self.args
