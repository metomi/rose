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
"""The web service client.

Classes:
    RosieWSClient  - sends requests, retrieves data from the web server

Functions:
    lookup  - run searches to retrieve suite properties
    main    - launcher for the other functions

"""


import ast
import os
import re
import requests
from rosie.suite_id import SuiteId, SuiteIdError
from rosie.ws_client_auth import (RosieWSClientAuthManager,
                                  UndefinedRosiePrefixWS)
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Reporter, Event
from rose.resource import ResourceLocator
import shlex
import simplejson
import sys
import time

ERR_INVALID_URL = "Invalid url: {0}"
ERR_NO_SUITES_FOUND = "{0}: no suites found."
ERR_NO_TARGET_AT_REV = "{0}: target does not exist at this revision"
ERR_SYNTAX = "Syntax error: {0}"
ERR_USAGE = "rosie: incorrect usage"

PRINT_FORMAT_DEFAULT = "%local %suite %owner %project %title"
PRINT_FORMAT_QUIET = "%suite"

REC_COL_IN_FORMAT = re.compile("(?:^|[^%])%([\w-]+)")
REC_ID = re.compile("\A(?:(\w+)-)?(\w+)(?:/([^\@/]+))?(?:@([^\@/]+))?\Z")

STATUS_CR = "X"
STATUS_DO = ">"
STATUS_OK = "="
STATUS_MO = "M"
STATUS_NO = " "
STATUS_SW = "S"
STATUS_UP = "<"


class QueryError(Exception):

    """Raised if no data were retrieved from the server."""

    pass


class RosieWSClient(object):

    """A client for the Rosie web service."""

    def __init__(self, prefix=None, popen=None, prompt_func=None):
        if prefix is None:
            prefix = SuiteId.get_prefix_default()
        self.prefix = prefix
        self.auth_manager = RosieWSClientAuthManager(
                        self.prefix, popen=popen, prompt_func=prompt_func)
        self.root = self.auth_manager.root
        self.requests_kwargs = {}
        res_loc = ResourceLocator.default()
        https_ssl_verify_mode_str = res_loc.get_value([
            "rosie-id",
            "prefix-https-ssl-verify." + prefix])
        if https_ssl_verify_mode_str:
            https_ssl_verify_mode = ast.literal_eval(https_ssl_verify_mode_str)
            self.requests_kwargs["verify"] = bool(https_ssl_verify_mode)
        https_ssl_cert_str = res_loc.get_value([
            "rosie-id",
            "prefix-https-ssl-cert." + prefix])
        if https_ssl_cert_str:
            https_ssl_cert = shlex.split(https_ssl_cert_str)
            if len(https_ssl_cert) == 1:
                self.requests_kwargs["cert"] = https_ssl_cert[0]
            else:
                self.requests_kwargs["cert"] = tuple(https_ssl_cert[0:2])

    def _get(self, method, **kwargs):
        """Send a JSON object to the web server and retrieve results."""
        if method == "address":
            url = kwargs.pop("url").replace("&format=json", "")
        else:
            url = self.root + method
        kwargs["format"] = "json"

        is_retry = False
        while True:
            auth = self.auth_manager.get_auth(is_retry)
            try:
                requests_kwargs = dict(self.requests_kwargs)
                requests_kwargs["params"] = kwargs
                requests_kwargs["auth"] = auth
                response = requests.get(url, **requests_kwargs)
            except requests.exceptions.ConnectionError as exc:
                raise QueryError("%s: %s: %s" % (url, method, str(exc)))
            except requests.exceptions.MissingSchema as exc:
                raise QueryError("URL Error: %s" % (str(exc)))

            if response.status_code != requests.codes["unauthorized"]: # not 401
                break
            is_retry = True

        try:
            response.raise_for_status()
        except:
            raise QueryError("%s: %s: %s" % (url, kwargs, response.status_code))

        self.auth_manager.store_password()

        try:
            response_url = response.url.replace("&format=json", "")
            return simplejson.loads(response.text), response_url
        except ValueError:
            raise QueryError("%s: %s" % (method, kwargs))

    def get_known_keys(self):
        """Return the known query keys."""
        return self._get("get_known_keys")[0]

    def get_optional_keys(self):
        """Return the optional query keys."""
        return self._get("get_optional_keys")[0]

    def get_query_operators(self):
        """Return the query operators."""
        return self._get("get_query_operators")[0]

    def hello(self):
        """Ask the server to say hello."""
        return self._get("hello")[0]

    def query(self, q, **kwargs):
        """Query the Rosie database."""
        return self._get("query", q=q, **kwargs)

    def search(self, s, **kwargs):
        """Search the Rosie database for a matching string."""
        return self._get("search", s=s, **kwargs)

    def address_search(self, a, **kwargs):
        """Repeat a Rosie query or search by address."""
        return self._get("address", a=a, **kwargs)


