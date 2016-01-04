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
# Test "rose app-run", generation of files in incremental mode (1).
# Remote host sources.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -z $JOB_HOST ]]; then
    skip_all '"[t]job-host" not defined'
fi
#-------------------------------------------------------------------------------
tests 9
#-------------------------------------------------------------------------------
set -e
JOB_HOST=$(rose host-select -q $JOB_HOST)
JOB_HOST_TEST_DIR=$(ssh -oBatchMode=yes $JOB_HOST 'TMPDIR=$HOME mktemp -d')
JOB_HOST_TEST_DIR=$(tail -1 <<<"$JOB_HOST_TEST_DIR")
MY_FINALLY() {
    FINALLY "$@"
    ssh -oBatchMode=yes $JOB_HOST \
        "bash -l -c 'rm -r $JOB_HOST_TEST_DIR'" 1>/dev/null 2>&1
}
for S in $SIGNALS; do
    trap "MY_FINALLY $S" $S
done
#-------------------------------------------------------------------------------
# mode=auto, source is a file
mkdir hello
echo "Fred" >hello/stranger1.txt
echo "Freddie" >hello/stranger1.1.txt
# mode=auto, source is a directory
mkdir hello/stranger2
echo "Bob" >hello/stranger2/person1.txt
echo "Alice" >hello/stranger2/person2.txt
mkdir hello/stranger2/persons
echo "Holly" >hello/stranger2/persons/person3.txt
echo "Alex" >hello/stranger2/persons/person4.txt
# mode=auto, source is a list of files
mkdir hello/plants
echo "Heather" >hello/plants/heather.txt
echo "Fern" >hello/plants/fern.txt
echo "Holly" >hello/plants/holly.txt
# mode=auto, source is a list of directories
mkdir -p hello/animals/{mammals,birds}
echo "cow" >hello/animals/mammals/cow.txt
echo "pig" >hello/animals/mammals/pig.txt
echo "pigeon" >hello/animals/birds/pigeon.txt
echo "duck" >hello/animals/birds/duck.txt

rsync -a hello $JOB_HOST:$JOB_HOST_TEST_DIR/
set +e

test_init <<__CONFIG__
[command]
default=true

[file:hello/stranger1.txt]
source=$JOB_HOST:$JOB_HOST_TEST_DIR/hello/stranger1.txt

[file:hello/stranger2]
source=$JOB_HOST:$JOB_HOST_TEST_DIR/hello/stranger2

[file:hello/plants.txt]
source=$JOB_HOST:$JOB_HOST_TEST_DIR/hello/plants/heather.txt
      =$JOB_HOST:$JOB_HOST_TEST_DIR/hello/plants/fern.txt
      =$JOB_HOST:$JOB_HOST_TEST_DIR/hello/plants/holly.txt

[file:hello/animals]
source=$JOB_HOST:$JOB_HOST_TEST_DIR/hello/animals/birds
       $JOB_HOST:$JOB_HOST_TEST_DIR/hello/animals/mammals
__CONFIG__

mkdir config/opt
cat >config/opt/rose-app-1.1.conf <<__CONFIG__
[file:hello/stranger1.txt]
source=$JOB_HOST:$JOB_HOST_TEST_DIR/hello/stranger1.1.txt
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-null-change"
test_setup
rose app-run --config=../config -q || exit 1
find hello -type f | LANG=C sort >'find-hello-before.out'
touch timeline # Nothing should be created after "timeline"
sleep 1
run_pass "$TEST_KEY" rose app-run --config=../config -q
find hello -type f | LANG=C sort >'find-hello-after.out'
file_cmp "$TEST_KEY.find-hello" 'find-hello-before.out' 'find-hello-after.out'
find hello -type f -newer timeline | LANG=C sort >'find-hello-after-newer.out'
file_cmp "$TEST_KEY.find-hello-newer" 'find-hello-after-newer.out' </dev/null
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-change-source"
test_setup
rose app-run --config=../config -q || exit 1
find hello -type f | LANG=C sort >'find-hello-before.out'
touch timeline # Only changes updated after "timeline"
sleep 1
run_pass "$TEST_KEY" rose app-run --config=../config -O1.1 -q
find hello -type f | LANG=C sort >'find-hello-after.out'
file_cmp "$TEST_KEY.find-hello" 'find-hello-before.out' 'find-hello-after.out'
find hello -type f -newer timeline | LANG=C sort >'find-hello-after-newer.out'
file_cmp "$TEST_KEY.find-hello-newer" 'find-hello-after-newer.out' <<'__OUT__'
hello/stranger1.txt
__OUT__
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-change-content"
test_setup
rose app-run --config=../config -q || exit 1
find hello -type f | LANG=C sort >'find-hello-before.out'
touch timeline # Only changes updated after "timeline"
sleep 1
set -e
echo "Bob" >$TEST_DIR/hello/stranger1.txt
echo "chicken" >$TEST_DIR/hello/animals/birds/chicken.txt
rsync -a $TEST_DIR/hello $JOB_HOST:$JOB_HOST_TEST_DIR/
set +e
run_pass "$TEST_KEY" rose app-run --config=../config -q
find hello -type f | LANG=C sort >'find-hello-after.out'
{
    echo 'hello/animals/chicken.txt'
    cat 'find-hello-before.out'
} >'find-hello-after-expected.out'
file_cmp "$TEST_KEY.find-hello" \
    'find-hello-after-expected.out' 'find-hello-after.out'
find hello -type f -newer timeline | LANG=C sort >'find-hello-after-newer.out'
file_cmp "$TEST_KEY.find-hello-newer" 'find-hello-after-newer.out' <<'__OUT__'
hello/animals/chicken.txt
hello/stranger1.txt
__OUT__
test_teardown
#-------------------------------------------------------------------------------
exit
