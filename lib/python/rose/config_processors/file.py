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
from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.fs_util import FileSystemEvent
from rose.reporter import Event
from rose.config_processor import ConfigProcessError, ConfigProcessorBase
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

    def __str__(self):
        return ("Unmatched checksum, expected=%s, actual=%s" % tuple(self))


class ChecksumEvent(Event):

    def __str__(self):
        return "checksum: %s: %s" % self.args


class ConfigProcessorForFile(ConfigProcessorBase):

    KEY = "file"
    RE_FCM_SRC = re.compile(r"(?:\A[A-z][\w\+\-\.]*:)|(?:@[^/@]+\Z)")

    def process(self, config, item, orig_keys=None, orig_value=None, **kwargs):
        """Install a file according to a section in "config"."""
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
        for key, node in sorted(nodes.items()):
            target = key[len(self.PREFIX):]
            if os.path.exists(target) and kwargs.get("no_overwrite_mode"):
                e = FileOverwriteError(target)
                raise ConfigProcessError([key], None, e)
            self.manager.fs_util.makedirs(self.manager.fs_util.dirname(target))

            # FIXME: this is not always necessary
            self.manager.fs_util.delete(target)
            content_node = node.get(["content"], no_ignore=True)
            if content_node:
                # Embedded content
                if os.path.isdir(target):
                    self.manager.fs_util.delete(target)
                target_file = open(target, 'wb')
                contents = shlex.split(content_node.value)
                for content in contents:
                    target_file.write(self.manager.process(
                            config, content,
                            [key, "content"], content_node.value))
                target_file.close()
                self.manager.event_handler(
                        FileSystemEvent("content", target, " ".join(contents)))
            else:
                # Free format file
                source_str = getattr(node.get(["source"], no_ignore=True),
                                     "value", "")
                sources = []
                for source in shlex.split(source_str):
                    try:
                        source = env_var_process(source)
                    except UnboundEnvironmentVariableError as e:
                        raise ConfigProcessError(
                                [key, "source"], source_str, e)
                    sources.append(os.path.expanduser(source))
                mode = getattr(node.get(["mode"], no_ignore=True),
                               "value", None)
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
                checksum_node = node.get(["checksum"], no_ignore=True)
                if checksum_node is not None:
                    checksum_expected = checksum_node.value
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
