#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
#-------------------------------------------------------------------------------
# Test "rose app-run", file installation source with a leading tilde.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
N_TESTS=3
tests $N_TESTS
#-------------------------------------------------------------------------------
WORK_DIR=$(mktemp -d --tmpdir=$HOME)
WORK_BASE=$(basename $WORK_DIR)
cat >$WORK_DIR/al2o3.txt <<'__TXT__'
print "I am aluminium oxide"
__TXT__
cat >$WORK_DIR/cr.txt <<'__TXT__'
print "with added chromium"
__TXT__
test_init <<__CONFIG__
[command]
default=true

[file:shiny.rb]
source=~/$WORK_BASE/al2o3.txt ~/$WORK_BASE/cr.txt
__CONFIG__

TILDE_LOCS=$(rose config --default= 't' 'tilde-locs')
OPT_CONF=
if [[ -n $TILDE_LOCS ]]; then
    mkdir config/opt
    cat >config/opt/rose-app-more.conf <<__CONFIG__
[file:copying2]
source=$TILDE_LOCS
__CONFIG__
    OPT_CONF='-O more'
fi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE"
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -q $OPT_CONF
file_cmp "$TEST_KEY-shiny.rb" shiny.rb <<'__TXT__'
print "I am aluminium oxide"
print "with added chromium"
__TXT__
if [[ -n $TILDE_LOCS ]]; then
    file_cmp "$TEST_KEY-copying2" copying2 <<<"$(eval cat $TILDE_LOCS)"
else
    skip 1 '[t]tilde-locs not defined'
fi
test_teardown
#-------------------------------------------------------------------------------
rm $WORK_DIR/al2o3.txt $WORK_DIR/cr.txt
rmdir $WORK_DIR
exit
