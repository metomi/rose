#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
# Test "rose app-run", alternate command keys.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
USER=${USER:-$(whoami)}
init <<__CONFIG__
[command]
default = true
false = false
hello-world = hello
hello-user = hello $USER
__CONFIG__
mkdir $PWD/config/bin
cat > $PWD/config/bin/hello <<'__SCRIPT__'
#!/bin/bash
echo "Hello ${@:-world}!"
__SCRIPT__
chmod +x $PWD/config/bin/hello
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Normal mode, command=true.
TEST_KEY=$TEST_KEY_BASE-true
setup
run_pass "$TEST_KEY" rose app-run -C ../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Normal mode, alternate command key, command-key=false.
TEST_KEY=$TEST_KEY_BASE-false
setup
run_fail "$TEST_KEY" rose app-run -C ../config -q -c false
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] false # rc=1
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Normal mode, alternate command key, command-key=hello-world.
TEST_KEY=$TEST_KEY_BASE-hello-world
setup
run_pass "$TEST_KEY" rose app-run -C ../config -q --command-key=hello-world
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
Hello world!
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Normal mode, alternate command key, command-key=hello-user.
TEST_KEY=$TEST_KEY_BASE-hello-user
setup
run_pass "$TEST_KEY" rose app-run -C ../config -q --command-key=hello-user
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
Hello $USER!
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
