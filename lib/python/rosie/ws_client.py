# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
    Client  - sends requests, retrieves data from the web server

Functions:
    lookup  - run searches to retrieve suite properties
    main    - launcher for the other functions

"""


import os
import re
import requests
import simplejson
import sys
import time

import rose.config
import rose.env
from rosie.suite_id import SuiteId, SuiteIdError
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener
from rose.reporter import Reporter, Event
from rose.resource import ResourceLocator

ERR_INVALID_URL = "Invalid url: {0}"
ERR_NO_SUITES_FOUND = "{0}: no suites found."
ERR_NO_TARGET_AT_REV = "{0}: target does not exist at this revision"
ERR_SYNTAX = "Syntax error: {0}"
ERR_USAGE = "rosie: incorrect usage"

FORMAT_DEFAULT = "%local %suite %owner %project %title"
FORMAT_QUIET = "%suite"

REC_COL_IN_FORMAT = re.compile("(?:^|[^%])%([\w-]+)")
REC_ID = re.compile("\A(?:(\w+)-)?(\w+)(?:/([^\@/]+))?(?:@([^\@/]+))?\Z")

STATUS_DO = ">"
STATUS_NO = " "
STATUS_OK = "="
STATUS_MO = "M"
STATUS_SW = "S"
STATUS_UP = "<"


class QueryError(Exception):

    """Raised if no data were retrieved from the server."""

    pass


class Client(object):

    """A Client for the Rosie Web Service."""

    def __init__(self, root=None, prefix=None):
        if root is None:
            config = ResourceLocator.default().get_conf()
            node = config.get(["rosie-ws-client", "ws-root-default"])
            root = node.value
        self.root = root
        if prefix is None:
            prefix = SuiteId.get_prefix_default()
        self.prefix = prefix

    def _get(self, method, **kwargs):
        """Send a JSON object to the web server and retrieve results."""
        if method != "address":
            url = self.root + self.prefix + "/" + method
            kwargs["format"] = "json"
        else:
            url = kwargs['url']
            del kwargs['url']
        try:
            response = requests.get(url, params=kwargs)
        except requests.exceptions.ConnectionError as e:
            raise QueryError("%s: %s: %s" % (url, method, str(e)))
        except requests.exceptions.MissingSchema as e:
            raise QueryError("URL Error: %s" % (str(e)))
            
        try:
            response.raise_for_status()
        except:
            raise QueryError("%s: %s: %s" % (method, kwargs, response.status_code))
        try:
            if method in ["query", "search"]:
                return simplejson.loads(response.text), response.url
            else:
                return simplejson.loads(response.text)
        except ValueError:
            raise QueryError("%s: %s" % (method, kwargs))
    
    def get_known_keys(self):
        return self._get("get_known_keys")

    def get_optional_keys(self):
        return self._get("get_optional_keys")

    def get_prefix(self):
        return self.prefix
        
    def get_root(self):
        return self.root

    def get_query_operators(self):
        return self._get("get_query_operators")

    def get_query_prefix(self):
        return self.get_root() + self.get_prefix() + "/"

    def info(self, idx, branch, revision=None):
        if revision is None:
            return self._get("info", idx=idx, branch=branch)
        else:
            return self._get("info", idx=idx, branch=branch, revision=revision)

    def query(self, q, **kwargs):
        return self._get("query", q=q, **kwargs)

    def search(self, s, **kwargs):
        return self._get("search", s=s, **kwargs)
        
    def address_search(self, a, **kwargs):
        return self._get("address", a=a, **kwargs)    


class URLEvent(Event):
    
    def __str__(self):
        return "url: " + self.args[0]


class SuiteEvent(Event):

    def __str__(self):
        return self.args[0]


class SuiteInfo(Event):
    
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
                if key == "date":    
                    out = (out + "\t" + key + ": " + 
                           time.strftime(time_format, 
                                         time.localtime(value)) + "\n") 
                else:                                         
                    out = out + "\t" + key + ": " + str(value) + "\n"                                            
        return out


def local_suites(argv):
    """CLI command to list all the locally checked out suites"""
    opt_parser = RoseOptionParser().add_my_options("format", "prefix", 
                                                   "reverse", "sort")    
    opts, args = opt_parser.parse_args(argv)

    ws_client = Client()
    if opts.prefix is not None: 

        results = get_local_suite_details(opts.prefix)
        return _display_maps(opts, ws_client, results)
    else:
        id_list = get_local_suites()   
        if len(id_list) > 0:
            prefixes = []
            for id_ in id_list:
                prefixes.append(id_.prefix)
            for p in sorted(set(prefixes)):
                if len(prefixes) == 1:
                    suites_this_prefix = id_list
                else:
                    suites_this_prefix = []
                    for id_ in id_list:
                        if id_.prefix == p:
                            suites_this_prefix.append(id_)
            
                results = get_local_suite_details(p, id_list)
                opts.prefix = p
                _display_maps(opts, ws_client, results, 
                              local_suites=suites_this_prefix)
        return


def lookup(argv):
    """CLI command to run the various search types"""
    opt_parser = RoseOptionParser().add_my_options("format", "all_revs",
                                                   "prefix", "query", 
                                                   "reverse", "search", "sort",
                                                   "url")    
    opts, args = opt_parser.parse_args(argv)
    if not args:
        sys.exit(opt_parser.print_usage())
    if not opts.query and not opts.search and not opts.url:
        if args[0].startswith("http"):
            opts.url = True
        else:
            opts.search = True
    results = None
    if opts.url:
        ws_client = Client()
        addr = args[0]
        if not addr.endswith("&format=json"):
            addr += "&format=json"
        
        if opts.debug_mode:
            results = ws_client.address_search(None,url=addr)
            url = addr
        else:        
            try:
                results = ws_client.address_search(None,url=addr)
                url = addr
            except QueryError as e:
                sys.exit(ERR_INVALID_URL.format(args[0]))
    elif opts.query:
        q = query_split(args)
        if q is None:
            sys.exit(ERR_SYNTAX.format(" ".join(args)))
        for i, p in enumerate(q):
            q[i] = " ".join(p)
        ws_client = Client(prefix=opts.prefix)
        if opts.all_revs:
            results, url = ws_client.query(q, all_revs=True)
        else:
            results, url = ws_client.query(q)
    elif opts.search:
        ws_client = Client(prefix=opts.prefix)
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
    q = []  # Query list
    p = []  # Individual query pieces list
    level = 0  # Number of open brackets
    while args:
        arg = args.pop(0)
        arg_1 = args[0] if args else None
        if (arg in ["and", "or"] and arg_1 not in ["and", "or"]):
            if len(p) >= 4:
                q.append(p)
                p = []
        elif not args:
            p.append(arg)
            if len(p) < 4:
               return None
            q.append(p)
            p = []
        p.append(arg)
        level += len(arg) if all([c == "(" for c in arg]) else 0
        level -= len(arg) if all([c == ")" for c in arg]) else 0
    if len(p) > 1 or level != 0 or any([len(p) > 6 or len(p) < 4 for p in q]):
        return None
    return q


def get_local_suites(prefix=None):
    """Returns a dict of prefixes and id tuples for locally-present suites."""
    local_copies = []
    local_copy_root = SuiteId.get_local_copy_root()
    if not os.path.isdir(local_copy_root):
        return local_copies
    for path in os.listdir(local_copy_root):
        location = os.path.join(local_copy_root, path)
        try:
            id = SuiteId(location=location)
        except SuiteIdError as e:
            continue
        if prefix is None or id.prefix == prefix:
            local_copies.append(id)
    return local_copies


def get_local_suite_details(prefix=None, id_list=None):
    """returns details of the local suites as if they had been obtained using
       a search or query.
       """
    if prefix == None:
        return   
    
    if id_list == None:   
        id_list = get_local_suites()
    
    if not id_list:
        return []
    
    result_maps = []
    for id_ in id_list:
    
        if id_.prefix == prefix:
        
            local_copy_root = id_.get_local_copy_root()
            info_file_path = os.path.join(local_copy_root, str(id_), 
                                          rose.INFO_CONFIG_NAME)
            try:
                id_config = rose.config.load(info_file_path)
            except Exception:
                continue
            
            id_info_map = {u"idx": id_.idx, 
                           u"branch": id_.branch,
                           u"revision": int(id_.revision)}

            id_info_map[u"title"] = id_config[u"title"].value
            id_info_map[u"owner"] = id_config[u"owner"].value
            id_info_map[u"project"] = id_config[u"project"].value
            
            if id_.modified:
                id_info_map[u"local"] = STATUS_MO
            else:
                id_info_map[u"local"] = STATUS_OK
            id_info_map[u"status"] = None
            id_info_map[u"from_idx"] = None
        
            for key, node in id_config.value.items():
                if node.is_ignored():
                    continue
                id_info_map.update({key: node.value})
        
            result_maps.append(id_info_map)
    
    return result_maps


def get_local_status(suites, prefix, idx, branch, revision):
    """Return a text token denoting the local status of a suite."""
    status = STATUS_NO
    for suite_id in suites:
        if prefix is not None and suite_id.prefix != prefix:
            continue
        if suite_id.idx == idx:
            status = STATUS_SW
            if suite_id.branch == branch:
                status = STATUS_DO
                if int(suite_id.revision) < int(revision):
                    status = STATUS_UP
                if int(suite_id.revision) == int(revision):
                    status = STATUS_OK
                    if suite_id.modified:
                        status = STATUS_MO
            break
    return status


def align(res, keys):
    """Function to align results to be displayed by display map"""
    if len(res) <= 1:
        return res
    for k in keys:
        if k != "date":
            try:
                max_len = max([len(res[i].get(k,"%" + k)) 
                               for i in range(len(res))])
                for r in res:
                    r[k] = r.get(k, "%" + k) + " " * (max_len -
                                                      len(r.get(k, "%" + k)))
            except (TypeError, KeyError):
                pass
        else:
            time_format = "%Y-%m-%d %H:%M:%S %Z" #possibly put a T in
            for r in res:
                r[k] = time.strftime(time_format, time.localtime(r.get(k)))
    return res


def _display_maps(opts, ws_client, dict_rows, url=None, local_suites=None):
    """Display returned suite details."""
    report = Reporter(opts.verbosity - opts.quietness)
    popen = RosePopener(event_handler=report)
    
    try:
        terminal_cols = int(popen('stty size', shell=True)[0].split()[1])
    except:
        terminal_cols = None
    
    if terminal_cols == 0:
        terminal_cols = None

    if not opts.prefix:
        opts.prefix = ws_client.prefix

    if opts.quietness:
        opts.format = FORMAT_QUIET
    elif not opts.format:
        opts.format = FORMAT_DEFAULT

    all_keys = ws_client.get_known_keys()
    
    if local_suites == None:
        local_suites = get_local_suites(opts.prefix)

    check_local = "%local" in opts.format

    for dict_row in dict_rows:
        dict_row["suite"] = "%s-%s/%s@%s" % (
                            opts.prefix,
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
    for key in REC_COL_IN_FORMAT.findall(opts.format):
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
        if "%" + key in opts.format:
            keylist.append(key)
    
    dict_rows = align(dict_rows, keylist)
    
    for dict_row in dict_rows:
        out = opts.format
        for key, value in dict_row.items():
            if "%" + key in out:
                out = out.replace("%" + key, str(value), 1)
        out = out.replace("%%", "%")
        out = out.expandtabs()
        suite = SuiteEvent(out.expandtabs() + "\n", level=0)
        
        if (opts.verbosity - opts.quietness) <= report.DEFAULT:
           report(suite, clip=terminal_cols)
        report(SuiteInfo(dict_row), prefix="")
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
        f = globals()[argv[0]]  # Potentially bad.
    except KeyError:
        sys.exit("rosie.ws_client: %s: incorrect usage" % argv[0])
    sys.exit(f(argv[1:]))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
