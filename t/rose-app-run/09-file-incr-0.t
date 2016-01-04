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
# Test "rose app-run", generation of files in incremental mode (0).
# Basic tests: Null change and minor changes.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
# mode=auto, source is a file
mkdir $TEST_DIR/hello
echo "Fred" >$TEST_DIR/hello/stranger1.txt
echo "Freddie" >$TEST_DIR/hello/stranger1.1.txt
# mode=auto, source is a directory
mkdir $TEST_DIR/hello/stranger2
echo "Bob" >$TEST_DIR/hello/stranger2/person1.txt
echo "Alice" >$TEST_DIR/hello/stranger2/person2.txt
# mode=auto, source is a list of files
mkdir $TEST_DIR/hello/plants
echo "Heather" >$TEST_DIR/hello/plants/heather.txt
echo "Fern" >$TEST_DIR/hello/plants/fern.txt
echo "Holly" >$TEST_DIR/hello/plants/holly.txt
# mode=auto, source is a list of directories
mkdir -p $TEST_DIR/hello/animals/{mammals,birds}
echo "cow" >$TEST_DIR/hello/animals/mammals/cow.txt
echo "pig" >$TEST_DIR/hello/animals/mammals/pig.txt
echo "pigeon" >$TEST_DIR/hello/animals/birds/pigeon.txt
echo "duck" >$TEST_DIR/hello/animals/birds/duck.txt
# mode=symlink
mkdir -p $TEST_DIR/hello/man/man1
echo "Hello Manual..." >$TEST_DIR/hello/man/man1/hello.1

test_init <<__CONFIG__
[command]
default=true

[file:hello/nobody]
source=

[file:hello/stranger1.txt]
source=$TEST_DIR/hello/stranger1.txt

[file:hello/stranger2]
source=$TEST_DIR/hello/stranger2

[file:hello/plants.txt]
source=$TEST_DIR/hello/plants/*.txt

[file:hello/animals]
source=$TEST_DIR/hello/animals/*

[file:hello/etc]
mode=mkdir

[file:hello/man/man1]
source=$TEST_DIR/hello/man/man1
mode=symlink
__CONFIG__

mkdir config/opt
cat >config/opt/rose-app-1.1.conf <<__CONFIG__
[file:hello/stranger1.txt]
source=$TEST_DIR/hello/stranger1.1.txt
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
TEST_KEY="$TEST_KEY_BASE-change-content"
test_setup
rose app-run --config=../config -q || exit 1
find hello -type f | LANG=C sort >'find-hello-before.out'
touch timeline # Only changes updated after "timeline"
sleep 1
echo "Bob" >$TEST_DIR/hello/stranger1.txt
echo "chicken" >$TEST_DIR/hello/animals/birds/chicken.txt
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
exit
