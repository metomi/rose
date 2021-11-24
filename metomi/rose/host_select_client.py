# Copyright (C) British Crown (Met Office) & Contributors.
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
import json
from pathlib import Path
import sys

import psutil


def usage():
    print('''
rose host-select-client

Internal command for obtaining information about hosts using the
Python psutil module.

The names of psutil methods are passed to stdin along with any arguments
as a JSON list.

EXAMPLES:
    # return the virtual memory and cpu usage
    [["virtual_memory"], ["cpu_percent"]]

    # return disk usage for the filesystem mounted at "/"
    [["disk_usage", "/"]]

The input json should be preceded by \n**start**\n
and followed by \n**end**\n to avoid issues with user profile scripts
and stdin deadlock.

$ rose host-select-client <<'__HERE__'
> **start**
> [["virtual_memory"]]
> **end**
> __HERE__
[{"total": 17179869184, "available": 6276612096, "percent": 63.5, ...}]
'''.strip())


def main():
    if set(sys.argv) & {'--help', '-h'}:
        usage()
        sys.exit(0)
    # read metrics from stdin
    started = False
    line = True
    metrics = ''
    while True:
        line = sys.stdin.readline().strip()
        if '**start**' in line:
            started = True
            continue
        elif not started:
            continue
        elif '**end**' in line:
            break
        metrics += f'\n{line}'
    metrics = json.loads(metrics)

    # extract metrics using psutil
    ret = [
        getattr(psutil, key)(
            *args
            if key != 'disk_usage'
            else [
                # expand ~ in paths for disk usage queries
                Path(arg).expanduser()
                for arg in args
            ]
        )
        for key, *args in metrics
    ]

    # serialise results
    for ind, item in enumerate(ret):
        if hasattr(item, '_asdict'):
            ret[ind] = item._asdict()

    # output results as json
    print(json.dumps(ret))


if __name__ == '__main__':
    main()
