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
"""Select an available host machine by load or by random."""

from collections import namedtuple
from functools import lru_cache
import json
import os
from random import choice, random, shuffle
import shlex
import signal
from socket import error as SocketError
from socket import (
    getaddrinfo,
    getfqdn,
    gethostbyname_ex,
    gethostname,
)
import sys
import textwrap
from time import sleep, time
import traceback
from typing import List, Optional

from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopener
from metomi.rose.reporter import Event, Reporter
from metomi.rose.resource import ResourceLocator


class NoHostError(Exception):

    """An exception when no (default) hosts are specified."""

    def __str__(self):
        return "No (default) hosts specified."


class NoHostSelectError(Exception):

    """An exception when no hosts are selected."""

    def __str__(self):
        return "No hosts selected."


class HostSelectCommandFailedEvent(Event):

    """A remote host select command failed."""

    KIND = Event.KIND_ERR

    def __init__(
        self, host: str, return_code: int, stderr: Optional[str] = None
    ):
        self.host = host
        self.return_code = return_code
        self.stderr = stderr
        Event.__init__(self)

    def __str__(self) -> str:
        if self.return_code == 255:
            msg = 'ssh failed'
        else:
            msg = f"failed ({self.return_code})"
            if self.stderr is not None:
                msg += f"\n{textwrap.indent(self.stderr, '    ')}"
        return f"{self.host}: {msg}"


class HostThresholdNotMetEvent(Event):

    """An error raised when a host does not meet a threshold."""

    KIND = Event.KIND_ERR
    FMT = (
        "%(host)s: %(method)s:%(method_arg)s threshold not met: "
        + "%(score)s %(scorer_op)s %(value)s"
    )

    def __str__(self):
        host, threshold_conf, score = self.args
        scorer_op = ">"
        if threshold_conf.scorer.SIGN < 0:
            scorer_op = "<"
        fmt_map = {
            "host": host,
            "score": score,
            "scorer_op": scorer_op,
            "method": threshold_conf.method,
            "method_arg": threshold_conf.method_arg,
            "value": threshold_conf.value,
        }
        for key, value in fmt_map.items():
            if value is None:
                fmt_map[key] = ""
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
        value = "Rank method: " + self.args[0]
        if self.args[1] is not None:
            value += ":" + self.args[1]
        return value


class TimedOutHostEvent(Event):

    """An event raised when contact to a host is timed out."""

    KIND = Event.KIND_ERR

    def __str__(self):
        return self.args[0] + ": (timed out)"


