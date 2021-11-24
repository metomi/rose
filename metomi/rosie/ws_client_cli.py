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
"""The CLI of the web service client."""


import re
import sys
import time
import traceback

from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopenError
from metomi.rose.reporter import Event, Reporter
from metomi.rosie.suite_id import SuiteId
from metomi.rosie.ws_client import (
    RosieWSClient,
    RosieWSClientConfError,
    RosieWSClientError,
)
from metomi.rosie.ws_client_auth import UndefinedRosiePrefixWS

ERR_PREFIX_UNREACHABLE = "Cannot connect to prefix(es) {0}"
ERR_SYNTAX = "Syntax error: {0}"

PRINT_FORMAT_DEFAULT = "%local %suite %owner %project %title"
PRINT_FORMAT_QUIET = "%suite"

REC_COL_IN_FORMAT = re.compile(r"(?:^|[^%])%([\w-]+)")
DATE_TIME_FORMAT = r"%FT%H:%M:%SZ"


def cli(fcn):
    """Launcher for the utility functions."""

    def _inner():
        nonlocal fcn
        try:
            sys.exit(fcn())
        except KeyboardInterrupt:
            pass
        except (
            RosieWSClientError,
            RosieWSClientConfError,
            UndefinedRosiePrefixWS,
        ) as exc:
            sys.exit(str(exc))

    return _inner


class URLEvent(Event):

    """Print query URL."""

    def __str__(self):
        return "url: " + self.args[0]


class SuiteEvent(Event):

    """Notify a suite is found."""

    LEVEL = 0

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

        dict_row = dict(self.args[0].items())
        out = ""
        out = out + "id: %s\n" % dict_row["idx"]
        for key in sorted(dict_row.keys()):
            value = dict_row[key]
            if key != "idx":
                if value and isinstance(value, list):
                    value = " ".join(value)
                if key == "date" and isinstance(value, int):
                    out = (
                        out
                        + "\t"
                        + key
                        + ": "
                        + time.strftime(DATE_TIME_FORMAT, time.gmtime(value))
                        + "\n"
                    )
                else:
                    out = out + "\t" + key + ": " + str(value) + "\n"
        return out


@cli
def hello():
    """Set up connection to a Rosie web service."""
    opt_parser = RoseOptionParser(
        description=(
            'Set up connection to one or more Rosie web service servers.'
        ),
    ).add_my_options("prefixes")
    opts = opt_parser.parse_args()[0]
    report = Reporter(opts.verbosity - opts.quietness)
    ws_client = RosieWSClient(prefixes=opts.prefixes, event_handler=report)
    for response_data, response_url in ws_client.hello():
        report("%s: %s" % (response_url, response_data), level=0)


@cli
def list_local_suites():
    """CLI command to list all the locally checked out suites"""
    opt_parser = RoseOptionParser(
        description='''
List the local suites.

Search for locally checked out suites and print their details.

The default format includes a local working copy status field (`%local`)
in the first column.
A blank field means there is no related suite checked out.

* `=` means that the suite is checked out at this branch and revision.
* `<` means that the suite is checked out but at an older revision.
* `>` means that the suite is checked out but at a newer revision.
* `S` means that the suite is checked out but on a different branch.
* `M` means that the suite is checked out and modified.
* `X` means that the suite is checked out but is corrupted.
        ''',
    ).add_my_options(
        "no_headers", "prefixes", "print_format", "reverse", "sort", "user"
    )
    opt_parser.modify_option(
        'verbosity',
        help=(
            'Display full info for each returned suite.'
        ),
    )
    opts = opt_parser.parse_args()[0]
    report = Reporter(opts.verbosity - opts.quietness)

    if opts.user:
        alternative_roses_dir = SuiteId.get_local_copy_root(opts.user)
        report(UserSpecificRoses(alternative_roses_dir), prefix=None)

    ws_client = RosieWSClient(prefixes=opts.prefixes, event_handler=report)
    if ws_client.unreachable_prefixes:
        bad_prefix_string = " ".join(ws_client.unreachable_prefixes)
        report(
            RosieWSClientError(
                ERR_PREFIX_UNREACHABLE.format(bad_prefix_string)
            )
        )
    _display_maps(opts, ws_client, ws_client.query_local_copies(opts.user))


