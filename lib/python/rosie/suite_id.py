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
"""Suite ID utilities.

Classes:
    SuiteId[...]Error - classes for various processing problems.
    SuiteId - class that holds and processes suite id information.

Functions:
    main - CLI interface function.

"""

import os
import re
import rose.env
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Reporter
from rose.resource import ResourceLocator
from rose.suite_engine_proc import SuiteEngineProcessor
import string
import sys
import xml.parsers.expat


class SvnCaller(RosePopener):

    """Call "svn" commands."""

    def __call__(self, *args):
        out, err = self.run_ok("svn", *args)
        return out


class SuiteIdError(ValueError):

    """Base class for all exceptions related to bad IDs."""

    pass


class SuiteIdLatestError(SuiteIdError):

    """Exception raised when the latest ID in a suite repository cannot be
    determined.
    """

    def __str__(self):
        return "%s: cannot determine latest suite ID" % (self.args[0])


class SuiteIdLocationError(SuiteIdError):

    """Exception raised when a location is not associated with a suite ID."""

    def __str__(self):
        return "%s: location not associated with a suite ID" % (self.args[0])


class SuiteIdOverflowError(SuiteIdError):

    """Exception raised when the latest ID in a suite repository cannot be
    incremented.
    """

    def __str__(self):
        return "%s: cannot increment ID" % (self.args[0])


class SuiteIdPrefixError(SuiteIdError):

    """Exception raised when a prefix location cannot be determined."""

    def __str__(self):
        arg = "(default)"
        if self.args:
            arg = self.args[0]
        return "%s: cannot determine prefix location" % (arg)


class SuiteIdTextError(SuiteIdError):

    """Exception raised when an invalid suite ID is specified."""

    def __str__(self):
        return "%s: invalid suite ID" % (self.args[0])


