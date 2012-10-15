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
"""Process a file: section in a rose.config.ConfigNode."""

import hashlib
import os
import re
from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.reporter import Event
from rose.config_processor import ConfigProcessError, ConfigProcessorBase
import shlex
import shutil
import tempfile


class UnmatchedChecksumError(Exception):

    def __str__(self):
        return ("Unmatched checksum, expected=%s, actual=%s" % tuple(self))


class ConfigProcessFileEvent(Event):

    IM_CONTENT = "IM_CONTENT"
    IM_DIR = "IM_DIR"
    IM_SYMLINK = "IM_SYMLINK"

    def __init__(self, target, source_str, install_mode, checksum):
        self.target = target
        self.source_str = source_str
        self.install_mode = install_mode
        self.checksum = checksum
        Event.__init__(self, target, source_str, install_mode, checksum)

    def __str__(self):
        out_mode = ""
        if self.install_mode == self.IM_CONTENT:
            out_mode = " <= (content) "
        elif self.install_mode == self.IM_DIR:
            out_mode = " <= (directory)"
        elif self.install_mode == self.IM_SYMLINK:
            out_mode = " <= (symlink) "
        elif self.source_str:
            out_mode = " <= "
        ret = "install: %s%s%s" % (self.target, out_mode, self.source_str)
        if self.checksum:
            ret += "\nchecksum: %s: %s" % (self.target, self.checksum)
        return ret


class ConfigProcessorForFile(ConfigProcessorBase):

    RE_FCM_SRC = re.compile(r"(?:\A[A-z][\w\+\-\.]*:)|(?:@[^/@]+\Z)")

    def process(self, config, item, orig_keys=None, orig_value=None):
        """Install a file according to a section in "config"."""
        if config.get([item], no_ignore=True) is None:
            return
        target = item[len("file:"):]
        if os.path.isdir(target):
            shutil.rmtree(target)
        elif os.path.isfile(target):
            os.unlink(target)
        target_dir = os.path.dirname(target)
        if target_dir and not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        install_mode = None
        checksum = None
        keys = [item, "content"]
        if config.get(keys, no_ignore=True):
            value = config.get(keys).value
            contents = shlex.split(value)
            target_file = open(target, 'wb')
            for content in contents:
                s = self.manager.process(config, content, keys, value)
                target_file.write(s)
            target_file.close()
            source_str = " ".join(contents)
            install_mode = ConfigProcessFileEvent.IM_CONTENT
        else:
            source_str = ""
            keys = [item, "source"]
            source_node = config.get([item, "source"], no_ignore=True)
            if source_node:
                source_str = source_node.value
            sources = []
            for source in shlex.split(source_str):
                try:
                    source = env_var_process(source)
                except UnboundEnvironmentVariableError as e:
                    raise ConfigProcessError(keys, source_node.value, e)
                sources.append(os.path.expanduser(source))
            mode = None
            keys = [item, "mode"]
            mode_node = config.get(keys, no_ignore=True)
            if mode_node:
                mode = mode_node.value
            if len(sources) > 1:
                target_file = open(target, 'wb')
                for source in sources:
                    target_file.write(self._source_load(source))
                target_file.close()
            elif sources:
                source = sources[0]
                if mode == "symlink":
                    os.stat(source)
                    os.symlink(source, target)
                    install_mode = ConfigProcessFileEvent.IM_SYMLINK
                else:
                    self._source_export(source, target)
            elif mode == "mkdir":
                os.mkdir(target)
                install_mode = ConfigProcessFileEvent.IM_DIR
            else:
                open(target, 'wb').close()
            keys = [item, "checksum"]
            checksum_node = config.get(keys, no_ignore=True)
            if checksum_node is not None:
                checksum_expected = checksum_node.value
                target_file = open(target)
                md5 = hashlib.md5()
                md5.update(target_file.read())
                checksum = md5.hexdigest()
                if checksum_expected and checksum_expected != checksum:
                    e = UnmatchedChecksumError(checksum_expected, checksum)
                    raise ConfigProcessError(keys, checksum_expected, e)
                target_file.close()
        event = ConfigProcessFileEvent(target,
                                       source_str,
                                       install_mode,
                                       checksum)
        self.manager.event_handler(event)


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
