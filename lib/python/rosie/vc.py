# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
"""Wrap version control system functionalities required by Rosie."""

import atexit
from fnmatch import fnmatch
import os
import pwd
import re
import rose.config
import rose.external
import rose.metadata_check
import rose.reporter
from rose.fs_util import FileSystemUtil
from rose.config_cli import get_meta_path
from rose.macro import (load_meta_config, add_site_meta_paths,
                        add_env_meta_paths)
from rose.macros import DefaultValidators
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Event, Reporter
from rose.resource import ResourceLocator
from rosie.suite_id import SuiteId, SuiteIdOverflowError, SuiteIdPrefixError
import shlex
import shutil
from StringIO import StringIO
import sys
import tempfile
import time
from urlparse import urlparse


CREATE_INFO_CONFIG_COMMENT = """
# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
"""


class FileExistError(Exception):
    """Raised when a file exists and can't be overwritten.

    e.args is a list containing the items that cannot be overwritten.

    """
    def __str__(self):
        return "%s: already exists" % " ".join(self.args)


class LocalCopyStatusError(Exception):
    """Raised when a local copy contains uncommitted changes.

    It also cannot be overwritten.
    e.id is the SuiteId of the suite.
    e.status is the "svn status" output of the local copy.

    """
    def __init__(self, id, status):
        self.id = id
        self.status = status
        super(LocalCopyStatusError, self).__init__(id, status)

    def __str__(self):
        data = (str(self.id), self.id.to_local_copy(), self.status)
        return "%s: %s: local copy has uncommitted changes:\n%s" % data


class SuiteInfoFieldError(Exception):
    """Raised when the rose-suite.info doesn't contain a required field."""
    def __str__(self):
        return "rose-suite.info: compulsory field \"%s\" not defined" % self.args[0]


class SuiteInfoError(Exception):
    """Raised when the rose-suite.info doesn't contain the required
    information.
    """
    def __str__(self):
        return "rose-suite.info:\n \"%s\"" % self.args[0]


class LocalCopyCreateEvent(Event):
    """An event raised after the creation of a local copy of a suite.

    event.args[0] is the SuiteId of the suite.

    """
    def __str__(self):
        id = self.args[0]
        return "%s: local copy created at %s" % (str(id), id.to_local_copy())


class LocalCopyCreateSkipEvent(Event):
    """An event raised after skipped creation of a local suite copy.

    event.args[0] is the SuiteId of the suite.

    """

    KIND = Reporter.KIND_ERR

    def __str__(self):
        id = self.args[0]
        return "%s: skip, local copy already exists at %s" % (str(id), id.to_local_copy())


class SuiteCreateEvent(Event):
    """An event raised when a suite is created.

    event.args[0] is the SuiteId of the suite.

    """

    def __str__(self):
        id = self.args[0]
        return "%s: created at %s" % (str(id), id.to_origin())


class SuiteCopyEvent(Event):
    """An event raised when copying suite items into a new suite.

    event.args[0] is the SuiteId of the target suite.
    event.args[1] is the SuiteId of the source suite.

    """

    def __str__(self):
        return "%s: copied items from %s" % tuple(self.args)


class SuiteDeleteEvent(Event):
    """An event raised after the delete of a suite.

    event.args[0] is the SuiteId of the suite.

    """

    def __str__(self):
        id = self.args[0]
        return "delete: %s" % id.to_origin()