class SuiteId(object):

    """Represent a suite ID."""

    FORMAT_ID = r"%s-%s"
    FORMAT_VERSION = r"/%s@%s"
    IDX_0 = "aa000"
    IDX_LEN = len(IDX_0)
    REC_ID = re.compile("\A(?:(\w+)-)?(\w+)(?:/([^\@/]+))?(?:@([^\@/]+))?\Z")
    BRANCH_TRUNK = "trunk"
    REV_HEAD = "HEAD"
    svn = SvnCaller()

    @classmethod
    def get_latest(cls, prefix=None):
        """Return the previous (latest) ID in the suite repository."""
        config = ResourceLocator.default().get_conf()
        if not prefix:
            prefix = cls.get_prefix_default()
        dir_url = cls.get_prefix_location(prefix)
        for i in range(cls.IDX_LEN - 1):
            out = cls.svn("ls", dir_url)
            if out is None:
                raise SuiteIdLatestError(prefix)
            if not out:
                if i == 0:
                    return None
                raise SuiteIdLatestError(prefix)
            dirs = filter(lambda line: line.endswith("/"), out.splitlines())
            # Note - 'R/O/S/I/E' sorts to top for lowercase initial idx letter
            dir_url = dir_url + "/" + sorted(dirs)[-1].rstrip("/")

        # FIXME: not sure why a closure for "state" does not work here?
        state = {"idx": None, "stack": [], "try_text": False}

        def _handle_tag0(state, name, attr_map):
            if state["idx"]:
                return
            state["stack"].append(name)
            state["try_text"] = (
                state["stack"] == ["log", "logentry", "paths", "path"]
                and attr_map.get("kind") == "dir"
                and attr_map.get("action") == "A")
     
        def _handle_tag1(state, name):
            if state["idx"]:
                return
            state["stack"].pop()

        def _handle_text(state, text):
            if state["idx"] or not state["try_text"]:
                return
            names = text.strip().lstrip("/").split("/", cls.IDX_LEN)
            if len(names) == cls.IDX_LEN:
                idx = "".join(names[0:cls.IDX_LEN])
                if cls.REC_ID.match(idx):
                    state["idx"] = idx

        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = lambda *args: _handle_tag0(state, *args)
        parser.EndElementHandler = lambda *args: _handle_tag1(state, *args)
        parser.CharacterDataHandler = lambda *args: _handle_text(state, *args)
        parser.Parse(cls.svn("log", "--verbose", "--xml", dir_url))
        if not state["idx"]:
            return None
        return cls(id_text=cls.FORMAT_ID % (prefix, state["idx"]))

    @classmethod
    def get_local_copy_root(cls):
        """Return the root directory for hosting the local suite copies."""
        config = ResourceLocator.default().get_conf()
        node = config.get(["rosie-id", "local-copy-root"], no_ignore=True)
        if node:
            local_copy_root = node.value
        else:
            local_copy_root = "$HOME/roses"
        local_copy_root = rose.env.env_var_process(local_copy_root)
        return local_copy_root

    @classmethod
    def get_next(cls, prefix=None):
        """Return the next available ID in a repository."""
        id = cls.get_latest(prefix)
        if id:
            return id.incr()
        elif prefix:
            return cls(id_text=cls.FORMAT_ID % (prefix, cls.IDX_0))
        else:
            return cls(id_text=cls.IDX_0)

    @classmethod
    def get_output_root(cls):
        """Return the root output directory for suites."""
        config = ResourceLocator.default().get_conf()
        node = config.get(["rosie-id", "output-root"], no_ignore=True)
        if node:
            path = node.value
        else:
            suite_engine_proc = SuiteEngineProcessor.get_processor()
            path = os.path.join("~", suite_engine_proc.RUN_DIR_REL_ROOT)
        return rose.env.env_var_process(os.path.expanduser(path))

    @classmethod
    def get_prefix_default(cls):
        """Return the default prefix."""
        config = ResourceLocator.default().get_conf()
        node = config.get(["rosie-id", "prefix-default"], no_ignore=True)
        if node is None:
            raise SuiteIdPrefixError()
        return node.value

    @classmethod
    def get_prefix_location(cls, prefix=None):
        """Return the repository location of a given prefix."""
        if prefix is None:
            prefix = cls.get_prefix_default()
        key = "prefix-location." + prefix
        config = ResourceLocator.default().get_conf()
        node = config.get(["rosie-id", key], no_ignore=True)
        if node is None:
            raise SuiteIdPrefixError(prefix)
        return node.value.rstrip("/")

    @classmethod
    def get_prefix_locations(cls):
        """Return a dict containing the known prefixes and their repository
        locations.
        """
        ret = {}
        config = ResourceLocator.default().get_conf()
        rosie_id_node = config.get(["rosie-id"], no_ignore=True)
        if rosie_id_node is None:
            return ret
        for key, node in rosie_id_node.value.items():
            if node.state:
                continue
            if key.startswith("prefix-location."):
                ret[key[len("prefix-location."):]] = node.value
        return ret

    @classmethod
    def get_prefix_web(cls, prefix=None):
        """Return a url for the prefix repository source url."""
        if prefix is None:
            prefix = cls.get_prefix_default()
        key = "prefix-web." + prefix
        config = ResourceLocator.default().get_conf()
        node = config.get(["rosie-id", key], no_ignore=True)
        if node is None:
            raise SuiteIdPrefixError(prefix)
        return node.value.rstrip("/")

    def __init__(self, id_text=None, location=None):
        """Initialise either from an id_text or from a location."""
        self.prefix = None
        self.idx = None
        self.branch = None
        self.revision = None
        self.modified = False
        self.out_of_date = False
        if id_text:
            self._from_id_text(id_text)
        elif location:
            self._from_location(location)

    def __str__(self):
        return self.FORMAT_ID % (self.prefix, self.idx)

    def __eq__(self, other):
        return (self.to_string_with_version() == other.to_string_with_version()
                and self.modified == other.modified)

    def __ne__(self, other):
        return not self.__eq__(other)

    __repr__ = __str__

    def _from_id_text(self, id_text):
        match = self.REC_ID.match(id_text)
        if not match:
            raise SuiteIdTextError(id_text)
        self.prefix, self.idx, self.branch, self.revision = match.groups()
        if not self.prefix:
            config = ResourceLocator.default().get_conf()
            self.prefix = self.get_prefix_default()
            if not self.prefix:
                raise SuiteIdPrefixError(id_text)

    def _from_location(self, location):
        """Return the ID of a location (origin URL or local copy path).
        """
        # FIXME: not sure why a closure for "state" does not work here?
        info_parser = ParseXML()
        try:
            state = info_parser.parse(self.svn("info", "--xml", location))
        except RosePopenError as e:
            raise SuiteIdLocationError(location)

        info_entry = state["entry"]
        if not info_entry.has_key("url"):
            raise SuiteIdLocationError(location)
        root = info_entry["repository:root"]
        url = info_entry["url"]
        path = url[len(root):]
        if not path:
            raise SuiteIdLocationError(location)
        locations = self.get_prefix_locations()
        if not locations:
            raise SuiteIdLocationError(location)
        for key, value in locations.items():
            if value == root:
                self.prefix = key
                break
        else:
            raise SuiteIdPrefixError(location)
        names = path.lstrip("/").split("/", self.IDX_LEN + 1)
        if len(names) < self.IDX_LEN:
            raise SuiteIdLocationError(location)
        idx = "".join(names[0:self.IDX_LEN])
        if not self.REC_ID.match(idx):
            raise SuiteIdLocationError(location)
        self.idx = idx
        if len(names) > self.IDX_LEN:
            self.branch = names[self.IDX_LEN]
        if info_entry.has_key("commit:revision"):
            self.revision = info_entry["commit:revision"]
        self._set_statuses(location)

    def _set_statuses(self, path):
        if os.path.exists(path):
            try:
                status_lines = self.svn("st", "-u", path).splitlines()
            except RosePopenError:
                raise SuiteIdLocationError(path)
            latest_rev = int(status_lines.pop().split()[-1])
            self.out_of_date = (latest_rev > int(self.revision))
            self.modified = any([l[:7].strip() for l in status_lines])

    def incr(self):
        """Return an SuiteId object that represents the ID after this ID."""
        idx_chars = list(self.idx)
        incr_next = True
        i = self.IDX_LEN
        alphabet = string.lowercase
        while incr_next and i:
            i -= 1
            incr_next = False
            if idx_chars[i].isdigit():
                idx_chars[i] = str((int(idx_chars[i]) + 1) % 10)
                incr_next = (idx_chars[i] == "0")
            else:
                index = alphabet.index(idx_chars[i])
                new_index = (index + 1) % len(alphabet)
                idx_chars[i] = alphabet[new_index]
                incr_next = (new_index == 0)
            if incr_next and i == 0:
                raise SuiteIdOverflowError(self)
        idx = "".join(idx_chars)
        return self.__class__(id_text=self.FORMAT_ID % (self.prefix, idx))

    def to_origin(self):
        """Return the origin URL of this ID."""
        return self.get_prefix_location(self.prefix) + "/" + "/".join(self.idx)

    def to_local_copy(self):
        """Return the local copy path of this ID."""
        local_copy_root = self.get_local_copy_root()
        return os.path.join(local_copy_root, "%s-%s" % (self.prefix, self.idx))

    def to_string_with_version(self):
        branch = self.branch
        if not branch:
            branch = self.BRANCH_TRUNK
        revision = self.revision
        if not revision:
            revision = self.REV_HEAD
        return str(self) + self.FORMAT_VERSION % (branch, revision)

    def to_web(self):
        """Return the source browse URL for this suite."""
        prefix_source = self.get_prefix_web(self.prefix)
        url = prefix_source + "/browser/" + "/".join(self.idx)
        branch = self.branch
        if not branch:
            branch = self.BRANCH_TRUNK
        revision = self.revision
        if not revision:
            revision = self.REV_HEAD
        return url + "/" + branch + "?rev=" + revision

    def to_output(self):
        """Return the output directory for this suite."""
        output_root = self.get_output_root()
        directory = os.path.join(output_root, str(self), "log")
        return directory


