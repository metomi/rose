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
# Test "rose config", basic usage.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
FILE=$PWD/rose-t.conf
cat >$FILE <<'__CONF__'
# Location
#
# London
location=London

# London bus
[bus]
decks=2
colour=red
name=Routemaster

# London taxi
[taxi]
colour=black
name=Hackney Carriage
!decks=1

[]
greeting=Hello
my-home=$HOME

[!tram]
colour=green
__CONF__
#-------------------------------------------------------------------------------
tests 69
#-------------------------------------------------------------------------------
# Empty file.
TEST_KEY=$TEST_KEY_BASE-empty
setup
run_pass "$TEST_KEY" rose config -f /dev/null
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Empty file, quiet, no such item.
TEST_KEY=$TEST_KEY_BASE-empty-q-no-such-item
setup
run_fail "$TEST_KEY" rose config -f /dev/null -q foo bar
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Empty file, no such item.
TEST_KEY=$TEST_KEY_BASE-empty-no-such-item
setup
run_fail "$TEST_KEY" rose config -f /dev/null foo bar
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Empty file, no such item, default.
TEST_KEY=$TEST_KEY_BASE-empty-no-such-item-default
setup
run_pass "$TEST_KEY" rose config -f /dev/null --default=baz foo bar
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
baz
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Dump file.
TEST_KEY=$TEST_KEY_BASE-dump
setup
run_pass "$TEST_KEY" rose config -f $FILE
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
# Location
#
# London

greeting=Hello
location=London
my-home=$HOME

# London bus
[bus]
colour=red
decks=2
name=Routemaster

# London taxi
[taxi]
colour=black
!decks=1
name=Hackney Carriage

[!tram]
colour=green
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value at root level.
TEST_KEY=$TEST_KEY_BASE-value-root
setup
run_pass "$TEST_KEY" rose config -f $FILE greeting
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
Hello
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value at root level, print-conf.
TEST_KEY=$TEST_KEY_BASE-value-root--print-conf
setup
run_pass "$TEST_KEY" rose config -f $FILE --print-conf greeting
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[]
greeting=Hello
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value.
TEST_KEY=$TEST_KEY_BASE-value
setup
run_pass "$TEST_KEY" rose config -f $FILE bus colour
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
red
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value.
TEST_KEY=$TEST_KEY_BASE-value--print-conf
setup
run_pass "$TEST_KEY" rose config -f $FILE --print-conf bus colour
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[bus]
colour=red
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value, ignored.
TEST_KEY=$TEST_KEY_BASE-value-ignored
setup
run_fail "$TEST_KEY" rose config -f $FILE taxi decks
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value, ignored, default.
TEST_KEY=$TEST_KEY_BASE-value-ignored-default
setup
run_pass "$TEST_KEY" rose config -f $FILE --default=-na- taxi decks
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
-na-
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value, ignored, default, --print-conf
TEST_KEY=$TEST_KEY_BASE-value-ignored-default--print-conf
setup
run_pass "$TEST_KEY" rose config -f $FILE --default=-na- --print-conf taxi decks
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[taxi]
decks=-na-
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value, ignored, print.
TEST_KEY=$TEST_KEY_BASE-value-ignored-print
setup
run_pass "$TEST_KEY" rose config -f $FILE -i taxi decks
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
1
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value, no-such-item.
TEST_KEY=$TEST_KEY_BASE-value-no-such-item
setup
run_fail "$TEST_KEY" rose config -f $FILE taxi oyster
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value, no-such-item.
TEST_KEY=$TEST_KEY_BASE-value-no-such-item--print-conf
setup
run_fail "$TEST_KEY" rose config -f $FILE --print-conf taxi oyster
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value, no-such-item, default.
TEST_KEY=$TEST_KEY_BASE-value-no-such-item-default
setup
run_pass "$TEST_KEY" rose config -f $FILE --default=false taxi oyster
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
false
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value, no-such-item, default, --print-conf.
TEST_KEY=$TEST_KEY_BASE-value-no-such-item-default--print-conf
setup
run_pass "$TEST_KEY" \
    rose config -f $FILE --print-conf --default=false taxi oyster
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[taxi]
oyster=false
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value with environment variable syntax.
TEST_KEY=$TEST_KEY_BASE-value-env
setup
run_pass "$TEST_KEY" rose config -f $FILE my-home
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
$HOME
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Value with environment variable syntax, processed.
TEST_KEY=$TEST_KEY_BASE-value-env-process
setup
run_pass "$TEST_KEY" rose config -f $FILE -E my-home
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$HOME
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Root keys
TEST_KEY=$TEST_KEY_BASE-keys
setup
run_pass "$TEST_KEY" rose config -f $FILE --keys
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
bus
greeting
location
my-home
taxi
tram
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Keys in section
TEST_KEY=$TEST_KEY_BASE-keys-section
setup
run_pass "$TEST_KEY" rose config -f $FILE --keys taxi
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
colour
decks
name
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Non-ignored keys
TEST_KEY=$TEST_KEY_BASE-section-with-ignored-option
setup
run_pass "$TEST_KEY" rose config -f $FILE taxi
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
colour=black
name=Hackney Carriage
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Non-ignored keys
TEST_KEY=$TEST_KEY_BASE-section-with-ignored-option--print-conf
setup
run_pass "$TEST_KEY" rose config -f $FILE --print-conf taxi
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[taxi]
colour=black
!decks=1
name=Hackney Carriage
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit 0
