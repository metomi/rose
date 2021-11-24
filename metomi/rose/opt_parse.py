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
"""Common option parser for Rose command utilities."""

from optparse import OptionParser, HelpFormatter
from textwrap import dedent, wrap

import metomi.rose.resource


class RoseHelpFormatter(HelpFormatter):

    def format_usage(self, usage):
        return "Usage: %s\n" % usage

    def format_heading(self, heading):
        return "%*s%s:\n" % (self.current_indent, "", heading.upper())

    def format_description(self, description):
        if description:
            return dedent(description).strip() + '\n'
        else:
            return ""

    def format_epilog(self, epilog):
        if epilog:
            return '\n' + dedent(epilog).strip() + '\n'
        return ''

    def format_option(self, option):
        # Acknowledgment:
        #     Slight modification of the optparse source to preserve line
        #     breaks.
        #
        # Copyright © 2001-2021 Python Software Foundation; All Rights
        # Reserved.
        result = []
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            opts = "%*s%s\n" % (self.current_indent, "", opts)
            indent_first = self.help_position
        else:                       # start help on same line as opts
            opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
            indent_first = 0
        result.append(opts)
        if option.help:
            help_text = self.expand_default(option).replace('\n', '\n\n')
            help_lines = [
                line
                # for help_line in help_text.splitlines()
                for help_line in help_text.split('\n')
                for line in wrap(
                    help_line or '\n',
                    self.help_width,
                    drop_whitespace=False,
                )
            ]
            result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
            result.extend(["%*s%s\n" % (self.help_position, "", line)
                           for line in help_lines[1:]])
        elif opts[-1] != "\n":
            result.append("\n")
        return "".join(result)


