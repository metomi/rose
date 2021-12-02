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
"""Wrap version control system functionalities required by Rosie."""

import atexit
from fnmatch import fnmatch
from io import StringIO
import os
import pwd
import shutil
import sys
from tempfile import mkdtemp, mkstemp
from urllib.parse import urlparse

import metomi.rose.config
import metomi.rose.external
from metomi.rose.fs_util import FileSystemUtil
from metomi.rose.macro import add_meta_paths, load_meta_config
from metomi.rose.macros import DefaultValidators
import metomi.rose.metadata_check
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopener, RosePopenError
import metomi.rose.reporter
from metomi.rose.reporter import Event, Reporter
from metomi.rose.resource import ResourceLocator
from metomi.rosie.suite_id import (
    SuiteId,
    SuiteIdOverflowError,
    SuiteIdPrefixError,
)

CREATE_INFO_CONFIG_COMMENT = """
# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
"""
YES = "y"
YES_TO_ALL = "a"
PROMPT_TAIL_YN = " [" + YES + " or n (default)] "
PROMPT_TAIL_YNA = (
    " [" + YES + " or n (default) or " + YES_TO_ALL + " (yes to all)] "
)
PROMPT_COPY = "Copy \"%s\" to \"%s-?????\"?" + PROMPT_TAIL_YN
PROMPT_CREATE = "Create suite as \"%s-?????\"?" + PROMPT_TAIL_YN
PROMPT_FIX_INFO_CONFIG = (
    "rose-suite.info has invalid settings. Try again?" + PROMPT_TAIL_YN
)
PROMPT_DELETE = "%s: delete local+repository copies?" + PROMPT_TAIL_YNA
PROMPT_DELETE_LOCAL = "%s: delete local copy?" + PROMPT_TAIL_YNA


def cli(fcn):
    """Launcher for the CLI functions."""

    def _inner(argv):
        nonlocal fcn
        add_meta_paths()
        return fcn()

    return _inner


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

    def __init__(self, id_, status):
        self.id_ = id_
        self.status = status
        super(LocalCopyStatusError, self).__init__(id_, status)

    def __str__(self):
        data = (str(self.id_), self.id_.to_local_copy(), self.status)
        return "%s: %s: local copy has uncommitted changes:\n%s" % data


class SuiteInfoError(Exception):
    """Raised when settings in rose-suite.info are invalid."""

    def __str__(self):
        return metomi.rose.macro.get_reports_as_text(
            {None: self.args[0]}, "rose-suite.info"
        )


class LocalCopyCreateEvent(Event):
    """An event raised after the creation of a local copy of a suite.

    event.args[0] is the SuiteId of the suite.

    """

    def __str__(self):
        id_ = self.args[0]
        return "%s: local copy created at %s" % (str(id_), id_.to_local_copy())


class LocalCopyCreateSkipEvent(Event):
    """An event raised after skipped creation of a local suite copy.

    event.args[0] is the SuiteId of the suite.

    """

    KIND = Reporter.KIND_ERR

    def __str__(self):
        id_ = self.args[0]
        return "%s: skip, local copy already exists at %s" % (
            str(id_),
            id_.to_local_copy(),
        )


class SuiteCreateEvent(Event):
    """An event raised when a suite is created.

    event.args[0] is the SuiteId of the suite.

    """

    def __str__(self):
        id_ = self.args[0]
        return "%s: created at %s" % (str(id_), id_.to_origin())


class SuiteCopyEvent(Event):
    """An event raised when copying suite items into a new suite.

    event.args[0] is the SuiteId of the target suite.
    event.args[1] is the SuiteId of the source suite.

    """

    def __str__(self):
        new_id, from_id = self.args
        return "%s: copied items from %s" % (
            new_id,
            from_id.to_string_with_version(),
        )


class SuiteDeleteEvent(Event):
    """An event raised after the delete of a suite.

    event.args[0] is the SuiteId of the suite.

    """

    def __str__(self):
        id_ = self.args[0]
        return "delete: %s" % id_.to_origin()