class RosieVCClient(object):

    """Client for version control functionalities."""

    SUBVERSION_SERVERS_CONF = "~/.subversion/servers"

    def __init__(self, event_handler=None, popen=None, fs_util=None,
                 force_mode=False):
        if event_handler is None:
            event_handler = self._dummy
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        self.popen = popen
        if fs_util is None:
            fs_util = FileSystemUtil(event_handler)
        self.fs_util = fs_util
        self.force_mode = force_mode
        self._work_dir = None
        atexit.register(self._delete_work_dir)
        self.subversion_servers_conf = None
        subversion_servers_conf = os.getenv("ROSIE_SUBVERSION_SERVERS_CONF")
        if subversion_servers_conf:
            self.subversion_servers_conf = subversion_servers_conf
        else:
            subversion_servers_conf = os.path.expanduser(
                                        self.SUBVERSION_SERVERS_CONF)
            if os.path.exists(subversion_servers_conf):
                self.subversion_servers_conf = subversion_servers_conf

    def _delete_work_dir(self):
        if self._work_dir is not None and os.path.isdir(self._work_dir):
            shutil.rmtree(self._work_dir)
            self._work_dir = None

    def _dummy(*args, **kwargs):
        pass

    def _get_work_dir(self):
        if self._work_dir is None:
            self._work_dir = tempfile.mkdtemp()
        return self._work_dir

    def checkout(self, id):
        """Create a local copy of a suite with the given ID.

        Return the SuiteId of the suite on success.

        """
        if isinstance(id, str):
            id = SuiteId(id_text=id)
        if id.revision is None:
            id.revision = id.REV_HEAD
        if id.branch is None:
            id.branch = id.BRANCH_TRUNK
        local_copy = id.to_local_copy()
        if os.path.exists(local_copy):
            id0 = SuiteId(location=local_copy)
            if id.to_string_with_version() == id0.to_string_with_version():
                self.event_handler(LocalCopyCreateSkipEvent(id))
                return id
            elif self.force_mode:
                self.fs_util.delete(local_copy)
            else:
                raise FileExistError(local_copy)
        local_copy_dir = os.path.dirname(local_copy)
        if not os.path.isdir(local_copy_dir):
            self.fs_util.makedirs(os.path.dirname(local_copy))
        origin = "%s/%s@%s" % (id.to_origin(), id.branch, id.revision)
        self.popen("svn", "checkout", "-q", origin, local_copy)
        self.event_handler(LocalCopyCreateEvent(id))
        return id

    def create(self, info_config, from_id=None, prefix=None,
               meta_suite_mode=True):
        """Create a suite.

        info_config -- A rose.config.ConfigNode object, which will be used as
                       the content of the "rose-suite.info" file of the new
                       suite.
        from_id -- If defined, copy items from it.
        prefix -- If defined, create the suite in the suite repository named by
                  the prefix instead of the default one.
        meta_suite_mode -- If True, create the special metadata suite.
                           Ignored if from_id is not None.

        Return the SuiteId of the suite on success.

        """
        if from_id is not None:
            return self._copy(info_config, from_id)
        new_id = None
        while new_id is None:
            if meta_suite_mode:
                if prefix is None:
                    new_id = SuiteId(id_text="ROSIE")
                else:
                    idx = SuiteId.FORMAT_IDX % (prefix, "ROSIE")
                    new_id = SuiteId(id_text=idx)
            else:
                new_id = SuiteId.get_next(prefix)
            new_origin = new_id.to_origin() + "/" + new_id.BRANCH_TRUNK
            dir = self._get_work_dir()
            rose.config.dump(info_config, os.path.join(dir, "rose-suite.info"))
            open(os.path.join(dir, "rose-suite.conf"), "w").close()
            try:
                self.popen("svn", "import",
                           "-q",
                           "-m", "%s: new suite." % str(new_id),
                           dir,
                           new_origin)
                self.event_handler(SuiteCreateEvent(new_id))
            except RosePopenError as e:
                try:
                    self.popen("svn", "info", new_origin)
                    if not meta_suite_mode:
                        new_id = None
                except RosePopenError:
                    raise e
            finally:
                self._delete_work_dir()
        return new_id

    def delete(self, id, local_only=False):
        """Delete the local copy and the origin of a suite.

        It takes the suite ID as an argument.
        Return the SuiteId of the suite on success.

        """
        if isinstance(id, str):
            id = SuiteId(id_text=id)
        local_copy = id.to_local_copy()
        if os.path.exists(local_copy):
            if not self.force_mode:
                status = self.popen("svn", "status", local_copy)[0]
                if status:
                    raise LocalCopyStatusError(id, status)
            if os.getcwd() == local_copy:
                self.fs_util.chdir(os.path.expanduser("~"))
            self.fs_util.delete(local_copy)
        if not local_only:
            self.popen("svn", "delete",
                       "-q", "-m", "%s: deleted." % str(id),
                       id.to_origin())
            self.event_handler(SuiteDeleteEvent(id))
        return id

    def generate_info_config(self, from_id=None, prefix=None, project=None,
                             info_config=""):
        """Generate a rose.config.ConfigNode for a rose-suite.info.

        This is suitable for passing into the create method of this
        class.
        If from_id is defined, copy items from it.
        Return the rose.config.ConfigNode instance.

        """
        from_project = None
        from_title = None
        if from_id is not None:
            from_info_url = "%s/%s/rose-suite.info@%s" % (from_id.to_origin(),
                                                          from_id.branch,
                                                          from_id.revision)
            out_data = self.popen("svn", "cat", from_info_url)[0]
            from_config = rose.config.load(StringIO(out_data))

        res_loc = ResourceLocator.default()
        older_config = None
        if info_config:
            older_config = info_config
        info_config = rose.config.ConfigNode()

        # Determine project if given as a command-line option on create
        if from_id is None and project is not None:
            info_config.set(["project"], project)

        # Set the compulsory fields and use the project and metadata if
        #  available.
        meta_config = load_meta_config(info_config, directory=None,
                                       config_type=rose.INFO_CONFIG_NAME,
                                       error_handler=None,
                                       ignore_meta_error=False)
        if from_id is None and project is not None:
            for node_keys, node in meta_config.walk(no_ignore=True):
                if isinstance(node.value, dict):
                    continue
                sect, key = node_keys
                value = node.value
                sect = sect.translate(None, "=")
                if key == "compulsory" and value == "true":
                    info_config.set([sect], "")
            info_config.set(["project"], project)
        else:
            if from_project is None:
                info_config.set(["project"], "")
            if from_title is None:
                info_config.set(["title"], "")

        # Determine prefix
        if from_id is not None:
            prefix = from_id.prefix
        elif prefix is None:
            prefix = SuiteId.get_prefix_default()

        # Determine owner:
        # 1. From user configuration [rosie-id]prefix-username
        # 2. From username of a matching group in [groups] in
        #    ~/.subversion/servers
        # 3. Current user ID
        owner = res_loc.get_conf().get_value(
                        ["rosie-id", "prefix-username." + prefix])
        if not owner and self.subversion_servers_conf:
            servers_conf = rose.config.load(self.subversion_servers_conf)
            groups_node = servers_conf.get(["groups"])
            if groups_node is not None:
                group = None
                prefix_loc = SuiteId.get_prefix_location(prefix)
                prefix_host = urlparse(prefix_loc).hostname
                for key, node in groups_node.value.items():
                    if fnmatch(prefix_host, node.value):
                        owner = servers_conf.get_value([key, "username"])
                        break
        if not owner:
            owner = pwd.getpwuid(os.getuid())[0]
        info_config.set(["owner"], owner)

        # Copy description
        try:
            from_id.to_string_with_version()
            info_config.set(
                ["description"],
                "Copy of %s" % (from_id.to_string_with_version()))
        except AttributeError:
            pass

        # Copy fields provided by the user
        try:
            from_config.walk(no_ignore=False)
            for node_keys, node in from_config.walk(no_ignore=False):
                if isinstance(node.value, dict):
                    continue
                sect, key = node_keys
                value = node.value
                if (key == "description" or key == "owner" or
                    key == "access-list" or
                        (key == "project" and from_project is not None)):
                    pass
                else:
                    info_config.set([key], value)
        except UnboundLocalError:
            pass

        # Determine access list
        access_list_str = res_loc.get_conf().get_value(
            ["rosie-vc", "access-list-default"])
        if access_list_str:
            info_config.set(["access-list"], access_list_str)

        # Use metadata to give value hints
        meta_config = load_meta_config(info_config, directory=None,
                                       config_type=rose.INFO_CONFIG_NAME,
                                       error_handler=None,
                                       ignore_meta_error=False)
        if from_id is None and project is not None:
            for node_keys, node in meta_config.walk(no_ignore=True):
                if isinstance(node.value, dict):
                    continue
                sect, key = node_keys
                value = node.value
                sect = sect.translate(None, "=")
                if key == "value-hints" or key == "values":
                    reminder = ("please remove all commented hints/lines " +
                                "in the main/top section before saving.")
                    info_config.set([sect],
                                    rose.variable.array_split(value)[0],
                                    comments=[value, reminder])
        if older_config is not None:
            for node_keys, node in older_config.walk(no_ignore=True):
                if isinstance(node.value, dict):
                    continue
                sect, key = node_keys
                value = node.value
                info_config.set([key], value)

        return info_config

    def check_fields(self, info_config, interactive_mode, from_id=None,
                     optional_file=None, prefix=None, error_reported=False):
        """Check the fields in the info config"""
        for key in ["owner", "project", "title"]:
            if not info_config.get([key], no_ignore=True):
                if optional_file is not None:
                    raise SuiteInfoFieldError(key)
                info_config_new = info_config
                error_reported = True
                if interactive_mode:
                    question = ("rose-suite.info: \n compulsory field \"%s\"" +
                                " not defined,\n try again?") % key
                    try:
                        response = raw_input(question + " y/n (default n) ")
                    except EOFError:
                        sys.exit(1)
                    if response != 'y':
                        sys.exit(1)
                    return info_config_new, error_reported
                else:
                    raise SuiteInfoFieldError(key)
        meta_config = load_meta_config(info_config, directory=None,
                                       config_type=rose.INFO_CONFIG_NAME,
                                       error_handler=None,
                                       ignore_meta_error=False)
        reports = DefaultValidators().validate(info_config, meta_config)
        if reports != []:
            reports_map = {None: reports}
            text = (rose.macro.get_reports_as_text
                    (reports_map, "rose.macro.DefaultValidators"))
            if interactive_mode:
                reporter = rose.reporter.Reporter()
                reporter(text, kind=reporter.KIND_ERR,
                         level=reporter.FAIL, prefix="")
                info_config_new = info_config
                error_reported = True
                question = "Metadata issue, do you want to try again?"
                try:
                    response = raw_input(question + " y/n (default n) ")
                except EOFError:
                    sys.exit(1)
                if response != 'y':
                    sys.exit(1)
                return info_config_new, error_reported
            else:
                raise SuiteInfoError(text)
        elif error_reported:
            return None, error_reported
        elif error_reported is False:
            return info_config, error_reported
        if from_id is not None:
            return self._copy(info_config, from_id)
        return info_config, error_reported

    def _copy(self, info_config, from_id):
        from_id_url = "%s/%s@%s" % (from_id.to_origin(), from_id.branch,
                                    from_id.revision)
        self.popen("svn", "info", from_id_url) # Die if from_id not exists
        prefix = from_id.prefix
        temp_local_copy = os.path.join(self._get_work_dir(), "work")
        new_id = None
        # N.B. This is probably the simplest logic to maintain,
        #      but not the most efficient for runtime. Does it matter?
        while new_id is None:
            if os.path.exists(temp_local_copy):
                shutil.rmtree(temp_local_copy)
            self.popen("svn", "checkout", "-q", "--depth", "empty",
                       SuiteId.get_prefix_location(prefix), temp_local_copy)
            new_id = SuiteId.get_next(prefix)
            for i in range(len(new_id.sid)):
                d = os.path.join(temp_local_copy,
                                 os.sep.join(new_id.sid[0:i + 1]))
                self.popen("svn", "update", "-q", "--depth", "empty", d)
                if not os.path.isdir(d):
                    os.mkdir(d)
                    self.popen("svn", "add", "-q", d)
            d = os.path.join(temp_local_copy, os.sep.join(new_id.sid))
            self.popen("svn", "cp", "-q", from_id_url, os.path.join(d, "trunk"))
            rose.config.dump(info_config,
                             os.path.join(d, "trunk", "rose-suite.info"))
            message = "%s: new suite, a copy of %s" % (new_id,
                       from_id.to_string_with_version())
            try:
                self.popen("svn", "commit", "-q", "-m", message, temp_local_copy)
                self.event_handler(SuiteCreateEvent(new_id))
                self.event_handler(SuiteCopyEvent(new_id, from_id))
            except RosePopenError as e:
                try:
                    self.popen("svn", "info", new_id.to_origin())
                    new_id = None
                except RosePopenError:
                    raise e
            finally:
                self._delete_work_dir()
        return new_id


