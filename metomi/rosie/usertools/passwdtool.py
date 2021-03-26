#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
"""User information via Unix password info."""

from pwd import getpwnam


class PasswdUserTool:

    """User information tool via Unix password info."""

    SCHEME = "passwd"

    def __init__(self, *_, **kwargs):
        self.manager = kwargs["manager"]

    @classmethod
    def get_emails(cls, users):
        """Return a list of user IDs in users that are valid users.

        This assumes that it is possible to email the user IDs.

        """
        good_users = []
        for user in users:
            try:
                getpwnam(user)
            except KeyError:
                pass
            else:
                good_users.append(user)
        return good_users

    @classmethod
    def verify_users(cls, users):
        """Verify list of users are in the Unix password file.

        Return a list of bad users.

        """
        bad_users = []
        for user in users:
            try:
                getpwnam(user)
            except KeyError:
                bad_users.append(user)
        return bad_users
