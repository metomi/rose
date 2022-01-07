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
# -----------------------------------------------------------------------------
"""Suite ID utilities.

Classes:
    SuiteId[...]Error - classes for various processing problems.
    SuiteId - class that holds and processes suite id information.

Functions:
    main - CLI interface function.

"""
import json
import os
from pathlib import Path
import re
import shlex
import string
import sys
import traceback
from typing import Optional
import xml.parsers.expat

import metomi.rose.env
from metomi.rose.loc_handlers.svn import SvnInfoXMLParser
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopener, RosePopenError
from metomi.rose.reporter import Reporter
from metomi.rose.resource import ResourceLocator
from metomi.rose.suite_engine_proc import NoSuiteLogError, SuiteEngineProcessor


class SvnCaller(RosePopener):

    """Call "svn" commands."""

    def __call__(self, *args):
        environ = dict(os.environ)
        environ["LANG"] = "C"
        return self.run_ok("svn", env=environ, *args)[0]


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


class SuiteId:

    """Represent a suite ID."""

    FORMAT_IDX = r"%s-%s"
    FORMAT_VERSION = r"/%s@%s"
    SID_0 = "aa000"
    SID_LEN = len(SID_0)
    REC_IDX = re.compile(r"\A(?:(\w+)-)?(\w+)(?:/([^\@/]+))?(?:@([^\@/]+))?\Z")
    BRANCH_TRUNK = "trunk"
    REV_HEAD = "HEAD"
    VC_FILENAME = "log/version/vcs.json"
    svn = SvnCaller()

    STATUS_CR = "X"
    STATUS_DO = ">"
    STATUS_OK = "="
    STATUS_MO = "M"
    STATUS_NO = " "
    STATUS_SW = "S"
    STATUS_UP = "<"

    @classmethod
    def get_latest(cls, prefix=None):
        """Return the previous (latest) ID in the suite repository."""
        if not prefix:
            prefix = cls.get_prefix_default()
        dir_url = cls.get_prefix_location(prefix)
        for i in range(cls.SID_LEN - 1):
            out = cls.svn("ls", dir_url)
            if out is None:
                raise SuiteIdLatestError(prefix)
            if not out:
                if i == 0:
                    return None
                raise SuiteIdLatestError(prefix)
            dirs = [
                line
                for line in out.splitlines()
                if line.endswith("/")
            ]
            # Note - 'R/O/S/I/E' sorts to top for lowercase initial idx letter
            dir_url = dir_url + "/" + sorted(dirs)[-1].rstrip("/")

        # FIXME: not sure why a closure for "state" does not work here?
        state = {"idx-sid": None, "stack": [], "try_text": False}

        def _handle_tag0(state, name, attr_map):
            """Handle XML start tag."""
            if state["idx-sid"]:
                return
            state["stack"].append(name)
            state["try_text"] = (
                state["stack"] == ["log", "logentry", "paths", "path"]
                and attr_map.get("kind") == "dir"
                and attr_map.get("action") == "A"
            )

        def _handle_tag1(state, _):
            """Handle XML end tag."""
            if state["idx-sid"]:
                return
            state["stack"].pop()

        def _handle_text(state, text):
            """Handle XML text."""
            if state["idx-sid"] or not state["try_text"]:
                return
            names = text.strip().lstrip("/").split("/", cls.SID_LEN)
            if len(names) == cls.SID_LEN:
                sid = "".join(names[0 : cls.SID_LEN])
                if cls.REC_IDX.match(sid):
                    state["idx-sid"] = sid

        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = lambda *args: _handle_tag0(state, *args)
        parser.EndElementHandler = lambda *args: _handle_tag1(state, *args)
        parser.CharacterDataHandler = lambda *args: _handle_text(state, *args)
        parser.Parse(cls.svn("log", "--verbose", "--xml", dir_url))
        if not state["idx-sid"]:
            return None
        return cls(id_text=cls.FORMAT_IDX % (prefix, state["idx-sid"]))

    @classmethod
    def get_checked_out_suite_ids(cls, prefix=None, user=None):
        """Returns a list of suite IDs with local copies."""
        local_copies = []
        local_copy_root = cls.get_local_copy_root(user)

        if not os.path.isdir(local_copy_root):
            return local_copies
        for path in os.listdir(local_copy_root):
            location = os.path.join(local_copy_root, path)
            try:
                id_ = cls(location=location)
            except SuiteIdError:
                continue
            if (prefix is None or id_.prefix == prefix) and str(id_) == path:
                local_copies.append(id_)
        return local_copies

    @classmethod
    def get_local_copy_root(cls, user=None):
        """Return the root directory for hosting the local suite copies."""
        config = ResourceLocator.default().get_conf()
        value = config.get_value(["rosie-id", "local-copy-root"])
        if user:
            # N.B. Only default location at the moment.
            # In theory, we can try obtaining the setting from the user's
            # "~/.metomi/rose.conf", but it may contain environment variables
            # that are only correct in the user's environment.
            local_copy_root = os.path.expanduser(
                os.path.join("~" + user, "roses")
            )
        elif value:
            local_copy_root = metomi.rose.env.env_var_process(value)
        else:
            local_copy_root = os.path.expanduser(os.path.join("~", "roses"))
        return local_copy_root

    @classmethod
    def from_idx_branch_revision(cls, idx, branch=None, revision=None):
        """Factory method from idx, (branch and revision)."""
        if idx is None:
            return None
        id_ = cls(id_text=idx)
        if not branch:
            branch = cls.BRANCH_TRUNK
        if not revision:
            revision = cls.REV_HEAD
        id_.branch = branch
        id_.revision = revision
        if id_.revision == cls.REV_HEAD:
            id_.to_string_with_version()
        return id_

    @classmethod
    def get_next(cls, prefix=None):
        """Return the next available ID in a repository."""
        id_ = cls.get_latest(prefix)
        if id_:
            return id_.incr()
        elif prefix:
            return cls(id_text=cls.FORMAT_IDX % (prefix, cls.SID_0))
        else:
            return cls(id_text=cls.SID_0)

    @classmethod
    def get_prefix_default(cls):
        """Return the default prefix."""
        config = ResourceLocator.default().get_conf()
        value = config.get_value(["rosie-id", "prefix-default"])
        if not value or not value.strip():
            raise SuiteIdPrefixError()
        return shlex.split(value)[0]

    @classmethod
    def get_prefix_from_location_root(cls, root):
        locations = cls.get_prefix_locations()
        if not locations:
            raise SuiteIdLocationError(root)
        for key, value in locations.items():
            if value == root:
                return key
        else:
            raise SuiteIdPrefixError(root)

    @classmethod
    def get_prefix_location(cls, prefix=None):
        """Return the repository location of a given prefix."""
        if prefix is None:
            prefix = cls.get_prefix_default()
        key = "prefix-location." + prefix
        config = ResourceLocator.default().get_conf()
        value = config.get_value(["rosie-id", key])
        if value is None:
            raise SuiteIdPrefixError(prefix)
        return value.rstrip("/")

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
                ret[key[len("prefix-location.") :]] = node.value
        return ret

    @classmethod
    def get_prefix_web(cls, prefix=None):
        """Return a url for the prefix repository source url."""
        if prefix is None:
            prefix = cls.get_prefix_default()
        key = "prefix-web." + prefix
        config = ResourceLocator.default().get_conf()
        value = config.get_value(["rosie-id", key])
        if value is None:
            raise SuiteIdPrefixError(prefix)
        return value.rstrip("/")

    def __init__(self, id_text=None, location=None):
        """Initialise either from an id_text or from a location."""
        self.prefix = None  # Repos id e.g. repo1
        self.sid = None  # Short/Sub/Suffix id e.g. aa000
        self.idx = None  # Full idx, join of self.prefix and self.sid
        self.branch = None
        self.revision = None
        # self.statuses = {
        #     None: STATUS_??, # current user
        #     "user1": STATUS_??,
        #     # ...
        # }
        self.statuses = None
        if id_text:
            self._from_id_text(id_text)
        elif location:
            self._from_location(location)
        else:
            raise SuiteIdTextError(None)

    def __str__(self):
        return self.idx

    def __eq__(self, other):
        return (
            self.to_string_with_version() == other.to_string_with_version()
            and self.get_status() == other.get_status()
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    __repr__ = __str__

    def _get_sid(self):
        """Strip ID of prefix and return the result."""
        return self.idx.split("-", 1)[1]

    def _from_id_text(self, id_text):
        """Parse the ID text."""
        match = self.REC_IDX.match(id_text)
        if not match:
            raise SuiteIdTextError(id_text)
        self.prefix, self.sid, self.branch, self.revision = match.groups()
        try:
            self.revision = int(self.revision)
        except (TypeError, ValueError):
            pass
        if not self.prefix:
            self.prefix = self.get_prefix_default()
            if not self.prefix:
                raise SuiteIdPrefixError(id_text)
        self.idx = self.FORMAT_IDX % (self.prefix, self.sid)

    def _from_location(self, location):
        """Return the ID of a location (origin URL or local copy path)."""
        # Get Version control file location and convert to a URL if rqd.
        loc = self._find_vc_file_from_location(location)
        if loc:
            location = self._parse_cylc_vc_file(loc)

        # Assume location is a Subversion working copy of a Rosie suite
        info_parser = SvnInfoXMLParser()
        try:
            info_entry = info_parser.parse(
                self.svn("info", "--xml", location))
        except RosePopenError:
            raise SuiteIdLocationError(location)
        if "url" not in info_entry:
            raise SuiteIdLocationError(location)
        root = info_entry["repository:root"]
        url = info_entry["url"]
        path = url[len(root) :]
        if not path:
            raise SuiteIdLocationError(location)
        self.prefix = self.get_prefix_from_location_root(root)
        names = path.lstrip("/").split("/", self.SID_LEN + 1)
        if len(names) < self.SID_LEN:
            raise SuiteIdLocationError(location)
        sid = "".join(names[0 : self.SID_LEN])
        if not self.REC_IDX.match(sid):
            raise SuiteIdLocationError(location)
        self.idx = self.FORMAT_IDX % (self.prefix, sid)
        self.sid = sid
        if len(names) > self.SID_LEN:
            self.branch = names[self.SID_LEN]
        if "commit:revision" in info_entry:
            self.revision = info_entry["commit:revision"]

    @staticmethod
    def _find_vc_file_from_location(location):
        """Search a location and parents for a version control log file.

        Args:
            location: Path to search.

        Returns:
            If a file is found, a path, else None.
        """
        suite_engine_proc = SuiteEngineProcessor.get_processor()
        suite_dir_rel_root = getattr(
            suite_engine_proc, "SUITE_DIR_REL_ROOT", None
        )
        loc = Path(location).expanduser().resolve()
        if suite_dir_rel_root:
            sdrr = Path('~', suite_dir_rel_root).expanduser().resolve()
            try:
                loc.relative_to(sdrr)
            except ValueError:
                # Not an installed Cylc8 workflow run directory
                pass
            else:
                # Slightly odd construction = loc + parents
                for loc in (loc.relative_to(sdrr) / '_').parents:
                    vcfilepath = sdrr / loc / SuiteId.VC_FILENAME
                    if os.access(vcfilepath, os.F_OK | os.R_OK):
                        return vcfilepath
        return None

    @staticmethod
    def _parse_cylc_vc_file(fpath: str) -> Optional[str]:
        """Take a path to a Cylc VC file and returns an svn URL.

        Args:
            fpath: Location of Cylc Version Control log file.

        Returns: SVN location, e.g. '/a/b/c@4242', or None if not SVN repo.
        """
        with open(fpath, 'r') as f:
            info: dict = json.loads(f.read())
        vcsystem = info['version control system']
        url = info.get('url')
        rev = info.get('revision')
        if vcsystem == 'svn' and url and rev:
            return url + "@" + rev
        return None

    def get_status(self, user=None, force_mode=False):
        """Determine and return local status for this suite.

        If user is not specified, assume current user ID.

        If force_mode is specified, always update status. Otherwise, use
        previously determined status.

        """
        if (
            not force_mode
            and self.statuses is not None
            and self.statuses.get(user) is not None
        ):
            return self.statuses.get(user)
        if self.statuses is None:
            self.statuses = {}
        if user not in self.statuses:
            self.statuses[user] = {}
        location = self.to_local_copy(user)
        try:
            location_suite_id = SuiteId(location=location)
        except SuiteIdLocationError:
            self.statuses[user] = self.STATUS_NO
        else:
            if self.branch != location_suite_id.branch:
                self.statuses[user] = self.STATUS_SW
            elif location_suite_id.revision and int(self.revision) > int(
                location_suite_id.revision
            ):
                self.statuses[user] = self.STATUS_UP
            elif location_suite_id.revision and int(self.revision) < int(
                location_suite_id.revision
            ):
                self.statuses[user] = self.STATUS_DO
            else:
                try:
                    out = self.svn("status", location)
                except RosePopenError:
                    # Corrupt working copy.
                    self.statuses[user] = self.STATUS_CR
                else:
                    if any(line[:7].strip() for line in out.splitlines()):
                        self.statuses[user] = self.STATUS_MO
                    else:
                        self.statuses[user] = self.STATUS_OK
        return self.statuses[user]

    def incr(self):
        """Return an SuiteId object that represents the ID after this ID."""
        sid_chars = list(self._get_sid())
        incr_next = True
        i = self.SID_LEN
        alphabet = string.ascii_lowercase
        while incr_next and i:
            i -= 1
            incr_next = False
            if sid_chars[i].isdigit():
                sid_chars[i] = str((int(sid_chars[i]) + 1) % 10)
                incr_next = sid_chars[i] == "0"
            else:
                index = alphabet.index(sid_chars[i])
                new_index = (index + 1) % len(alphabet)
                sid_chars[i] = alphabet[new_index]
                incr_next = new_index == 0
            if incr_next and i == 0:
                raise SuiteIdOverflowError(self)
        self.sid = "".join(sid_chars)
        return self.__class__(
            id_text=self.FORMAT_IDX % (self.prefix, self.sid)
        )

    def to_origin(self):
        """Return the origin URL of this ID."""
        return (
            self.get_prefix_location(self.prefix)
            + "/"
            + "/".join(self._get_sid())
        )

    def to_local_copy(self, user=None):
        """Return the local copy path of this ID."""
        return os.path.join(self.get_local_copy_root(user), self.idx)

    def to_string_with_version(self):
        """Return the full ID in the form prefix-idx/branch@rev."""
        branch = self.branch
        if not branch:
            branch = self.BRANCH_TRUNK
        revision = self.revision
        if not revision:
            revision = self.REV_HEAD
        if revision == self.REV_HEAD:
            location = self.to_origin()
            location += self.FORMAT_VERSION % (branch, str(revision))
            info_parser = SvnInfoXMLParser()
            try:
                info_entry = info_parser.parse(
                    self.svn("info", "--xml", location)
                )
            except RosePopenError:
                raise SuiteIdTextError(location)
            else:
                if "commit:revision" in info_entry:
                    revision = int(info_entry["commit:revision"])
        return str(self) + self.FORMAT_VERSION % (branch, revision)

    def to_web(self):
        """Return the source browse URL for this suite."""
        # FIXME: This is Trac specific.
        prefix_source = self.get_prefix_web(self.prefix)
        url = prefix_source + "/" + "/".join(self._get_sid())
        branch = self.branch
        if not branch:
            branch = self.BRANCH_TRUNK
        revision = self.revision
        if not revision:
            revision = self.REV_HEAD
        return url + self.FORMAT_VERSION % (branch, revision)


def main():
    """Implement the "rose suite-id" command."""
    opt_parser = RoseOptionParser(
        description='''
Utility for working with suite IDs.

EXAMPLES:
    # Print the repository URL of a given suite ID
    rosie id --to-origin mo1-abc45

    # Print the local location of a given suite ID
    rosie id --to-local-copy mo1-abc45

    # Print the web URL of a given suite ID
    rosie id --to-web mo1-abc45

    # Print suite ID of working copy in $PWD
    rosie id

    # Print suite ID of working copy in a directory
    rosie id /path/to/working/copy

    # Print suite ID of a given URL
    rosie id svn://fcm1/rose_mo1_svn/a/b/c/4/5

    # Print latest suite ID in the default repository
    rosie id --latest

    # Print latest suite ID in the given repository
    rosie id --latest mot

    # Print next suite ID in the default repository
    rosie id --next
        ''',
    )
    opt_parser.add_my_options(
        "latest", "next", "to_local_copy", "to_origin", "to_web"
    )
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    SuiteId.svn.event_handler = report  # FIXME: ugly?
    arg = None
    if args:
        arg = args[0]

    try:
        if opts.to_origin:
            for arg in args:
                report(str(SuiteId(id_text=arg).to_origin()) + "\n", level=0)
        elif opts.to_local_copy:
            for arg in args:
                report(
                    str(SuiteId(id_text=arg).to_local_copy()) + "\n", level=0
                )
        elif opts.to_web:
            for arg in args:
                report(str(SuiteId(id_text=arg).to_web()) + "\n", level=0)
        elif opts.latest:
            suite_id = SuiteId.get_latest(prefix=arg)
            if suite_id is not None:
                report(str(suite_id) + "\n", level=0)
        elif opts.next:
            suite_id = SuiteId.get_next(prefix=arg)
            if suite_id is not None:
                report(str(suite_id) + "\n", level=0)
        else:
            if not arg:
                arg = os.getcwd()
            report(str(SuiteId(location=arg)) + "\n", level=0)
    except (NoSuiteLogError, SuiteIdError) as exc:
        report(exc)
        if opts.debug_mode:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