class RosieVCClient:

    """Client for version control functionalities."""

    SUBVERSION_SERVERS_CONF = "~/.subversion/servers"
    COMMIT_MESSAGE_COPY = "%s: new suite, a copy of %s"
    COMMIT_MESSAGE_CREATE = "%s: new suite"
    COMMIT_MESSAGE_DELETE = "%s: deleted"

    def __init__(
        self, event_handler=None, popen=None, fs_util=None, force_mode=False
    ):
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
                self.SUBVERSION_SERVERS_CONF
            )
            if os.path.exists(subversion_servers_conf):
                self.subversion_servers_conf = subversion_servers_conf

    def _delete_work_dir(self):
        """Remove the temporary working directory, if necessary."""
        if self._work_dir is not None and os.path.isdir(self._work_dir):
            shutil.rmtree(self._work_dir)
            self._work_dir = None

    @staticmethod
    def _dummy(*args, **kwargs):
        """Dummy event handler."""
        pass

    def _get_work_dir(self):
        """Create a temporary working directory."""
        if self._work_dir is None:
            self._work_dir = mkdtemp()
        return self._work_dir

    def checkout(self, id_):
        """Create a local copy of a suite with the given ID.

        Return the SuiteId of the suite on success.

        """
        if isinstance(id_, str):
            id_ = SuiteId(id_text=id_)
        if id_.revision is None:
            id_.revision = id_.REV_HEAD
        if id_.branch is None:
            id_.branch = id_.BRANCH_TRUNK
        local_copy = id_.to_local_copy()
        if os.path.exists(local_copy):
            id0 = SuiteId(location=local_copy)
            if id_.to_string_with_version() == id0.to_string_with_version():
                self.event_handler(LocalCopyCreateSkipEvent(id_))
                return id_
            elif self.force_mode:
                self.fs_util.delete(local_copy)
            else:
                raise FileExistError(local_copy)
        local_copy_dir = os.path.dirname(local_copy)
        if not os.path.isdir(local_copy_dir):
            self.fs_util.makedirs(os.path.dirname(local_copy))
        origin = "%s/%s@%s" % (id_.to_origin(), id_.branch, id_.revision)
        self.popen("svn", "checkout", "-q", origin, local_copy)
        self.event_handler(LocalCopyCreateEvent(id_))
        return id_

    def create(
        self, info_config, from_id=None, prefix=None, meta_suite_mode=False
    ):
        """Create a suite.

        info_config -- A metomi.rose.config.ConfigNode object, which will be
                       used as the content of the "rose-suite.info" file of the
                       new suite.
        from_id -- If defined, copy items from it.
        prefix -- If defined, create the suite in the suite repository named by
                  the prefix instead of the default one.
        meta_suite_mode -- If True, create the special metadata suite.
                           Ignored if from_id is not None.

        Return the SuiteId of the suite on success.

        """
        if from_id is not None and (not prefix or from_id.prefix == prefix):
            return self._copy1(info_config, from_id)
        dir_ = self._get_work_dir()
        try:
            # Create a temporary suite in the file system
            if from_id:
                from_id_url = "%s/%s@%s" % (
                    from_id.to_origin(),
                    from_id.branch,
                    from_id.revision,
                )
                self.popen("svn", "export", "-q", "--force", from_id_url, dir_)
            else:
                open(os.path.join(dir_, "rose-suite.conf"), "w").close()
            metomi.rose.config.dump(
                info_config, os.path.join(dir_, "rose-suite.info")
            )

            # Attempt to import the temporary suite to the repository
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
                try:
                    if from_id:
                        message = self.COMMIT_MESSAGE_COPY % (
                            new_id,
                            from_id.to_string_with_version(),
                        )
                    else:
                        message = self.COMMIT_MESSAGE_CREATE % str(new_id)
                    self.popen(
                        "svn", "import", "-q", "-m", message, dir_, new_origin
                    )
                    self.event_handler(SuiteCreateEvent(new_id))
                    if from_id:
                        self.event_handler(SuiteCopyEvent(new_id, from_id))
                except RosePopenError as exc:
                    try:
                        self.popen("svn", "info", new_origin)
                        if not meta_suite_mode:
                            new_id = None
                    except RosePopenError:
                        raise exc
            return new_id
        finally:
            self._delete_work_dir()

    def delete(self, id_, local_only=False):
        """Delete the local copy and the origin of a suite.

        It takes the suite ID as an argument.
        Return the SuiteId of the suite on success.

        """
        if isinstance(id_, str):
            id_ = SuiteId(id_text=id_)
        local_copy = id_.to_local_copy()
        if os.path.exists(local_copy):
            if not self.force_mode:
                status = self.popen("svn", "status", local_copy)[0]
                if status:
                    raise LocalCopyStatusError(id_, status)
            if os.getcwd() == local_copy:
                self.fs_util.chdir(os.path.expanduser("~"))
            self.fs_util.delete(local_copy)
        if not local_only:
            self.popen(
                "svn",
                "delete",
                "-q",
                "-m",
                self.COMMIT_MESSAGE_DELETE % str(id_),
                id_.to_origin(),
            )
            self.event_handler(SuiteDeleteEvent(id_))
        return id_

    def generate_info_config(self, from_id=None, prefix=None, project=None):
        """Generate a metomi.rose.config.ConfigNode for a rose-suite.info.

        This is suitable for passing into the create method of this
        class.
        If from_id is defined, copy items from it.
        Return the metomi.rose.config.ConfigNode instance.

        """
        from_project = None
        from_title = None
        if from_id is not None:
            from_info_url = "%s/%s/rose-suite.info@%s" % (
                from_id.to_origin(),
                from_id.branch,
                from_id.revision,
            )
            out_data = self.popen("svn", "cat", from_info_url)[0]
            from_config = metomi.rose.config.load(StringIO(out_data))

        res_loc = ResourceLocator.default()
        older_config = None
        info_config = metomi.rose.config.ConfigNode()

        # Determine project if given as a command-line option on create
        if from_id is None and project is not None:
            info_config.set(["project"], project)

        # Set the compulsory fields and use the project and metadata if
        #  available.
        meta_config = load_meta_config(
            info_config, config_type=metomi.rose.INFO_CONFIG_NAME
        )
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
        if prefix is None:
            if from_id is None:
                prefix = SuiteId.get_prefix_default()
            else:
                prefix = from_id.prefix

        # Determine owner:
        # 1. From user configuration [rosie-id]prefix-username
        # 2. From username of a matching group in [groups] in
        #    ~/.subversion/servers
        # 3. Current user ID
        owner = res_loc.get_conf().get_value(
            ["rosie-id", "prefix-username." + prefix]
        )
        if not owner and self.subversion_servers_conf:
            servers_conf = metomi.rose.config.load(
                self.subversion_servers_conf
            )
            groups_node = servers_conf.get(["groups"])
            if groups_node is not None:
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
                "Copy of %s" % (from_id.to_string_with_version()),
            )
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
                if key in ["description", "owner", "access-list"] or (
                    key == "project" and from_project is not None
                ):
                    pass
                else:
                    info_config.set([key], value)
        except UnboundLocalError:
            pass

        # Determine access list
        access_list_str = res_loc.get_conf().get_value(
            ["rosie-vc", "access-list-default"]
        )
        if access_list_str:
            info_config.set(["access-list"], access_list_str)
        if from_id is None and project is not None:
            for node_keys, node in meta_config.walk(no_ignore=True):
                if isinstance(node.value, dict):
                    continue
                sect, key = node_keys
                value = node.value
                sect = sect.translate(None, "=")
                if key == "value-hints" or key == "values":
                    reminder = (
                        "please remove all commented hints/lines "
                        + "in the main/top section before saving."
                    )
                    info_config.set(
                        [sect],
                        metomi.rose.variable.array_split(value)[0],
                        comments=[value, reminder],
                    )
        if older_config is not None:
            for node_keys, node in older_config.walk(no_ignore=True):
                if isinstance(node.value, dict):
                    continue
                sect, key = node_keys
                value = node.value
                info_config.set([key], value)

        return info_config

    @classmethod
    def validate_info_config(cls, info_config):
        """Validate contents in suite info file."""
        reports = DefaultValidators().validate(
            info_config,
            load_meta_config(
                info_config, config_type=metomi.rose.INFO_CONFIG_NAME
            ),
        )
        if reports:
            raise SuiteInfoError(reports)

    def _copy1(self, info_config, from_id):
        """Copy a suite from the same repository."""
        from_id_url = "%s/%s@%s" % (
            from_id.to_origin(),
            from_id.branch,
            from_id.revision,
        )
        self.popen("svn", "info", from_id_url)  # Die if from_id not exists
        prefix = from_id.prefix
        temp_local_copy = os.path.join(self._get_work_dir(), "work")
        new_id = None
        # N.B. This is probably the simplest logic to maintain,
        #      but not the most efficient for runtime. Does it matter?
        while new_id is None:
            if os.path.exists(temp_local_copy):
                shutil.rmtree(temp_local_copy)
            self.popen(
                "svn",
                "checkout",
                "-q",
                "--depth",
                "empty",
                SuiteId.get_prefix_location(prefix),
                temp_local_copy,
            )
            new_id = SuiteId.get_next(prefix)
            for i in range(len(new_id.sid)):
                dir_ = os.path.join(
                    temp_local_copy, os.sep.join(new_id.sid[0 : i + 1])
                )
                self.popen("svn", "update", "-q", "--depth", "empty", dir_)
                if not os.path.isdir(dir_):
                    os.mkdir(dir_)
                    self.popen("svn", "add", "-q", dir_)
            dir_ = os.path.join(temp_local_copy, os.sep.join(new_id.sid))
            self.popen(
                "svn", "cp", "-q", from_id_url, os.path.join(dir_, "trunk")
            )
            metomi.rose.config.dump(
                info_config, os.path.join(dir_, "trunk", "rose-suite.info")
            )
            message = self.COMMIT_MESSAGE_COPY % (
                new_id,
                from_id.to_string_with_version(),
            )
            try:
                self.popen(
                    "svn", "commit", "-q", "-m", message, temp_local_copy
                )
                self.event_handler(SuiteCreateEvent(new_id))
                self.event_handler(SuiteCopyEvent(new_id, from_id))
            except RosePopenError as exc:
                try:
                    self.popen("svn", "info", new_id.to_origin())
                    new_id = None
                except RosePopenError:
                    raise exc
            finally:
                self._delete_work_dir()
        return new_id


