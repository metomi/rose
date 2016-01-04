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
# Test "rose app-run", STDIN.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
test_init <<'__CONFIG__'
[command]
default = cat

[file:STDIN]
__CONFIG__
#-------------------------------------------------------------------------------
tests 24
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
# Normal mode, empty STDIN.
TEST_KEY=$TEST_KEY_BASE-empty
test_setup
run_pass "$TEST_KEY" rose app-run -C ../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Verbose mode, empty STDIN.
TEST_KEY=$TEST_KEY_BASE-empty-v1
test_setup
run_pass "$TEST_KEY" rose app-run -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[INFO] export PATH=$PATH
[INFO] install: STDIN
[INFO] command: cat <STDIN
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, STDIN is /etc/passwd.
TEST_KEY=$TEST_KEY_BASE
test_setup
run_pass "$TEST_KEY" \
    rose app-run -C ../config '--define=[file:STDIN]source=/etc/passwd' -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" /etc/passwd
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Verbose mode, STDIN is /etc/passwd.
TEST_KEY=$TEST_KEY_BASE--v1
test_setup
run_pass "$TEST_KEY" rose app-run \
     -C ../config \
    '--define=[file:STDIN]source=/etc/passwd'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[INFO] export PATH=$PATH
[INFO] install: STDIN
[INFO]     source: /etc/passwd
[INFO] command: cat <STDIN
$(</etc/passwd)
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, STDIN is /etc/passwd, MD5 checksum.
TEST_KEY=$TEST_KEY_BASE-md5
test_setup
run_pass "$TEST_KEY" rose app-run \
     -q \
     -C ../config \
    '--define=[file:STDIN]source=/etc/passwd' \
    "--define=[file:STDIN]checksum=$(md5sum /etc/passwd | cut -d\  -f1)"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" /etc/passwd
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, STDIN is /etc/passwd, MD5 checksum, --verbose.
TEST_KEY=$TEST_KEY_BASE-md5-verbose
test_setup
MD5_EXP=$(md5sum /etc/passwd | cut -d\  -f1)
run_pass "$TEST_KEY" rose app-run -v \
     -q \
     -C ../config \
    '--define=[file:STDIN]source=/etc/passwd' \
    "--define=[file:STDIN]checksum=$MD5_EXP"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[INFO] export PATH=$PATH
[INFO] install: STDIN
[INFO]     source: /etc/passwd
[INFO] checksum: STDIN: $MD5_EXP
[INFO] command: cat <STDIN
$(< /etc/passwd)
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, STDIN is /etc/passwd, MD5 checksum, incorrect checksum.
TEST_KEY=$TEST_KEY_BASE-md5-incorrect
test_setup
run_fail "$TEST_KEY" rose app-run \
     -q \
     -C ../config \
    '--define=[file:STDIN]source=/etc/passwd' \
    "--define=[file:STDIN]checksum=$(md5sum /dev/null | cut -d\  -f1)"
MD5_EXP=$(md5sum /dev/null | cut -d' ' -f1)
MD5_ACT=$(md5sum /etc/passwd | cut -d' ' -f1)
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[FAIL] file:STDIN=checksum=$MD5_EXP: Unmatched checksum, expected=$MD5_EXP, actual=$MD5_ACT
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, STDIN is /etc/passwd, SHA1 checksum.
TEST_KEY="${TEST_KEY_BASE}-sha1"
test_setup
run_pass "${TEST_KEY}" rose app-run \
     -q \
     -C '../config' \
    '--define=[file:STDIN]source=/etc/passwd' \
    "--define=[file:STDIN]checksum=$(sha1sum '/etc/passwd' | cut -d\  -f1)"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" '/etc/passwd'
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
test_teardown
#-------------------------------------------------------------------------------
exit
