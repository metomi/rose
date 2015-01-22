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
"""The authentication manager for the Rosie web service client."""


import ast
from getpass import getpass
try:
    import gnomekeyring
    import gtk
except (ImportError, RuntimeError):
    pass
#try:
#    import keyring
#except ImportError:
#    pass
import os
import re
import rose.config
from rose.env import env_var_process
from rose.popen import RosePopener
from rose.resource import ResourceLocator
import shlex
import socket
import sys
from urlparse import urlparse


class UndefinedRosiePrefixWS(Exception):

    """Raised if a prefix has no config."""

    def __str__(self):
        return "[rosie-id]prefix-ws.%s: configuration not defined" % self.args



class GPGAgentStoreConnectionError(Exception):

    """Raised if a client can't (safely) connect to the gpg-agent daemon."""

    def __str__(self):
        return "Cannot connect to gpg-agent: %s" % self.args[0]


class RosieWSClientAuthManager(object):

    """Manage authentication info for a Rosie web service client."""

    ST_UNC = "UNC"  # Item is unchanged
    ST_MOD = "MOD"  # Item is modified
    PASSWORD_STORE_NAMES = [
        "GnomekeyringStore",
        "GPGAgentStore",
        #KeyringStore,
    ]
    PROMPT_USERNAME = "Username for %(prefix)r: "
    PROMPT_PASSWORD = "Password for %(username)s at %(prefix)r: "
    STR_CANCELLED = "cancelled by user"

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

        self.requests_kwargs = {}
        self._init_https_params()

    def _init_https_params(self):
        """Helper for __init__. Initialise HTTPS related parameters."""
        res_loc = ResourceLocator.default()
        https_ssl_verify_mode_str = res_loc.default().get_conf().get_value([
            "rosie-id",
            "prefix-https-ssl-verify." + self.prefix])
        if https_ssl_verify_mode_str:
            https_ssl_verify_mode = ast.literal_eval(https_ssl_verify_mode_str)
            self.requests_kwargs["verify"] = bool(https_ssl_verify_mode)
        https_ssl_cert_str = res_loc.default().get_conf().get_value([
            "rosie-id",
            "prefix-https-ssl-cert." + self.prefix])
        if https_ssl_cert_str:
            https_ssl_cert = shlex.split(https_ssl_cert_str)
            if len(https_ssl_cert) == 1:
                self.requests_kwargs["cert"] = https_ssl_cert[0]
            else:
                self.requests_kwargs["cert"] = tuple(https_ssl_cert[0:2])

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

    def clear_password(self):
        """Clear stored password information in password_store."""
        if self.password_store is not None:
            self.password_store.clear_password(
                self.scheme, self.host, self.username)

    def store_password(self):
        """Store the authentication information for self.prefix."""
        if self.username and self.username_orig != self.username:
            user_rose_conf_path = os.path.join(ResourceLocator.USER_CONF_PATH,
                                               ResourceLocator.ROSE_CONF)
            if os.access(user_rose_conf_path, os.F_OK | os.R_OK | os.W_OK):
                config = rose.config.load(user_rose_conf_path)
            else:
                config = rose.config.ConfigNode()
            config.set(
                ["rosie-id", "prefix-username." + self.prefix], self.username)
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
        if (callable(self.prompt_func) and
                not hasattr(self.password_store, "prompt_password")):
            self.username, self.password = self.prompt_func(
                self.username, self.password, is_retry)
            return

        icon_path = ResourceLocator.default().locate("images/rosie-icon.png")
        if is_retry:
            username = ""
            if self.username:
                username = ""

            prompt = self.PROMPT_USERNAME % {"prefix": self.prefix}
            if self.popen.which("zenity") and os.getenv("DISPLAY"):
                username = self.popen.run(
                    "zenity", "--entry",
                    "--title=Rosie",
                    "--window-icon=" + icon_path,
                    "--text=" + prompt)[1].strip()
            else:
                username = raw_input(prompt)
            if not username:
                raise KeyboardInterrupt(self.STR_CANCELLED)
            if username and username != self.username:
                self.username = username
                self._load_password()
                if self.password:
                    return

        if self.username and self.password is None or is_retry:
            prompt = self.PROMPT_PASSWORD % {"prefix": self.prefix,
                                             "username": self.username}
            if hasattr(self.password_store, "prompt_password"):
                password = self.password_store.prompt_password(
                    prompt, self.scheme, self.host, self.username)
            elif self.popen.which("zenity") and os.getenv("DISPLAY"):
                password = self.popen.run(
                    "zenity", "--entry", "--hide-text",
                    "--title=Rosie",
                    "--window-icon=" + icon_path,
                    "--text=" + prompt)[1].strip()
            else:
                password = getpass(prompt)
            if not password:
                raise KeyboardInterrupt(self.STR_CANCELLED)
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

    def clear_password(self, scheme, host, username):
        """Remove the password from the cache."""
        try:
            if (scheme, host, username) in self.item_ids:
                ring_id, item_id = self.item_ids[(scheme, host, username)]
                gnomekeyring.item_delete_sync(ring_id, item_id)
        except gnomekeyring.NoKeyringDaemonError:
            pass

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
        self.clear_password(scheme, host, username)
        try:
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