@cli
def checkout():
    """CLI function: checkout."""
    opt_parser = RoseOptionParser(
        usage='rosie checkout [OPTIONS] ID ...',
        description='''
Checkout local copies of suites.

For each `ID` in the argument list, checkout a working copy of the suite
identified by `ID` to the standard location.
        ''',
    ).add_my_options("force_mode")
    opt_parser.modify_option(
        'force_mode',
        help=(
            'If working copy for suite identified by `ID` already exists,'
            ' remove it. Continue to the next `ID` if checkout of a suite'
            ' fails.'
        ),
    )
    opts, args = opt_parser.parse_args()
    verbosity = opts.verbosity - opts.quietness
    report = Reporter(verbosity)
    client = RosieVCClient(event_handler=report, force_mode=opts.force_mode)
    SuiteId.svn.event_handler = client.event_handler
    ret_code = 0
    for arg in args:
        try:
            client.checkout(arg)
        except (FileExistError, RosePopenError, SuiteIdPrefixError) as exc:
            ret_code = 1
            report(exc)
            if not opts.force_mode:
                sys.exit(1)
    if ret_code:
        sys.exit(ret_code)


@cli
def create():
    """CLI function: create and copy."""
    opt_parser = RoseOptionParser(
        usage=(
            'rosie create [OPTIONS]'
            '\n       rosie copy [OPTIONS] ID-OF-EXISTING-SUITE'
        ),
        description='''
rosie create: Create a new suite
rosie copy  : Create a new suite and copy content from an existing one.

Assign a new `ID` and create the directory structure in the central
repository for a new suite.

The location of the repository for the new suite is determined in order
of preference:

1. `--prefix=PREFIX` option
2. prefix of the `ID-OF-EXISTING-SUITE`
3. `[rosie-id]prefix-default` option in the site/user configuration.

If `ID-OF-EXISTING-SUITE` is specified, copy items from the existing suite
`ID-OF-EXISTING-SUITE` when the suite is created. It is worth noting that
revision history of the copied items can only be preserved if
`ID-OF-EXISTING-SUITE` is in the same repository of the new suite

The syntax of the ID-OF-EXISTING-SUITE is PREFIX-xxNNN[/BRANCH][@REV]
(e.g. my-su173, my-su173/trunk, my-su173/trunk@HEAD). If REV is not specified,
the last changed revision of the branch is used. If BRANCH is not specified,
"trunk" is used.

NOTE: ID-OF-EXISTING-SUITE is _not_ a filepath.
        ''',
    )
    opt_parser.add_my_options(
        "checkout_mode",
        "info_file",
        "meta_suite_mode",
        "non_interactive",
        "prefix",
        "project",
    )
    opts, args = opt_parser.parse_args()
    verbosity = opts.verbosity - opts.quietness
    client = RosieVCClient(event_handler=Reporter(verbosity))
    SuiteId.svn.event_handler = client.event_handler
    from_id = None
    if args:
        from_id = SuiteId(id_text=args[0])
        if from_id.branch is None:
            from_id.branch = from_id.BRANCH_TRUNK
        if from_id.revision is None:
            from_id.revision = from_id.REV_HEAD
            from_id = SuiteId(id_text=from_id.to_string_with_version())
    interactive_mode = not opts.non_interactive
    if opts.info_file is None:
        info_config = client.generate_info_config(
            from_id, opts.prefix, opts.project
        )
        if from_id is not None:
            meta_config = load_meta_config(
                info_config,
                directory=None,
                config_type=metomi.rose.INFO_CONFIG_NAME,
                error_handler=None,
                ignore_meta_error=False,
            )
            for node_keys, node in meta_config.walk(no_ignore=True):
                if isinstance(node.value, dict):
                    continue
                sect, key = node_keys
                value = node.value
                sect = sect.replace("=", "")
                if key == "copy-mode" and value == "clear":
                    info_config.set([sect], "")
                if key == "copy-mode" and value == "never":
                    info_config.unset([sect])

        info_config = _edit_info_config(opts, client, info_config)
    else:
        file_ = opts.info_file
        if opts.info_file == "-":
            file_ = sys.stdin
        info_config = metomi.rose.config.load(file_)
    info_config = _validate_info_config(opts, client, info_config)
    if interactive_mode:
        prefix = opts.prefix
        if from_id:
            if not prefix:
                prefix = from_id.prefix
            question = PROMPT_COPY % (from_id.to_string_with_version(), prefix)
        else:
            if not prefix:
                prefix = SuiteId.get_prefix_default()
            question = PROMPT_CREATE % prefix
        try:
            response = input(question)
        except EOFError:
            sys.exit(1)
        if response != YES:
            sys.exit(1)
    try:
        id_ = client.create(
            info_config, from_id, opts.prefix, opts.meta_suite_mode
        )
    except (RosePopenError, SuiteIdOverflowError) as exc:
        client.event_handler(exc)
        sys.exit(1)
    if opts.checkout_mode:
        try:
            client.checkout(id_)
        except (FileExistError, RosePopenError) as exc:
            client.event_handler(exc)
            sys.exit(1)


