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
"""The authentication manager for the Rosie web service client."""

import ast
from getpass import getpass
import os
import re
import shlex
import socket
import sys
from urllib.parse import urlparse
import warnings

import metomi.rose.config
from metomi.rose.env import env_var_process
from metomi.rose.popen import RosePopener
from metomi.rose.reporter import Reporter
from metomi.rose.resource import ResourceLocator

try:
    from gi import require_version, pygtkcompat

    require_version('Gtk', '3.0')  # For GTK+ >=v3 use PyGObject; v2 use PyGTK
    require_version('Secret', '1')
    from gi.repository import Secret

    del pygtkcompat
    GI_FLAG = True
except (ImportError, ValueError):
    GI_FLAG = False
try:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        import gtk
    import gnomekeyring
except ImportError:
    pass


class UndefinedRosiePrefixWS(Exception):
    """Raised if a prefix has no config."""

    def __str__(self):
        return "[rosie-id]prefix-ws.%s: configuration not defined" % self.args


class GPGAgentStoreConnectionError(Exception):

    """Raised if a client can't (safely) connect to the gpg-agent daemon."""

    def __str__(self):
        return "Cannot connect to gpg-agent: %s" % self.args[0]


class RosieStoreRetrievalError(Exception):

    """Raised if a client cannot retrieve info from the password store."""

    def __str__(self):
        message = "Cannot retrieve username/password: %s" % self.args[0]
        if self.args[1]:
            message += ": %s" % self.args[1]
        return message


class GnomekeyringStore:

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
                username, None, host, None, scheme
            )
            ring_id = res[0]["keyring"]
            item_id = res[0]["item_id"]
            self.item_ids[(scheme, host, username)] = (ring_id, item_id)
            return res[0]["password"]
        except (gnomekeyring.NoMatchError, gnomekeyring.NoKeyringDaemonError):
            return
        except gnomekeyring.Error as exc:
            exc_type = "gnomekeyring." + type(exc).__name__
            exc_string = str(exc)
            raise RosieStoreRetrievalError(exc_type, exc_string)

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
                True,
            )
        except (
            gnomekeyring.CancelledError,
            gnomekeyring.NoKeyringDaemonError,
        ):
            pass
        self.item_ids[(scheme, host, username)] = (None, item_id)


class GPGAgentStore:

    """Password management with gpg-agent."""

    RECV_BUFSIZE = 4096

    @classmethod
    def usable(cls):
        """Can this store be used?"""
        try:
            cls.get_socket()
        except GPGAgentStoreConnectionError:
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
        cls._socket_receive(gpg_socket, b"^OK .*\n")
        gpg_socket.send(b"GETINFO socket_name\n")
        reply = cls._socket_receive(gpg_socket, b"^(?!OK)[^ ]+ .*\n")
        if not reply.startswith(b"D"):
            raise GPGAgentStoreConnectionError("socket: bad reply: %r" % reply)
        reply_socket_address = reply.split()[1]
        if reply_socket_address != socket_address:
            # The gpg-agent documentation advises making this check.
            raise GPGAgentStoreConnectionError("daemon socket mismatch")
        tty = os.environ.get("GPG_TTY")
        if tty is None:
            if not sys.stdin.isatty():
                raise GPGAgentStoreConnectionError(
                    "no $GPG_TTY env var and failed to extrapolate it"
                )
            tty = os.ttyname(sys.stdin.fileno())
        gpg_socket.send(b"OPTION putenv=GPG_TTY=%s\n" % tty)
        cls._socket_receive(gpg_socket, b"^OK\n")
        for name in ("TERM", "LANG", "LC_ALL", "DISPLAY"):
            val = os.environ.get(name)
            if val is not None:
                gpg_socket.send(b"OPTION putenv=%s=%s\n" % (name, val))
                cls._socket_receive(gpg_socket, b"^OK\n")
        return gpg_socket

    @classmethod
    def _socket_receive(cls, gpg_socket, pattern):
        reply = b""
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
        self._socket_receive(gpg_socket, b"^OK")

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
        gpg_socket.send(
            "GET_PASSPHRASE --data %s rosie:%s:%s X X %s\n"
            % (no_ask_option, scheme, host, prompt)
        )
        reply = self._socket_receive(gpg_socket, b"^(?!OK)[^ ]+ .*\n")
        replylines = reply.splitlines()
        for line in replylines:
            if line.startswith("D"):
                return line.split(None, 1)[1]
        if not no_ask:
            # We want gpg-agent to prompt for a password.
            for line in replylines:
                if (
                    line.startswith("INQUIRE ")
                    or "Operation cancelled" in line
                ):
                    # Prompt was launched, or a launched prompt was cancelled.
                    return None
            # Prompt couldn't be launched.
            raise RosieStoreRetrievalError(
                "gpg-agent", reply.replace("OK\n", "").replace("\n", " ")
            )
        return None

    def prompt_password(self, prompt, scheme, host, username):
        """Prompt for the password of username@root."""
        return self.get_password(scheme, host, username, prompt=prompt)

    def store_password(self, scheme, host, username, password):
        """Store the password of username@root... but it's already stored."""
        pass