class GPGAgentStore(object):

    """Password management with gpg-agent."""

    RECV_BUFSIZE = 4096

    @classmethod
    def usable(cls):
        """Can this store be used?"""
        try:
            gpg_socket = cls.get_socket()
        except GPGAgentStoreConnectionError as exc:
            return False
        return True

    @classmethod
    def get_socket(cls):
        """Get a connected, ready-to-use socket for gpg-agent."""
        agent_info = os.environ.get("GPG_AGENT_INFO")
        if agent_info is None:
            raise GPGAgentStoreConnectionError("no $GPG_AGENT_INFO env var")
        socket_address = agent_info.split(":")[0]
        gpg_socket = socket.socket(socket.AF_UNIX)
        try:
            gpg_socket.connect(socket_address)
        except socket.error as exc:
            raise GPGAgentStoreConnectionError("socket error: %s" % exc)
        cls._socket_receive(gpg_socket, "^OK .*\n")
        gpg_socket.send("GETINFO socket_name\n")
        reply = cls._socket_receive(gpg_socket, "^(?!OK)[^ ]+ .*\n")
        if not reply.startswith("D"):
            raise GPGAgentStoreConnectionError(
                "socket: bad reply: %r" % reply)
        reply_socket_address = reply.split()[1]
        if reply_socket_address != socket_address:
            # The gpg-agent documentation advises making this check.
            raise GPGAgentStoreConnectionError("daemon socket mismatch")
        tty = os.environ.get("GPG_TTY")
        if tty is None:
            if not sys.stdin.isatty():
                raise GPGAgentStoreConnectionError(
                    "no $GPG_TTY env var and failed to extrapolate it")
            tty = os.ttyname(sys.stdin.fileno())
        gpg_socket.send("OPTION putenv=GPG_TTY=%s\n" % tty)
        cls._socket_receive(gpg_socket, "^OK\n")
        for name in ("TERM", "LANG", "LC_ALL", "DISPLAY"):
            val = os.environ.get(name)
            if val is not None:
                gpg_socket.send("OPTION putenv=%s=%s\n" % (name, val))
                cls._socket_receive(gpg_socket, "^OK\n")
        return gpg_socket

    @classmethod
    def _socket_receive(cls, gpg_socket, pattern):
        reply = ""
        while not reply or not re.search(pattern, reply, re.M):
            reply += gpg_socket.recv(cls.RECV_BUFSIZE)
        return reply

    def __init__(self):
        pass

    def clear_password(self, scheme, host, username):
        """Remove the password from the cache."""
        gpg_socket = self.get_socket()
        gpg_socket.send("CLEAR_PASSPHRASE rosie:%s:%s\n" % (scheme, host))
        # This command always returns 'OK', even when the cache id is invalid.
        reply = self._socket_receive(gpg_socket, "^OK")

    def find_password(self, scheme, host, username):
        """Return the password of username@root."""
        return self.get_password(scheme, host, username, no_ask=True)

    def get_password(self, scheme, host, username, no_ask=False, prompt=None):
        """Store and retrieve the password."""
        gpg_socket = self.get_socket()
        no_ask_option = ""
        if no_ask:
            no_ask_option = "--no-ask"
        if prompt is None:
            prompt = "X"
        else:
            prompt = prompt.replace(" ", "+")
        gpg_socket.send("GET_PASSPHRASE --data %s rosie:%s:%s X X %s\n" % (
            no_ask_option, scheme, host, prompt))
        reply = self._socket_receive(gpg_socket, "^(?!OK)[^ ]+ .*\n")
        for line in reply.splitlines():
            if line.startswith("D"):
                return line.split(None, 1)[1]
        return None

    def prompt_password(self, prompt, scheme, host, username):
        """Prompt for the password of username@root."""
        return self.get_password(scheme, host, username, prompt=prompt)

    def store_password(self, scheme, host, username, password):
        """Store the password of username@root... but it's already stored."""
        pass


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
