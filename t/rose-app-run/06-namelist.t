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
# Test "rose app-run", generation of files with namelists.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
test_init <<'__CONFIG__'
[command]
default = mkdir out && cp *.nl out/

[file:empty.nl]
source = namelist:empty

[file:hello.nl]
source = namelist:hello

[file:empty-and-hello.nl]
source = namelist:empty
         namelist:hello

[file:vegetables.nl]
source = namelist:vegetables{green}(:)

[file:shopping-list-2.nl]
source = namelist:shopping_list(10) namelist:shopping_list(1)

[file:shopping-list.nl]
source = namelist:shopping_list(:)

[namelist:empty]

[namelist:hello]
greeting = 'hi'
names = 'Fred','Bob','Alice','$USER'

[namelist:shopping_list(1)]
egg = 'free-range',12
bacon = 'back',6
beans = 2
bread = 1
milk = 4,2.0

[namelist:shopping_list(2)]
egg = 'organic',6
bacon = 'streaky',12
tomato = 4
bread = 2
butter = 5.0E-1

[namelist:shopping_list(10)]
butter = 5.0E-1
flour = 2.0
sugar = 1.0
milk = 2,0.5

[namelist:vegetables{green}(1)]
cabbage = 1
broccoli = 2
lime = 3
spinach = 4
mint = 5

[namelist:vegetables{green}(2)]
cabbage = 5
broccoli = 4
lime = 3
spinach = 2
mint = 1

[namelist:vegetables{red}]
beetroot = 1
radish = 2
red_onion = 3

[namelist:vegetables{orange}(1)]
carrot = 1
__CONFIG__
#-------------------------------------------------------------------------------
tests 21
#-------------------------------------------------------------------------------
# Normal mode with namelist files.
TEST_KEY=$TEST_KEY_BASE
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY: empty.nl" "out/empty.nl" <<'__CONTENT__'
&empty
/
__CONTENT__
file_cmp "$TEST_KEY: hello.nl" "out/hello.nl" <<__CONTENT__
&hello
greeting='hi',
names='Fred','Bob','Alice','$USER',
/
__CONTENT__
file_cmp "$TEST_KEY: empty-and-hello.nl" "out/empty-and-hello.nl" <<__CONTENT__
&empty
/
&hello
greeting='hi',
names='Fred','Bob','Alice','$USER',
/
__CONTENT__
file_cmp "$TEST_KEY: vegetables.nl" "out/vegetables.nl" <<'__CONTENT__'
&vegetables
broccoli=2,
cabbage=1,
lime=3,
mint=5,
spinach=4,
/
&vegetables
broccoli=4,
cabbage=5,
lime=3,
mint=1,
spinach=2,
/
__CONTENT__
file_cmp "$TEST_KEY: shopping-list-2.nl" "out/shopping-list-2.nl" <<'__CONTENT__'
&shopping_list
butter=5.0E-1,
flour=2.0,
milk=2,0.5,
sugar=1.0,
/
&shopping_list
bacon='back',6,
beans=2,
bread=1,
egg='free-range',12,
milk=4,2.0,
/
__CONTENT__
file_cmp "$TEST_KEY: shopping-list.nl" "out/shopping-list.nl" <<'__CONTENT__'
&shopping_list
bacon='back',6,
beans=2,
bread=1,
egg='free-range',12,
milk=4,2.0,
/
&shopping_list
bacon='streaky',12,
bread=2,
butter=5.0E-1,
egg='organic',6,
tomato=4,
/
&shopping_list
butter=5.0E-1,
flour=2.0,
milk=2,0.5,
sugar=1.0,
/
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Install-only mode with namelist files.
TEST_KEY=$TEST_KEY_BASE-install-only
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -i --debug
python3 -c "import re, sys
print(''.join(sorted(sys.stdin.readlines(),
                     key=re.compile('hello(\d+)').findall)).rstrip())" \
    <"$TEST_KEY.out" >"$TEST_KEY.sorted.out"
cat > "$TEST_KEY.out.control" <<__CONTENT__
[INFO] export PATH=$PATH
[INFO] install: vegetables.nl
[INFO]     source: namelist:vegetables{green}(:)
[INFO] install: shopping-list.nl
[INFO]     source: namelist:shopping_list(:)
[INFO] install: shopping-list-2.nl
[INFO]     source: namelist:shopping_list(10)
[INFO]     source: namelist:shopping_list(1)
[INFO] install: hello.nl
[INFO]     source: namelist:hello
[INFO] install: empty.nl
[INFO]     source: namelist:empty
[INFO] install: empty-and-hello.nl
[INFO]     source: namelist:empty
[INFO]     source: namelist:hello
[INFO] command: mkdir out && cp *.nl out/
__CONTENT__
python3 -c "import re, sys
print(''.join(sorted(sys.stdin.readlines(),
                     key=re.compile('hello(\d+)').findall)).rstrip())" \
    <"$TEST_KEY.out.control" >"$TEST_KEY.sorted.out.control"
file_cmp "$TEST_KEY.sorted.out" "$TEST_KEY.sorted.out.control"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with file referencing a non-existent namelist.
TEST_KEY=$TEST_KEY_BASE-non-existent
test_setup
run_fail "$TEST_KEY" rose app-run --config=../config -q \
    '--define=[file:shopping-list-3.nl]source=namelist:shopping_list'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] file:shopping-list-3.nl=source=namelist:shopping_list: bad or missing value
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with file referencing an ignored namelist section.
TEST_KEY=$TEST_KEY_BASE-ignored
test_setup
run_fail "$TEST_KEY" rose app-run --config=../config -q \
    '--define=[file:shopping-list-3.nl]source=namelist:shopping_list' \
    '--define=[!namelist:shopping_list]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] file:shopping-list-3.nl=source=namelist:shopping_list: bad or missing value
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with namelist referencing an unbound environment variable.
TEST_KEY=$TEST_KEY_BASE-unbound-variable
test_setup
unset NO_SUCH_VARIABLE
run_fail "$TEST_KEY" rose app-run --config=../config -q \
    '--define=[namelist:hello]greeting=$NO_SUCH_VARIABLE'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] namelist:hello=greeting: NO_SUCH_VARIABLE: unbound variable
[FAIL] source: namelist:hello
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
exit
