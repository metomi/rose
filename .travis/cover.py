# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
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

import sys

from subprocess import call


def main():
    command = ['etc/bin/rose-test-battery', '-j', '5']
    if call(command + ['--state=save']):
        # Non-zero return code
        sys.stderr.write('\n\nRerunning Failed Tests...\n\n')
        # Exit with final return code
        sys.exit(call(command + ['--state=save,failed', '-v']))


if __name__ == '__main__':
    main()
