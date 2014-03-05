#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
# Test "rose stem".
#-------------------------------------------------------------------------------
export HERE=$PWD/$(dirname $0)
export DELAY=20
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#Create repository to run on
svnadmin create foo
URL=file://$PWD/foo
(cd $(mktemp -d); mkdir -p trunk/rose-stem; svn import -m ""  $URL)
#-------------------------------------------------------------------------------
#Set up a keyword in the user's fcm keywords file (will delete later)
cat >> $HOME/.metomi/fcm/keyword.cfg << __EOF__
location{primary}[foo] = $URL
__EOF__
#-------------------------------------------------------------------------------
#Check out a copy of the repository
WORKINGCOPY=$PWD/foo_trunk
fcm checkout fcm:foo_tr $WORKINGCOPY
#-------------------------------------------------------------------------------
#Copy suite into working copy
cp $HERE/00-run-basic/suite.rc $WORKINGCOPY/rose-stem
touch $WORKINGCOPY/rose-stem/rose-suite.conf
#We should now have a valid rose-stem suite.
#-------------------------------------------------------------------------------
N_TESTS=15
tests $N_TESTS
#-------------------------------------------------------------------------------
#Test for successful execution
TEST_KEY=$TEST_KEY_BASE-basic-check
run_pass "$TEST_KEY" \
   rose stem --group=earl_grey --source=$WORKINGCOPY --source=fcm:foo_tr@head --no-gcontrol
sleep $DELAY
#Test output
OUTPUT=$HOME/cylc-run/foo_trunk/log/job/my_task_1.1.1.out
TEST_KEY=$TEST_KEY_BASE-basic-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[earl_grey\]" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source
file_grep $TEST_KEY "SOURCE_FOO=$WORKINGCOPY $URL/trunk@head" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=$WORKINGCOPY\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=\$" $OUTPUT
#-------------------------------------------------------------------------------
# Second test, using suite redirection
TEST_KEY=$TEST_KEY_BASE-suite-redirection
run_pass "$TEST_KEY" \
   rose stem --group=earl_grey -C $WORKINGCOPY/rose-stem --source=fcm:foo_tr@head --no-gcontrol
sleep $DELAY
#Test output
OUTPUT=$HOME/cylc-run/foo_trunk/log/job/my_task_1.1.1.out
TEST_KEY=$TEST_KEY_BASE-suite-redirection-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[earl_grey\]" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-suite-redirection-source
file_grep $TEST_KEY "SOURCE_FOO=$URL/trunk@head\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-suite-redirection-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=fcm:foo_tr\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-suite-redirection-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=@1\$" $OUTPUT
#-------------------------------------------------------------------------------
# Third test, checking subdirectory is working
TEST_KEY=$TEST_KEY_BASE-subdirectory
run_pass "$TEST_KEY" \
   rose stem --group=earl_grey --source=$WORKINGCOPY/rose-stem --no-gcontrol
sleep $DELAY
#Test output
OUTPUT=$HOME/cylc-run/foo_trunk/log/job/my_task_1.1.1.out
TEST_KEY=$TEST_KEY_BASE-subdirectory-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[earl_grey\]" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-subdirectory-source
file_grep $TEST_KEY "SOURCE_FOO=$WORKINGCOPY" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-subdirectory-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=$WORKINGCOPY\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-subdirectory-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=\$" $OUTPUT
#-------------------------------------------------------------------------------
#Remove repository working copy
rm -rf $WORKINGCOPY
#-------------------------------------------------------------------------------
#Tidy up keyword.cfg - remove foo repository which is the last line
sed -i '$d' $HOME/.metomi/fcm/keyword.cfg
#-------------------------------------------------------------------------------
exit 0