class URLEvent(Event):

    """Print query URL."""

    def __str__(self):
        return "url: " + self.args[0]


class SuiteEvent(Event):

    """Notify a suite is found."""

    def __str__(self):
        return self.args[0]

class UserSpecificRoses(Event):

    """Print local "roses" location."""

    def __str__(self):
        return "Listing suites in: " + self.args[0]

class SuiteInfo(Event):

    """Print suite info."""

    LEVEL = Event.V

    def __str__(self):

        time_format = "%Y-%m-%dT%H:%M:%S %Z"
        dict_row = dict(self.args[0].items())
        out = ""
        out = out + "id: %s\n" % dict_row["idx"]
        for key in sorted(dict_row.keys()):
            value = dict_row[key]
            if key != "idx":
                if value and isinstance(value, list):
                    value = " ".join(value)
                if key == "date" and isinstance(value, int):
                    out = (out + "\t" + key + ": " +
                           time.strftime(time_format,
                                         time.localtime(value)) + "\n")
                else:
                    out = out + "\t" + key + ": " + str(value) + "\n"
        return out


def list_local_suites(argv):
    """CLI command to list all the locally checked out suites"""
    opt_parser = RoseOptionParser().add_my_options(
            "no_headers", "prefix", "print_format", "reverse", "sort", "user")
    opts = opt_parser.parse_args(argv)[0]

    if opts.user:
        report = Reporter(opts.verbosity - opts.quietness)
        alternative_roses_dir = os.path.expanduser(opts.user) + "/roses"
        report(UserSpecificRoses(alternative_roses_dir), prefix=None)

    ws_client = RosieWSClient(prefix=opts.prefix)
    if opts.prefix is not None:
        try:
            results, id_list = get_local_suite_details(opts.prefix,
                                                       user=opts.user)
            return _display_maps(opts, ws_client,
                                 results, local_suites=id_list)
        except QueryError:
            sys.exit("Error querying details of local suites")
    else:
        id_list = get_local_suites(user=opts.user)
        if len(id_list) > 0:
            prefixes = []
            for id_ in id_list:
                prefixes.append(id_.prefix)
            for prefix in sorted(set(prefixes)):
                if len(prefixes) == 1:
                    suites_this_prefix = id_list
                else:
                    suites_this_prefix = []
                    for id_ in id_list:
                        if id_.prefix == prefix:
                            suites_this_prefix.append(id_)

                results = get_local_suite_details(
                                prefix, id_list, user=opts.user)[0]
                opts.prefix = prefix
                _display_maps(opts, ws_client, results,
                              local_suites=suites_this_prefix)
        return


def hello(argv):
    """Set up connection to a Rosie web service."""
    opt_parser = RoseOptionParser().add_my_options("prefix")
    opts = opt_parser.parse_args(argv)[0]
    report = Reporter(opts.verbosity - opts.quietness)
    popen = RosePopener(event_handler=report)
    ws_client = RosieWSClient(prefix=opts.prefix, popen=popen)
    report(ws_client.prefix + ": " + ws_client.hello(), level=0)


