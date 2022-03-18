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
"""Write version control information of sources used in run time."""

import os
import sys

from metomi.rose.popen import RosePopener
from metomi.rose.unicode_utils import write_safely


def write_source_vc_info(run_source_dir, output=None, popen=None):
    """Write version control information of sources used in run time.

    run_source_dir -- The source directory we are interested in.
    output -- An open file handle or a string containing a writable path.
              If not specified, use sys.stdout.
    popen -- A metomi.rose.popen.RosePopener instance for running vc commands.
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
    msg = "%s\n" % run_source_dir
    write_safely(msg, handle)
    environ = dict(os.environ)
    environ["LANG"] = "C"
    for vcs, args_list in [
        (
            "svn",
            [
                ["info", "--non-interactive"],
                ["status", "--non-interactive"],
                ["diff", "--internal-diff", "--non-interactive"],
            ],
        ),
        ("git", [["describe"], ["status"], ["diff"]]),
    ]:
        if not popen.which(vcs):
            continue
        cwd = os.getcwd()
        os.chdir(run_source_dir)
        try:
            for args in args_list:
                cmd = [vcs, *args]
                ret_code, out, _ = popen.run(*cmd, env=environ)
                if out:
                    write_safely(("#" * 80 + "\n"), handle)
                    write_safely(
                        ("# %s\n" % popen.shlex_join(cmd)), handle
                    )
                    write_safely(("#" * 80 + "\n"), handle)
                    write_safely(out, handle)
                if ret_code:  # If cmd fails once, it will likely fail again
                    break
        finally:
            os.chdir(cwd)