def _validate_info_config(opts, client, info_config):
    """Validate content of suite info file, may prompt in interactive mode."""
    while True:
        try:
            client.validate_info_config(info_config)
        except SuiteInfoError as exc:
            client.event_handler(exc)
            if opts.non_interactive:
                sys.exit(1)
            try:
                response = input(PROMPT_FIX_INFO_CONFIG)
            except EOFError:
                sys.exit(1)
            if response != YES:
                sys.exit(1)
            info_config = _edit_info_config(opts, client, info_config)
        else:
            return info_config


def _edit_info_config(opts, client, info_config):
    """Helper for "create", launch editor to edit the suite info."""
    if opts.non_interactive:
        return info_config
    temp_desc, temp_name = mkstemp()
    try:
        temp_file = os.fdopen(temp_desc, "w")
        metomi.rose.config.dump(info_config, temp_file)
        temp_file.write(CREATE_INFO_CONFIG_COMMENT)
        temp_file.close()
        command_list = client.popen.get_cmd("editor", temp_name)
        client.popen(*command_list, stdin=sys.stdin, stdout=sys.stdout)
    except (IOError, OSError, RosePopenError) as exc:
        client.event_handler(exc)
        sys.exit(1)
    else:
        return metomi.rose.config.load(temp_name)
    finally:
        os.unlink(temp_name)


