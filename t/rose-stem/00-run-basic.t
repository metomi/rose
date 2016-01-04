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
# Test "rose stem" without site/user configuration
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
if ! fcm --version 1>/dev/null 2>&1; then
    skip_all '"FCM" not installed'
fi
#-------------------------------------------------------------------------------
#Create repository to run on
REPO=$PWD/rose-test-battery-stemtest-repo
mkdir -p $REPO
svnadmin create $REPO/foo
URL=file://$REPO/foo
BASEINSTALL=$(mktemp -d --tmpdir=$PWD)
(cd $BASEINSTALL; mkdir -p trunk/rose-stem; svn import -q -m ""  $URL)
#Keywords for the foo repository
mkdir -p conf
echo "location{primary}[foo.x]=$URL" >conf/keyword.cfg
export FCM_CONF_PATH=$PWD/conf
cd $TEST_DIR
#-------------------------------------------------------------------------------
#Check out a copy of the repository
WORKINGCOPY=$(mktemp -d --tmpdir=$PWD)
SUITENAME=$(basename $WORKINGCOPY)
fcm checkout -q fcm:foo.x_tr $WORKINGCOPY
#-------------------------------------------------------------------------------
#Copy suite into working copy
cp $TEST_SOURCE_DIR/00-run-basic/suite.rc $WORKINGCOPY/rose-stem
cp $TEST_SOURCE_DIR/00-run-basic/rose-suite.conf $WORKINGCOPY/rose-stem
touch $WORKINGCOPY/rose-stem/rose-suite.conf
#We should now have a valid rose-stem suite.
#-------------------------------------------------------------------------------
N_TESTS=32
tests $N_TESTS
#-------------------------------------------------------------------------------
#Test for successful execution
TEST_KEY=$TEST_KEY_BASE-basic-check
run_pass "$TEST_KEY" \
   rose stem --group=earl_grey --task=milk,sugar --group=spoon,cup,milk \
             --source=$WORKINGCOPY --source=fcm:foo.x_tr@head --no-gcontrol \
             --name $SUITENAME -- --debug
#Test output
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/1/my_task_1/01/job.out
TEST_KEY=$TEST_KEY_BASE-basic-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[earl_grey, milk, sugar, spoon, cup, milk\]" \
          $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source
file_grep $TEST_KEY "SOURCE_FOO=$WORKINGCOPY fcm:foo.x_tr@head" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=$WORKINGCOPY\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-basic-source-mirror
file_grep $TEST_KEY "SOURCE_FOO_MIRROR=fcm:foo.xm/trunk@1\$" $OUTPUT
#-------------------------------------------------------------------------------
# Second test, using suite redirection
TEST_KEY=$TEST_KEY_BASE-suite-redirection
run_pass "$TEST_KEY" \
   rose stem --group=lapsang -C $WORKINGCOPY/rose-stem --source=fcm:foo.x_tr@head\
             --no-gcontrol --name $SUITENAME -- --debug
#Test output
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/1/my_task_1/01/job.out
TEST_KEY=$TEST_KEY_BASE-suite-redirection-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[lapsang\]" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-suite-redirection-source
file_grep $TEST_KEY "SOURCE_FOO=fcm:foo.x_tr@head\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-suite-redirection-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=fcm:foo.x_tr\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-suite-redirection-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=@1\$" $OUTPUT
#-------------------------------------------------------------------------------
# Third test, checking subdirectory is working
TEST_KEY=$TEST_KEY_BASE-subdirectory
run_pass "$TEST_KEY" \
   rose stem --group=assam --source=$WORKINGCOPY/rose-stem --no-gcontrol \
             --name $SUITENAME -- --debug
#Test output
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/1/my_task_1/01/job.out
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
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/1/my_task_1/01/job.out
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
# Test "rose stem" with site/user configuration
export ROSE_CONF_PATH=$TEST_DIR
cat > rose.conf << EOF
[rose-stem]
automatic-options=MILK=true
EOF
#-------------------------------------------------------------------------------
# Fifth test - for successful execution with site/user configuration
TEST_KEY=$TEST_KEY_BASE-check-with-config
run_pass "$TEST_KEY" \
   rose stem --group=earl_grey --task=milk,sugar --group=spoon,cup,milk \
             --source=$WORKINGCOPY --source=fcm:foo.x_tr@head --no-gcontrol \
             --name $SUITENAME -- --debug
#Test output
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/1/my_task_1/01/job.out
TEST_KEY=$TEST_KEY_BASE-check-with-config-groups-to-run
file_grep $TEST_KEY "RUN_NAMES=\[earl_grey, milk, sugar, spoon, cup, milk\]" \
          $OUTPUT
TEST_KEY=$TEST_KEY_BASE-check-with-config-source
file_grep $TEST_KEY "SOURCE_FOO=$WORKINGCOPY fcm:foo.x_tr@head" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-check-with-config-source-base
file_grep $TEST_KEY "SOURCE_FOO_BASE=$WORKINGCOPY\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-check-with-config-source-rev
file_grep $TEST_KEY "SOURCE_FOO_REV=\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-check-with-config-single-auto-option
file_grep $TEST_KEY "MILK=true\$" $OUTPUT
#-------------------------------------------------------------------------------
# Sixth test - multiple automatic-options in the site/user configuration
cat > rose.conf << EOF
[rose-stem]
automatic-options=MILK=true TEA=darjeeling
EOF
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-check-with-config
run_pass "$TEST_KEY" \
   rose stem --group=assam --source=$WORKINGCOPY/rose-stem --no-gcontrol \
             --name $SUITENAME -- --debug
#Test output
OUTPUT=$HOME/cylc-run/$SUITENAME/log/job/1/my_task_1/01/job.out
TEST_KEY=$TEST_KEY_BASE-multi-auto-config-first
file_grep $TEST_KEY "MILK=true\$" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-multi-auto-config-second
file_grep $TEST_KEY "TEA=darjeeling\$" $OUTPUT
#-------------------------------------------------------------------------------
# Seventh test - check incompatible rose-stem versions
cp $TEST_SOURCE_DIR/00-run-basic/rose-suite2.conf $WORKINGCOPY/rose-stem/rose-suite.conf
TEST_KEY=$TEST_KEY_BASE-incompatible_versions
run_fail "$TEST_KEY" \
   rose stem --group=earl_grey --task=milk,sugar --group=spoon,cup,milk \
             --source=$WORKINGCOPY --source=fcm:foo.x_tr@head --no-gcontrol \
             --name $SUITENAME -- --debug 
OUTPUT=$TEST_DIR/${TEST_KEY}.err
TEST_KEY=$TEST_KEY_BASE-incompatible-versions-correct_error
file_grep $TEST_KEY "Running rose-stem version 1 but suite is at version 0" $OUTPUT
#-------------------------------------------------------------------------------
#Clean suite
rose suite-clean -q -y $SUITENAME
#-------------------------------------------------------------------------------
exit 0