def lookup(argv):
    """CLI command to run the various search types"""
    opt_parser = RoseOptionParser().add_my_options(
            "all_revs", "no_headers", "prefix", "print_format", "query",
            "reverse", "search", "sort", "url")
    opts, args = opt_parser.parse_args(argv)
    if not args:
        sys.exit(opt_parser.print_usage())
    if not opts.query and not opts.search and not opts.url:
        if args[0].startswith("http"):
            opts.url = True
        else:
            opts.search = True
    ws_client = RosieWSClient(prefix=opts.prefix)
    results = None
    if opts.url:
        addr = args[0]
        if opts.debug_mode:
            results, url = ws_client.address_search(None, url=addr)
        else:
            try:
                results, url = ws_client.address_search(None, url=addr)
            except QueryError:
                sys.exit(ERR_INVALID_URL.format(args[0]))
    elif opts.query:
        q_items = query_split(args)
        if q_items is None:
            sys.exit(ERR_SYNTAX.format(" ".join(args)))
        for i, q_item in enumerate(q_items):
            q_items[i] = " ".join(q_item)
        if opts.all_revs:
            results, url = ws_client.query(q_items, all_revs=True)
        else:
            results, url = ws_client.query(q_items)
    elif opts.search:
        if opts.all_revs:
            results, url = ws_client.search(args, all_revs=True)
        else:
            results, url = ws_client.search(args)
    if results is not None:
        return _display_maps(opts, ws_client, results, url)


def query_split(args):
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
        if (arg in ["and", "or"] and arg_1 not in ["and", "or"]):
            if len(q_item) >= 4:
                q_list.append(q_item)
                q_item = []
        elif not args:
            q_item.append(arg)
            if len(q_item) < 4:
                return None
            q_list.append(q_item)
            q_item = []
        q_item.append(arg)
        level += len(arg) if all([c == "(" for c in arg]) else 0
        level -= len(arg) if all([c == ")" for c in arg]) else 0
    if (len(q_item) > 1 or level != 0 or
            any([len(q_item) > 6 or len(q_item) < 4 for q_item in q_list])):
        return None
    return q_list


def get_local_suites(prefix=None, skip_status=False, user=None):
    """Returns a dict of prefixes and id tuples for locally-present suites."""
    local_copies = []

    if user:
        local_copy_root = os.path.expanduser(user) + "/roses"
    else:
        local_copy_root = SuiteId.get_local_copy_root()

    if not os.path.isdir(local_copy_root):
        return local_copies
    for path in os.listdir(local_copy_root):
        location = os.path.join(local_copy_root, path)
        try:
            id_ = SuiteId(location=location, skip_status=skip_status)
        except SuiteIdError:
            continue
        if prefix is None or id_.prefix == prefix:
            if str(id_) == path:
                local_copies.append(id_)
    return local_copies


def get_local_suite_details(prefix=None, id_list=None, skip_status=False,
                            user=None):
    """returns details of the local suites as if they had been obtained using
       a search or query.
       """
    if prefix == None:
        return [], []

    if id_list == None:
        id_list = get_local_suites(skip_status=skip_status, user=user)

    if not id_list:
        return [], []

    result_maps = []
    q_list = []
    prefix_id_list = []
    for id_ in id_list:
        if id_.prefix == prefix:
            prefix_id_list.append(id_)
            q_list.extend(["or ( idx eq " + id_.idx,
                           "and branch eq " + id_.branch + " )"])
    ws_client = RosieWSClient(prefix=prefix)
    if q_list:
        result_maps = ws_client.query(q_list)[0]
    else:
        result_maps = []
    result_idx_branches = [(r[u"idx"], r[u"branch"]) for r in result_maps]
    q_list = []
    for id_ in prefix_id_list:
        if (id_.idx, id_.branch) not in result_idx_branches:
            # A branch may have been deleted - we need all_revs True.
            # We only want to use all_revs on demand as it's slow.
            q_list.extend(["or ( idx eq " + id_.idx,
                           "and branch eq " + id_.branch + " )"])
    if q_list:
        missing_result_maps = ws_client.query(q_list, all_revs=True)[0]
        new_results = {}
        for result_map in missing_result_maps:
            missing_id = (result_map[u"idx"], result_map[u"branch"])
            if (missing_id not in new_results or
                result_map[u"revision"] > new_results[missing_id][u"revision"]):
                new_results.update({missing_id: result_map})
        for key in sorted(new_results):
            result_maps.append(new_results[key])
    return result_maps, id_list


def get_local_status(suites, prefix, idx, branch, revision):
    """Return a text token denoting the local status of a suite."""
    status = STATUS_NO
    for suite_id in suites:
        if prefix is not None and suite_id.prefix != prefix:
            continue
        if suite_id.idx == idx:
            status = STATUS_SW
            if suite_id.corrupt:
                status = STATUS_CR
            elif suite_id.branch == branch:
                status = STATUS_DO
                if int(suite_id.revision) < int(revision):
                    status = STATUS_UP
                elif int(suite_id.revision) == int(revision):
                    status = STATUS_OK
                    if suite_id.modified:
                        status = STATUS_MO
            break
    return status


