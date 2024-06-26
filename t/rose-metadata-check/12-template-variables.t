#!/usr/bin/env bash
#-------------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
# Test "rose metadata-check":
# Check that hack allowing section name [template variables] works.
# Follows example in https://github.com/metomi/rose/issues/2737

. $(dirname $0)/test_header

CHECKS=(
    "basic@template variables=FOO == 2"
    # Check we don't need to deal with loop: Number-like-strings into numbers.
    "num string@template variables=FOO == \"2e1\""
    # Check we don't need to deal with loop: Strings into proper string variables.
    "str@template variables=FOO == \"Sir Topham Hat\""
    "amy@any(template variables=FOO == 2)"
    "len@len(template variables=FOO) > 42"
    "in list@template variables=FOO in [3, 4, 8]"
    "combined@len(template variables=FOO) > 42 and any(template variables=FOO == 2)"
    )


# 3 tests for each case:
tests $(( ${#CHECKS[@]} * 5 ))

setup

mkdir -p ../meta

# Allows array members to have spaces without splitting:
for ((i = 0; i < ${#CHECKS[@]}; i++)); do
    ID=$(echo "${CHECKS[$i]}" | awk -F '@' '{print $1}')
    CHECK_=$(echo "${CHECKS[$i]}" | awk -F '@' '{print $2}')

    TEST_KEY="$TEST_KEY_BASE::${ID}"
    cat > ../meta/rose-meta.conf <<__META_CONFIG__
[template variables=FOO]
fail-if=${CHECK_}
trigger=template variables=BAR: this == 1;

[template variables=BAR]
__META_CONFIG__

    cat > ../rose-app.conf <<__ICI__
[template variables]
FOO=1
!BAR=22
__ICI__

    run_pass "$TEST_KEY" rose metadata-check -C ../meta
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
    file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
    # Also covers upgrade macros, because these subclass
    # --transform macros:
    run_pass \
        "$TEST_KEY.macro --transform" \
        rose macro --transform -y -C ../
    run_pass \
        "$TEST_KEY.macro --validate" \
        rose macro --validate -C ../

done

teardown
