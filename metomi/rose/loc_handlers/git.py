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

import os
import re
import tempfile
from urllib.parse import urlparse


REC_COMMIT_HASH = re.compile(r"^[0-9a-f]+$")


class GitLocHandler:
    """Handler of Git locations."""

    GIT = "git"
    SCHEMES = [GIT]
    WEB_SCHEMES = ["https"]
    URI_SEPARATOR = "::"

    def __init__(self, manager):
        self.manager = manager
        ret_code, versiontext, stderr = self.manager.popen.run(
            "git", "version")
        if ret_code:
            self.git_version = None
        else:
            version_nums = []
            for num_string in versiontext.split()[-1].split("."):
                try:
                    version_nums.append(int(num_string))
                except ValueError:
                    break
            self.git_version = tuple(version_nums)

    def can_pull(self, loc):
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
                "git", "ls-remote", "--exit-code", remote)[0]
            # https://superuser.com/questions/227509/git-ping-check-if-remote-repository-exists
        )

    def parse(self, loc, conf_tree):
        """Set loc.real_name, loc.scheme, loc.loc_type.

        Within Git we have a lot of trouble figuring out remote
        loc_type - a clone is required, unfortunately.

        Short commit hashes will not work since there is no remote
        rev-parse functionality. Long commit hashes will work if the
        uploadpack.allowAnySHA1InWant configuration is set on the
        remote repo or server.

        Filtering requires uploadpack.allowFilter to be set true on
        the remote repo or server.

        """
        loc.scheme = self.SCHEMES[0]
        remote, path, ref = self._parse_name(loc)
        with tempfile.TemporaryDirectory() as tmpdirname:
            git_dir_opt = f"--git-dir={tmpdirname}/.git"
            self.manager.popen.run_ok(
                "git", git_dir_opt, "init"
            )

            # Make sure we configure for minimum fetching.
            if self.git_version < (2, 25, 0):
                self.manager.popen.run_ok(
                    "git", git_dir_opt, "config", "extensions.partialClone",
                    "true"
                )

            # Extract the commit hash if we don't already have it.
            commithash = self._get_commithash(remote, ref)

            # Fetch the ref/commit as efficiently as we can.
            ret_code, _, stderr = self.manager.popen.run(
                "git", git_dir_opt, "fetch", "--depth=1",
                "--filter=blob:none", remote, commithash
            )
            if ret_code:
                raise ValueError(f"source={loc.name}: {stderr}")

            # Determine the type of the path object.
            ret_code, typetext, stderr = self.manager.popen.run(
                "git", git_dir_opt, "cat-file", "-t", f"{commithash}:{path}"
            )  # N.B. git versions >1.8 can use '-C' to set git dir.
            if ret_code:
                raise ValueError(f"source={loc.name}: {stderr}")

        if typetext.strip() == "tree":
            loc.loc_type = loc.TYPE_TREE
        else:
            loc.loc_type = loc.TYPE_BLOB
        loc.real_name = (
            f"remote:{remote} ref:{ref} commit:{commithash} path:{path}"
        )
        loc.key = commithash

    async def pull(self, loc, conf_tree):
        """Get loc to its cache.

        git sparse-checkout is not available below Git 2.25, and seems to omit
        contents altogether if set to the root of the repo (as of 2.40.1).

        """
        if not loc.real_name:
            self.parse(loc, conf_tree)
        remote, path, ref = self._parse_name(loc)
        with tempfile.TemporaryDirectory() as tmpdirname:
            git_dir_opt = f"--git-dir={tmpdirname}/.git"
            await self.manager.popen.run_ok_async(
                "git", git_dir_opt, "init"
            )
            if self.git_version >= (2, 25, 0) and path != "./":
                await self.manager.popen.run_ok_async(
                    "git", git_dir_opt, "sparse-checkout", "set", path,
                    "--no-cone"
                )
                await self.manager.popen.run_ok_async(
                    "git", git_dir_opt, "fetch", "--depth=1",
                    "--filter=blob:none", remote, loc.key
                )
            else:
                await self.manager.popen.run_ok_async(
                    "git", git_dir_opt, "fetch", "--depth=1", remote, loc.key
                )

            await self.manager.popen.run_ok_async(
                "git", git_dir_opt, f"--work-tree={tmpdirname}", "checkout",
                loc.key
            )
            name = tmpdirname + "/" + path
            dest = loc.cache
            if loc.loc_type == "tree":
                dest += "/"
            cmd = self.manager.popen.get_cmd("rsync", name, dest)
            await self.manager.popen.run_ok_async(*cmd)

    def _parse_name(self, loc):
        scheme, nonscheme = loc.name.split(":", 1)
        return re.split(self.URI_SEPARATOR, nonscheme, maxsplit=3)

    def _get_commithash(self, remote, ref):
        ret_code, info, _ = self.manager.popen.run(
            "git", "ls-remote", "--exit-code", remote, ref)
        if ret_code:
            err = f"ls-remote: could not find ref '{ref}' in '{remote}'"
            if REC_COMMIT_HASH.match(ref):
                if len(ref) == 40:
                    # Likely a full commit hash.
                    return ref
                err += ": you may be using an unsupported short commit hash"
            raise ValueError(err)
        return info.split()[0]
