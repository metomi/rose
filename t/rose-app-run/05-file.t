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
# Test "rose app-run", generation of files.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
test_init <<'__CONFIG__'
[command]
default = cat hello1 hello2 hello3/text
test-empty = cat hello1 hello2 hello3/text && cmp hello4 /dev/null
test-directory = cat hello1 hello2 hello3/text && test -d hello4/directory
test-sources = cat hello1 hello2 hello3/text hello4/text
test-root = cat $TEST_DIR/test-root/hello1 $TEST_DIR/test-root/hello2 $TEST_DIR/test-root/hello3/text
__CONFIG__
mkdir -p config/file
cat >config/file/hello1 <<__CONTENT__
Hello $(whoami), how are you?
__CONTENT__
cat >config/file/hello2 <<'__CONTENT__'
Hello world!
Hello earth!
Hello universe!
__CONTENT__
mkdir config/file/hello3
cat >config/file/hello3/text <<'__CONTENT__'
Hello and good bye.
Hello and good bye.
__CONTENT__
OUT=$(cd config/file && cat hello1 hello2 hello3/text)
#-------------------------------------------------------------------------------
tests 65
#-------------------------------------------------------------------------------
# Normal mode with free format files.
TEST_KEY=$TEST_KEY_BASE
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<"$OUT"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with free format files and an empty file.
TEST_KEY=$TEST_KEY_BASE-empty
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    --command-key=test-empty --define='[file:hello4]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<"$OUT"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with free format files and a file with an invalid content.
TEST_KEY=$TEST_KEY_BASE-invalid-content
test_setup
run_fail "$TEST_KEY" rose app-run --config=../config -q \
    --define='[file:hello4]source=stuff:ing'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] Rose tried all other file install handlers and decided this must be an Rsync handler.
[FAIL] 	If it is then host "stuff" is uncontactable (ssh 255 error).
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with free format files and a file with an invalid scheme.
TEST_KEY=$TEST_KEY_BASE-invalid-content
test_setup
run_fail "$TEST_KEY" rose app-run --config=../config -q \
    --define='schemes=stuff*=where_is_the_stuff' --define='[file:hello4]source=stuff:ing'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] file:hello4=source=stuff:ing: don't support scheme where_is_the_stuff
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Verbose mode with free format files.
TEST_KEY=$TEST_KEY_BASE-v1
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config
DIR=$(cd ..; pwd)
python3 -c "import re, sys
print(''.join(sorted(sys.stdin.readlines(),
                     key=re.compile('hello(\d+)').findall)).rstrip())" \
    <"$TEST_KEY.out" >"$TEST_KEY.sorted.out"
file_cmp "$TEST_KEY.sorted.out" "$TEST_KEY.sorted.out" <<__CONTENT__
[INFO] export PATH=$PATH
$OUT
[INFO] install: hello1
[INFO]     source: $DIR/config/file/hello1
[INFO] command: cat hello1 hello2 hello3/text
[INFO] install: hello2
[INFO]     source: $DIR/config/file/hello2
[INFO] create: hello3
[INFO] install: hello3
[INFO]     source: $DIR/config/file/hello3
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
# ... and in incremental mode
TEST_KEY=$TEST_KEY_BASE-v1-incr
run_pass "$TEST_KEY" rose app-run --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[INFO] export PATH=$PATH
[INFO] command: cat hello1 hello2 hello3/text
$OUT
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with free format files and a file with multiple sources.
TEST_KEY=$TEST_KEY_BASE-sources
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    --command-key=test-sources \
    '--define=[file:hello4/text]source=/etc/passwd /etc/profile'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
$OUT
$(</etc/passwd)
$(</etc/profile)
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with free format files and a file with globs sources.
TEST_KEY="$TEST_KEY_BASE-globs"
test_setup
mkdir -p "$TEST_DIR/$TEST_KEY"
for I in $(seq 1 9); do
    echo "Hello World $I" >"$TEST_DIR/$TEST_KEY/hello-$I.txt"
done
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    --command-key=test-sources \
    '--define=[file:hello4/text]source='"$TEST_DIR/$TEST_KEY"'/hello-*.txt'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
$OUT
Hello World 1
Hello World 2
Hello World 3
Hello World 4
Hello World 5
Hello World 6
Hello World 7
Hello World 8
Hello World 9
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
(cd "$TEST_DIR/$TEST_KEY"; rm hello-*.txt)
rmdir "$TEST_DIR/$TEST_KEY"
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with free format files and a directory.
TEST_KEY=$TEST_KEY_BASE-directory
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    --command-key=test-directory \
    --define='[file:hello4/directory]mode=mkdir'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<"$OUT"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# As above, but directory already exists with a file.
