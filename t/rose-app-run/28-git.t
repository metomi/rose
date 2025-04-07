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
# Test "rose app-run", Git installation.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

mkdir $TEST_DIR/hellorepo
echo "Holly" >$TEST_DIR/hellorepo/tree.txt
echo "Timothy" >$TEST_DIR/hellorepo/grass.txt
mkdir $TEST_DIR/hellorepo/fruit
echo "Octavia" >$TEST_DIR/hellorepo/fruit/raspberry.txt
START_PWD=$PWD
cd $TEST_DIR/hellorepo
git init -q
git add .
git commit -m "Initial import" >/dev/null
MAIN_BRANCH=$(git branch --show-current) # main or master
COMMITHASH1=$(git rev-parse HEAD)
git tag -a v1.0 -m "Version 1 tagged"
git checkout -q -b branch1
echo "Willow" >>$TEST_DIR/hellorepo/tree.txt
git commit -a -m "Add a tree" >/dev/null
git checkout -q $MAIN_BRANCH
echo "Clementine" >fruit/orange.txt
git add fruit
git commit -a -m "Add another fruit" >/dev/null
COMMITHASH2=$(git rev-parse HEAD)
git tag -a v2.0 -m "Version 2 tagged"
git config uploadpack.allowAnySHA1InWant true

mkdir $TEST_DIR/git-http/
git clone -q --bare $TEST_DIR/hellorepo $TEST_DIR/git-http/hellorepo.git
cd $TEST_DIR/git-http/hellorepo.git
git config uploadpack.allowFilter true
git config uploadpack.allowAnySHA1InWant true
touch git-daemon-export-ok
mkdir cgi-bin
BACKEND_LOCATION=$(locate --regex "/git-http-backend\$" | head -1)
if [[ -n "$BACKEND_LOCATION" ]]; then
    ln -s $BACKEND_LOCATION cgi-bin/git
fi
GIT_WS_PORT="$((RANDOM + 10000))"
while port_is_busy "${GIT_WS_PORT}"; do
    GIT_WS_PORT="$((RANDOM + 10000))"
done
python -c "import http.server; http.server.CGIHTTPRequestHandler.have_fork = False; http.server.test(HandlerClass=http.server.CGIHTTPRequestHandler, port=$GIT_WS_PORT)" >/dev/null 2>&1 &
GIT_WS_PID=${!}
sleep 10
cd $START_PWD
#-------------------------------------------------------------------------------
tests 57
#-------------------------------------------------------------------------------
remote_test_modes=("ssh" "http" "local")
remote_locations=("$HOSTNAME:$TEST_DIR/hellorepo/" "http://localhost:$GIT_WS_PORT/cgi-bin/git" "$TEST_DIR/hellorepo/")
for i in 0 1 2; do
    remote_mode="${remote_test_modes[$i]}"
    remote="${remote_locations[$i]}"
    if [[ "$remote_mode" == "ssh" ]] && ! ssh -n -q -oBatchMode=yes $HOSTNAME true 1>'/dev/null' 2>/dev/null; then
        skip 14 "cannot ssh to localhost $HOSTNAME"
        echo "Skip $remote" >/dev/tty        
        continue
    fi
    if [[ "$remote_mode" == "http" ]] && ! curl --head --silent --fail $remote >/dev/null 2>&1; then
        skip 14 "failed to launch http on localhost"
        echo "Skip $remote" >/dev/tty        
        continue
    fi
    test_init <<__CONFIG__
[command]
default=true

[file:hello/fruit_main]
source=git:$remote::fruit/::$MAIN_BRANCH

[file:hello/fruit_tag1]
source=git:$remote::fruit/::v1.0

[file:hello/fruit_tag2]
source=git:$remote::fruit/::v2.0

[file:hello/fruit_commit1]
source=git:$remote::fruit/::$COMMITHASH1

[file:hello/fruit_commit2]
source=git:$remote::fruit/::$COMMITHASH2

[file:hello/tree_main.txt]
source=git:$remote::tree.txt::$MAIN_BRANCH

[file:hello/tree_branch1.txt]
source=git:$remote::tree.txt::branch1

[file:hello/tree_tag1.txt]
source=git:$remote::tree.txt::v1.0