class HostSelector:

    """Select an available host machine by load of by random."""

    RANK_METHOD_LOAD = "load"
    RANK_METHOD_FS = "fs"
    RANK_METHOD_RANDOM = "random"
    RANK_METHOD_MEM = "mem"
    RANK_METHOD_DEFAULT = RANK_METHOD_LOAD
    SSH_CMD_POLL_DELAY = 0.05
    SSH_CMD_TIMEOUT = 10.0

    def __init__(self, event_handler=None, popen=None):
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler=event_handler)
        self.popen = popen
        self.scorers = {}
        self.local_host_strs = None

    def get_local_host_strs(self):
        """Return a list of names associated with the current host."""
        if self.local_host_strs is None:
            self.local_host_strs = []
            items = []
            for item in gethostname, getfqdn:
                try:
                    items.append(item())
                except SocketError:
                    pass
            for item in items + ["localhost"]:
                if item in self.local_host_strs:
                    continue
                self.local_host_strs.append(item)
                try:
                    name = gethostbyname_ex(item)[0]
                except (IndexError, SocketError):
                    pass
                else:
                    if name not in self.local_host_strs:
                        self.local_host_strs.append(name)
                try:
                    for addrinfo_item in getaddrinfo(item, None):
                        if addrinfo_item[4][0] not in self.local_host_strs:
                            self.local_host_strs.append(addrinfo_item[4][0])
                except (IndexError, SocketError):
                    pass
        return self.local_host_strs

    def get_local_host(self):
        """Return the normal name of the current host."""
        return self.get_local_host_strs()[0]

    def is_local_host(self, name):
        """Return True is name appears to be the localhost."""
        return name in self.get_local_host_strs()

    def get_scorer(self, method=None):
        """Return a suitable scorer for a given scoring method."""
        if method is None:
            method = self.RANK_METHOD_DEFAULT
        if method not in self.scorers:
            for value in globals().values():
                if (
                    isinstance(value, type)
                    and issubclass(value, RandomScorer)
                    and value.KEY == method
                ):
                    self.scorers[method] = value()
        return self.scorers[method]

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def expand(self, names=None, rank_method=None, thresholds=None):
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
            node = conf.get(["rose-host-select", "default"], no_ignore=True)
            if node:
                names = [node.value]
            else:
                raise NoHostError()

        host_names = []
        rank_method_set = set()
        thresholds_set = set()
        while names:
            name = names.pop()
            key = "group{" + name + "}"
            value = conf.get_value(["rose-host-select", key])
            if value is None:
                host_names.append(name)
            else:
                for val in value.split():
                    names.append(val)
                if rank_method is None:
                    key = "method{" + name + "}"
                    method_str = conf.get_value(["rose-host-select", key])
                    if method_str is None:
                        rank_method_set.add(self.RANK_METHOD_DEFAULT)
                    else:
                        rank_method_set.add(method_str)
                if thresholds is None:
                    key = "thresholds{" + name + "}"
                    threshold_str = conf.get_value(["rose-host-select", key])
                    if threshold_str is None:
                        thresholds_set.add(())
                    else:
                        thresholds_set.add(
                            tuple(sorted(shlex.split(threshold_str)))
                        )

        # If default rank method differs in hosts, use load:15.
        if rank_method is None:
            if len(rank_method_set) == 1:
                rank_method = rank_method_set.pop()
            else:
                rank_method = self.RANK_METHOD_DEFAULT

        if thresholds is None:
            if len(thresholds_set) == 1:
                thresholds = thresholds_set.pop()

        return host_names, rank_method, thresholds

    @staticmethod
    def _bash_login_cmd(cmd: List[str]) -> List[str]:
        """Return the given command as a bash login shell command.

        This allows users to set env vars.

        Example:
        >>> HostSelector._bash_login_cmd(["echo", "-n", "Multiple words"])
        ['bash', '-l', '-c', "echo -n 'Multiple words'"]
        """
        return ['bash', '-l', '-c', RosePopener.shlex_join(cmd)]

    def select(
        self,
        names=None,
        rank_method=None,
        thresholds=None,
        ssh_cmd_timeout=None,
    ):
        """Return a list. Element 0 is most desirable.
        Each element of the list is a tuple (host, score).

        names: a list of known host groups or host names.
        rank_method: the ranking method. Can be one of:
                     load:1, load:5, load:15 (=load =default), fs:FS and
                     random.  The "load" methods determines the load using the
                     average load as returned by the "uptime" command divided
                     by the number of CPUs. The "fs" method determines the load
                     using the usage in the file system specified by FS. The
                     "mem" method ranks by highest free memory. The "random"
                     method ranks everything by random.

        thresholds: a list of thresholds which each host must not exceed.
                    Should be in the format rank_method:value, where
                    rank_method is one of load:1, load:5, load:15 or fs:FS; and
                    value is number that must be be exceeded.

        ssh_cmd_timeout: timeout of SSH commands to hosts. A float in seconds.

        """

        host_names, rank_method, thresholds = self.expand(
            names, rank_method, thresholds
        )

        # Load scorers, ranking and thresholds
        rank_method_arg = None
        if rank_method:
            if ":" in rank_method:
                rank_method, rank_method_arg = rank_method.split(":", 1)
        else:
            rank_method = self.RANK_METHOD_DEFAULT
        rank_conf = ScorerConf(self.get_scorer(rank_method), rank_method_arg)
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
                threshold_conf = ScorerConf(
                    self.get_scorer(method), method_arg, value
                )
                threshold_confs.append(threshold_conf)

        if ssh_cmd_timeout is None:
            conf = ResourceLocator.default().get_conf()
            ssh_cmd_timeout = float(
                conf.get_value(
                    ["rose-host-select", "timeout"], self.SSH_CMD_TIMEOUT
                )
            )

        host_name_list = list(host_names)
        host_names = []
        for host_name in host_name_list:
            if self.is_local_host(host_name):
                if self.get_local_host() not in host_names:
                    host_names.append(self.get_local_host())
            else:
                host_names.append(host_name)

        # Random selection with no thresholds. Return the 1st available host.
        if rank_conf.method == self.RANK_METHOD_RANDOM and not threshold_confs:
            shuffle(host_names)
            for host_name in host_names:
                if self.is_local_host(host_name):
                    return [("localhost", 1)]
                command = self.popen.get_cmd("ssh", host_name, "true")
                proc = self.popen.run_bg(*command, preexec_fn=os.setpgrp)
                time0 = time()
                while (
                    proc.poll() is None and time() - time0 <= ssh_cmd_timeout
                ):
                    sleep(self.SSH_CMD_POLL_DELAY)
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.wait()
                    self.handle_event(TimedOutHostEvent(host_name))
                elif proc.wait():
                    self.handle_event(
                        HostSelectCommandFailedEvent(
                            host_name, proc.returncode
                        )
                    )
                else:
                    return [(host_name, 1)]
            else:
                raise NoHostSelectError()

        # ssh to each host to return its score(s).
        host_proc_dict = {}
        for host_name in sorted(host_names):
            # build host-select-client command
            command: List[str] = []

            # pass through CYLC_VERSION to support use of cylc wrapper script
            try:
                import cylc.flow
            except ModuleNotFoundError:
                pass
            else:
                command.extend([
                    'env',
                    f'CYLC_VERSION={cylc.flow.__version__}',
                ])
                cylc_env_name = os.getenv('CYLC_ENV_NAME')
                if cylc_env_name:
                    command.append(f'CYLC_ENV_NAME={cylc_env_name}')

            command.extend(
                self._bash_login_cmd(['rose', 'host-select-client'])
            )

            # build list of metrics to obtain for each host
            metrics = rank_conf.get_command()
            for threshold_conf in threshold_confs:
                for metric in threshold_conf.get_command():
                    if metric not in metrics:
                        metrics.append(metric)

            # convert metrics list to JSON stdin
            stdin = '\n***start**\n' + json.dumps(metrics) + '\n**end**\n'

            if not self.is_local_host(host_name):
                command = [
                    *self.popen.get_cmd('ssh', host_name),
                    RosePopener.shlex_join(command)
                ]
            # fire off host-select-client processes
            proc = self.popen.run_bg(
                *command, stdin=stdin, preexec_fn=os.setpgrp
            )
            proc.stdin.write(stdin)
            proc.stdin.flush()
            host_proc_dict[host_name] = (proc, metrics)

        # Retrieve score for each host name
        host_score_list = []
        time0 = time()
        while host_proc_dict:
            sleep(self.SSH_CMD_POLL_DELAY)
            for host_name, (proc, metrics) in list(host_proc_dict.items()):
                if proc.poll() is None:  # still running
                    continue
                stdout, stderr = proc.communicate()
                if proc.returncode:
                    self.handle_event(
                        HostSelectCommandFailedEvent(
                            host_name, proc.returncode, stderr
                        )
                    )
                    host_proc_dict.pop(host_name)
                else:
                    out = _deserialise(metrics, json.loads(stdout.strip()))

                    host_proc_dict.pop(host_name)
                    for threshold_conf in threshold_confs:
                        try:
                            score = threshold_conf.command_out_parser(
                                out, metrics
                            )
                            is_bad = threshold_conf.check_threshold(score)
                        except ValueError:
                            is_bad = True
                            score = None
                        if is_bad:
                            self.handle_event(
                                HostThresholdNotMetEvent(
                                    host_name, threshold_conf, score
                                )
                            )
                            break
                    else:
                        try:
                            score = rank_conf.command_out_parser(out, metrics)
                            host_score_list.append((host_name, score))
                        except ValueError:
                            score = None
                        self.handle_event(
                            HostSelectScoreEvent(host_name, score)
                        )
            if time() - time0 > ssh_cmd_timeout:
                break

        # Report timed out hosts
        for host_name, (proc, _) in sorted(host_proc_dict.items()):
            self.handle_event(TimedOutHostEvent(host_name))
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait()

        if not host_score_list:
            raise NoHostSelectError()
        host_score_list.sort(
            key=lambda a: a[1], reverse=rank_conf.scorer.SIGN < 0
        )
        return host_score_list

    __call__ = select


