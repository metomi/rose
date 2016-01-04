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
# Test "rose env-cat --match-mode=brace".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 18
export USER=${USER:-$(whoami)}
export HOME=${HOME:-$(cd ~$USER && pwd)}
#-------------------------------------------------------------------------------
# Read from STDIN.
TEST_KEY=$TEST_KEY_BASE-stdin
setup
run_pass "$TEST_KEY" rose env-cat --match-mode=brace <<'__STDIN__'
I am \$USER $USER.
my \$HOME is at ${HOME}.
__STDIN__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
I am \\\$USER \$USER.
my \\\$HOME is at ${HOME}.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Read from STDIN as -.
TEST_KEY=$TEST_KEY_BASE-stdin-2
setup
run_pass "$TEST_KEY" rose env-cat -m brace - <<'__STDIN__'
I am \$USER $USER.
my \$HOME is at ${HOME}.
__STDIN__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
I am \\\$USER \$USER.
my \\\$HOME is at ${HOME}.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Files
TEST_KEY=$TEST_KEY_BASE-files
setup
cat >file1 <<'__FILE__'
I am \$USER \$USER.
my \$HOME is at ${HOME}.
__FILE__
cat >file2 <<'__FILE__'
The \$PATH to enlightenment is ${PATH}.
\$PWD is where I am working at the moment. Not sure if I am at \$HOME or not.
__FILE__
run_pass "$TEST_KEY" rose env-cat -m brace file1 file2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
I am \\\$USER \\\$USER.
my \\\$HOME is at ${HOME}.
The \\\$PATH to enlightenment is ${PATH}.
\\\$PWD is where I am working at the moment. Not sure if I am at \\\$HOME or not.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Unbound
TEST_KEY=$TEST_KEY_BASE-unbound
setup
run_fail "$TEST_KEY" rose env-cat -m brace <<'__STDIN__'
I am OK.
I am ${NOT_OK}.
__STDIN__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
I am OK.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
<STDIN>:2: [UNDEFINED ENVIRONMENT VARIABLE] NOT_OK
__ERR__
teardown
#-------------------------------------------------------------------------------
# Unbound-OK, empty substitution
TEST_KEY=$TEST_KEY_BASE-unbound-ok
setup
run_pass "$TEST_KEY" rose env-cat -m brace --unbound= <<'__STDIN__'
I am OK.
I am ${NOT_OK}.
__STDIN__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
I am OK.
I am .
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Unbound-OK, non-empty substitution.
TEST_KEY=$TEST_KEY_BASE-unbound-ok-2
setup
run_pass "$TEST_KEY" rose env-cat -m brace --unbound=undef <<'__STDIN__'
I am OK.
I am ${NOT_OK}.
__STDIN__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
I am OK.
I am undef.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