def align(rows, keys):
    """Function to align results to be displayed by display map"""
    if len(rows) <= 1:
        return rows
    for k in keys:
        if k == "date":
            time_format = "%Y-%m-%d %H:%M:%S %z" #possibly put a T in
            for row in rows:
                try:
                    row[k] = time.strftime(time_format,
                                           time.localtime(row.get(k)))
                except (TypeError):
                    pass
        else:
            try:
                max_len = max([len(rows[i].get(k, "%" + k))
                               for i in range(len(rows))])
                for row in rows:
                    row[k] = row.get(k, "%" + k) + " " * (max_len -
                                                      len(row.get(k, "%" + k)))
            except (TypeError, KeyError):
                pass
    return rows


def _display_maps(opts, ws_client, dict_rows, url=None, local_suites=None):
    """Display returned suite details."""
    report = Reporter(opts.verbosity - opts.quietness)
    popen = RosePopener(event_handler=report)

    try:
        terminal_cols = int(popen("stty size", shell=True)[0].split()[1])
    except (IndexError, RosePopenError, ValueError):
        terminal_cols = None

    if terminal_cols == 0:
        terminal_cols = None

    if not opts.prefix:
        opts.prefix = ws_client.prefix

    if opts.quietness and not opts.print_format:
        opts.print_format = PRINT_FORMAT_QUIET
    elif not opts.print_format:
        opts.print_format = PRINT_FORMAT_DEFAULT

    all_keys = ws_client.get_known_keys()

    if local_suites == None:
        local_suites = get_local_suites(opts.prefix)

    check_local = "%local" in opts.print_format

    for dict_row in dict_rows:
        dict_row["suite"] = "%s/%s@%s" % (
                            dict_row["idx"],
                            dict_row["branch"],
                            dict_row["revision"])
        if check_local:
            dict_row["local"] = get_local_status(local_suites,
                                                 opts.prefix,
                                                 dict_row["idx"],
                                                 dict_row["branch"],
                                                 dict_row["revision"])
    all_keys += ["suite"]
    if check_local:
        all_keys += ["local"]

    more_keys = []
    for key in REC_COL_IN_FORMAT.findall(opts.print_format):
        if key not in all_keys:
            more_keys.append(key)
    all_keys += more_keys

    if opts.sort is None or opts.sort not in all_keys:
        opts.sort = "revision"
    dict_rows.sort(lambda x, y: cmp(x[opts.sort], y[opts.sort]))
    if opts.reverse:
        dict_rows.reverse()

    keylist = []
    for key in all_keys:
        if "%" + key in opts.print_format:
            keylist.append(key)

    if not opts.no_headers:
        dummy_row = {}
        for key in all_keys:
            dummy_row[key] = key
        dict_rows.insert(0, dummy_row)

    dict_rows = align(dict_rows, keylist)

    for dict_row in dict_rows:
        out = opts.print_format
        for key, value in dict_row.items():
            if "%" + key in out:
                out = out.replace("%" + key, str(value), 1)
        out = out.replace("%%", "%")
        out = out.expandtabs()
        suite = SuiteEvent(out.expandtabs() + "\n", level=0)

        if (opts.verbosity - opts.quietness) <= report.DEFAULT:
            report(suite, clip=terminal_cols)
        report(SuiteInfo(dict_row), prefix=None)
    if url is not None:
        if url.endswith("&format=json"):
            url = url.replace("&format=json", "")
        report(URLEvent(url + "\n"), prefix="")


def main():
    """Launcher for the utility functions."""
    argv = sys.argv[1:]
    if not argv:
        return sys.exit(1)
    try:
        func = globals()[argv[0]]  # Potentially bad.
    except KeyError:
        sys.exit("rosie.ws_client: %s: incorrect usage" % argv[0])
    try:
        sys.exit(func(argv[1:]))
    except KeyboardInterrupt:
        pass
    except UndefinedRosiePrefixWS as exc:
        sys.exit(str(exc))

if __name__ == "__main__":
    main()