@lru_cache()
def _tuple_factory(name, params):
    """Wrapper to namedtuple which caches results to prevent duplicates."""
    return namedtuple(name, params)


def _deserialise(metrics, data):
    """Convert dict to named tuples.

    Examples:
        >>> _deserialise(
        ...     [
        ...         ['foo', 'bar'],
        ...         ['baz']
        ...     ],
        ...     [
        ...         {'a': 1, 'b': 2, 'c': 3},
        ...         [1, 2, 3]
        ...     ]
        ... )
        [foo(a=1, b=2, c=3), [1, 2, 3]]

    """
    for index, (metric, datum) in enumerate(zip(metrics, data)):
        if isinstance(datum, dict):
            data[index] = _tuple_factory(metric[0], tuple(datum.keys()))(
                *datum.values()
            )
    return data


class ScorerConf:

    """Wrap a threshold/ranking scorer + extra configuration."""

    def __init__(self, scorer, method_arg, value=None):
        self.scorer = scorer
        self.method = scorer.KEY
        self.method_arg = method_arg
        self.value = value

    def get_command(self):
        """Return a shell command to get the info for scoring a host."""
        return self.scorer.get_command(self.method_arg)

    def check_threshold(self, score):
        """Parse command output. Return True if threshold not met."""
        return (
            float(score) * self.scorer.SIGN
            > float(self.value) * self.scorer.SIGN
        )

    def command_out_parser(self, out, metrics):
        """Parse command output to return a numeric score."""
        results = self.get_results(out, metrics)
        return self.scorer.command_out_parser(results, self.method_arg)

    def get_results(self, out, metrics):
        """Return list of results for the requested metrics."""
        return [
            out[metrics.index(metric)]
            for metric in self.scorer.get_command(self.method_arg)
        ]