@cli
def delete():
    """CLI function: delete."""
    opt_parser = RoseOptionParser(
        usage='rosie delete [OPTIONS] [--] [ID ...]',
        description='''
Delete suites.

Check the standard working copy location for a checked out suite
matching `ID` and remove it if there is no uncommitted change (or if
`--force` is specified).

Delete the suite directory structure from the HEAD of the central
repository matching the `ID`.

If no `ID` is specified and `$PWD` is a working copy of a suite, use the
`ID` of the suite in the working copy.
        '''
    ).add_my_options(
        "force_mode", "non_interactive", "local_only"
    )
    opt_parser.modify_option(
        'force_mode',
        help=(
            "Remove working copies even if there are uncommitted changes."
            "\nContinue with the next `ID` if delete of a suite fails."
        ),
    )
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    client = RosieVCClient(event_handler=report, force_mode=opts.force_mode)
    SuiteId.svn.event_handler = client.event_handler
    if not args:
        args.append(SuiteId(location=os.getcwd()))
    interactive_mode = not opts.non_interactive
    prompt = PROMPT_DELETE
    if opts.local_only:
        prompt = PROMPT_DELETE_LOCAL
    ret_code = 0
    for arg in args:
        if interactive_mode:
            try:
                response = input(prompt % arg)
            except EOFError:
                ret_code = 1
                continue
            if response == YES_TO_ALL:
                interactive_mode = False
            elif response != YES:
                ret_code = 1
                continue
        if opts.debug_mode:
            client.delete(arg, opts.local_only)
        else:
            try:
                client.delete(arg, opts.local_only)
            except (
                LocalCopyStatusError,
                RosePopenError,
                SuiteIdPrefixError,
            ) as exc:
                client.event_handler(exc)
                ret_code = 1
                if not opts.force_mode:
                    sys.exit(1)
    if ret_code:
        sys.exit(ret_code)
