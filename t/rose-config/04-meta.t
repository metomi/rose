#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
#
# This file is part of Rose, a framework for scientific suites.
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
# Test "rose config --meta" usage.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
FILE=$PWD/rose-app.conf
touch $FILE
META_DIR=$PWD/meta
#-------------------------------------------------------------------------------
tests 18
#-------------------------------------------------------------------------------
# No metadata for this file.
TEST_KEY=$TEST_KEY_BASE-no-metadata
setup
run_pass "$TEST_KEY" rose config -f $FILE --meta
cat $TEST_KEY.out >/dev/tty
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
mkdir $META_DIR
cat >$META_DIR/rose-meta.conf <<'__CONF__'
[coffee=l_milk]
description=Add milk?
type=logical
__CONF__
# Some metadata for the file.
TEST_KEY=$TEST_KEY_BASE-metadata-all
setup
run_pass "$TEST_KEY" rose config -f $FILE --meta
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" $META_DIR/rose-meta.conf
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Specific metadata section.
TEST_KEY=$TEST_KEY_BASE-metadata-section
setup
run_pass "$TEST_KEY" rose config -f $FILE --meta coffee=l_milk
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
description=Add milk?
type=logical
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Specific metadata section, option.
TEST_KEY=$TEST_KEY_BASE-metadata-section-option
setup
run_pass "$TEST_KEY" rose config -f $FILE --meta coffee=l_milk type
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
logical
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Specific metadata section (not found)
TEST_KEY=$TEST_KEY_BASE-metadata-section-no-such-section
setup
run_fail "$TEST_KEY" rose config -f $FILE --meta coffee=l_sugar
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Specific metadata section, option (not found)
TEST_KEY=$TEST_KEY_BASE-metadata-section-option-no-such-option
setup
run_fail "$TEST_KEY" rose config -f $FILE --meta coffee=l_milk title
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit 0
