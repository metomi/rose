# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------
"""Select an available host machine by load or by random."""

from random import random
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener
from rose.reporter import Reporter, Event
from rose.resource import ResourceLocator
import sys
from time import sleep, time


class NoHostError(Exception):

    """An exception when no (default) hosts are specified."""

    def __str__(self):
        return "No (default) hosts specified."


class NoHostSelectError(Exception):

    """An exception when no hosts are selected."""

    def __str__(self):
        return "No hosts selected."


class DeadHostEvent(Event):

    """An error raised when a host is not contactable."""

    TYPE = Event.TYPE_ERR

    def __str__(self):
        return self.args[0] + ": (ssh failed)"


class HostExceedThresholdEvent(Event):

    """An error raised when a host exceeds a threshold."""

    TYPE = Event.TYPE_ERR
    FMT = "%(host)s: %(score)s > threshold %(method)s:%(method_arg)s:%(value)s"

    def __str__(self):
        host, threshold_conf, score = self.args
        fmt_map = {"host": host, "score": score}
        fmt_map.update(threshold_conf)
        return self.FMT % fmt_map


class HostSelectScoreEvent(Event):

    """An event to report the score of each host."""

    LEVEL = Event.V

    def __str__(self):
        return "%s: %s" % (self.args[0], str(self.args[1]))


class RankMethodEvent(Event):

    """An event to report the chosen rank method."""

    LEVEL = Event.V

    def __str__(self):
        s = "Rank method: " + self.args[0]
        if self.args[1] is not None:
            s += ":" + self.args[1]
        return s


class TimedOutHostEvent(Event):

    """An event raised when contact to a host is timed out."""

    TYPE = Event.TYPE_ERR

    def __str__(self):
        return self.args[0] + ": (timed out)"


class HostSelector(object):

    """Select an available host machine by load of by random."""

    RANK_METHOD_LOAD = "load"
    RANK_METHOD_FS = "fs"
    RANK_METHOD_RANDOM = "random"
    RANK_METHOD_DEFAULT = RANK_METHOD_LOAD
    TIMEOUT_DELAY = 1.0

    def __init__(self, event_handler=None, popen=None):
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler=event_handler)
        self.popen = popen
        self.scorers = {}

    def get_scorer(self, method=None):
        """Return a suitable scorer for a given scoring method."""
        if method is None:
            method = self.RANK_METHOD_DEFAULT
        if not self.scorers.has_key(method):
            for value in globals().values():
                if (isinstance(value, type) and
                    issubclass(value, RandomScorerConf) and
                    value.KEY == method):
                    self.scorers[method] = value()
        return self.scorers[method]

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def expand(self, names=None, rank_method=None):
        """Expand each name in names, and look up rank method for each name.

        names, if specified, should be a list of host names or known groups in
        the site / user configuration file. Otherwise, the default setting in
        the site / user configuration file will be used.

        rank_method, if specified, should be the name of a supported ranking
        method. If not specified, use the default specified for a host group.
        If the default differs in hosts, use "load:15".

        """
        conf = ResourceLocator.default().get_conf()
        if not names:
            node = conf.get(["rose-host-select", "default"],
                            no_ignore=True)
            if node:
                names = [node.value]
            else:
                raise NoHostError()

        host_names = []
        rank_methods = set()
        while names:
            name = names.pop()
            key = "group{" + name + "}"
            node = conf.get(["rose-host-select", key], no_ignore=True)
            if node is None:
                host_names.append(name)
            else:
                for v in node.value.split():
                    names.append(v)
                if rank_method is None:
                    key = "method{" + name + "}"
                    node = conf.get(["rose-host-select", key], no_ignore=True)
                    if node is None:
                        rank_methods.add(self.RANK_METHOD_DEFAULT)
                    else:
                        rank_methods.add(node.value)
        # If default rank method differs in hosts, use load:15.
        if rank_method is None:
            if len(rank_methods) == 1:
                rank_method = rank_methods.pop()
            else:
                rank_method = self.RANK_METHOD_DEFAULT
        return host_names, rank_method

    def select(self, names=None, rank_method=None, thresholds=None):
        """Return a list. Element 0 is most desirable.
        Each element of the list is a tuple (host, score).

        names: a list of known host groups or host names.
        rank_method: the ranking method. Can be one of:
                     load:1, load:5, load:15 (=load =default), fs:FS and random.
                     The "load" methods determines the load using the average
                     load as returned by the "uptime" command divided by the
                     number of CPUs. The "fs" method determines the load using
                     the usage in the file system specified by FS. The
                     "random" method ranks everything by random.

        thresholds: a list of thresholds which each host must not exceed.
                    Should be in the format rank_method:value, where rank_method
                    is one of load:1, load:5, load:15 or fs:FS; and value is
                    number that must be be exceeded.
        """

        host_names, rank_method = self.expand(names, rank_method)

        # Load scorers, ranking and thresholds
        rank_method_arg = None
        if rank_method:
            if ":" in rank_method:
                rank_method, rank_method_arg = rank_method.split(":", 1)
        else:
            rank_method = self.RANK_METHOD_DEFAULT
        rank_conf = {"scorer": self.get_scorer(rank_method),
                     "method": rank_method,
                     "method_arg": rank_method_arg}
        self.handle_event(RankMethodEvent(rank_method, rank_method_arg))

        threshold_confs = []
        if thresholds:
            for threshold in thresholds:
                method = self.RANK_METHOD_DEFAULT
                method_arg = None
                value = threshold
                if ":" in threshold:
                    head, value = threshold.rsplit(":", 1)
                    method = head
                    if ":" in head:
                        method, method_arg = head.split(":", 1)
                try:
                    float(value)
                except ValueError:
                    raise ValueError(threshold)
                scorer = self.get_scorer(method)
                if method_arg is None:
                    method_arg = scorer.ARG
                threshold_conf = {"scorer": self.get_scorer(method),
                                  "method": method,
                                  "method_arg": method_arg,
                                  "value": value}
                threshold_confs.append(threshold_conf)

        # ssh to each host to return its score(s).
        host_proc_dict = {}
        for host_name in sorted(host_names):
            command = ""
            if host_name != "localhost":
                command = self.popen.list_to_shell_str(
                        self.popen.get_cmd("ssh", host_name))
            command += " bash <<'__BASH__'\n"
            command += rank_conf["scorer"].get_command(rank_conf["method_arg"])
            for threshold_conf in threshold_confs:
                scorer = threshold_conf["scorer"]
                command += scorer.get_command(threshold_conf["method_arg"])
            command += "__BASH__\n"
            proc = self.popen.run_bg(command, shell=True)
            host_proc_dict[host_name] = proc

        # Retrieve score for each host name
        conf = ResourceLocator.default().get_conf()
        timeout_node = conf.get(["rose-host-select", "timeout"],
                                no_ignore=True)
        timeout = getattr(timeout_node, "value", None)
        can_timeout = timeout is not None
        if can_timeout:
            timeout = float(timeout)
            time0 = time()
        host_score_list = []
        while host_proc_dict:
            for host_name, proc in host_proc_dict.items():
                if can_timeout and proc.poll() is None:
                    score = None
                elif proc.wait():
                    self.handle_event(DeadHostEvent(host_name))
                    host_proc_dict.pop(host_name)
                else:
                    out, err = proc.communicate()
                    host_proc_dict.pop(host_name)
                    for threshold_conf in threshold_confs:
                        scorer = threshold_conf["scorer"]
                        method_arg = threshold_conf["method_arg"]
                        score = scorer.command_out_parser(out, method_arg)
                        if score > float(threshold_conf["value"]):
                            self.handle_event(HostExceedThresholdEvent(
                                    host_name, threshold_conf, score))
                            break
                    else:
                        scorer = rank_conf["scorer"]
                        method_arg = rank_conf["method_arg"]
                        score = scorer.command_out_parser(out, method_arg)
                        host_score_list.append((host_name, score))
                        self.handle_event(HostSelectScoreEvent(host_name, score))
            if can_timeout:
                dt = time() - time0
                if host_proc_dict:
                    if dt >= timeout:
                        break
                    if timeout - dt > self.TIMEOUT_DELAY:
                        sleep(self.TIMEOUT_DELAY)
                    else:
                        sleep(timeout - dt)
        for host_name in sorted(host_proc_dict.keys()):
            self.handle_event(TimedOutHostEvent(host_name))
            
        if not host_score_list:
            raise NoHostSelectError()
        host_score_list.sort(lambda a, b: cmp(a[1], b[1]))
        return host_score_list

    __call__ = select