class ParseXML(object):

    def __init__(self):
        self.state = {"entry": {}, "index": None, "stack": []}
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self._handle_tag0
        self.parser.EndElementHandler = self._handle_tag1
        self.parser.CharacterDataHandler = self._handle_text

    def parse(self, text):
        self.parser.Parse(text)
        return self.state

    def _handle_tag0(self, name, attr_map):
        self.state["stack"].append(name)
        self.state["index"] = ":".join(self.state["stack"][2:])
        if self.state["entry"]:
            self.state["entry"][self.state["index"]] = ""
        for key, value in attr_map.items():
            name = key
            if self.state["index"]:
                name = self.state["index"] + ":" + key
            self.state["entry"][name] = value
    
    def _handle_tag1(self, name):
        self.state["stack"].pop()

    def _handle_text(self, text):
        if self.state["index"]:
            self.state["entry"][self.state["index"]] += text.strip()


def main():
    """Implement the "rose suite-id" command."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("latest", "next", "to_local_copy", "to_origin",
                              "to_output", "to_web")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    SuiteId.svn.event_handler = report # FIXME: ugly?
    arg = None
    if args:
        arg = args[0]

    try:
        if opts.to_origin:
            for arg in args:
                report(str(SuiteId(id_text=arg).to_origin()) + "\n", level=0)
        elif opts.to_local_copy:
            for arg in args:
                report(str(SuiteId(id_text=arg).to_local_copy()) + "\n", level=0)
        elif opts.to_output:
            for arg in args:
                report(str(SuiteId(id_text=arg).to_output()) + "\n", level=0)
        elif opts.to_web:
            for arg in args:
                report(str(SuiteId(id_text=arg).to_web()) + "\n", level=0)
        elif opts.latest:
            report(str(SuiteId.get_latest(prefix=arg)) + "\n", level=0)
        elif opts.next:
            report(str(SuiteId.get_next(prefix=arg)) + "\n", level=0)
        else:
            if not arg:
                arg = os.getcwd()
            report(str(SuiteId(location=arg)) + "\n", level=0)
    except SuiteIdError as e:
        report(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