TEST_KEY=$TEST_KEY_BASE-directory-exists
test_setup
mkdir -p hello4/directory
touch hello4/directory/file
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    --command-key=test-directory \
    --define='[file:hello4/directory]mode=mkdir'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<"$OUT"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_test "$TEST_KEY.hello4/directory/file" hello4/directory/file
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, copying in an executable file.
TEST_KEY=$TEST_KEY_BASE-file-mod-bits
test_setup
TRUE_PATH=$(which true)
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    --define="[file:bin/my-true]source=$TRUE_PATH"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<"$OUT"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.my-true" 'bin/my-true' "$TRUE_PATH"
ACT_STAT=$(stat -c %a 'bin/my-true')
EXP_STAT=$(stat -c %a "$TRUE_PATH")
run_pass "$TEST_KEY.mod" test "$ACT_STAT" = "$EXP_STAT"
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with free format files and an existing file, with --no-overwrite.
TEST_KEY=$TEST_KEY_BASE--no-overwrite
test_setup
touch hello1
run_fail "$TEST_KEY" rose app-run --config=../config -q --no-overwrite
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] file:hello1: hello1: file already exists (and in no-overwrite mode)
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with free format files, overwrite an existing file.
TEST_KEY=$TEST_KEY_BASE-overwrite
test_setup
touch hello1
run_pass "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<"$OUT"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Install-only mode with free format files.
TEST_KEY=$TEST_KEY_BASE--install-only
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config --install-only
DIR=$(cd ..; pwd)
python3 -c "import re, sys
print(''.join(sorted(sys.stdin.readlines(),
                     key=re.compile('hello(\d+)').findall)).rstrip())" \
    <"$TEST_KEY.out" >"$TEST_KEY.sorted.out"
file_cmp "$TEST_KEY.sorted.out" "$TEST_KEY.sorted.out" <<__CONTENT__
[INFO] export PATH=$PATH
[INFO] install: hello1
[INFO]     source: $DIR/config/file/hello1
[INFO] command: cat hello1 hello2 hello3/text
[INFO] install: hello2
[INFO]     source: $DIR/config/file/hello2
[INFO] create: hello3
[INFO] install: hello3
[INFO]     source: $DIR/config/file/hello3
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.hello1" hello1 ../config/file/hello1
file_cmp "$TEST_KEY.hello2" hello2 ../config/file/hello2
file_cmp "$TEST_KEY.hello3" hello3/text ../config/file/hello3/text
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with an alternate install root, specified in the environment.
TEST_KEY=$TEST_KEY_BASE-env-root
test_setup
ROSE_FILE_INSTALL_ROOT="$TEST_DIR/test-root" \
TEST_DIR=$TEST_DIR \
    run_pass "$TEST_KEY" \
    rose app-run --config=../config -q --command-key=test-root
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<"$OUT"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
run_pass "$TEST_KEY.db" test -f ".rose-config_processors-file.db"
run_pass "$TEST_KEY.hello1" test -f "$TEST_DIR/test-root/hello1"
run_pass "$TEST_KEY.hello2" test -f "$TEST_DIR/test-root/hello2"
run_pass "$TEST_KEY.hello3" test -f "$TEST_DIR/test-root/hello3/text"
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with an alternate install root, specified in the configuration.
TEST_KEY=$TEST_KEY_BASE-conf-root
test_setup
TEST_DIR=$TEST_DIR \
    run_pass "$TEST_KEY" \
    rose app-run --config=../config -q --command-key=test-root \
    -D "file-install-root=$TEST_DIR/test-root"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<"$OUT"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
run_pass "$TEST_KEY.db" test -f ".rose-config_processors-file.db"
run_pass "$TEST_KEY.hello1" test -f "$TEST_DIR/test-root/hello1"
run_pass "$TEST_KEY.hello2" test -f "$TEST_DIR/test-root/hello2"
run_pass "$TEST_KEY.hello3" test -f "$TEST_DIR/test-root/hello3/text"
test_teardown
#-------------------------------------------------------------------------------
# Normal mode with environment variable substituion syntax in target name.
TEST_KEY=$TEST_KEY_BASE-target-env-syntax
test_setup
HELLO=hello \
HELLO_NUM=4 \
    run_pass "$TEST_KEY" rose app-run --config=../config -q \
        --command-key=test-sources \
        '--define=[file:${HELLO}$HELLO_NUM/text]source=/etc/passwd /etc/profile'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$OUT
$(</etc/passwd)
$(</etc/profile)
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
exit
