# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
"""Common option parser for Rose command utilities."""

from optparse import OptionParser
from metomi.rose.resource import ResourceLocator


class RoseOptionParser(OptionParser):

    """Option parser base class for Rose command utilities.

    Warning: do not use a list or dict as a default.

    """

    OPTIONS = {
        "address_mode": [
            ["--address-mode", "--url", "-A", "-U"],
            {"action": "store_const",
             "const": "address",
             "dest": "lookup_mode",
             "help": "Shorthand for --lookup-mode=url"}],
        "all_revs": [
            ["--all-revs"],
            {"action": "store_true",
             "default": False,
             "help": "Return all revisions of matched items."}],
        "all_versions": [
            ["--all-versions", "-a"],
            {"action": "store_true",
             "default": False,
             "help": "Use all tagged versions."}],
        "app_key": [
            ["--app-key"],
            {"action": "store",
             "metavar": "KEY",
             "help": "Specify a named application configuration."}],
        "app_mode": [
            ["--app-mode"],
            {"action": "store",
             "metavar": "MODE",
             "help": "Run a command or a builtin application."}],
        "archive_mode": [
            ["--archive"],
            {"action": "store_true",
             "dest": "archive_mode",
             "help": "Switch on archive mode."}],
        "auto_type": [
            ["--auto-type"],
            {"action": "store_true",
             "default": False,
             "dest": "type",
             "help": "Automatically guess types of settings."}],
        "as_total": [
            ["--as-total"],
            {"action": "store",
             "dest": "duration_print_format",
             "help": "Express a duration string in the provided units."}],
        "calendar": [
            ["--calendar"],
            {"action": "store",
             "choices": ["360day", "365day", "366day", "gregorian"],
             "metavar": "MODE",
             "help": "Set the calendar mode."}],
        "case_mode": [
            ["--case"],
            {"action": "store",
             "choices": ["lower", "upper"],
             "dest": "case_mode",
             "metavar": "MODE",
             "help": "Output names in lower|upper case."}],
        "checkout_mode": [
            ["--no-checkout"],
            {"action": "store_false",
             "default": True,
             "dest": "checkout_mode",
             "help": "Do not checkout after creating the suite."}],
        "choice": [
            ["--choice"],
            {"action": "store",
             "default": 1,
             "metavar": "N",
             "help": "Choose from any of the top N items."}],
        "command_key": [
            ["--command-key", "-c"],
            {"action": "store",
             "metavar": "KEY",
             "help": ("Run the command in [command]KEY " +
                      "instead of [command]default.")}],
        "conf_dir": [
            ["--config", "-C"],
            {"action": "store",
             "dest": "conf_dir",
             "metavar": "DIR",
             "help": "Use configuration in DIR instead of $PWD."}],
        "cycle": [
            ["--cycle", "-t"],
            {"action": "store",
             "metavar": "TIME",
             "help": "Specify current cycle time."}],
        "cycle_offsets": [
            ["--cycle-offset", "-T"],
            {"action": "append",
             "dest": "cycle_offsets",
             "metavar": "TIME-DELTA",
             "help": "Specify cycle offsets."}],
        "default": [
            ["--default"],
            {"metavar": "VALUE",
             "help": "Specify a default value"}],
        "debug_mode": [
            ["--debug"],
            {"action": "store_true",
             "dest": "debug_mode",
             "help": "Report trace back."}],
        "defines": [
            ["--define", "-D"],
            {"action": "append",
             "dest": "defines",
             "metavar": "[SECTION]KEY=VALUE",
             "help": "Set [SECTION]KEY to VALUE."}],
        "defines_suite": [
            ["--define-suite", "-S"],
            {"action": "append",
             "dest": "defines_suite",
             "metavar": "KEY=VALUE",
             "help": "Set suite variable KEY to VALUE."}],
        "diff": [
            ["--diff"],
            {"action": "store",
             "dest": "diff",
             "default": None,
             "help": "Set a datetime to subtract from DATE-TIME."}],
        "diff_tool": [
            ["--diff-tool"],
            {"action": "store",
             "dest": "diff_tool",
             "default": None,
             "help": "Specify an alternate diff tool like diffuse."}],
        "distance": [
            ["--distance", "-d"],
            {"action": "store",
             "dest": "distance",
             "default": None,
             "type": "int",
             "help": "Specify a maximum distance."}],
        "downgrade": [
            ["--downgrade", "-d"],
            {"action": "store_true",
             "dest": "downgrade",
             "help": "Downgrade instead of upgrade."}],
        "env_var_process_mode": [
            ["--env-var-process", "-E"],
            {"action": "store_true",
             "dest": "env_var_process_mode",
             "help": "Process environment variable syntax."}],
        "files": [
            ["--file", "-f"],
            {"action": "append",
             "dest": "files",
             "metavar": "FILE",
             "help": "Specify the configuration file(s)."}],
        "fix": [
            ["--fix", "-F"],
            {"action": "store_true",
             "default": False,
             "dest": "fix",
             "help": ("Prepend all internal transformer (fixer) macros to"
                      "the argument list.")}],
        "force_mode": [
            ["--force", "-f"],
            {"action": "store_true",
             "dest": "force_mode",
             "help": "Switch on force mode."}],
        "graphical": [
            ["--graphical", "-g"],
            {"action": "store_true",
             "dest": "graphical_mode",
             "default": False,
             "help": "Run in graphical mode (X windows, etc.)"}],
        "group": [
            ["--group", "-g"],
            {"action": "append",
             "dest": "group",
             "help": "Switch a group of tasks on."}],
        "host": [
            ["--host"],
            {"metavar": "HOST",
             "help": "Specify a host"}],
        "ignore": [
            ["--ignore", "-i"],
            {"action": "append",
             "dest": "ignore_patterns",
             "metavar": "PATTERN",
             "help": "Ignore setting ids that contain (regex) PATTERN."}],
        "info_file": [
            ["--info-file"],
            {"metavar": "FILE",
             "help": "Specify the discovery information file."}],
        "install_only_mode": [
            ["--install-only", "-i"],
            {"action": "store_true",
             "dest": "install_only_mode",
             "help": "Install only. Don't run."}],
        "keys": [
            ["--keys", "-k"],
            {"action": "store_true",
             "dest": "keys_mode",
             "help": "Print SECTION/OPTION keys only."}],
        "latest": [
            ["--latest"],
            {"action": "store_true",
             "help": "Print the latest ID in the repository."}],
        "load_all_apps": [
            ["--load-all-apps"],
            {"action": "store_true",
             "dest": "load_all_apps",
             "default": False,
             "help": "Override preview mode and load in all apps"}],
        "load_no_apps": [
            ["--load-no-apps"],
            {"action": "store_true",
             "dest": "load_no_apps",
             "default": False,
             "help": "Load app configs on demand."}],
        "local_install_only_mode": [
            ["--local-install-only", "-l"],
            {"action": "store_true",
             "dest": "local_install_only_mode",
             "help": "Install locally only. Don't run."}],
        "local_only": [
            ["--local-only"],
            {"action": "store_true",
             "help": "Delete only the local copy of a suite."}],
        "log_archive_mode": [
            ["--no-log-archive"],
            {"action": "store_false",
             "default": True,
             "dest": "log_archive_mode",
             "help": "Do not archive old logs."}],
        "log_keep": [
            ["--log-keep"],
            {"action": "store",
             "dest": "log_keep",
             "metavar": "DAYS",
             "help": "Specify number of days a log directory is" +
                     " kept."}],
        "log_name": [
            ["--log-name"],
            {"action": "store",
             "metavar": "NAME",
             "help": "Name the log directory of this run."}],
        "lookup_mode": [
            ["--lookup-mode", "--mode", "-m"],
            {"action": "store",
             "choices": ["address", "query", "search"],
             "dest": "lookup_mode",
             "metavar": "MODE",
             "help": "Specify the lookup mode."}],
        "lower": [
            ["--lower", "-l"],
            {"action": "store_const",
             "const": "lower",
             "dest": "case_mode",
             "help": "Shorthand for --case=lower."}],
        "mail_cc": [
            ["--mail-cc"],
            {"action": "append",
             "metavar": "LIST",
             "help": "Specify a comma-separated list of Cc "
                     "addresses in notification emails."}],
        "mail": [
            ["--mail"],
            {"action": "store_true",
             "default": False,
             "help": "Send notification emails."}],
        "meta": [
            ["--meta"],
            {"action": "store_true",
             "default": False,
             "help": "Operate on a config file's metadata."}],
        "meta_key": [
            ["--meta-key"],
            {"metavar": "KEY",
             "help": "Specify a meta-key to search for."}],
        "meta_path": [
            ["--meta-path", "-M"],
            {"action": "append",
             "metavar": "PATH",
             "help": "Prepend items to the metadata search path."}],
        "meta_suite_mode": [
            ["--meta-suite"],
            {"action": "store_true",
             "dest": "meta_suite_mode",
             "default": False,
             "help": "ADMIN-ONLY: Create the metadata suite."}],
        "name": [
            ["--name", "-n"],
            {"action": "store",
             "metavar": "NAME",
             "help": "Specify the suite name."}],
        "new_mode": [
            ["--new", "-N"],
            {"action": "store_true",
             "dest": "new_mode",
             "help": "Fresh start."}],
        "no_headers": [
            ["--no-headers", "-H"],
            {"action": "store_true",
             "dest": "no_headers",
             "help": "Suppress headers."}],
        "next": [
            ["--next"],
            {"action": "store_true",
             "help": "Print the next available ID in the " +
                     "repository."}],
        "non_interactive": [
            ["--non-interactive", "--yes", "-y"],
            {"action": "store_true",
             "default": False,
             "help": "Switch off interactive prompting."}],
        "no_ignore": [
            ["--print-ignored", "-i"],
            {"action": "store_false",
             "dest": "no_ignore",
             "default": True,
             "help": "Print ignored settings where relevant."}],
        "no_metadata": [
            ["--no-metadata"],
            {"action": "store_true",
             "dest": "no_metadata",
             "default": False,
             "help": "Start config editor without metadata " +
                     "switched on."}],
        "no_opts": [
            ["--no-opts"],
            {"action": "store_true",
             "dest": "no_opts",
             "help": "Do not load optional configurations."}],
        "no_overwrite_mode": [
            ["--no-overwrite"],
            {"action": "store_true",
             "dest": "no_overwrite_mode",
             "help": "Do not overwrite existing files."}],
        "no_pretty_mode": [
            ["--no-pretty"],
            {"action": "store_true",
             "default": False,
             "dest": "no_pretty_mode",
             "help": "Switch off format-specific prettyprinting."}],
        "no_warn": [
            ["--no-warn"],
            {"action": "append",
             "metavar": "WARNING_TYPE",
             "choices": ["version"],
             "dest": "no_warn",
             "help": "Warnings to disable."}],
        "offsets1": [
            ["--offset1", "--offset", "-s", "-1"],
            {"action": "append",
             "dest": "offsets1",
             "metavar": "OFFSET",
             "help": "Specify offsets for 1st date time point."}],
        "offsets2": [
            ["--offset2", "-2"],
            {"action": "append",
             "dest": "offsets2",
             "metavar": "OFFSET",
             "help": "Specify offsets for 2nd date time point."}],
        "opt_conf_keys": [
            ["--opt-conf-key", "-O"],
            {"action": "append",
             "dest": "opt_conf_keys",
             "metavar": "KEY",
             "help": ("Switch on an optional configuration " +
                      "file identified by KEY.")}],
        "opt_conf_keys_1": [
            ["--opt-conf-key-1"],
            {"action": "append",
             "dest": "opt_conf_keys_1",
             "metavar": "KEY",
             "help": ("Switch on an optional configuration " +
                      "file identified by KEY for the first item " +
                      "in a comparison.")}],
        "opt_conf_keys_2": [
            ["--opt-conf-key-2"],
            {"action": "append",
             "dest": "opt_conf_keys_2",
             "metavar": "KEY",
             "help": ("Switch on an optional configuration " +
                      "file identified by KEY for the second item " +
                      "in a comparison.")}],
        "output_dir": [
            ["--output", "-O"],
            {"action": "store",
             "dest": "output_dir",
             "metavar": "DIR",
             "help": "Specify the name of the output directory."}],
        "output_file": [
            ["--output", "-o"],
            {"action": "store",
             "dest": "output_file",
             "metavar": "FILE",
             "help": "Specify the name of the output file."}],
        "parse_format": [
            ["--parse-format", "-p"],
            {"metavar": "FORMAT",
             "help": "Specify the format for parsing inputs."}],
        "path_globs": [
            ["--path", "-P"],
            {"action": "append",
             "dest": "path_globs",
             "metavar": "PATTERN",
             "help": "Paths to prepend to PATH."}],
        "match_mode": [
            ["--match-mode", "-m"],
            {"metavar": "MODE",
             "choices": ["brace", "default"],
             "help": "Specify an alternate match mode."}],
        "only_items": [
            ["--only"],
            {"action": "append",
             "dest": "only_items",
             "metavar": "ITEM",
             "help": "Only operate on the specified items."}],
        "prefix": [
            ["--prefix"],
            {"metavar": "PREFIX",
             "help": "Specify the name of the suite repository."}],
        "prefixes": [
            ["--prefix"],
            {"action": "append",
             "dest": "prefixes",
             "metavar": "PREFIX",
             "help": "Specify the Rosie web service names."}],
        "prefix_delim": [
            ["--prefix-delim"],
            {"metavar": "DELIMITER",
             "help": "Specify the prefix delimiter."}],
        "print_conf_mode": [
            ["--print-conf"],
            {"action": "store_true",
             "dest": "print_conf_mode",
             "help": "Print result in Rose configuration format."}],
        "print_format": [
            ["--print-format", "--format", "-f"],
            {"metavar": "FORMAT",
             "help": "Specify the format for printing results."}],
        "profile_mode": [
            ["--profile"],
            {"action": "store_true",
             "default": False,
             "dest": "profile_mode",
             "help": "Switch on profiling."}],
        "project": [
            ["--project"],
            {"metavar": "PROJECT",
             "help": "Create using project metadata."}],
        "property": [
            ["--property", "-p"],
            {"action": "append",
             "metavar": "PROPERTY",
             "help": "Specify a property."}],
        "properties": [
            ["--properties", "-p"],
            {"action": "store",
             "metavar": "PROPERTIES",
             "help": "Specify a comma-separated list of properties."}],
        "prune_remote_mode": [
            ["--prune-remote", "--tidy-remote"],
            {"action": "store_true",
             "dest": "prune_remote_mode",
             "help": "Remove remote job logs after retrieval."}],
        "query_mode": [
            ["--query", "-Q"],
            {"action": "store_const",
             "const": "query",
             "dest": "lookup_mode",
             "help": "Shorthand for --lookup-mode=query."}],
        "quietness": [
            ["--quiet", "-q"],
            {"action": "count",
             "default": 0,
             "dest": "quietness",
             "help": "Decrement verbosity."}],
        "rank_method": [
            ["--rank-method"],
            {"action": "store",
             "metavar": "METHOD",
             "help": "Specify a ranking method."}],
        "reload_mode": [
            ["--reload"],
            {"action": "store_const",
             "const": "reload",
             "dest": "run_mode",
             "help": "Shorthand for --run=reload."}],
        "remote": [
            ["--remote"],
            {"action": "store",
             "metavar": "KEY=VALUE",
             "help": "(Internal option, do not use.)"}],
        "restart_mode": [
            ["--restart"],
            {"action": "store_const",
             "const": "restart",
             "dest": "run_mode",
             "help": "Shorthand for --run=restart."}],
        "retrieve_job_logs": [
            ["--retrieve-job-logs"],
            {"action": "store_true",
             "default": False,
             "help": "Retrieve remote task job logs."}],
        "run_mode": [
            ["--run"],
            {"action": "store",
             "choices": ["reload", "restart", "run"],
             "default": "run",
             "dest": "run_mode",
             "metavar": "MODE",
             "help": "Specify run|restart|reload."}],
        "reverse": [
            ["--reverse", "-r"],
            {"action": "store_true",
             "default": False,
             "help": "Reverse sort order"}],
        "search_mode": [
            ["--search", "-S"],
            {"action": "store_const",
             "const": "search",
             "dest": "lookup_mode",
             "help": "Shorthand for --lookup-mode=search."}],
        "service_root_mode": [
            ["--service-root", "-R"],
            {"action": "store_true",
             "default": False,
             "dest": "service_root_mode",
             "help": "Include web service name under root of URL."}],
        "shutdown": [
            ["--shutdown"],
            {"action": "store_true",
             "default": False,
             "help": "Trigger a suite shutdown."}],
        "sort": [
            ["--sort", "-s"],
            {"metavar": "FIELD",
             "help": "Sort result by FIELD."}],
        "source": [
            ["--source", "-s"],
            {"action": "append",
             "dest": "source",
             "help": "Add a source tree."}],
        "strict_mode": [
            ["--no-strict"],
            {"action": "store_false",
             "dest": "strict_mode",
             "default": True,
             "help": "Do not validate in strict mode."}],
        "suffix_delim": [
            ["--suffix-delim"],
            {"metavar": "DELIMITER",
             "help": "Specify the suffix delimiter."}],
        "suite_only": [
            ["--suite-only"],
            {"action": "store_true",
             "dest": "suite_only",
             "default": False,
             "help": "Run only for suite level macros."}],
        "task": [
            ["--task", "-t"],
            {"action": "append",
             "dest": "group",
             "help": "Switch a group of tasks on."}],
        "task_cycle_time_mode": [
            ["--use-task-cycle-time", "-c"],
            {"action": "store_true",
             "dest": "task_cycle_time_mode",
             "help": "Use ROSE_TASK_CYCLE_TIME."}],
        "text": [
            ["--text"],
            {"action": "store_true",
             "dest": "text",
             "help": "Print graph in text format"}],
        "thresholds": [
            ["--threshold"],
            {"action": "append",
             "dest": "thresholds",
             "metavar": "METHOD:METHOD-ARG:NUMBER",
             "help": "Specify one or more threshold."}],
        "timeout": [
            ["--timeout"],
            {"metavar": "FLOAT",
             "help": "Set a timeout in seconds."}],
        "to_local_copy": [
            ["--to-local-copy"],
            {"action": "store_true",
             "help": "Convert ID to to the local copy path"}],
        "to_origin": [
            ["--to-origin"],
            {"action": "store_true",
             "help": "Convert ID to the origin URL"}],
        "to_output": [
            ["--to-output"],
            {"action": "store_true",
             "help": "Get the ID output directory"}],
        "to_web": [
            ["--to-web"],
            {"action": "store_true",
             "help": "Convert ID to the web source URL"}],
        "transform_all": [
            ["-T", "--transform"],
            {"action": "store_true",
             "dest": "transform_all",
             "default": False,
             "help": "Prepend all transformer macros to the argument list."}],
        "unbound": [
            ["--unbound", "--undef"],
            {"metavar": "STRING",
             "help": "Substitute unbound variables with STRING"}],
        "update_mode": [
            ["--update", "-U"],
            {"action": "store_true",
             "dest": "update_mode",
             "default": False,
             "help": "Switch on update mode."}],
        "upper": [
            ["--upper", "-u"],
            {"action": "store_const",
             "const": "upper",
             "dest": "case_mode",
             "help": "Shorthand for --case=upper."}],
        "user": [
            ["--user", "-u"],
            {"action": "store",
             "default": None,
             "dest": "user",
             "help": "Apply to specified user."}],
        "utc_mode": [
            ["--utc", "-u"],
            {"action": "store_true",
             "default": False,
             "dest": "utc_mode",
             "help": "Switch on UTC mode."}],
        "validate_all": [
            ["--validate", "-V"],
            {"action": "store_true",
             "dest": "validate_all",
             "default": False,
             "help": "Prepend all validator macros to the argument list."}],
        "validate_suite_only": [
            ["--validate-suite-only"],
            {"action": "store_true",
             "dest": "validate_suite_only_mode",
             "default": False,
             "help": "Validate only. Don't install or run."}],
        "verbosity": [
            ["--verbose", "-v"],
            {"action": "count",
             "default": 1,
             "dest": "verbosity",
             "help": "Increment verbosity."}],
        "view_mode": [
            ["--view"],
            {"action": "store_true",
             "dest": "view_mode",
             "default": False,
             "help": "View with web browser."}]}

    def __init__(self, *args, **kwargs):
        if hasattr(kwargs, "prog"):
            namespace, util = kwargs["prog"].split(None, 1)
            resource_loc = ResourceLocator(namespace=namespace, util=util)
        else:
            resource_loc = ResourceLocator.default()
        kwargs["prog"] = resource_loc.get_util_name()
        if not hasattr(kwargs, "usage"):
            kwargs["usage"] = resource_loc.get_synopsis()
        OptionParser.__init__(self, *args, **kwargs)
        self.add_my_options("debug_mode", "profile_mode",
                            "quietness", "verbosity")

    def add_my_options(self, *args):
        """Add named options to this parser. Each element in args must be a key
        in RoseOptionParser.OPTIONS. Return self.
        """
        for arg in args:
            o_args, o_kwargs = self.OPTIONS[arg]
            self.add_option(*o_args, **o_kwargs)
        return self