[file:hello/tree_tag2.txt]
source=git:$remote::tree.txt::v2.0

[file:hello/tree_commit1.txt]
source=git:$remote::tree.txt::$COMMITHASH1
__CONFIG__
    TEST_KEY="$TEST_KEY_BASE-run-ok-$remote_mode"
    test_setup
    run_pass "$TEST_KEY" rose app-run --config=../config -q
    find hello -type f | LANG=C sort >'find-hello.out'
    file_cmp "$TEST_KEY.found" "find-hello.out" <<__CONTENT__
hello/fruit_commit1/raspberry.txt
hello/fruit_commit2/orange.txt
hello/fruit_commit2/raspberry.txt
hello/fruit_main/orange.txt
hello/fruit_main/raspberry.txt
hello/fruit_tag1/raspberry.txt
hello/fruit_tag2/orange.txt
hello/fruit_tag2/raspberry.txt
hello/tree_branch1.txt
hello/tree_commit1.txt
hello/tree_main.txt
hello/tree_tag1.txt
hello/tree_tag2.txt
__CONTENT__
    file_cmp "$TEST_KEY.found_file0" "hello/fruit_commit1/raspberry.txt" <<__CONTENT__
Octavia
__CONTENT__
    file_cmp "$TEST_KEY.found_file1" "hello/fruit_commit1/raspberry.txt" "hello/fruit_commit2/raspberry.txt"
    file_cmp "$TEST_KEY.found_file2" "hello/fruit_commit1/raspberry.txt" "hello/fruit_main/raspberry.txt"
    file_cmp "$TEST_KEY.found_file3" "hello/fruit_commit1/raspberry.txt" "hello/fruit_tag1/raspberry.txt"
    file_cmp "$TEST_KEY.found_file4" "hello/fruit_commit2/orange.txt" <<__CONTENT__
Clementine
__CONTENT__
    file_cmp "$TEST_KEY.found_file5" "hello/fruit_commit2/orange.txt" "hello/fruit_main/orange.txt"
    file_cmp "$TEST_KEY.found_file6" "hello/fruit_commit2/orange.txt" "hello/fruit_tag2/orange.txt"
    file_cmp "$TEST_KEY.found_file7" "hello/tree_commit1.txt" <<__CONTENT__
Holly
__CONTENT__
    file_cmp "$TEST_KEY.found_file8" "hello/tree_commit1.txt" "hello/tree_main.txt"
    file_cmp "$TEST_KEY.found_file9" "hello/tree_commit1.txt" "hello/tree_tag1.txt"
    file_cmp "$TEST_KEY.found_file9" "hello/tree_commit1.txt" "hello/tree_tag2.txt"
    file_cmp "$TEST_KEY.found_file10" "hello/tree_branch1.txt" <<__CONTENT__
Holly
Willow
__CONTENT__
    test_teardown
    repo_is_local_key="remote"
done

kill "$GIT_WS_PID"
wait "$GIT_WS_PID" 2>/dev/null

#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-null-change"
test_setup
test_init <<__CONFIG__
[command]
default=true

[file:hello/fruit_main]
source=git:$remote::fruit/::$MAIN_BRANCH

[file:hello/fruit_tag1]
source=git:$remote::fruit/::v1.0

[file:hello/fruit_tag2]
source=git:$remote::fruit/::v2.0

[file:hello/fruit_commit1]
source=git:$remote::fruit/::$COMMITHASH1

[file:hello/fruit_commit2]
source=git:$remote::fruit/::$COMMITHASH2

[file:hello/tree_main.txt]
source=git:$remote::tree.txt::$MAIN_BRANCH

[file:hello/tree_branch1.txt]
source=git:$remote::tree.txt::branch1

[file:hello/tree_tag1.txt]
source=git:$remote::tree.txt::v1.0

[file:hello/tree_tag2.txt]
source=git:$remote::tree.txt::v2.0