class LibsecretStore:

    """Password management with libsecret."""

    @classmethod
    def usable(cls):
        """Can this store be used?"""
        return bool(GI_FLAG)

    def __init__(self):
        # Attributes must be explicitly defined; not managed by the schema
        self.category = ("protocol", "server", "user")
        self.attributes = dict(
            (key, Secret.SchemaAttributeType.STRING) for key in self.category
        )
        self.schema = Secret.Schema.new(
            "org.rosie.disco.Store", Secret.SchemaFlags.NONE, self.attributes
        )

    def clear_password(self, scheme, host, username):
        """Remove the password from the cache."""
        template = dict(zip(self.category, (scheme, host, username)))
        Secret.password_clear_sync(self.schema, template, None)

    def find_password(self, scheme, host, username):
        """Return the password of username@root."""
        template = dict(zip(self.category, (scheme, host, username)))
        try:
            password = Secret.password_lookup_sync(self.schema, template, None)
        except Secret.SECRET_ERROR_PROTOCOL:
            return
        return password

    def store_password(self, scheme, host, username, password):
        """Return the password of username@root."""
        template = dict(zip(self.category, (scheme, host, username)))
        self.clear_password(scheme, host, username)
        try:
            Secret.password_store_sync(
                self.schema,
                template,
                Secret.COLLECTION_DEFAULT,
                host,
                password,
                None,
            )
        except Secret.SECRET_ERROR_PROTOCOL:
            pass