def checkout(argv):
    """CLI function: checkout."""
    opt_parser = RoseOptionParser().add_my_options("force_mode")
    opts, args = opt_parser.parse_args(argv)
    verbosity = opts.verbosity - opts.quietness
    report = Reporter(verbosity)
    client = RosieVCClient(event_handler=report, force_mode=opts.force_mode)
    SuiteId.svn.event_handler = client.event_handler # FIXME: ugly?
    rc = 0
    for arg in args:
        try:
            client.checkout(arg)
        except (FileExistError, RosePopenError, SuiteIdPrefixError) as e:
            rc = 1
            report(e)
            if not opts.force_mode:
                sys.exit(1)
    if rc:
        sys.exit(rc)


def create(argv):
    """CLI function: create and copy."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("checkout_mode", "info_file",
                              "meta_suite_mode", "non_interactive", "prefix",
                              "project")
    opts, args = opt_parser.parse_args(argv)
    verbosity = opts.verbosity - opts.quietness
    report = Reporter(verbosity)
    client = RosieVCClient(event_handler=report)
    SuiteId.svn.event_handler = client.event_handler # FIXME: ugly?
    from_id = None
    if args:
        from_id = SuiteId(id_text=args[0])
        if from_id.branch is None:
            from_id.branch = from_id.BRANCH_TRUNK
        if from_id.revision is None:
            from_id.revision = from_id.REV_HEAD
            from_id = SuiteId(id_text=from_id.to_string_with_version())
    info_config_new = None
    interactive_mode = not opts.non_interactive
    if opts.info_file is None:
        try:
            info_config = client.generate_info_config(from_id, opts.prefix,
                                                      opts.project)
        except (RosePopenError) as e:
            report(e)
            sys.exit(1)
        info_file = tempfile.NamedTemporaryFile()
        if args:
            meta_config = load_meta_config(info_config, directory=None,
                                           config_type=rose.INFO_CONFIG_NAME,
                                           error_handler=None,
                                           ignore_meta_error=False)
            for node_keys, node in meta_config.walk(no_ignore=True):
                if isinstance(node.value, dict):
                    continue
                sect, key = node_keys
                value = node.value
                sect = sect.translate(None, "=")
                if key == "copy-mode" and value == "clear":
                    info_config.set([sect], "")
                if key == "copy-mode" and value == "never":
                    info_config.unset([sect])
        rose.config.dump(info_config, info_file)
        info_file.write(CREATE_INFO_CONFIG_COMMENT)
        info_file.seek(0)
        command_list = client.popen.get_cmd("editor", info_file.name)
        client.popen(*command_list, stdout=sys.stdout)
        info_config = rose.config.load(info_file)
        try:
            info_config_new, error_reported = client.check_fields(info_config,
                                                              interactive_mode,
                                                              from_id,
                                                              opts.prefix)
        except (RosePopenError, SuiteInfoFieldError,
                SuiteIdOverflowError) as e:
            report(e)
            sys.exit(1)
        while error_reported is True:
            info_file = tempfile.NamedTemporaryFile()
            info_config = info_config_new
            if (info_config.get(["project"]).value is not None and
               opts.project is None):
                project = info_config.get(["project"]).value
                info_config = client.generate_info_config(from_id, opts.prefix,
                                                          project,
                                                          info_config)
            rose.config.dump(info_config, info_file)
            info_file.write(CREATE_INFO_CONFIG_COMMENT)
            info_file.seek(0)
            command_list = client.popen.get_cmd("editor", info_file.name)
            client.popen(*command_list, stdout=sys.stdout)
            info_config = rose.config.load(info_file)
            try:
                info_config_new, error_reported = client.check_fields(
                                                              info_config,
                                                              interactive_mode,
                                                              from_id,
                                                              opts.prefix)
            except (RosePopenError, SuiteInfoFieldError,
                    SuiteIdOverflowError) as e:
                report(e)
                sys.exit(1)
    elif opts.info_file == "-":
        info_config = rose.config.load(sys.stdin)
        try:
            info_config_new, error_reported = client.check_fields(info_config,
                                                          interactive_mode,
                                                          from_id,
                                                          opts.info_file,
                                                          opts.prefix)
        except (RosePopenError, SuiteInfoFieldError,
                SuiteIdOverflowError) as e:
            report(e)
            sys.exit(1)
    else:
        info_config = rose.config.load(opts.info_file)
        try:
            info_config_new, error_reported = client.check_fields(info_config,
                                                          interactive_mode,
                                                          from_id,
                                                          opts.info_file,
                                                          opts.prefix)
        except (RosePopenError, SuiteInfoFieldError,
                SuiteIdOverflowError) as e:
            report(e)
            sys.exit(1)
    if interactive_mode:
        if from_id:
            question = "Copy \"%s\"?" % from_id.to_string_with_version()
        else:
            prefix = opts.prefix
            if not prefix:
                prefix = SuiteId.get_prefix_default()
            question = "Create suite at \"%s\"?" % prefix
        try:
            response = raw_input(question + " y/n (default n) ")
        except EOFError:
            sys.exit(1)
        if response != 'y':
            sys.exit(1)
    try:
        id = client.create(info_config, from_id, opts.prefix,
                           opts.meta_suite_mode)
    except (RosePopenError, SuiteInfoFieldError, SuiteIdOverflowError) as e:
        report(e)
        sys.exit(1)
    if opts.checkout_mode:
        try:
            client.checkout(id)
        except (FileExistError, RosePopenError) as e:
            report(e)
            sys.exit(1)


def delete(argv):
    """CLI function: delete."""
    opt_parser = RoseOptionParser().add_my_options("force_mode",
                                                   "non_interactive",
                                                   "local_only")
    opts, args = opt_parser.parse_args(argv)
    report = Reporter(opts.verbosity - opts.quietness)
    client = RosieVCClient(event_handler=report, force_mode=opts.force_mode)
    SuiteId.svn.event_handler = client.event_handler # FIXME
    if not args:
        args.append(SuiteId(location=os.getcwd()))
    interactive_mode = not opts.non_interactive
    prompt = ("%s: delete local+repository copies? " +
              "y/n/a (default n, a=yes-to-all) ")
    if opts.local_only:
        prompt = "%s: delete local copy? y/n/a (default n, a=yes-to-all) "
    rc = 0
    for arg in args:
        if interactive_mode:
            try:
                response = raw_input(prompt % arg)
            except EOFError:
                rc = 1
                continue
            if response == 'a':
                interactive_mode = False
            elif response != 'y':
                rc = 1
                continue
        if opts.debug_mode:
            client.delete(arg, opts.local_only)
        else:
            try:
                client.delete(arg, opts.local_only)
            except (LocalCopyStatusError, RosePopenError,
                    SuiteIdPrefixError) as e:
                client.event_handler(e)
                rc = 1
                if not opts.force_mode:
                    sys.exit(1)
    if rc:
        sys.exit(rc)


def main():
    """Launcher for the CLI functions."""
    add_site_meta_paths()
    add_env_meta_paths()
    argv = sys.argv[1:]
    if not argv:
        return sys.exit(1)
    for name in ["checkout", "create", "delete"]:
        if argv[0] == name:
            return globals()[name](argv[1:])
    else:
        sys.exit("rosie.vc: %s: incorrect usage" % argv[0])


if __name__ == "__main__":
    main()
