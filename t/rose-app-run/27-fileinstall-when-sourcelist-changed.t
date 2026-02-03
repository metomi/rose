#!/bin/bash
#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------
# Test that "rose app-run" compares the current source list properly against
# database file: See https://github.com/metomi/rose/issues/2438
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
test_init </dev/null
#-------------------------------------------------------------------------------
tests 1
#-------------------------------------------------------------------------------
test_setup
mkdir opt
touch rose-app.conf

# Create two alternative source files:
tee source.1 <<__HERE__
source 1 file
__HERE__
tee source.2 <<__HERE__
source 2 file
__HERE__

# Create two optional configs:
tee opt/rose-app-one.conf <<__HERE__
[command]
default=echo "Hello Magrathea!"

[file:MyTargetFile]
source=source.1
__HERE__
tee opt/rose-app-two.conf <<__HERE__
[command]
default=echo "Hello Magrathea!"

[file:MyTargetFile]
source=source.2
__HERE__

rose app-run -C $PWD -O one -i
rose app-run -C $PWD -O two -i
rose app-run -C $PWD -O one -i
# Before the bugfix rose app-run would think it had already installed source 1.
file_cmp "${TEST_KEY_BASE}-1st-install-output" "MyTargetFile" <<__INSTALLED_FILE__
source 1 file
__INSTALLED_FILE__


test_teardown
