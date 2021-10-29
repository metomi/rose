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
"""User information via LDAP."""

try:
    import ldap3 as ldap
except ImportError:
    pass
import os

from metomi.rose.resource import ResourceLocator


class LDAPUserTool:

    """User information tool via LDAP."""

    USER_ATTRS = "uid cn mail"
    UID_IDX = 0
    CN_IDX = 1
    MAIL_IDX = 2
    PASSWD_FILE = "~/.ldappw"
    SCHEME = "ldap"

    def __init__(self, *_, **kwargs):
        self.manager = kwargs["manager"]

    @classmethod
    def get_emails(cls, users):
        """Return emails of valid users."""
        return cls._search(users, cls.MAIL_IDX)

    @classmethod
    def verify_users(cls, users):
        """Verify list of users are in the LDAP directory.

        Return a list of bad users.

        """
        # N.B. Will they be unique?
        good_users = cls._search(users, cls.UID_IDX)
        return [user for user in users if user not in good_users]

    @classmethod
    def _search(cls, users, attr_idx):
        """Search LDAP directory for the indexed attr for users.

        Attr index can be UID_IDX, CN_IDX or MAIL_IDX.

        Return a list containing the results.

        """
        conf = ResourceLocator.default().get_conf()
        uri = conf.get_value(["rosa-ldap", "uri"])
        binddn = conf.get_value(["rosa-ldap", "binddn"])
        passwd = ""
        passwd_file = conf.get_value(
            ["rosa-ldap", "password-file"], cls.PASSWD_FILE
        )
        if passwd_file:
            passwd = open(os.path.expanduser(passwd_file)).read().strip()
        basedn = conf.get_value(["rosa-ldap", "basedn"], "")
        filter_str = "(|(uid=" + ")(uid=".join(users) + "))"
        filter_more_str = conf.get_value(["rosa-ldap", "filter-more"], "")
        if filter_more_str:
            filter_str = "(&" + filter_str + filter_more_str + ")"
        user_attr_str = conf.get_value(["rosa-ldap", "attrs"], cls.USER_ATTRS)
        attr = user_attr_str.split()[attr_idx]

        tls_ca_file = conf.get_value(["rosa-ldap", "tls-ca-file"])
        if tls_ca_file:
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, tls_ca_file)
        conn = ldap.initialize(uri)
        conn.bind_s(binddn, passwd)
        results = conn.search_s(basedn, ldap.SCOPE_SUBTREE, filter_str, [attr])
        conn.unbind()
        return [result[1][attr][0] for result in results]