class RosieWSClientAuthManager:

    """Manage authentication info for a Rosie web service client."""

    ST_UNC = "UNC"  # Item is unchanged
    ST_MOD = "MOD"  # Item is modified
    PASSWORD_STORES_STR = "gpgagent gnomekeyring libsecret"
    PASSWORD_STORE_CLASSES = {
        "gpgagent": GPGAgentStore,
        "gnomekeyring": GnomekeyringStore,
        "libsecret": LibsecretStore,
    }
    PROMPT_USERNAME = "Username for %(prefix)r - %(root)r: "
    PROMPT_PASSWORD = "Password for %(username)s at %(prefix)r - %(root)r: "
    STR_CANCELLED = "cancelled by user"

    def __init__(
        self, prefix, popen=None, prompt_func=None, event_handler=None
    ):
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
        if event_handler is None:
            self.event_handler = Reporter()
        else:
            self.event_handler = event_handler
        res_loc = ResourceLocator.default()
        password_stores_str = (
            res_loc.default()
            .get_conf()
            .get_value(
                keys=["rosie-id", "prefix-password-store." + self.prefix],
                default=self.PASSWORD_STORES_STR,
            )
        )
        for password_store_name in shlex.split(password_stores_str):
            password_store_cls = self.PASSWORD_STORE_CLASSES.get(
                password_store_name
            )
            if password_store_cls is not None and password_store_cls.usable():
                self.password_store = password_store_cls()
                break
        else:
            self.password_store = None

        self.requests_kwargs = {}
        self._init_https_params()

    def _init_https_params(self):
        """Helper for __init__. Initialise HTTPS related parameters."""
        res_loc = ResourceLocator.default()
        https_ssl_verify_mode_str = (
            res_loc.default()
            .get_conf()
            .get_value(["rosie-id", "prefix-https-ssl-verify." + self.prefix])
        )
        if https_ssl_verify_mode_str:
            https_ssl_verify_mode = ast.literal_eval(https_ssl_verify_mode_str)
            self.requests_kwargs["verify"] = bool(https_ssl_verify_mode)
        https_ssl_cert_str = (
            res_loc.default()
            .get_conf()
            .get_value(["rosie-id", "prefix-https-ssl-cert." + self.prefix])
        )
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
        try:
            self._load_password()
        except RosieStoreRetrievalError as exc:
            self.event_handler(exc)
            return None
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
                self.scheme, self.host, self.username
            )

    def store_password(self):
        """Store the authentication information for self.prefix."""
        if self.username and self.username_orig != self.username:
            user_rose_conf_path = os.path.join(
                ResourceLocator.USER_CONF_PATH, ResourceLocator.ROSE_CONF
            )
            if os.access(user_rose_conf_path, os.F_OK | os.R_OK | os.W_OK):
                config = metomi.rose.config.load(user_rose_conf_path)
            else:
                config = metomi.rose.config.ConfigNode()
            config.set(
                ["rosie-id", "prefix-username." + self.prefix], self.username
            )
            metomi.rose.config.dump(config, user_rose_conf_path)
        if (
            self.password_store is not None
            and self.password
            and self.password_orig != self.password
        ):
            self.password_store.store_password(
                self.scheme, self.host, self.username, self.password
            )

    def _get_conf_value(self, name, default=None):
        """Return the value of a named conf setting for this prefix."""
        conf = ResourceLocator.default().get_conf()
        value = conf.get_value(
            ["rosie-id", "prefix-%s.%s" % (name, self.prefix)], default=default
        )
        if value:
            value = env_var_process(value)
        return value

    def _load_password(self, is_retry=False):
        """Load password from store, if possible."""
        if (
            self.password_store is not None
            and self.username
            and (self.password is None or is_retry)
        ):
            self.password = self.password_store.find_password(
                self.scheme, self.host, self.username
            )
            if self.password_orig is None:
                self.password_orig = self.password

    def _prompt(self, is_retry=False):
        """Prompt for the username and password, where necessary.

        Prompt with zenity or raw_input/getpass.

        """
        if callable(self.prompt_func) and not hasattr(
            self.password_store, "prompt_password"
        ):
            self.username, self.password = self.prompt_func(
                self.username, self.password, is_retry
            )
            return

        icon_path = ResourceLocator.default().locate("images/rosie-icon.png")
        if is_retry:
            username = ""

            prompt = self.PROMPT_USERNAME % {
                "prefix": self.prefix,
                "root": self.root,
            }
            if self.popen.which("zenity") and os.getenv("DISPLAY"):
                username = self.popen.run(
                    "zenity",
                    "--entry",
                    "--title=Rosie",
                    "--window-icon=" + icon_path,
                    "--text=" + prompt,
                )[1].strip()
            else:
                username = input(prompt)
            if not username:
                raise KeyboardInterrupt(self.STR_CANCELLED)
            if username and username != self.username:
                self.username = username
                self._load_password(is_retry)
                if self.password:
                    return

        if self.username and self.password is None or is_retry:
            prompt = self.PROMPT_PASSWORD % {
                "prefix": self.prefix,
                "root": self.root,
                "username": self.username,
            }
            password = None
            need_prompting = True
            if hasattr(self.password_store, "prompt_password"):
                try:
                    password = self.password_store.prompt_password(
                        prompt, self.scheme, self.host, self.username
                    )
                except RosieStoreRetrievalError as exc:
                    self.event_handler(exc)
                else:
                    need_prompting = False

            if not password and need_prompting:
                if self.popen.which("zenity") and os.getenv("DISPLAY"):
                    password = self.popen.run(
                        "zenity",
                        "--entry",
                        "--hide-text",
                        "--title=Rosie",
                        "--window-icon=" + icon_path,
                        "--text=" + prompt,
                    )[1].strip()
                else:
                    password = getpass(prompt)
            if not password:
                raise KeyboardInterrupt(self.STR_CANCELLED)
            if password and password != self.password:
                self.password = password
