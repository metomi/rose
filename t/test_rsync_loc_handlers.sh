#!/bin/bash
# Tests behaviour of rose/loc_handlers/rsync_remote_check.py against many
# versions of Python.

set -eu

python --version

mkdir -p foo/baz
echo "HI" > foo/bar
echo "THERE" > foo/baz/qux

python metomi/rose/loc_handlers/rsync_remote_check.py $PWD/foo 'blob' 'tree' > out.txt
test="it prints tree"
grep tree out.txt > /dev/null && echo "PASS ${test}" || exit 1

test="it prints foo/baz/qux"
grep "foo/baz/qux" out.txt > /dev/null && echo "PASS ${test}" || exit 1

test="it prints 4 lines"
test "$(cat out.txt | wc -l)" == 4 && echo "PASS ${test}" || exit 1

python metomi/rose/loc_handlers/rsync_remote_check.py $PWD/foo/bar 'blob' 'tree' > out.txt

test="it prints blob"
grep blob out.txt > /dev/null && echo "PASS ${test}" || exit 1

test="it prints foo/bar"
grep "foo/bar" out.txt > /dev/null && echo "PASS ${test}" || exit 1

test="it prints 2 lines"
test "$(cat out.txt | wc -l)" == 2 && echo "PASS ${test}" || exit 1
