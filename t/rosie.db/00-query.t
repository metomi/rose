#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
# Test rosie.db parsing.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
TEST_PARSER="python3 $TEST_SOURCE_DIR/$TEST_KEY_BASE.py"
#-------------------------------------------------------------------------------
if ! python3 -c 'import sqlalchemy' 2>/dev/null; then
    skip_all '"sqlalchemy" not installed'
fi
tests 21
#-------------------------------------------------------------------------------
# Easy query.
TEST_KEY=$TEST_KEY_BASE-easy-query
run_pass "$TEST_KEY" $TEST_PARSER '[["and", "description", "eq", "shiny"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------

# Two filter query.
TEST_KEY=$TEST_KEY_BASE-double-query
run_pass "$TEST_KEY" $TEST_PARSER \
    '[["and", "description", "eq", "shiny"], ["or", "title", "eq", "Something"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------

# Three filter query.
TEST_KEY=$TEST_KEY_BASE-triple-query
run_pass "$TEST_KEY" $TEST_PARSER \
    '[["and", "description", "eq", "shiny"],
      ["or", "title", "eq", "Something"],
      ["and", "simulation", "contains", "Matrix"]]'
sed -i 's/%%/%/g' "${TEST_KEY}.out"
file_cmp_any "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1 AND optional.name = :name_2 AND optional.value LIKE '%' || :value_2 || '%'
__filesep__
optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1 AND optional.name = :name_2 AND (optional.value LIKE '%' || :value_2 || '%')
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------

# Null grouped query.
TEST_KEY=$TEST_KEY_BASE-null-group-query
run_pass "$TEST_KEY" $TEST_PARSER \
    '[["and", "(", "description", "eq", "shiny", ")"]]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------

# Simple grouped query.
TEST_KEY=$TEST_KEY_BASE-simple-group-query
run_pass "$TEST_KEY" $TEST_PARSER \
    '[["and", "(", "description", "eq", "shiny"],
      ["or", "title", "eq", "Something", ")"],
      ["and", "simulation", "contains", "Matrix"]]'
sed -i 's/%%/%/g' "${TEST_KEY}.out"
file_cmp_any "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
(optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1) AND optional.name = :name_2 AND optional.value LIKE '%' || :value_2 || '%'
__filesep__
(optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1) AND optional.name = :name_2 AND (optional.value LIKE '%' || :value_2 || '%')
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------

# Complex grouped query.
TEST_KEY=$TEST_KEY_BASE-complex-group-query
run_pass "$TEST_KEY" $TEST_PARSER \
    '[["and", "description", "eq", "shiny"],
      ["or", "title", "eq", "Something"],
      ["and", "(", "owner", "eq", "bfitz"],
      ["or", "owner", "eq", "frbj", ")"],
      ["or", "((", "author", "contains", "fr"],
      ["or", "revision", "lt", "100", ")"],
      ["or", "title", "contains", "x", ")"]]'
sed -i 's/%%/%/g' "${TEST_KEY}.out"
file_cmp_any "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1 AND (main.owner = :owner_1 OR main.owner = :owner_2) OR main.author LIKE '%' || :author_1 || '%' OR latest.revision < :revision_1 OR main.title LIKE '%' || :title_2 || '%'
__filesep__
optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1 AND (main.owner = :owner_1 OR main.owner = :owner_2) OR (main.author LIKE '%' || :author_1 || '%') OR latest.revision < :revision_1 OR (main.title LIKE '%' || :title_2 || '%')
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------

# Very complex grouped query.
TEST_KEY=$TEST_KEY_BASE-complex-group-query
run_pass "$TEST_KEY" $TEST_PARSER \
    '[["and", "(", "description", "eq", "shiny"],
      ["or", "(", "title", "eq", "Something"],
      ["or", "title", "eq", "Something Else", "))"],
      ["and", "(", "owner", "eq", "bfitz"],
      ["or", "owner", "eq", "frbj", ")"],
      ["or", "((", "author", "contains", "fr"],
      ["or", "revision", "lt", "100", ")"],
      ["and", "title", "eq", "x", ")"]]'
sed -i 's/%%/%/g' "${TEST_KEY}.out"
file_cmp_any "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
(optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1 OR main.title = :title_2) AND (main.owner = :owner_1 OR main.owner = :owner_2) OR (main.author LIKE '%' || :author_1 || '%' OR latest.revision < :revision_1) AND main.title = :title_3
__filesep__
(optional.name = :name_1 AND optional.value = :value_1 OR main.title = :title_1 OR main.title = :title_2) AND (main.owner = :owner_1 OR main.owner = :owner_2) OR ((main.author LIKE '%' || :author_1 || '%') OR latest.revision < :revision_1) AND main.title = :title_3
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
exit