class RandomScorerConf(object):

    """Base class for ranking configuration.
    
    Score host by random.
 
    """

    ARG = None
    KEY = "random"
    CMD = "true\n"
    CMD_IS_FORMAT = False

    def get_command(self, method_arg=None):
        """Return a shell command to get the info for scoring a host."""

        if self.CMD_IS_FORMAT:
            return self.CMD % {"method_arg": method_arg}
        else:
            return self.CMD

    def command_out_parser(self, out, method_arg=None):
        """Parse command output to return a numeric score.
        
        Sub-class should override this to parse "out", the standard output
        returned by the command run on the remote host. Otherwise, this method
        returns a random number.
        """

        return random()


class LoadScorerConf(RandomScorerConf):

    """Score host by average uptime load."""

    ARG = "15"
    KEY = "load"
    INDEX_OF = {"1": 1, "5": 2, "15": 3}
    CMD = ("echo nproc=$((cat /proc/cpuinfo || lscfg) | grep -ic processor)\n"
           "echo uptime=$(uptime)\n")

    def command_out_parser(self, out, method_arg=None):
        if method_arg is None:
            method_arg = self.ARG
        nprocs = None
        load = None
        for line in out.splitlines():
            if line.startswith("nproc="):
                nprocs = line.split("=", 1)[1]
            elif line.startswith("uptime="):
                idx = self.INDEX_OF[method_arg]
                load = line.rsplit(None, 3)[idx].rstrip(",")
        if load is None or not nprocs:
            return None
        return float(load) / float(nprocs)


class FileSystemScorerConf(RandomScorerConf):

    """Score host by average file system percentage usage."""

    ARG = "~"
    KEY = "fs"
    CMD = """echo df:'%(method_arg)s'=$(df -Pk %(method_arg)s | tail -1)\n"""
    CMD_IS_FORMAT = True

    def command_out_parser(self, out, method_arg=None):
        if method_arg is None:
            method_arg = self.ARG
        for line in out.splitlines():
            if line.startswith("df:" + method_arg + "="):
                return int(line.rsplit(None, 2)[-2][0:-1])


def main():
    """Implement the "rose host-select" command."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("rank_method", "thresholds")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    popen = RosePopener(event_handler=report)
    select = HostSelector(event_handler=report, popen=popen)
    if opts.debug_mode:
        host_score_list = select(
                names=args,
                rank_method=opts.rank_method,
                thresholds=opts.thresholds)
    else:
        try:
            host_score_list = select(
                    names=args,
                    rank_method=opts.rank_method,
                    thresholds=opts.thresholds)
        except Exception as e:
            report(e)
            sys.exit(1)
    report(host_score_list[0][0] + "\n", level=0)


if __name__ == "__main__":
    main()
