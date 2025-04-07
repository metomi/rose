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
"""A handler of Git locations."""

import errno
import os
import re
import tempfile
from textwrap import indent
from typing import TYPE_CHECKING, Optional, Tuple
from urllib.parse import urlparse

from metomi.rose.popen import RosePopenError

if TYPE_CHECKING:
    from metomi.rose.config_processors.fileinstall import (
        PullableLocHandlersManager,
    )


REC_COMMIT_HASH = re.compile(r"^[0-9a-f]+$")


class GitLocHandler:
    """Handler of Git locations."""

    GIT = "git"
    SCHEMES = [GIT]
    WEB_SCHEMES = ["https"]
    URI_SEPARATOR = "::"

    def __init__(self, manager: 'PullableLocHandlersManager'):
        self.manager = manager
        # Determine (just once) what git version we have, if any.
        try:
            _ret_code, versiontext, _stderr = self.manager.popen.run(
                self.GIT, "version"
            )
        except RosePopenError as exc:
            if exc.ret_code == errno.ENOENT:
                # Git not installed.
                self.git_version: Optional[Tuple[int, ...]] = None
                return
            raise
        # Git is installed, get the version.
        version_nums = []
        for num_string in versiontext.split()[-1].split("."):
            try:
                version_nums.append(int(num_string))
            except ValueError:
                break
        self.git_version = tuple(version_nums)

    def can_pull(self, loc):
        """Determine if this is a suitable handler for loc."""
        if self.git_version is None:
            return False
        scheme = urlparse(loc.name).scheme
        if scheme in self.SCHEMES:
            return True
        if self.URI_SEPARATOR not in loc.name:
            return False
        remote = self._parse_name(loc)[0]
        return (
            scheme in self.WEB_SCHEMES
            and not os.path.exists(loc.name)  # same as svn...
            and not self.manager.popen.run(
                self.GIT, "ls-remote", "--exit-code", remote)[0]
            # https://superuser.com/questions/227509/git-ping-check-if-remote-repository-exists
        )

    def parse(self, loc, conf_tree):
        """Set loc.real_name, loc.scheme, loc.loc_type.

        Within Git we have a lot of trouble figuring out remote
        loc_type - a clone is required, unfortunately. There is a
        tradeoff between extra Git commands and bandwidth vs
        parse failure behaviour. We have decided to short cut the
        loc_type calculation to save commands and bandwidth,
        catching failures later.

        """
        loc.scheme = self.SCHEMES[0]
        remote, path, ref = self._parse_name(loc)

        # Extract the commit hash if we don't already have it.
        commithash = self._get_commithash(remote, ref)

        if path.endswith("/"):  # This is a short cut, checked later.
            loc.loc_type = loc.TYPE_TREE
        else:
            loc.loc_type = loc.TYPE_BLOB
        loc.real_name = (
            f"remote:{remote} ref:{ref} commit:{commithash} path:{path}"
        )
        loc.key = commithash  # We'll notice branch/tag updates.

    async def pull(self, loc, conf_tree):
        """Get loc to its cache.

        git sparse-checkout is not available below Git 2.25, and seems to omit
        contents altogether if set to the root of the repo (as of 2.40.1).

        Filtering requires uploadpack.allowFilter to be set true on
        the remote repo or server.

        """
        if not loc.real_name:
            self.parse(loc, conf_tree)
        remote, path, ref = self._parse_name(loc)
        with tempfile.TemporaryDirectory() as tmpdirname:
            git_dir_opt = f"--git-dir={tmpdirname}/.git"
            await self.manager.popen.run_ok_async(
                self.GIT, git_dir_opt, "init"
            )
            if self.git_version >= (2, 25, 0) and path != "./":
                # sparse-checkout available and suitable for this case.
                await self.manager.popen.run_ok_async(
                    self.GIT, git_dir_opt, "sparse-checkout", "set", path,
                    "--no-cone"
                )
                await self.manager.popen.run_ok_async(
                    self.GIT, git_dir_opt, "fetch", "--depth=1",
                    "--filter=blob:none", remote, loc.key
                )
            else:
                # Fallback.
                await self.manager.popen.run_ok_async(
                    self.GIT, git_dir_opt, "fetch", "--depth=1", remote,
                    loc.key
                )

            # Checkout to temporary location, then extract only 'path' later.
            await self.manager.popen.run_ok_async(
                self.GIT, git_dir_opt, f"--work-tree={tmpdirname}", "checkout",
                loc.key
            )
            name = tmpdirname + "/" + path

            # Check that we have inferred the right type from the path name.
            real_loc_type = (
                loc.TYPE_TREE if os.path.isdir(name) else loc.TYPE_BLOB
            )
            if real_loc_type != loc.loc_type:
                raise ValueError(
                    f"Expected path '{path}' to be type '{loc.loc_type}', "
                    + f"but it was '{real_loc_type}'. Check trailing slash."
                )

            # Extract only 'path' to cache.
            dest = loc.cache
            if loc.loc_type == "tree":
                dest += "/"
            cmd = self.manager.popen.get_cmd("rsync", name, dest)
            await self.manager.popen.run_ok_async(*cmd)

    def _parse_name(self, loc):
        scheme, nonscheme = loc.name.split(":", 1)
        return nonscheme.split(self.URI_SEPARATOR, maxsplit=3)

    def _get_commithash(self, remote, ref):
        """Get the commit hash given a branch, tag, or commit hash.

        Short commit hashes will not resolve since there is no remote
        rev-parse functionality.

        """
        ret_code, info, fail = self.manager.popen.run(
            self.GIT, "ls-remote", "--exit-code", remote, ref)
        if ret_code and ret_code != 2:
            # repo not found
            raise ValueError(
                f"ls-remote: could not locate '{remote}':"
                f"\n{indent(fail, ' ' * 4)}"
            )
        if ret_code:
            err = f"ls-remote: could not find ref '{ref}' in '{remote}'"
            if REC_COMMIT_HASH.match(ref):
                if len(ref) in [40, 64]:  # SHA1, SHA256 hashes.
                    # Likely a full commit hash, but the server
                    # uploadpack.allowAnySHA1InWant configuration is not set.
                    return ref
                err += ": you may be using an unsupported short commit hash"
            raise ValueError(err)
        return info.split()[0]