[file:hello/tree_commit1.txt]
source=git:$remote::tree.txt::$COMMITHASH1
__CONFIG__
rose app-run --config=../config -q || exit 1
find hello -type f | LANG=C sort >'find-hello-before.out'
touch timeline # Nothing should be created after "timeline"
sleep 1
run_pass "$TEST_KEY" rose app-run --config=../config -q
find hello -type f | LANG=C sort >'find-hello-after.out'
file_cmp "$TEST_KEY.find-hello" 'find-hello-before.out' 'find-hello-after.out'
find hello -type f -newer timeline | LANG=C sort >'find-hello-after-newer.out'
file_cmp "$TEST_KEY.find-hello-newer" 'find-hello-after-newer.out' </dev/null
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-entire-contents"
test_setup
test_init <<__CONFIG__
[command]
default=true

[file:hello]
source=git:$TEST_DIR/hellorepo::./::$MAIN_BRANCH
__CONFIG__
run_pass "$TEST_KEY" rose app-run --config=../config -q
find hello -type f | LANG=C sort >'find-hello.out'
file_cmp "$TEST_KEY.find" 'find-hello.out' <<__FILE__
hello/fruit/orange.txt
hello/fruit/raspberry.txt
hello/grass.txt
hello/tree.txt
__FILE__
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-bad-repo"
test_setup
test_init <<__CONFIG__
[command]
default=true

[file:hello/fruit_main]
source=git:$TEST_DIR/zz9+zα/::earth/::v1
__CONFIG__
run_fail "$TEST_KEY" rose app-run --config=../config
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[FAIL] file:hello/fruit_main=source=git:$TEST_DIR/zz9+zα/::earth/::v1: ls-remote: could not locate '$TEST_DIR/zz9+zα/':
[FAIL]     fatal: '$TEST_DIR/zz9+zα/' does not appear to be a git repository
[FAIL]     fatal: Could not read from remote repository.
[FAIL] 
[FAIL]     Please make sure you have the correct access rights
[FAIL]     and the repository exists.
__ERROR__
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-bad-ref"
test_setup
test_init <<__CONFIG__
[command]
default=true

[file:hello/fruit_main]
source=git:$TEST_DIR/hellorepo/::fruit/::bad_ref
__CONFIG__
run_fail "$TEST_KEY" rose app-run --config=../config
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[FAIL] file:hello/fruit_main=source=git:$TEST_DIR/hellorepo/::fruit/::bad_ref: ls-remote: could not find ref 'bad_ref' in '$TEST_DIR/hellorepo/'
__ERROR__
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-bad-short-commit"
test_setup
test_init <<__CONFIG__
[command]
default=true

[file:hello/fruit_main]
source=git:$TEST_DIR/hellorepo/::fruit/::${COMMITHASH1::7}
__CONFIG__
run_fail "$TEST_KEY" rose app-run --config=../config
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[FAIL] file:hello/fruit_main=source=git:$TEST_DIR/hellorepo/::fruit/::${COMMITHASH1::7}: ls-remote: could not find ref '${COMMITHASH1::7}' in '$TEST_DIR/hellorepo/': you may be using an unsupported short commit hash
__ERROR__
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-bad-path-blob-should-be-tree"
test_setup
test_init <<__CONFIG__
[command]
default=true

[file:hello/fruit_main]
source=git:$TEST_DIR/hellorepo::fruit::$MAIN_BRANCH
__CONFIG__
run_fail "$TEST_KEY" rose app-run --config=../config
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[FAIL] Expected path 'fruit' to be type 'blob', but it was 'tree'. Check trailing slash.
[FAIL] source: remote:$TEST_DIR/hellorepo ref:$MAIN_BRANCH commit:$COMMITHASH2 path:fruit (git:$TEST_DIR/hellorepo::fruit::$MAIN_BRANCH)
__ERROR__
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-bad-path-tree-should-be-blob"
test_setup
test_init <<__CONFIG__
[command]
default=true

[file:hello/fruit_main/txt]
source=git:$TEST_DIR/hellorepo::fruit/orange.txt/::$MAIN_BRANCH
__CONFIG__
run_fail "$TEST_KEY" rose app-run --config=../config
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[FAIL] Expected path 'fruit/orange.txt/' to be type 'tree', but it was 'blob'. Check trailing slash.
[FAIL] source: remote:$TEST_DIR/hellorepo ref:$MAIN_BRANCH commit:$COMMITHASH2 path:fruit/orange.txt/ (git:$TEST_DIR/hellorepo::fruit/orange.txt/::$MAIN_BRANCH)
__ERROR__
test_teardown
