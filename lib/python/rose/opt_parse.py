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
"""Common option parser for Rose command utilities."""

from optparse import OptionParser
from rose.resource import ResourceLocator


class RoseOptionParser(OptionParser):

    """Option parser base class for Rose command utilities."""

    OPTIONS = {"all": [
                       ["--all", "-a"],
                       {"action": "store_true",
                        "default": False,
                        "help": "Apply all available items."}],
               "all_revs": [
                       ["--all-revs"],
                       {"action": "store_true",
                        "default": False,
                        "help": "Return all revisions of matched items."}],
               "app_key": [
                       ["--app-key"],
                       {"action": "store",
                        "metavar": "KEY",
                        "help": "Specify a named application configuration."}],
               "auto_type": [
                       ["--auto-type"],
                       {"action": "store_true",
                        "default": False,
                        "dest": "type",
                        "help": "Automatically guess types of settings."}],
               "auto_util_mode": [
                       ["--no-auto-util"],
                       {"action": "store_false",
                        "default": True,
                        "dest": "auto_util_mode",
                        "help": ("Do not automatically select " +
                                 "a task utility based on the task name.")}],
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
               "confsource": [
                       ["--confsource", "-c"],
                       {"action": "store",
                        "dest": "confsource",
                        "help": "Specify root configuration directory."}],
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
               "diffsource": [
                       ["--diffsource", "-d"],
                       {"action": "append",
                        "dest": "diffsource",
                        "help": "Add a branch."}],
               "files": [
                       ["--file", "-f"],
                       {"action": "append",
                        "dest": "files",
                        "metavar": "FILE",
                        "help": "Specify the configuration file(s)."}],
               "force_mode": [
                       ["--force", "-f"],
                       {"action": "store_true",
                        "dest": "force_mode",
                        "help": ("Force file installation " +
                                 "even if it may be unsafe.")}],
               "format": [
                       ["--format", "-f"],
                       {"metavar": "FORMAT",
                        "help": "Specify the output format of each result."}],
               "gcontrol_mode": [
                       ["--no-gcontrol"],
                       {"action": "store_false",
                        "dest": "gcontrol_mode",
                        "default": True,
                        "help": "Do not run suite control GUI."}],
               "host": [
                       ["--host"],
                       {"metavar": "HOST",
                        "help": "Specify a host"}],
               "info_file": [
                       ["--info-file"],
                       {"metavar": "FILE",
                        "help": "Specify the discovery information file."}],
               "install_only_mode": [
                       ["--install-only", "-i"],
                       {"action": "store_true",
                        "dest": "install_only_mode",
                        "help": "Install files only. Don't run."}],
               "keys": [
                       ["--keys", "-k"],
                       {"action": "store_true",
                        "dest": "keys_mode",
                        "help": "Print SECTION/OPTION keys only"}],
               "latest": [
                       ["--latest"],
                       {"action": "store_true",
                        "help": "Print the latest ID in the repository"}],
               "local_only": [
                       ["--local-only"],
                       {"action": "store_true",
                        "help": "Delete only the local copy of a suite"}],
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
               "meta_path": [
                       ["--meta-path", "-M"],
                       {"action": "append",
                        "metavar": "PATH",
                        "help": "Prepend items to the metadata search path."}],
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
               "next": [
                       ["--next"],
                       {"action": "store_true",
                        "help": "Print the next available ID in the " +
                                "repository"}],
               "non_interactive": [
                       ["--non-interactive", "--yes", "-y"],
                       {"action": "store_true",
                        "default": False,
                        "help": "Switch off interactive prompting."}],
               "no_ignore": [
                       ["--print-ignored", "-i"],
                       {"action": "store_false",
                        "dest": "no_ignore",
                        "help": "print ignored settings where relevant"}],
               "no_overwrite_mode": [
                       ["--no-overwrite"],
                       {"action": "store_true",
                        "dest": "no_overwrite_mode",
                        "help": "Do not overwrite existing files."}],
               "opt_conf_keys": [
                       ["--opt-conf-key", "-O"],
                       {"action": "append",
                        "dest": "opt_conf_keys",
                        "metavar": "KEY",
                        "help": ("Switch on an optional configuration " +
                                 "file identified by KEY.")}],
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
               "path_globs": [
                       ["--path", "-P"],
                       {"action": "append",
                        "dest": "path_globs",
                        "metavar": "PATTERN",
                        "help": ("Paths to prepend to PATH.")}],
               "prefix": [
                       ["--prefix"],
                       {"metavar": "PREFIX",
                        "help": "Specify the name of the suite repository."}],
               "prefix_delim": [
                       ["--prefix-delim"],
                       {"metavar": "DELIMITER",
                        "help": "Specify the prefix delimiter."}],
               "query": [
                       ["--query", "-Q"],
                       {"action": "store_true",
                        "default": False,
                        "help": "Run a suite query."}],                  
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
               "remote": [
                       ["--remote"],
                       {"action": "store",
                        "metavar": "KEY=VALUE",
                        "help": "(Internal option, do not use.)"}],
               "reverse": [
                       ["--reverse", "-r"],
                       {"action": "store_true",
                        "default": False,
                        "help": "Reverse sort order"}],
               "search": [
                       ["--search", "-S"],
                       {"action": "store_true",
                        "default": False,
                        "help": "Run a suite search."}],
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
                        "help": "Add a trunk."}],
               "suffix_delim": [
                       ["--suffix-delim"],
                       {"metavar": "DELIMITER",
                        "help": "Specify the suffix delimiter."}],
               "task": [
                       ["--task", "-t"],
                       {"action": "append",
                        "dest": "task",
                        "help": "Switch a task on/off."}],
               "thresholds": [
                       ["--threshold"],
                       {"action": "append",
                        "dest": "thresholds",
                        "metavar": "METHOD:METHOD-ARG:NUMBER",
                        "help": "Specify one or more threshold."}],
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
               "upper": [
                       ["--upper", "-u"],
                       {"action": "store_const",
                        "const": "upper",
                        "dest": "case_mode",
                        "help": "Shorthand for --case=upper."}],
               "url": [
                       ["--url", "-U"],
                       {"action": "store_true",
                        "default": False,
                        "help": "Use search url"}],                        
               "util_key": [
                       ["--util-key"],
                       {"action": "store",
                        "metavar": "KEY",
                        "help": "Specify a named task utility."}],
               "validate_all": [
                       ["--validate", "-V"],
                       {"action": "store_true",
                        "dest": "validate_all",
                        "default": False,
                        "help": "Switch on all validators."}],
               "verbosity": [
                       ["--verbose", "-v"],
                       {"action": "count",
                        "default": 1,
                        "dest": "verbosity",
                        "help": "Increment verbosity."}],
               "web_browser_mode": [
                       ["--no-web-browse"],
                       {"action": "store_false",
                        "dest": "web_browser_mode",
                        "default": True,
                        "help": "Do not open web browser."}]}

    def __init__(self, *args, **kwargs):
        if hasattr(kwargs, "prog"):
            ns, util = kwargs["prog"].split(None, 1)
            resource_loc = ResourceLocator(ns=ns, util=util)
        else:
            resource_loc = ResourceLocator.default()
        kwargs["prog"] = resource_loc.get_util_name()
        if not hasattr(kwargs, "usage"):
            kwargs["usage"] = resource_loc.get_synopsis()
        OptionParser.__init__(self, *args, **kwargs)
        self.add_my_options("debug_mode", "quietness", "verbosity")

    def add_my_options(self, *args):
        """Add named options to this parser. Each element in args must be a key
        in RoseOptionParser.OPTIONS. Return self.
        """
        for arg in args:
            o_args, o_kwargs = self.OPTIONS[arg]
            self.add_option(*o_args, **o_kwargs)
        return self
