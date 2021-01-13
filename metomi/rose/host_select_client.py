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
import json
import sys

import psutil


def main():
    # read metrics from stdin
    line = True
    metrics = ''
    while True:
        line = sys.stdin.readline().strip()
        if '**start**' in line:
            continue
        if '**end**' in line:
            break
        metrics += f'\n{line}'
    metrics = json.loads(metrics)

    # extract metrics using psutil
    ret = [
        getattr(psutil, key[0])(*key[1:])
        for key in metrics
    ]

    # serialise results
    for ind, item in enumerate(ret):
        if hasattr(item, '_asdict'):
            ret[ind] = item._asdict()

    # output results as json
    print(json.dumps(ret))


if __name__ == '__main__':
    main()