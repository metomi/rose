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

import hashlib
from multiprocessing import Pool
import os
import re
import rose.config
from rose.config_processor import ConfigProcessError, ConfigProcessorBase
from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.fs_util import FileSystemEvent
from rose.reporter import Event
from rose.resource import ResourceLocator
import shlex
import shutil
import tempfile


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


class ConfigProcessorForFile(ConfigProcessorBase):

    KEY = "file"
    NPROC = 6
    RE_FCM_SRC = re.compile(r"(?:\A[A-z][\w\+\-\.]*:)|(?:@[^/@]+\Z)")

    def process(self, config, item, orig_keys=None, orig_value=None, **kwargs):
        """Install files according to the file:* sections in "config"."""
        nodes = {}
        if item == self.KEY:
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
            target = key[len(self.PREFIX):]
            if os.path.exists(target) and kwargs.get("no_overwrite_mode"):
                e = FileOverwriteError(target)
                raise ConfigProcessError([key], None, e)
            self.manager.fs_util.makedirs(self.manager.fs_util.dirname(target))

        # Start worker pool
        nproc = int(ResourceLocator.default().get_conf().get_value(
                ["rose.config_processors.file", "nproc"],
                default=self.NPROC))
        if nproc > len(nodes):
            nproc = len(nodes)
        pool = Pool(processes=nproc)

        # Use worker pool to do the work
        results = []
        for key, node in sorted(nodes.items()):
            result = pool.apply_async(_process_target, [self, config, key, node])
            results.append(result)
        pool.close()
        # N.B. Event messages will appear in the correct order, but not as each
        #      call completes.
        for result in results:
            for message, type, level, prefix, clip in result.get():
                self.manager.event_handler(message, type, level, prefix, clip)

    def process_target(self, config, key, node):
        """Install a target according to a file:target section."""
        target = key[len(self.PREFIX):]

        # FIXME: this is not always necessary
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
            self.manager.event_handler(
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
                    if os.path.exists(target):
                        self.manager.fs_util.delete(target)
                    self._source_export(source, target)
                    self.manager.event_handler(
                            FileSystemEvent("install", target, source))
            elif len(sources) > 1 or len(sources) == 0 and mode != "mkdir":
                if os.path.isdir(target):
                    self.manager.fs_util.delete(target)
                target_file = open(target, 'wb')
                for source in sources:
                    target_file.write(self._source_load(source))
                target_file.close()
                self.manager.event_handler(
                        FileSystemEvent("install", target, source_str))
            else:
                if os.path.isdir(target):
                    for name in os.listdir(target):
                        path = os.path.join(target, name)
                        self.manager.fs_util.delete(path)
                else:
                    self.manager.fs_util.delete(target)
                    self.manager.fs_util.makedirs(target)

            # Checksum
            checksum_expected = node.get_value(["checksum"])
            if checksum_expected is not None:
                target_file = open(target)
                md5 = hashlib.md5()
                md5.update(target_file.read())
                checksum = md5.hexdigest()
                if checksum_expected and checksum_expected != checksum:
                    e = UnmatchedChecksumError(checksum_expected, checksum)
                    raise ConfigProcessError(
                            [key, "checksum"], checksum_expected, e)
                target_file.close()
                self.manager.event_handler(ChecksumEvent(target, checksum))

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
