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
"""Rosie web service client.

Classes:
    RosieWSClient - sends requests, retrieves data from the web server

"""


import json
from multiprocessing import Pool
import shlex
from time import sleep

import requests

from metomi.rose.popen import RosePopener
from metomi.rose.reporter import Reporter
from metomi.rose.resource import ResourceLocator
from metomi.rosie.suite_id import SuiteId
from metomi.rosie.ws_client_auth import RosieWSClientAuthManager


class RosieWSClientConfError(Exception):

    """Raised if no Rosie service server is configured."""

    def __str__(self):
        msg = (
            "[metomi.rosie-id] settings not defined in site/user"
            " configuration."
        )
        return msg


class RosieWSClientError(Exception):

    """Raised if no data were retrieved from the server."""

    def __str__(self):
        return ": ".join([str(arg) for arg in self.args])


class RosieWSClientQuerySplitError(RosieWSClientError):

    """Raised on query items syntax error."""

    def __str__(self):
        return "Query syntax error: " + " ".join(self.args[0])


class RosieWSClient:

    """A client for the Rosie web service.

    Args:
        prefixes (list): List of prefix names as strings.
            (run ``rose config rosie-id`` for more info).
        prompt_func (function): Optional function for requesting user
            credentials. Takes and returns the arguments username and password.
        popen (rose.popen.RosePopener): Use initiated RosePopener instance
            create a new one if ``None``.
        event_handler : A callable object for reporting popen output,
            see :py:class:`metomi.rose.reporter.Reporter`.
    """

    MAX_LOCAL_QUERIES = 64
    POLL_DELAY = 0.1
    REMOVABLE_PARAMS = ["all_revs=0", "format=json"]

    def __init__(
        self, prefixes=None, prompt_func=None, popen=None, event_handler=None
    ):
        if not event_handler:
            event_handler = Reporter()
        if not popen:
            popen = RosePopener(event_handler=event_handler)
        self.event_handler = event_handler
        self.popen = popen
        self.prompt_func = prompt_func
        self.prefixes = []
        self.unreachable_prefixes = []
        self.auth_managers = {}
        conf = ResourceLocator.default().get_conf()
        conf_rosie_id = conf.get(["rosie-id"], no_ignore=True)
        if conf_rosie_id is None:
            raise RosieWSClientConfError()
        for key, node in conf_rosie_id.value.items():
            if node.is_ignored() or not key.startswith("prefix-ws."):
                continue
            prefix = key.replace("prefix-ws.", "")
            self.auth_managers[prefix] = RosieWSClientAuthManager(
                prefix, popen=self.popen, prompt_func=self.prompt_func
            )
        if not prefixes:
            prefixes_str = conf_rosie_id.get_value(["prefixes-ws-default"])
            if prefixes_str:
                prefixes = shlex.split(prefixes_str)
            else:
                prefixes = sorted(self.auth_managers.keys())
        self.set_prefixes(prefixes)

    def set_prefixes(self, prefixes):
        """Replace the default prefixes.

        Args:
            prefixes (list): List of prefix names as strings.
        """
        prefixes.sort()
        if self.prefixes != prefixes:
            self.prefixes = prefixes
        for prefix in self.prefixes:
            if prefix in self.auth_managers:
                continue
            self.auth_managers[prefix] = RosieWSClientAuthManager(
                prefix,
                popen=self.popen,
                prompt_func=self.prompt_func,
                event_handler=self.event_handler,
            )
        # Remove uncontactable prefixes from the list.
        ok_prefixes = self.hello(return_ok_prefixes=True)
        prefixes = []
        self.unreachable_prefixes = []
        for prefix in self.prefixes:
            if prefix in ok_prefixes:
                prefixes.append(prefix)
            else:
                self.unreachable_prefixes.append(prefix)
        self.prefixes = prefixes

    def _get(self, method, return_ok_prefixes=False, **kwargs):
        """Send an HTTP GET request to the known servers.

        Return a list, each element is the result from a successful request to
        a web server.

        """
        # Gather the details of the requests to send
        if method == "address":
            url = kwargs.pop("url")
            url = self._remove_params(url)
        else:
            url = method
        request_details = {}
        if url.startswith("http"):
            for prefix in self.prefixes:
                auth_manager = self.auth_managers[prefix]
                if url.startswith(auth_manager.root):
                    request_details[url] = self._create_request_detail(
                        url, prefix, kwargs, auth_manager
                    )
                    break
            else:
                request_details[url] = self._create_request_detail(
                    url, prefix, kwargs
                )
        else:
            for prefix in self.prefixes:
                auth_manager = self.auth_managers[prefix]
                full_url = auth_manager.root + url
                request_details[full_url] = self._create_request_detail(
                    full_url, prefix, kwargs, auth_manager
                )
        if not request_details:
            raise RosieWSClientError(method, kwargs)

        # Process the requests in parallel
        pool = Pool(len(request_details))
        results = {}
        for url, request_detail in request_details.items():
            results[url] = pool.apply_async(
                requests.get, [url], request_detail["requests_kwargs"]
            )
        while results:
            for url, result in list(results.items()):
                if not result.ready():
                    continue
                results.pop(url)
                try:
                    response = result.get()
                except (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.MissingSchema,
                ) as exc:
                    self.event_handler(RosieWSClientError(url, exc), level=1)
                    continue
                request_detail = request_details[url]
                # Retry request once, if it fails with a 401
                if (
                    response.status_code == requests.codes["unauthorized"]
                    and request_detail["can_retry"]
                ):
                    requests_kwargs = request_detail["requests_kwargs"]
                    auth_manager = request_detail["auth_manager"]
                    prev_auth = requests_kwargs["auth"]
                    try:
                        requests_kwargs["auth"] = auth_manager.get_auth(
                            is_retry=True
                        )
                    except KeyboardInterrupt as exc:
                        error = RosieWSClientError(url, kwargs, exc)
                        self.event_handler(error, level=1)
                        request_detail["can_retry"] = False
                    else:
                        results[url] = pool.apply_async(
                            requests.get, [url], requests_kwargs
                        )
                        request_detail["can_retry"] = (
                            prev_auth != requests_kwargs["auth"]
                        )
                    continue
                request_detail["response"] = response
            if results:
                sleep(self.POLL_DELAY)
        pool.close()
        pool.join()

        # Process and return the results
        ret = []
        for url, request_detail in sorted(request_details.items()):
            response = request_detail["response"]
            if response is None:
                continue
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException:
                if request_detail["auth_manager"] is not None:
                    request_detail["auth_manager"].clear_password()
                self.event_handler(
                    RosieWSClientError(url, kwargs, response.status_code),
                    level=1,
                )
                continue
            if request_detail["auth_manager"] is not None:
                request_detail["auth_manager"].store_password()
            response_url = self._remove_params(response.url)
            try:
                response_data = json.loads(response.text)
                if return_ok_prefixes:
                    ret.append(request_detail["prefix"])
                else:
                    ret.append((response_data, response_url))
            except ValueError:
                self.event_handler(RosieWSClientError(url, kwargs), level=1)

        if not ret:
            raise RosieWSClientError(method, kwargs)
        return ret

    @classmethod
    def _remove_params(cls, url):
        """Remove removable parameters from url."""
        for removable_param in cls.REMOVABLE_PARAMS:
            url = url.replace("?" + removable_param, "?")
            url = url.replace("&" + removable_param, "")
        return url.replace("?&", "?").rstrip("?")

    @classmethod
    def _create_request_detail(cls, url, prefix, params, auth_manager=None):
        """Helper for "_get". Return a dict with request details.

        The dict will be populated like this:
        {
            "url": url,
            "prefix": prefix,
            "auth_manager": auth_manager,
            "can_retry": False,
            "requests_kwargs": requests_kwargs,
            "response": None,
        }
        """
        params = dict(params)
        params["format"] = "json"
        requests_kwargs = {"params": params}
        can_retry = auth_manager is not None
        if auth_manager:
            requests_kwargs.update(auth_manager.requests_kwargs)
            requests_kwargs["auth"] = auth_manager.get_auth()
            if requests_kwargs["auth"] is None:
                # None implies a failure to get auth, unlike '()'.
                can_retry = False
                requests_kwargs.pop("auth")
        return {
            "auth_manager": auth_manager,
            "can_retry": can_retry,
            "requests_kwargs": requests_kwargs,
            "response": None,
            "prefix": prefix,
            "url": url,
        }

    def _get_keys(self, name):
        """Return named keys from web services."""
        ret = []
        for data, _ in self._get(name):
            for datum in data:
                if datum not in ret:
                    ret.append(datum)
        return ret

    def get_known_keys(self):
        """Return the known query keys."""
        return self._get_keys("get_known_keys")

    def get_optional_keys(self):
        """Return the optional query keys."""
        return self._get_keys("get_optional_keys")

    def get_query_operators(self):
        """Return the query operators."""
        return self._get_keys("get_query_operators")

    def hello(self, return_ok_prefixes=False):
        """Ask the server to say hello."""
        return self._get("hello", return_ok_prefixes=return_ok_prefixes)

    def query(self, q, **kwargs):
        """Query the Rosie database."""
        return self._get("query", q=q, **kwargs)

    def search(self, s, **kwargs):
        """Search the Rosie database for a matching string."""
        return self._get("search", s=s, **kwargs)

    def address_lookup(self, **kwargs):
        """Repeat a Rosie query or search by address."""
        return self._get("address", **kwargs)

    def query_local_copies(self, user=None):
        """Returns details of the local suites.

        As if they had been obtained using a search or query.

        """
        suite_ids = []
        for suite_id in SuiteId.get_checked_out_suite_ids(user=user):
            if suite_id.prefix in self.prefixes:
                suite_ids.append(suite_id)
        if not suite_ids:
            return []

        # Simple query
        results = []
        queued_suite_ids = list(suite_ids)
        while queued_suite_ids:  # Batch up queries
            q_list = []
            for _ in range(self.MAX_LOCAL_QUERIES):
                if not queued_suite_ids:
                    break
                suite_id = queued_suite_ids.pop()
                q_list.append("or ( idx eq %s" % suite_id.idx)
                q_list.append("and branch eq %s )" % suite_id.branch)
            for data, _ in self.query(q_list):
                results.extend(data)
        result_idx_branches = []
        for result in results:
            result_idx_branches.append((result["idx"], result["branch"]))

        # A branch may have been deleted - query with all_revs=1.
        # We only want to use all_revs on demand as it's slow.
        queued_suite_ids = []
        for suite_id in suite_ids:
            if (suite_id.idx, suite_id.branch) not in result_idx_branches:
                queued_suite_ids.append(suite_id)
        if not queued_suite_ids:
            return results
        while queued_suite_ids:  # Batch up queries
            q_list = []
            for _ in range(self.MAX_LOCAL_QUERIES):
                if not queued_suite_ids:
                    break
                suite_id = queued_suite_ids.pop()
                q_list.append("or ( idx eq %s" % suite_id.idx)
                q_list.append("and branch eq %s )" % suite_id.branch)
            more_results = []
            for data, _ in self.query(q_list, all_revs=1):
                more_results.extend(data)
            new_results = {}
            for result in more_results:
                idx_branch = (result["idx"], result["branch"])
                if (
                    idx_branch not in new_results
                    or result["revision"] > new_results[idx_branch]["revision"]
                ):
                    new_results.update({idx_branch: result})
            for _, result in sorted(new_results.items()):
                results.append(result)
        return results

    @classmethod
    def query_split(cls, args):
        """Split a list of arguments into a list of query items."""
        args = list(args)
        if args[0] not in ["and", "or"]:
            args.insert(0, "and")
        q_list = []  # Query list
        q_item = []  # Individual query pieces list
        level = 0  # Number of open brackets
        while args:
            arg = args.pop(0)
            arg_1 = args[0] if args else None
            if arg in ["and", "or"] and arg_1 not in ["and", "or"]:
                if len(q_item) >= 4:
                    q_list.append(q_item)
                    q_item = []
            elif not args:
                q_item.append(arg)
                if len(q_item) < 4:
                    raise RosieWSClientQuerySplitError(args)
                q_list.append(q_item)
                q_item = []
            q_item.append(arg)
            level += len(arg) if all([c == "(" for c in arg]) else 0
            level -= len(arg) if all([c == ")" for c in arg]) else 0
        if (
            len(q_item) > 1
            or level != 0
            or any(len(q_item) not in [4, 5, 6] for q_item in q_list)
        ):
            raise RosieWSClientQuerySplitError(args)
        return q_list