class RandomScorer:

    """Base class for threshold/ranking scorer.

    Score host by random.

    """

    ARG: Optional[str] = None
    KEY: str = "random"
    CMD: list = ['cpu_count']  # fetch an arbitrary metric
    CMD_IS_FORMAT: bool = False
    SIGN: int = 1  # Positive

    def get_command(self, method_arg=None):
        """Return a shell command to get the info for scoring a host."""
        return list(self.CMD)

    @classmethod
    def command_out_parser(cls, out, method_arg=None):
        """Parse command output to return a numeric score.

        Sub-class should override this to parse "out", the standard output
        returned by the command run on the remote host. Otherwise, this method
        returns a random number.
        """
        return random()


class LoadScorer(RandomScorer):

    """Score host by average uptime load."""

    ARG = "15"
    KEY = "load"
    VALUES = ('1', '5', '15')  # 1, 5, 15 min average values
    CMD = [["getloadavg"], ["cpu_count"]]

    def command_out_parser(self, out, method_arg=None):
        load = out[0][self.VALUES.index(method_arg or self.ARG)]
        cpus = out[1]
        return load / cpus


class MemoryScorer(RandomScorer):

    """Score host by amount of free memory"""

    KEY = "mem"
    CMD = [["virtual_memory"]]
    SIGN = -1  # Negative

    def command_out_parser(self, out, method_arg=None):
        return out[0].available


class FileSystemScorer(RandomScorer):

    """Score host by average file system percentage usage."""

    ARG = "~"
    KEY = "fs"

    def get_command(self, method_arg):
        return [['disk_usage', method_arg or self.ARG]]

    def command_out_parser(self, out, method_arg=None):
        return out[0].percent


def main():
    """Implement the "rose host-select" command."""
    opt_parser = RoseOptionParser(
        usage='rose host-select [OPTIONS] [GROUP/HOST ...]',
        description='''
Select a host from a set of groups or names by load, by free memory
or by random.

Print the selected host name.
        ''',
        epilog='''
RANKING METHODS IN DETAIL (--rank-method):
    `load`
        Rank by average load as reported by `uptime` divided by
        number of virtual processors.

        If `METHOD-ARG` is specified, it must be `1`, `5` or `15`.
        The default is to use the 15 minute load.
    `fs`
        Rank by % usage of a file system as reported by `df`.

        `METHOD-ARG` must be a valid file system in all the given
        hosts and host groups. The default is to use the `~`
        directory.
    `mem`
        Rank by largest amount of free memory. Uses `free -m` to
        return memory in Mb
    `random`
        No ranking is used.

CONFIGURATION
    The command reads its settings from the `[rose-host-select]` section in
    the Rose configuration. All settings are optional. Type
    `rose config rose-host-select` to print settings.

    Valid settings are:

    default = GROUP/HOST ...
       The default arguments to use for this command.
    group{NAME} = GROUP/HOST ...
       Declare a named group of hosts.
    method{NAME} = METHOD[:METHOD-ARG]
       Declare the default ranking method for a group of hosts.
    thresholds{NAME} = [METHOD[:METHOD-ARG]:]VALUE ...
       Declare the default threshold(s) for a group of hosts.
    timeout = FLOAT
       Set the timeout in seconds of SSH commands to hosts.
       (default=10.0)
        '''
    )
    opt_parser.add_my_options("choice", "rank_method", "thresholds", "timeout")
    opt_parser.modify_option(
        'timeout',
        help='Set the timeout in seconds of SSH commands to hosts.',
    )
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    popen = RosePopener(event_handler=report)
    select = HostSelector(event_handler=report, popen=popen)
    try:
        host_score_list = select(
            names=args,
            rank_method=opts.rank_method,
            thresholds=opts.thresholds,
            ssh_cmd_timeout=opts.timeout,
        )
    except (NoHostError, NoHostSelectError) as exc:
        report(exc)
        if opts.debug_mode:
            traceback.print_exc()
        sys.exit(1)
    opts.choice = int(opts.choice)
    report(choice(host_score_list[0 : opts.choice])[0] + "\n", level=0)


if __name__ == "__main__":
    main()
