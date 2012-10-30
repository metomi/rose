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
"""Wrap version control system functionalities required by Rosie."""

import atexit
import os
import pwd
import re
import rose.config
import rose.external
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Event, Reporter
from rosie.suite_id import SuiteId, SuiteIdOverflowError
import shlex
import shutil
from StringIO import StringIO
import sys
import tempfile
import time


PROMPT_CREATE = "Create? y/n (default n) "
PROMPT_DELETE = "Delete {0}? y/n (default n) "
PROMPT_DELETE_ALL = "Delete {0}? y/n/a (default n, a=yes-to-all) "


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


class FileCreateEvent(Event):
    """An event raised after when items are created in the file system.

    event.args is a list containing the path of the items created.

    """

    LEVEL = Reporter.V

    def __str__(self):
        return "%s: created" % " ".join(self.args)


class FileDeleteEvent(Event):
    """An event raised after items are removed from the file system.

    event.args is a list containing the path of the items removed.

    """

    TYPE = Reporter.TYPE_ERR

    def __str__(self):
        return "%s: deleted" % " ".join(self.args)


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

    TYPE = Reporter.TYPE_ERR

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
        return "%s: deleted" % id.to_origin()


class Client(object):

    """Client for version control functionalities."""

    def __init__(self, event_handler=None, popen=None, force_mode=False):
        if event_handler is None:
            event_handler = self._dummy
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        self.popen = popen
        self.force_mode = force_mode
        self._work_dir = None
        atexit.register(self._delete_work_dir)

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
                if os.path.isfile(local_copy):
                    unlink(local_copy)
                else:
                    shutil.rmtree(local_copy)
                self.event_handler(FileDeleteEvent(local_copy))
            else:
                raise FileExistError(local_copy)
        local_copy_dir = os.path.dirname(local_copy)
        if not os.path.isdir(local_copy_dir):
            os.makedirs(os.path.dirname(local_copy))
            self.event_handler(FileCreateEvent(local_copy_dir))
        origin = id.to_origin() + "/" + id.branch + "@" + id.revision
        self.popen("svn", "checkout", "-q", origin, local_copy)
        self.event_handler(LocalCopyCreateEvent(id))
        return id

    def create(self, info_config, from_id=None, prefix=None):
        """Create a suite.

        info_config should be a rose.config.ConfigNode object,
        which will be used as the content of the "rose-suite.info" file of the
        new suite.
        If from_id is defined, copy items from it.
        If prefix is defined, create the suite in the suite repository named by
        the prefix instead of the default one.
        Return the SuiteId of the suite on success.

        """
        for key in ["owner", "project", "title"]:
            if not info_config.get([key], no_ignore=True):
                raise SuiteInfoFieldError(key)
        if from_id is not None:
            prefix = from_id.prefix
        new_id = None
        while new_id is None:
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
                self._delete_work_dir()
            except RosePopenError as e:
                try:
                    self.popen("svn", "info", new_origin)
                    new_id = None
                except RosePopenError:
                    raise e
        if from_id is None:
            return new_id
        from_origin_base = "%s/%s" % (from_id.to_origin(), from_id.branch)
        from_origin = "%s@%s" % (from_origin_base, from_id.revision)
        copy_command_list = ["copy", "-q"]
        for from_item in self.popen("svn", "ls", from_origin)[0].split():
            if from_item not in ["rose-suite.conf", "rose-suite.info"]:
                item = "%s/%s@%s" % (from_origin_base, from_item, from_id.revision)
                copy_command_list.append(item)
        copy_command_list.append(".")
        log = "%s: copy items from %s" % (str(new_id),
                                          from_id.to_string_with_version())
        temp_local_copy = os.path.join(self._get_work_dir(), "work")
        try:
            self.popen("svn", "checkout", new_origin, temp_local_copy)
            cwd = os.getcwd()
            os.chdir(temp_local_copy)
            self.popen("svn", *copy_command_list)
            from_conf = "%s/%s@%s" % (from_origin_base,
                                      "rose-suite.conf",
                                      from_id.revision)
            f = open("rose-suite.conf", "w")
            f.write(self.popen("svn", "cat", from_conf)[0])
            f.close()
            self.popen("svn", "commit", "-m", log)
            self.event_handler(SuiteCopyEvent(new_id, from_id))
        finally:
            os.chdir(cwd)
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
                # TODO: Event?
                os.chdir(os.path.expanduser("~"))
            shutil.rmtree(local_copy)
            self.event_handler(FileDeleteEvent(local_copy))
        if not local_only:    
            self.popen("svn", "delete",
                       "-q", "-m", "%s: deleted." % str(id),
                       id.to_origin())
            self.event_handler(SuiteDeleteEvent(id))
        return id

    def generate_info_config(self, from_id=None):
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
            if from_config.get(["project"]) is not None:
                from_project = from_config.get(["project"]).value
            if from_config.get(["title"]) is not None:
                from_title = from_config.get(["title"]).value

        # TODO: use rose.resource?
        info_config_src = os.path.join(os.getenv("ROSE_HOME"),
                                       "etc",
                                       "rosie-create",
                                       "rose-suite.info")
        info_config = rose.config.load(info_config_src)
        # FIXME: Not necessarily true in an externally hosted repository.
        owner = pwd.getpwuid(os.getuid())[0]
        info_config.set(["owner"], owner)
        if from_project:
            info_config.set(["project"], from_project)
        else:
            info_config.set(["project"], "")
        if from_title:
            info_config.set(["title"], "Copy of %s: %s" % (from_id, from_title))
        else:
            info_config.set(["title"], "")
        return info_config