@cli
def lookup():
    """CLI command to run the various search types"""
    opt_parser = RoseOptionParser(
        usage='rosie lookup [OPTIONS] LOOKUP-TEXT ...',
        description='''
Find suites in the suite discovery database.

Search for suites using an address, a query or search words and display
the information of the matching suites.

Unless an option is used to specify the initial search type the argument
is interpreted as follows:

* A string beginning with "http": an address
* A string not beginning with "http": search words

An address URL may contain shell meta characters, so remember to put it
in quotes.

The default output format includes a local working copy status field
(`%local`) in the first column.

* A blank field means there is no related suite checked out.
* `=` means that the suite is checked out at this branch and revision.
* `<` means that the suite is checked out but at an older revision.
* `>` means that the suite is checked out but at a newer revision.
* `S` means that the suite is checked out but on a different branch.
* `M` means that the suite is checked out and modified.
* `X` means that the suite is checked out but is corrupted.

Search strings may contain SQL wildcard characters. E.g:

* `%` (percent) is a substitute for zero or more characters.
* `_` (underscore) is a substitute for a single character.
        ''',
    ).add_my_options(
        "address_mode",
        "all_revs",
        "lookup_mode",
        "no_headers",
        "prefixes",
        "print_format",
        "query_mode",
        "reverse",
        "search_mode",
        "sort",
    )
    opts, args = opt_parser.parse_args()
    if not args:
        sys.exit(opt_parser.print_usage())
    if not opts.lookup_mode:
        if args[0].startswith("http"):
            opts.lookup_mode = "address"
        else:
            opts.lookup_mode = "search"
    ws_client = RosieWSClient(
        prefixes=opts.prefixes,
        event_handler=Reporter(opts.verbosity - opts.quietness),
    )
    try:
        if opts.lookup_mode == "address":
            data_and_url_list = ws_client.address_lookup(url=args[0])
        elif opts.lookup_mode == "query":
            q_items = ws_client.query_split(args)
            for i, q_item in enumerate(q_items):
                q_items[i] = " ".join(q_item)
            data_and_url_list = ws_client.query(
                q_items, all_revs=int(opts.all_revs)
            )
        else:  # if opts.lookup_mode == "search":
            data_and_url_list = ws_client.search(
                args, all_revs=int(opts.all_revs)
            )
    except RosieWSClientError as exc:
        if opts.debug_mode:
            traceback.print_exc()
        sys.exit(str(exc))
    for data, url in data_and_url_list:
        _display_maps(opts, ws_client, data, url)


def _align(rows, keys):
    """Function to align results to be displayed by display map"""
    if len(rows) <= 1:
        return rows
    for key in keys:
        if key == "date":
            for row in rows:
                try:
                    row[key] = time.strftime(
                        DATE_TIME_FORMAT, time.gmtime(row.get(key))
                    )
                except (TypeError):
                    pass
        else:
            try:
                max_len = max(
                    [
                        len(rows[i].get(key, "%" + key))
                        for i in range(len(rows))
                    ]
                )
                for row in rows:
                    row[key] = row.get(key, "%" + key) + " " * (
                        max_len - len(row.get(key, "%" + key))
                    )
            except (TypeError, KeyError):
                pass
    return rows


def _display_maps(opts, ws_client, dict_rows, url=None):
    """Display returned suite details."""
    report = ws_client.event_handler

    try:
        terminal_cols = int(ws_client.popen("stty", "size")[0].split()[1])
    except (IndexError, RosePopenError, ValueError):
        terminal_cols = None

    if terminal_cols == 0:
        terminal_cols = None

    if opts.quietness and not opts.print_format:
        opts.print_format = PRINT_FORMAT_QUIET
    elif not opts.print_format:
        opts.print_format = PRINT_FORMAT_DEFAULT

    all_keys = ws_client.get_known_keys()

    for dict_row in dict_rows:
        suite_id = SuiteId.from_idx_branch_revision(
            dict_row["idx"], dict_row["branch"], dict_row["revision"]
        )
        dict_row["suite"] = suite_id.to_string_with_version()
        if "%local" in opts.print_format:
            dict_row["local"] = suite_id.get_status(
                getattr(opts, "user", None)
            )
    all_keys += ["suite"]
    if "%local" in opts.print_format:
        all_keys += ["local"]

    more_keys = []
    for key in REC_COL_IN_FORMAT.findall(opts.print_format):
        if key not in all_keys:
            more_keys.append(key)
    all_keys += more_keys

    if opts.sort is None or opts.sort not in all_keys:
        opts.sort = "revision"
    dict_rows.sort(key=lambda x: x[opts.sort])
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

    dict_rows = _align(dict_rows, keylist)

    for dict_row in dict_rows:
        out = opts.print_format
        for key, value in dict_row.items():
            if "%" + key in out:
                out = str(out).replace("%" + str(key), str(value), 1)
        out = str(out.replace("%%", "%").expandtabs().rstrip())

        report(
            SuiteEvent(out.expandtabs() + "\n"), prefix="", clip=terminal_cols
        )
        report(SuiteInfo(dict_row), prefix="")
    if url is not None:
        report(URLEvent(url + "\n"), prefix="")