class RoseOptionParser(OptionParser):

    """Option parser base class for Rose command utilities.

    Warning: do not use a list or dict as a default.

    """

    DEFAULT_OPTS = {
        "debug_mode",
        "profile_mode",
        "quietness",
        "verbosity",
    }

    OPTIONS = {
        "address_mode": [
            ["--address-mode", "--url", "-A", "-U"],
            {
                "action": "store_const",
                "const": "address",
                "dest": "lookup_mode",
                "help": "Shorthand for --lookup-mode=address",
            },
        ],
        "all_revs": [
            ["--all-revs"],
            {
                "action": "store_true",
                "default": False,
                "help": (
                    "Specify whether to search deleted suites and superceded"
                    " suites."
                ),
            },
        ],
        "all_versions": [
            ["--all-versions", "-a"],
            {
                "action": "store_true",
                "default": False,
                "help": "Use all tagged versions.",
            },
        ],
        "app_key": [
            ["--app-key"],
            {
                "action": "store",
                "metavar": "KEY",
                "help": "Specify a named application configuration.",
            },
        ],
        "app_mode": [
            ["--app-mode"],
            {
                "action": "store",
                "metavar": "MODE",
                "help": (
                    "Run a command or builtin application identified by"
                    " `MODE`."
                    " The default `MODE` is `command`."
                )
            },
        ],
        "archive_mode": [
            ["--archive"],
            {
                "action": "store_true",
                "dest": "archive_mode",
                "help": "Switch on archive mode.",
            },
        ],
        "auto_type": [
            ["--auto-type"],
            {
                "action": "store_true",
                "default": False,
                "dest": "type",
                "help": (
                    "Add a 'best guess' for the `type` and `length` metadata."
                ),
            },
        ],
        "as_total": [
            ["--as-total"],
            {
                "action": "store",
                "dest": "duration_print_format",
                "help": "Express a duration string in the provided units.",
            },
        ],
        "calendar": [
            ["--calendar"],
            {
                "action": "store",
                "choices": ["360day", "365day", "366day", "gregorian"],
                "metavar": "MODE",
                "help": "Set the calendar mode.",
            },
        ],
        "case_mode": [
            ["--case"],
            {
                "action": "store",
                "choices": ["lower", "upper"],
                "dest": "case_mode",
                "metavar": "MODE",
                "help": (
                    "Output names in lower|upper case."
                    "\nCan be `upper`, `lower` or `unchanged` (default)."
                ),
            },
        ],
        "checkout_mode": [
            ["--no-checkout"],
            {
                "action": "store_false",
                "default": True,
                "dest": "checkout_mode",
                "help": (
                    "Do not checkout a working copy of the newly created"
                    " suite. Default is to checkout."
                ),
            },
        ],
        "choice": [
            ["--choice"],
            {
                "action": "store",
                "default": 1,
                "metavar": "N",
                "help": "Choose from any of the top N items.",
            },
        ],
        "command_key": [
            ["--command-key", "-c"],
            {
                "action": "store",
                "metavar": "KEY",
                "help": (
                    "Run the command in [command]KEY"
                    " instead of [command]default."
                ),
            },
        ],
        "conf_dir": [
            ["--config", "-C"],
            {
                "action": "store",
                "dest": "conf_dir",
                "metavar": "DIR",
                "help": (
                    "Specify the configuration directory of the application."
                    "\nIf not specified, the current directory will be used."
                ),
            },
        ],
        "cycle": [
            ["--cycle", "-t"],
            {
                "action": "store",
                "metavar": "TIME",
                "help": (
                    "Specify current cycle time."
                    "\nIf not defined, use the cycle time provided by the"
                    " suite environment. `TIME` can be in an ISO date/time"
                    " format, `CCYYMMDDhh` (deprecated) date/time format, or a"
                    " `TIME-DELTA` string described in the"
                    "`--cycle-offset=TIME-DELTA` option."
                ),
            },
        ],
        "cycle_offsets": [
            ["--cycle-offset", "-T"],
            {
                "action": "append",
                "dest": "cycle_offsets",
                "metavar": "TIME-DELTA",
                "help": (
                    "Specify one or more cycle offsets to determine what"
                    " `ROSE_DATAC????` environment variables to export."
                    "\nThe `TIME-DELTA` argument uses the syntax explained"
                    "in the `ROSE_DATAC????` environment variable."
                    "\nE.g. `--cycle-offset=PT3H --cycle-offset=PT6H` will"
                    " tell `rose task-env` to export `ROSE_DATACPT3H` and"
                    " `ROSE_DATACPT6H`."
                    "\nNOTE: The main usage of this option is to reference a"
                    " cycle time in the past, so a positive offset is used to"
                    " go backward in time, and a negative offset is used to go"
                    " forward in time."
                    "\nE.g. `--cycle-offset=-PT3H` will tell `rose task-env`"
                    " to export `ROSE_DATAC__PT3H` for `ROSE_DATAC` of 3 hours"
                    " ahead of the current cycle time."
                )
            },
        ],
        "default": [
            ["--default"],
            {
                "metavar": "VALUE",
                "help": "Specify a default value",
            },
        ],
        "debug_mode": [
            ["--debug"],
            {
                "action": "store_true",
                "dest": "debug_mode",
                "help": "Report trace back on error.",
            },
        ],
        "defines": [
            ["--define", "-D"],
            {
                "action": "append",
                "dest": "defines",
                "metavar": "[SECTION]KEY=VALUE",
                "help": (
                    "Each of these overrides the `[SECTION]KEY` setting with"
                    " a given `VALUE`."
                    "\nCan be used to disable a setting using the syntax"
                    "`--define=[SECTION]!KEY` or even `--define=[!SECTION]`."
                )
            },
        ],
        "defines_suite": [
            ["--define-suite", "-S"],
            {
                "action": "append",
                "dest": "defines_suite",
                "metavar": "KEY=VALUE",
                "help": "Set suite variable KEY to VALUE.",
            },
        ],
        "diff": [
            ["--diff"],
            {
                "action": "store",
                "dest": "diff",
                "default": None,
                "help": "Set a datetime to subtract from DATE-TIME.",
            },
        ],
        "diff_tool": [
            ["--diff-tool"],
            {
                "action": "store",
                "dest": "diff_tool",
                "default": None,
                "help": (
                    "Specify an alternate diff tool."
                    "\nE.G: diffuse, vimdiff or kompare."
                ),
            },
        ],
        "distance": [
            ["--distance", "-d"],
            {
                "action": "store",
                "dest": "distance",
                "default": None,
                "type": "int",
                "help": (
                    "The maximum distance (graph depth) for suites related"
                    " to `ID` to be plotted. For example, if the distance is"
                    " 1, only the parents and children (but not siblings) of"
                    "`ID` will be plotted.  If not given, this is unlimited."
                    "Requires `ID` to be specified."
                ),
            },
        ],
        "downgrade": [
            ["--downgrade", "-d"],
            {
                "action": "store_true",
                "dest": "downgrade",
                "help": (
                    "Downgrade the version instead of upgrade."
                ),
            },
        ],
        "env_var_process_mode": [
            ["--env-var-process", "-E"],
            {
                "action": "store_true",
                "dest": "env_var_process_mode",
                "help": (
                    "Process environment variable substitution."
                    "\nOnly works when returning a string value."
                ),
            },
        ],
        "files": [
            ["--file", "-f"],
            {
                "action": "append",
                "dest": "files",
                "metavar": "FILE",
                "help": (
                    "Specify the configuration file(s)."
                    "\nIf none specified, read from `$THIS/../etc/rose.conf`"
                    " and `$HOME/.metomi/rose.conf` (where `$THIS` is the"
                    " location of this command)."
                ),
            },
        ],
        "fix": [
            ["--fix", "-F"],
            {
                "action": "store_true",
                "default": False,
                "dest": "fix",
                "help": (
                    "Prepend all internal transformer (fixer) macros to"
                    "the argument list."
                ),
            },
        ],
        "force_mode": [
            ["--force", "-f"],
            {
                "action": "store_true",
                "dest": "force_mode",
                "help": "Switch on force mode.",
            },
        ],
        "graphical": [
            ["--graphical", "-g"],
            {
                "action": "store_true",
                "dest": "graphical_mode",
                "default": False,
                "help": "Run in graphical mode (X windows, etc.)",
            },
        ],
        "group": [
            ["--group", "-g"],
            {
                "action": "append",
                "dest": "group",
                "help": "Switch a group of tasks on.",
            },
        ],
        "host": [["--host"], {"metavar": "HOST", "help": "Specify a host"}],
        "ignore": [
            ["--ignore", "-i"],
            {
                "action": "append",
                "dest": "ignore_patterns",
                "metavar": "PATTERN",
                "help": (
                    "Ignore setting ids that contain (regex) PATTERN."
                    "\nCan be specified more than once. `PATTERN` may also be"
                    "a key used in site or user configuration which expands to"
                    "a list of patterns. See `CONFIGURATION` below."
                ),
            },
        ],
        "info_file": [
            ["--info-file"],
            {
                "metavar": "FILE",
                "help": (
                    "Specify the discovery information file."
                    "\nIf `FILE` is `-`, read from STDIN. The default"
                    " behaviour is to open an editor to add suite discovery"
                    " information."
                ),
            },
        ],
        "install_only_mode": [
            ["--install-only", "-i"],
            {
                "action": "store_true",
                "dest": "install_only_mode",
                "help": "Install files only, don't run the command.",
            },
        ],
        "keys": [
            ["--keys", "-k"],
            {
                "action": "store_true",
                "dest": "keys_mode",
                "help": (
                    "Only print the `SECTION` keys in the configuration file"
                    " or the `OPTION` keys in a `SECTION`."
                ),
            },
        ],
        "latest": [
            ["--latest"],
            {
                "action": "store_true",
                "help": "Print the latest ID in the repository.",
            },
        ],
        "load_all_apps": [
            ["--load-all-apps"],
            {
                "action": "store_true",
                "dest": "load_all_apps",
                "default": False,
                "help": "Override preview mode and load in all apps",
            },
        ],
        "load_no_apps": [
            ["--load-no-apps"],
            {
                "action": "store_true",
                "dest": "load_no_apps",
                "default": False,
                "help": "Load app configs on demand.",
            },
        ],
        "local_install_only_mode": [
            ["--local-install-only", "-l"],
            {
                "action": "store_true",
                "dest": "local_install_only_mode",
                "help": "Install locally only. Don't run.",
            },
        ],
        "local_only": [
            ["--local-only"],
            {
                "action": "store_true",
                "help": "Delete only the local copy of a suite.",
            },
        ],
        "log_archive_mode": [
            ["--no-log-archive"],
            {
                "action": "store_false",
                "default": True,
                "dest": "log_archive_mode",
                "help": "Do not archive old logs.",
            },
        ],
        "log_keep": [
            ["--log-keep"],
            {
                "action": "store",
                "dest": "log_keep",
                "metavar": "DAYS",
                "help": "Specify number of days a log directory is" + " kept.",
            },
        ],
        "log_name": [
            ["--log-name"],
            {
                "action": "store",
                "metavar": "NAME",
                "help": "Name the log directory of this run.",
            },
        ],
        "lookup_mode": [
            ["--lookup-mode", "--mode", "-m"],
            {
                "action": "store",
                "choices": ["address", "query", "search"],
                "dest": "lookup_mode",
                "metavar": "MODE",
                "help": (
                    "Specify the lookup mode."
                    "\n`MODE` can be `address`, `query` or `search`."
                ),
            },
        ],
        "lower": [
            ["--lower", "-l"],
            {
                "action": "store_const",
                "const": "lower",
                "dest": "case_mode",
                "help": "Shorthand for --case=lower.",
            },
        ],
        "mail_cc": [
            ["--mail-cc"],
            {
                "action": "append",
                "metavar": "LIST",
                "help": "Specify a comma-separated list of Cc "
                "addresses in notification emails.",
            },
        ],
        "mail": [
            ["--mail"],
            {
                "action": "store_true",
                "default": False,
                "help": "Send notification emails.",
            },
        ],
        "meta": [
            ["--meta"],
            {
                "action": "store_true",
                "default": False,
                "help": "Operate on a config file's metadata.",
            },
        ],
        "meta_key": [
            ["--meta-key"],
            {
                "metavar": "KEY",
                "help": (
                    "Prints the value of a specified metadata flag `KEY`."
                    "\nCannot be used in conjunction with `--file=FILE`."
                ),
            },
        ],
        "meta_path": [
            ["--meta-path", "-M"],
            {
                "action": "append",
                "metavar": "PATH",
                "help": (
                    "Prepend items to the metadata search path."
                    "\nThis option can be used repeatedly to load multiple"
                    " paths."
                )
            },
        ],
        "meta_suite_mode": [
            ["--meta-suite"],
            {
                "action": "store_true",
                "dest": "meta_suite_mode",
                "default": False,
                "help": (
                    "(Admin-only) Create the special suite in the repository"
                    " containing discovery metadata and known keys."
                ),
            },
        ],
        "name": [
            ["--name", "-n"],
            {
                "action": "store",
                "metavar": "NAME",
                "help": "Specify the suite name.",
            },
        ],
        "new_mode": [
            ["--new", "-N"],
            {
                "action": "store_true",
                "dest": "new_mode",
                "help": (
                    "Remove all items in `$PWD` before doing anything."
                    "\nThis option only works with the `--config=DIR` option"
                    " and if `$PWD` is not `DIR`."
                ),
            },
        ],
        "no_headers": [
            ["--no-headers", "-H"],
            {
                "action": "store_true",
                "dest": "no_headers",
                "help": "Do not print column headers.",
            },
        ],
        "next": [
            ["--next"],
            {
                "action": "store_true",
                "help": "Print the next available ID in the repository.",
            },
        ],
        "non_interactive": [
            ["--non-interactive", "--yes", "-y"],
            {
                "action": "store_true",
                "default": False,
                "help": "Switch off interactive prompting.",
            },
        ],
        "no_ignore": [
            ["--print-ignored", "-i"],
            {
                "action": "store_false",
                "dest": "no_ignore",
                "default": True,
                "help": (
                    "Print ignored settings."
                    "\nE.G. !OPTION=VALUE. These are not output by default."
                ),
            },
        ],
        "no_metadata": [
            ["--no-metadata"],
            {
                "action": "store_true",
                "dest": "no_metadata",
                "default": False,
                "help": "Start config editor without metadata "
                + "switched on.",
            },
        ],
        "no_opts": [
            ["--no-opts"],
            {
                "action": "store_true",
                "dest": "no_opts",
                "help": "Do not load optional configurations.",
            },
        ],
        "no_overwrite_mode": [
            ["--no-overwrite"],
            {
                "action": "store_true",
                "dest": "no_overwrite_mode",
                "help": "Do not overwrite existing files.",
            },
        ],
        "no_pretty_mode": [
            ["--no-pretty"],
            {
                "action": "store_true",
                "default": False,
                "dest": "no_pretty_mode",
                "help": "Switch off format-specific prettyprinting.",
            },
        ],
        "no_warn": [
            ["--no-warn"],
            {
                "action": "append",
                "metavar": "WARNING_TYPE",
                "choices": ["version"],
                "dest": "no_warn",
                "help": "Warnings to disable.",
            },
        ],
        "offsets1": [
            ["--offset1", "--offset", "-s", "-1"],
            {
                "action": "append",
                "dest": "offsets1",
                "metavar": "OFFSET",
                "help": "Specify offsets for 1st date time point.",
            },
        ],
        "offsets2": [
            ["--offset2", "-2"],
            {
                "action": "append",
                "dest": "offsets2",
                "metavar": "OFFSET",
                "help": "Specify offsets for 2nd date time point.",
            },
        ],
        "opt_conf_keys": [
            ["--opt-conf-key", "-O"],
            {
                "action": "append",
                "dest": "opt_conf_keys",
                "metavar": "KEY",
                "help": (
                    "Each of these switches on an optional configuration"
                    " identified by `KEY`."
                    "\nThe configurations are applied first-to-last."
                    "\nThe `(KEY)` syntax denotes an optional configuration"
                    " that can be missing. Otherwise, the optional "
                    " configuration must exist."
                ),
            },
        ],
        "opt_conf_keys_1": [
            ["--opt-conf-key-1"],
            {
                "action": "append",
                "dest": "opt_conf_keys_1",
                "metavar": "KEY",
                "help": (
                    "Switch on an optional configuration"
                    " file the first item in a comparison."
                ),
            },
        ],
        "opt_conf_keys_2": [
            ["--opt-conf-key-2"],
            {
                "action": "append",
                "dest": "opt_conf_keys_2",
                "metavar": "KEY",
                "help": (
                    "Switch on an optional configuration"
                    " file the first item in a comparison."
                ),
            },
        ],
        "output_dir": [
            ["--output", "-O"],
            {
                "action": "store",
                "dest": "output_dir",
                "metavar": "DIR",
                "help": "Specify the name of the output directory.",
            },
        ],
        "output_file": [
            ["--output", "-o"],
            {
                "action": "store",
                "dest": "output_file",
                "metavar": "FILE",
                "help": "Specify the name of the output file.",
            },
        ],
        "parse_format": [
            ["--parse-format", "-p"],
            {
                "metavar": "FORMAT",
                "help": "Specify the format for parsing inputs.",
            },
        ],
        "path_globs": [
            ["--path", "-P"],
            {
                "action": "append",
                "dest": "path_globs",
                "metavar": "PATTERN",
                "help": (
                    "Specify glob patterns for paths to prepend to an"
                    " environment variable called `NAME`"
                    " (or `PATH` if `NAME` is not specified)."
                    "\nCan be used multiple times."
                    "\nIf a relative path is given, it is relative to"
                    " `$ROSE_SUITE_DIR`. An empty value resets the default"
                    " and any previous `--path=PATTERN` settings."
                    '\n(Default for `PATH` is `"share/fcm[_-]make*/*/bin"` and'
                    ' `"work/fcm[_-]make*/*/bin"`)'
                )
            },
        ],
        "match_mode": [
            ["--match-mode", "-m"],
            {
                "metavar": "MODE",
                "choices": ["brace", "default"],
                "help": (
                    "Specify the match mode."
                    "\ncan be `brace` or `default`."
                ),
            },
        ],
        "only_items": [
            ["--only"],
            {
                "action": "append",
                "dest": "only_items",
                "metavar": "ITEM",
                "help": "Only operate on the specified items.",
            },
        ],
        "prefix": [
            ["--prefix"],
            {
                "metavar": "PREFIX",
                "help": "Specify the name of the suite repository.",
            },
        ],
        "prefixes": [
            ["--prefix"],
            {
                "action": "append",
                "dest": "prefixes",
                "metavar": "PREFIX",
                "help": "Specify the Rosie web service names.",
            },
        ],
        "prefix_delim": [
            ["--prefix-delim"],
            {
                "metavar": "DELIMITER",
                "help": (
                    "Specify the delimiter used to determine the task"
                    " name prefix. Default=`_`"
                ),
            },
        ],
        "print_conf_mode": [
            ["--print-conf"],
            {
                "action": "store_true",
                "dest": "print_conf_mode",
                "help": (
                    "Prints the result as a Rose configuration file snippet."
                    "\nThis allows the output to be concatenated into another"
                    " Rose configuration file."
                ),
            },
        ],
        "print_format": [
            ["--print-format", "--format", "-f"],
            {
                "metavar": "FORMAT",
                "help": (
                    "Specify the format for printing results."
                    "\nControl the output format of the results using a string"
                    " containing column names or properties preceded by `%`."
                    '\nFor example: `rosie ls --format="%idx from %owner"`'
                    " might give: `abc01 from daisy`"
                ),
            },
        ],
        "profile_mode": [
            ["--profile"],
            {
                "action": "store_true",
                "default": False,
                "dest": "profile_mode",
                "help": "Switch on profiling.",
            },
        ],
        "project": [
            ["--project"],
            {
                "metavar": "PROJECT",
                "help": (
                    "Create using project metadata."
                    "\nSpecify a project to check/query any available"
                    " metadata. The default behaviour is to use no"
                    "project and metadata."
                ),
            },
        ],
        "property": [
            ["--property", "-p"],
            {
                "action": "append",
                "metavar": "PROPERTY",
                "help": "Specify a property.",
            },
        ],
        "properties": [
            ["--properties", "-p"],
            {
                "action": "store",
                "metavar": "PROPERTIES",
                "help": (
                    "Filter metadata properties."
                    "\nThis should be a comma separated list of metadata"
                    " options, such as title,description,help."
                ),
            },
        ],
        "prune_remote_mode": [
            ["--prune-remote", "--tidy-remote"],
            {
                "action": "store_true",
                "dest": "prune_remote_mode",
                "help": "Remove remote job logs after retrieval.",
            },
        ],
        "query_mode": [
            ["--query", "-Q"],
            {
                "action": "store_const",
                "const": "query",
                "dest": "lookup_mode",
                "help": "Shorthand for --lookup-mode=query.",
            },
        ],
        "quietness": [
            ["--quiet", "-q"],
            {
                "action": "count",
                "default": 0,
                "dest": "quietness",
                "help": "Decrement verbosity.",
            },
        ],
        "rank_method": [
            ["--rank-method"],
            {
                "action": "store",
                "metavar": "METHOD",
                "help": (
                    "Specify the method for ranking hosts."
                    "\nCan be load, fs, mem or random."
                )
            },
        ],
        "reload_mode": [
            ["--reload"],
            {
                "action": "store_const",
                "const": "reload",
                "dest": "run_mode",
                "help": "Shorthand for --run=reload.",
            },
        ],
        "remote": [
            ["--remote"],
            {
                "action": "store",
                "metavar": "KEY=VALUE",
                "help": "(Internal option, do not use.)",
            },
        ],
        "restart_mode": [
            ["--restart"],
            {
                "action": "store_const",
                "const": "restart",
                "dest": "run_mode",
                "help": "Shorthand for --run=restart.",
            },
        ],
        "retrieve_job_logs": [
            ["--retrieve-job-logs"],
            {
                "action": "store_true",
                "default": False,
                "help": "Retrieve remote task job logs.",
            },
        ],
        "run_mode": [
            ["--run"],
            {
                "action": "store",
                "choices": ["reload", "restart", "run"],
                "default": "run",
                "dest": "run_mode",
                "metavar": "MODE",
                "help": "Specify run|restart|reload.",
            },
        ],
        "reverse": [
            ["--reverse", "-r"],
            {
                "action": "store_true",
                "default": False,
                "help": "Reverse sort order",
            },
        ],
        "search_mode": [
            ["--search", "-S"],
            {
                "action": "store_const",
                "const": "search",
                "dest": "lookup_mode",
                "help": "Shorthand for --lookup-mode=search.",
            },
        ],
        "service_root_mode": [
            ["--service-root", "-R"],
            {
                "action": "store_true",
                "default": False,
                "dest": "service_root_mode",
                "help": (
                    "Include web service name under root of URL"
                    " (for start only)."
                ),
            },
        ],
        "shutdown": [
            ["--shutdown"],
            {
                "action": "store_true",
                "default": False,
                "help": "Trigger a suite shutdown.",
            },
        ],
        "sort": [
            ["--sort", "-s"],
            {
                "metavar": "FIELD",
                "help": (
                    "Sort results by the field `FIELD` instead of revision."
                ),
            },
        ],
        "source": [
            ["--source", "-s"],
            {
                "action": "append",
                "dest": "source",
                "help": "Add a source tree.",
            },
        ],
        "strict_mode": [
            ["--no-strict"],
            {
                "action": "store_false",
                "dest": "strict_mode",
                "default": True,
                "help": "Do not validate in strict mode.",
            },
        ],
        "suffix_delim": [
            ["--suffix-delim"],
            {
                "metavar": "DELIMITER",
                "help": (
                    "Specify the delimiter used to determine the task"
                    " name suffix. (Default=`_`."
                )
            },
        ],
        "suite_only": [
            ["--suite-only"],
            {
                "action": "store_true",
                "dest": "suite_only",
                "default": False,
                "help": "Run only for suite level macros.",
            },
        ],
        "task": [
            ["--task", "-t"],
            {
                "action": "append",
                "dest": "group",
                "help": "Switch a group of tasks on.",
            },
        ],
        "task_cycle_time_mode": [
            ["--use-task-cycle-time", "-c"],
            {
                "action": "store_true",
                "dest": "task_cycle_time_mode",
                "help": "Use ROSE_TASK_CYCLE_TIME.",
            },
        ],
        "text": [
            ["--text"],
            {
                "action": "store_true",
                "dest": "text",
                "help": (
                    "Print graph in text format"
                    "\nPrints parent and child suites of a suite `ID`."
                    '\nFor example, for a suite "bar" you may get results'
                    "like:"
                    "\n* `[parent] foo`"
                    "\n* `[child1] baz`"
                    "\n* `[child1] qux`"
                    "\n* `[child2] quux`"
                    "\n* `[child3] corge`"
                    '\nwhere "foo" is the parent of "bar", "baz" and "qux"'
                    ' its first generation children, "quux" its second'
                    ' generation child and "corge" its third generation child.'
                    '\nAlso supports use of the `--property` option for'
                    ' producing output. Requires `ID` to be specified.'
                ),
            },
        ],
        "thresholds": [
            ["--threshold"],
            {
                "action": "append",
                "dest": "thresholds",
                "metavar": "METHOD:METHOD-ARG:NUMBER",
                "help": (
                    "Specify a threshold for excluding hosts."
                    "\nEach of these option specifies a numeric value of a"
                    " threshold of which the hosts must either not exceed or"
                    " must be greater than depending on the specified method."
                    "\nAccepts the same `METHOD` and `METHOD-ARG`"
                    " (and the same defaults) as the"
                    " `--rank-method=METHOD[:METHOD-ARG]` option. (Obviously,"
                    " the `random` method does not make sense in this case.)"
                    " `load` and `fs` must not exceed threshold while `mem`"
                    " must be greater than threshold. A host not meeting a"
                    " threshold condition will be excluded from the ranking"
                    " list."
                ),
            },
        ],
        "timeout": [
            ["--timeout"],
            {
                "metavar": "FLOAT",
                "help": "Set a timeout in seconds.",
            },
        ],
        "to_local_copy": [
            ["--to-local-copy"],
            {
                "action": "store_true",
                "help": "Convert ID to to the local copy path",
            },
        ],
        "to_origin": [
            ["--to-origin"],
            {
                "action": "store_true",
                "help": "Convert ID to the origin URL",
            },
        ],
        "to_web": [
            ["--to-web"],
            {
                "action": "store_true",
                "help": "Convert ID to the web source URL",
            },
        ],
        "transform_all": [
            ["-T", "--transform"],
            {
                "action": "store_true",
                "dest": "transform_all",
                "default": False,
                "help": "Prepend all transformer macros to the argument list.",
            },
        ],
        "unbound": [
            ["--unbound", "--undef"],
            {
                "metavar": "STRING",
                "help": (
                    "Substitute unbound variables with the provided STRING."
                    "\nThe command will normally fail on unbound"
                    " (or undefined) variables."
                    "\nIf this option is specified, the command will"
                    " substitute an unbound variable with the value of"
                    " `STRING`, (which can be an empty string), instead"
                    " of failing."
                )
            },
        ],
        "update_mode": [
            ["--update", "-U"],
            {
                "action": "store_true",
                "dest": "update_mode",
                "default": False,
                "help": "Switch on update mode.",
            },
        ],
        "upper": [
            ["--upper", "-u"],
            {
                "action": "store_const",
                "const": "upper",
                "dest": "case_mode",
                "help": "Shorthand for --case=upper.",
            },
        ],
        "user": [
            ["--user", "-u"],
            {
                "action": "store",
                "default": None,
                "dest": "user",
                "help": (
                    "Specify another user whose roses directory you want to"
                    " list e.g. `--user=~bob`"
                ),
            },
        ],
        "utc_mode": [
            ["--utc", "-u"],
            {
                "action": "store_true",
                "default": False,
                "dest": "utc_mode",
                "help": "Switch on UTC mode.",
            },
        ],
        "validate_all": [
            ["--validate", "-V"],
            {
                "action": "store_true",
                "dest": "validate_all",
                "default": False,
                "help": "Prepend all validator macros to the argument list.",
            },
        ],
        "validate_suite_only": [
            ["--validate-suite-only"],
            {
                "action": "store_true",
                "dest": "validate_suite_only_mode",
                "default": False,
                "help": "Validate only. Don't install or run.",
            },
        ],
        "verbosity": [
            ["--verbose", "-v"],
            {
                "action": "count",
                "default": 1,
                "dest": "verbosity",
                "help": "Increment verbosity.",
            },
        ],
        "view_mode": [
            ["--view"],
            {
                "action": "store_true",
                "dest": "view_mode",
                "default": False,
                "help": "View with web browser.",
            },
        ],
    }

    def __init__(self, *args, **kwargs):
        if hasattr(kwargs, "prog"):
            namespace, util = kwargs["prog"].split(None, 1)
            resource_loc = metomi.rose.resource.ResourceLocator(
                namespace=namespace, util=util
            )
        else:
            resource_loc = metomi.rose.resource.ResourceLocator.default()
        kwargs["prog"] = resource_loc.get_util_name()
        if "usage" not in kwargs:
            kwargs["usage"] = resource_loc.get_synopsis()
        kwargs['formatter'] = RoseHelpFormatter(2, 24, None, 1)
        OptionParser.__init__(self, *args, **kwargs)
        self.add_my_options(*self.DEFAULT_OPTS)

    def add_my_options(self, *args):
        """Add named options to this parser. Each element in args must be a key
        in RoseOptionParser.OPTIONS. Return self.
        """
        for arg in args:
            o_args, o_kwargs = self.OPTIONS[arg]
            self.add_option(*o_args, **o_kwargs)
        return self

    def modify_option(self, dest, **kwargs):
        """Override option attributes.

        Use to handle non-standard option variants.
        E.G. To provide more specific help messages.

        Args:
            dest:
                The "dest" attribute of the option to modify.
            kwargs:
                Key:value pairs of attributes to override.

        """
        for option in self.option_list:
            if option.dest == dest:
                for key, value in kwargs.items():
                    setattr(option, key, value)
                break
        else:
            raise ValueError(f'No such option {dest}')

    def format_option_help(self, formatter=None):
        # put the default options at the end of the list
        self.option_list.sort(key=self.option_sort_key)
        return super().format_option_help(formatter=formatter)

    @classmethod
    def option_sort_key(cls, option):
        return (
            # put the default options at the end of the list
            option.dest in cls.DEFAULT_OPTS,
            # sort the options alphabetically
            option.get_opt_string()
        )