def checkout(argv):
    """CLI function: checkout."""
    opt_parser = RoseOptionParser().add_my_options("force_mode")
    opts, args = opt_parser.parse_args(argv)
    verbosity = opts.verbosity - opts.quietness
    report = Reporter(verbosity)
    client = Client(event_handler=report, force_mode=opts.force_mode)
    SuiteId.svn.event_handler = client.event_handler # FIXME: ugly?
    for arg in args:
        try:
            client.checkout(arg)
        except (FileExistError, RosePopenError) as e:
            report(e)
            if not opts.force_mode:
                sys.exit(1)


def create(argv):
    """CLI function: create and copy."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("checkout_mode", "info_file", "prefix",
                              "non_interactive")
    opts, args = opt_parser.parse_args(argv)
    verbosity = opts.verbosity - opts.quietness
    report = Reporter(verbosity)
    client = Client(event_handler=report)
    SuiteId.svn.event_handler = client.event_handler # FIXME: ugly?
    from_id = None
    if args:
        from_id = SuiteId(id_text=args[0])
        if from_id.branch is None:
            from_id.branch = from_id.BRANCH_TRUNK
        if from_id.revision is None:
            from_id.revision = from_id.REV_HEAD
    if opts.info_file is None:
        try:
            info_config = client.generate_info_config(from_id)
        except (RosePopenError) as e:
            report(e)
            sys.exit(1)
        info_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            rose.config.dump(info_config, info_file)
            info_file.close()
            command_list = client.popen.get_cmd("editor", info_file.name)
            client.popen(*command_list, stdout=sys.stdout)
            info_config = rose.config.load(info_file.name)
        finally:
            os.unlink(info_file.name)
    elif opts.info_file == "-":
        info_config = rose.config.load(sys.stdin)
    else:
        info_config = rose.config.load(opts.info_file)
    if not opts.non_interactive:
        try:
            response = raw_input(PROMPT_CREATE)
        except EOFError:
            sys.exit(1)
        if response != 'y':
            sys.exit(1)
    try:
        id = client.create(info_config, from_id, opts.prefix)
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
    client = Client(event_handler=report, force_mode=opts.force_mode)
    SuiteId.svn.event_handler = client.event_handler # FIXME
    if not args:
        args.append(SuiteId(location=os.getcwd()))
    skip_prompt = opts.non_interactive
    prompt = PROMPT_DELETE
    if len(args) > 1:
        prompt = PROMPT_DELETE_ALL
    for arg in args:
        if not skip_prompt:
            try:
                response = raw_input(prompt.format(arg))
            except EOFError:
                continue
            if response == 'a' and len(args) > 1:
                skip_prompt = True
            elif response != 'y':
                continue
        if opts.debug_mode:
            client.delete(arg, opts.local_only)
        else:    
            try:
                client.delete(arg, opts.local_only)
            except (LocalCopyStatusError, RosePopenError) as e:
                client.event_handler(e)
                if not opts.force_mode:
                    sys.exit(1)


def main():
    """Launcher for the CLI functions."""
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
