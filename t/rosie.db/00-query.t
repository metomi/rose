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
# Test rosie.db parsing.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init </dev/null
export PYTHONPATH=$PYTHONPATH:$(dirname $0)/../../lib/python:~fcm/lib/python
export ROSE_NS ROSE_UTIL ROSE_HOME
#-------------------------------------------------------------------------------
tests 21
#-------------------------------------------------------------------------------

# Easy query.
TEST_KEY=$TEST_KEY_BASE-easy-query
setup
run_pass "$TEST_KEY" parse_query '[["and", "description", "eq", "shiny"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Two filter query.
TEST_KEY=$TEST_KEY_BASE-double-query
setup
run_pass "$TEST_KEY" parse_query '[["and", "description", "eq", "shiny"], ["or", "title", "eq", "Something"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Three filter query.
TEST_KEY=$TEST_KEY_BASE-triple-query
setup
run_pass "$TEST_KEY" parse_query '[["and", "description", "eq", "shiny"], ["or", "title", "eq", "Something"], ["and", "simulation", "contains", "Matrix"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1 AND optional.name = :name_2 AND optional.value LIKE '%%' || :value_2 || '%%'
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Null grouped query.
TEST_KEY=$TEST_KEY_BASE-null-group-query
setup
run_pass "$TEST_KEY" parse_query '[["and", "(", "description", "eq", "shiny", ")"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Simple grouped query.
TEST_KEY=$TEST_KEY_BASE-simple-group-query
setup
run_pass "$TEST_KEY" parse_query '[["and", "(", "description", "eq", "shiny"], ["or", "title", "eq", "Something", ")"], ["and", "simulation", "contains", "Matrix"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
(optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1) AND optional.name = :name_2 AND optional.value LIKE '%%' || :value_2 || '%%'
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Complex grouped query.
TEST_KEY=$TEST_KEY_BASE-complex-group-query
setup
run_pass "$TEST_KEY" parse_query '[["and", "description", "eq", "shiny"], ["or", "title", "eq", "Something"], ["and", "(", "owner", "eq", "bfitz"], ["or", "owner", "eq", "frbj", ")"], ["or", "((", "author", "contains", "fr"], ["or", "revision", "lt", "100", ")"], ["or", "title", "contains", "x", ")"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1 AND (main.owner = :owner_1 OR main.owner = :owner_2) OR latest.author LIKE '%%' || :author_1 || '%%' OR latest.revision < :revision_1 OR main.title LIKE '%%' || :title_2 || '%%'
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Very complex grouped query.
TEST_KEY=$TEST_KEY_BASE-complex-group-query
setup
run_pass "$TEST_KEY" parse_query '[["and", "(", "description", "eq", "shiny"], ["or", "(", "title", "eq", "Something"], ["or", "title", "eq", "Something Else", "))"], ["and", "(", "owner", "eq", "bfitz"], ["or", "owner", "eq", "frbj", ")"], ["or", "((", "author", "contains", "fr"], ["or", "revision", "lt", "100", ")"], ["and", "title", "eq", "x", ")"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
(optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1 OR main.title = :title_2) AND (main.owner = :owner_1 OR main.owner = :owner_2) OR (latest.author LIKE '%%' || :author_1 || '%%' OR latest.revision < :revision_1) AND main.title = :title_3
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
