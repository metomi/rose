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
# SVN sources.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

# mode=auto, source is a file
mkdir hello
echo "Fred" >hello/stranger1.txt
echo "Freddie" >hello/stranger1.1.txt
# mode=auto, source is a directory
mkdir hello/stranger2
echo "Bob" >hello/stranger2/person1.txt
echo "Alice" >hello/stranger2/person2.txt
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

set -e
mkdir repos
svnadmin create repos/foo
REPOS_ROOT=file://$PWD/repos/foo
svn import -q -m 'Import Hello' hello $REPOS_ROOT/hello
rm -rf hello
set +e

test_init <<__CONFIG__
[command]
default=true

[file:hello/stranger1.txt]
source=$REPOS_ROOT/hello/stranger1.txt

[file:hello/stranger2]
source=$REPOS_ROOT/hello/stranger2

[file:hello/plants.txt]
source=$REPOS_ROOT/hello/plants/heather.txt
      =$REPOS_ROOT/hello/plants/fern.txt
      =$REPOS_ROOT/hello/plants/holly.txt

[file:hello/animals]
source=$REPOS_ROOT/hello/animals/birds $REPOS_ROOT/hello/animals/mammals

[file:hello/etc]
mode=mkdir
__CONFIG__

mkdir config/opt
cat >config/opt/rose-app-1.1.conf <<__CONFIG__
[file:hello/stranger1.txt]
source=$REPOS_ROOT/hello/stranger1.1.txt
__CONFIG__
#-------------------------------------------------------------------------------
tests 9
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
svn co -q $REPOS_ROOT/hello $TEST_DIR/hello
echo "Bob" >$TEST_DIR/hello/stranger1.txt
echo "chicken" >$TEST_DIR/hello/animals/birds/chicken.txt
svn add -q $TEST_DIR/hello/animals/birds/chicken.txt
svn ci -q -m "$TEST_KEY" $TEST_DIR/hello
rm -rf $TEST_DIR/hello
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
