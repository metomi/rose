# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
"""The authentication manager for the Rosie web service client."""


from getpass import getpass
try:
    import gnomekeyring
    import gtk
except ImportError:
    pass
#try:
#    import keyring
#except ImportError:
#    pass
import os
import rose.config
from rose.env import env_var_process
from rose.popen import RosePopener
from rose.resource import ResourceLocator
from urlparse import urlparse


class UndefinedRosiePrefixWS(Exception):

    """Raised if a prefix has no config."""

    def __str__(self):
        return "[rosie-id]prefix-ws.%s: configuration not defined" % self.args


class RosieWSClientAuthManager(object):

    """Manage authentication info for a Rosie web service client."""

    ST_UNC = "UNC" # Item is unchanged
    ST_MOD = "MOD" # Item is modified
    PASSWORD_STORE_NAMES = [
        "GnomekeyringStore",
        #KeyringStore,
    ]
    PROMPT_USERNAME = "Username for %(prefix)s: "
    PROMPT_PASSWORD = "Password for %(username)s at %(prefix)s: "

    def __init__(self, prefix, popen=None, prompt_func=None):
        self.prefix = prefix
        root = self._get_conf_value("ws")
        if root is None:
            raise UndefinedRosiePrefixWS(self.prefix)
        if not root.endswith("/"):
            root += "/"
        self.root = root
        urlparse_res = urlparse(self.root)
        self.scheme = urlparse_res[0]
        self.host = urlparse_res[1]
        self.password_orig = None
        self.username_orig = None
        self.password = None
        self.username = None
        if popen is None:
            popen = RosePopener()
        self.popen = popen
        self.prompt_func = prompt_func
        for password_store_name in self.PASSWORD_STORE_NAMES:
            password_store_cls = globals()[password_store_name]
            if password_store_cls.usable():
                self.password_store = password_store_cls()
                break
        else:
            self.password_store = None

    def get_auth(self, is_retry=False):
        """Return the authentication information for self.prefix."""
        if self.username is None:
            self.username = self._get_conf_value("username")
            if self.username_orig is None:
                self.username_orig = self.username
        self._load_password()
        if (self.username and not self.password) or is_retry:
            self._prompt(is_retry)
        if self.username and self.password:
            return (self.username, self.password)
        else:
            return ()

    def store_password(self):
        """Store the authentication information for self.prefix."""
        if self.username and self.username_orig != self.username:
            user_rose_conf_path = os.path.join(ResourceLocator.USER_CONF_PATH,
                                               ResourceLocator.ROSE_CONF)
            if os.access(user_rose_conf_path, os.F_OK | os.R_OK | os.W_OK):
                config = rose.config.load(user_rose_conf_path)
                config.set(["rosie-id", "prefix-username." + self.prefix],
                           self.username)
                rose.config.dump(config, user_rose_conf_path)
        if (self.password_store is not None and
                self.password and self.password_orig != self.password):
            self.password_store.store_password(
                        self.scheme, self.host, self.username, self.password)

    def _get_conf_value(self, name, default=None):
        """Return the value of a named conf setting for this prefix."""
        conf = ResourceLocator.default().get_conf()
        value = conf.get_value(
                        ["rosie-id", "prefix-%s.%s" % (name, self.prefix)],
                        default=default)
        if value:
            value = env_var_process(value)
        return value

    def _load_password(self):
        """Load password from store, if possible."""
        if (self.password_store is not None and
                self.username and self.password is None):
            if self.password_store is not None:
                self.password = self.password_store.find_password(
                                        self.scheme, self.host, self.username)
                if self.password_orig is None:
                    self.password_orig = self.password

    def _prompt(self, is_retry=False):
        """Prompt for the username and password, where necessary.

        Prompt with zenity or raw_input/getpass.

        """
        if callable(self.prompt_func):
            self.username, self.password = self.prompt_func(
                                    self.username, self.password, is_retry)
            return

        if is_retry:
            username = ""
            if self.username:
                username = ""

            prompt = self.PROMPT_USERNAME % {"prefix": self.prefix}
            if self.popen.which("zenity") and os.getenv("DISPLAY"):
                username = self.popen.run(
                            "zenity", "--entry",
                            "--title=Rosie",
                            "--text=" + prompt)[1].strip()
            else:
                username = raw_input(prompt)
            if not username:
                raise KeyboardInterrupt()
            if username and username != self.username:
                self.username = username
                self._load_password()
                if self.password:
                    return

        if self.username and self.password is None or is_retry:
            prompt = self.PROMPT_PASSWORD % {"prefix": self.prefix,
                                             "username": self.username}
            if self.popen.which("zenity") and os.getenv("DISPLAY"):
                password = self.popen.run(
                            "zenity", "--entry", "--hide-text",
                            "--title=Rosie",
                            "--text=" + prompt)[1].strip()
            else:
                password = getpass(prompt)
            if not password:
                raise KeyboardInterrupt()
            if password and password != self.password:
                self.password = password


class GnomekeyringStore(object):

    """Password management with gnomekeyring."""

    @classmethod
    def usable(cls):
        """Can this store be used?"""
        if "gnomekeyring" in globals() and gnomekeyring.is_available():
            if "gtk" in globals() and not hasattr(gtk, "application_name"):
                gtk.application_name = "rosie.ws_client"
            return True
        return False

    def __init__(self):
        self.item_ids = {}

    def find_password(self, scheme, host, username):
        """Return the password of username@root."""
        try:
            res = gnomekeyring.find_network_password_sync(
                                        username, None, host, None, scheme)
            ring_id = res[0]["keyring"]
            item_id = res[0]["item_id"]
            self.item_ids[(scheme, host, username)] = (ring_id, item_id)
            return res[0]["password"]
        except (gnomekeyring.NoMatchError, gnomekeyring.NoKeyringDaemonError):
            return

    def store_password(self, scheme, host, username, password):
        """Return the password of username@root."""
        try:
            if (scheme, host, username) in self.item_ids:
                ring_id, item_id = self.item_ids[(scheme, host, username)]
                gnomekeyring.item_delete_sync(ring_id, item_id)
            item_id = gnomekeyring.item_create_sync(
                    None,
                    gnomekeyring.ITEM_NETWORK_PASSWORD,
                    host,
                    {"user": username, "protocol": scheme, "server": host},
                    password,
                    True)
        except (gnomekeyring.CancelledError,
                gnomekeyring.NoKeyringDaemonError):
            pass
        self.item_ids[(scheme, host, username)] = (None, item_id)


#class KeyringStore(object):
#
#    """Password management with keyring."""
#
#    @classmethod
#    def usable(cls):
#        """Can this store be used?"""
#        return "keyring" in globals()
#
#    @classmethod
#    def find_password(cls, scheme, host, username):
#        """Return the password of username@root."""
#        return keyring.get_password(scheme + "://" + host, username)
#
#    @classmethod
#    def store_password(cls, scheme, host, username, password):
#        """Return the password of username@root."""
#        keyring.set_password(scheme + "://" + host, username, password)
