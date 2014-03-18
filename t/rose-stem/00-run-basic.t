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
# Test "rose stem" without site/user configuration
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
if ! fcm --version 1>/dev/null 2>&1; then
    skip_all 'FCM not installed'
fi
#-------------------------------------------------------------------------------
#Create repository to run on
REPO=$PWD/rose-test-battery-stemtest-repo
mkdir -p $REPO
svnadmin create $REPO/foo
URL=file://$REPO/foo
BASEINSTALL=$(mktemp -d --tmpdir=$PWD)
(cd $BASEINSTALL; mkdir -p trunk/rose-stem; svn import -q -m ""  $URL)
cd $TEST_DIR
#-------------------------------------------------------------------------------
#Set up a keyword in the user's fcm keywords file (will delete later)
#This should be replaced by the functionality in FCM:#105 when that is the 
#site default.
mkdir -p $HOME/.metomi/fcm
cat >> $HOME/.metomi/fcm/keyword.cfg << __EOF__
location{primary}[foo] = $URL
__EOF__
#-------------------------------------------------------------------------------
#Check out a copy of the repository
WORKINGCOPY=$(mktemp -d --tmpdir=$PWD)
SUITENAME=$(basename $WORKINGCOPY)
fcm checkout -q fcm:foo_tr $WORKINGCOPY
#-------------------------------------------------------------------------------
#Copy suite into working copy
cp $TEST_SOURCE_DIR/00-run-basic/suite.rc $WORKINGCOPY/rose-stem
touch $WORKINGCOPY/rose-stem/rose-suite.conf
#We should now have a valid rose-stem suite.
#-------------------------------------------------------------------------------
N_TESTS=20
tests $N_TESTS
#-------------------------------------------------------------------------------
#Test for successful execution
TEST_KEY=$TEST_KEY_BASE-basic-check
run_pass "$TEST_KEY" \
   rose stem --group=earl_grey --source=$WORKINGCOPY --source=fcm:foo_tr@head \
             --no-gcontrol --name $SUITENAME -- --debug
#Test output
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/my_task_1.1.1.out
TEST_KEY=$TEST_KEY_BASE-basic-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[earl_grey\]" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source
file_grep $TEST_KEY "SOURCE_FOO=$WORKINGCOPY fcm:foo_tr@head" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=$WORKINGCOPY\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=\$" $OUTPUT
#-------------------------------------------------------------------------------
# Second test, using suite redirection
TEST_KEY=$TEST_KEY_BASE-suite-redirection
run_pass "$TEST_KEY" \
   rose stem --group=lapsang -C $WORKINGCOPY/rose-stem --source=fcm:foo_tr@head\
             --no-gcontrol --name $SUITENAME -- --debug
#Test output
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/my_task_1.1.1.out
TEST_KEY=$TEST_KEY_BASE-suite-redirection-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[lapsang\]" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-suite-redirection-source
file_grep $TEST_KEY "SOURCE_FOO=fcm:foo_tr@head\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-suite-redirection-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=fcm:foo_tr\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-suite-redirection-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=@1\$" $OUTPUT
#-------------------------------------------------------------------------------
# Third test, checking subdirectory is working
TEST_KEY=$TEST_KEY_BASE-subdirectory
run_pass "$TEST_KEY" \
   rose stem --group=assam --source=$WORKINGCOPY/rose-stem --no-gcontrol \
             --name $SUITENAME -- --debug
#Test output
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/my_task_1.1.1.out
TEST_KEY=$TEST_KEY_BASE-subdirectory-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[assam\]" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-subdirectory-source
file_grep $TEST_KEY "SOURCE_FOO=$WORKINGCOPY" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-subdirectory-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=$WORKINGCOPY\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-subdirectory-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=\$" $OUTPUT
#-------------------------------------------------------------------------------
# Fourth test, checking relative path with -C is working
TEST_KEY=$TEST_KEY_BASE-relative-path
cd $WORKINGCOPY
run_pass "$TEST_KEY" \
   rose stem --group=ceylon -C rose-stem \
             --no-gcontrol --name $SUITENAME -- --debug
#Test output
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/my_task_1.1.1.out
cp $OUTPUT ~/thingy
TEST_KEY=$TEST_KEY_BASE-relative-path-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[ceylon\]" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-relative-path-source
file_grep $TEST_KEY "SOURCE_FOO=$WORKINGCOPY" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-relative-path-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=$WORKINGCOPY\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-relative-path-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=\$" $OUTPUT
#-------------------------------------------------------------------------------
cd $TEST_DIR
#-------------------------------------------------------------------------------
#Tidy up keyword.cfg - remove foo repository which is the last line
sed -i '$d' $HOME/.metomi/fcm/keyword.cfg
#-------------------------------------------------------------------------------
#Clean suite
rose suite-clean -q -y $SUITENAME
#-------------------------------------------------------------------------------
exit 0
