# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
# -----------------------------------------------------------------------------
"""Write version control information of sources used in run time."""

import os
from rose.popen import RosePopener
import sys


def write_source_vc_info(run_source_dir, output=None, popen=None):
    """Write version control information of sources used in run time.

    run_source_dir -- The source directory we are interested in.
    output -- An open file handle or a string containing a writable path.
              If not specified, use sys.stdout.
    popen -- A rose.popen.RosePopener instance for running vc commands.
             If not specified, use a new local instance.

    """
    if popen is None:
        popen = RosePopener()
    if output is None:
        handle = sys.stdout
    elif hasattr(output, "write"):
        handle = output
    else:
        handle = open(output, "wb")
    environ = dict(os.environ)
    environ["LANG"] = "C"
    for vcs, args_list in [
            ("svn", [
                ["info", "--non-interactive"],
                ["status", "--non-interactive"],
                ["diff", "--internal-diff", "--non-interactive"]]),
            ("git", [["describe"], ["status"], ["diff"]])]:
        if not popen.which(vcs):
            continue
        cwd = os.getcwd()
        os.chdir(run_source_dir)
        try:
            for args in args_list:
                cmd = [vcs] + args
                rc, out, err = popen.run(*cmd, env=environ)
                if out:
                    handle.write("#" * 80 + "\n")
                    handle.write(("# %s\n" % popen.list_to_shell_str(cmd)))
                    handle.write("#" * 80 + "\n")
                    handle.write(out)
                if rc:  # If cmd fails once, chances are, it will fail again
                    break
        finally:
            os.chdir(cwd)
