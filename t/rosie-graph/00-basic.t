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
# Basic tests for "rosie graph".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header_extra
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
if ! python3 -c 'import tornado, sqlalchemy' 2>/dev/null; then
    skip_all '"tornado" or "sqlalchemy" not installed'
fi
if ! python3 -c 'import pygraphviz' 2>/dev/null; then
    skip_all '"pygraphviz" not installed'
fi
tests 33
#-------------------------------------------------------------------------------
# Setup Rose site/user configuration for the tests.
export TZ='UTC'

mkdir repos
svnadmin create repos/foo || exit 1
SVN_URL=file://$PWD/repos/foo

# Setup configuration file.
mkdir conf
cat >conf/rose.conf <<__ROSE_CONF__
opts=port

[rosie-db]
repos.foo=$PWD/repos/foo
db.foo=sqlite:///$PWD/repos/foo.db

[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-location.foo=$SVN_URL
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD/conf

mkdir 'conf/opt'
touch 'conf/opt/rose-port.conf'

# Setup repository - create a suite.
cat >repos/foo/hooks/post-commit <<__POST_COMMIT__
#!/bin/bash
export ROSE_CONF_PATH=$ROSE_CONF_PATH
$ROSE_HOME/sbin/rosa svn-post-commit --debug "\$@" \\
    1>$PWD/rosa-svn-post-commit.out 2>$PWD/rosa-svn-post-commit.err
echo \$? >$PWD/rosa-svn-post-commit.rc
__POST_COMMIT__
chmod +x repos/foo/hooks/post-commit
export LANG=C
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
description=Bad corn ear and pew pull
owner=iris
project=eye pad
title=Should have gone to ...
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info --no-checkout || exit 1
echo "2009-02-13T23:31:30.000000Z" >foo-date-1.txt
svnadmin setrevprop $PWD/repos/foo -r 1 svn:date foo-date-1.txt

# Setup repository - create and update another suite.
# Create a suite.
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
description=Violets are Blue...
owner=roses
project=poetry
title=Roses are Red,...
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info foo-aa000 || exit 1
echo "2009-02-13T23:31:31.000000Z" >foo-date-2.txt
svnadmin setrevprop $PWD/repos/foo -r 2 svn:date foo-date-2.txt
# Update this suite.
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=roses violets
owner=roses
project=poetry
title=Roses are Red; Violets are Blue,...
__ROSE_SUITE_INFO
cp rose-suite.info $PWD/roses/foo-aa001/
(cd $PWD/roses/foo-aa001 && svn commit -q -m "update" && \
     svn update -q) || exit 1
echo "2009-02-13T23:31:32.000000Z" >foo-date-3.txt
svnadmin setrevprop $PWD/repos/foo -r 3 svn:date foo-date-3.txt

# Setup repository - delete the first suite.
rosie delete -q -y foo-aa000 || exit 1
echo "2009-02-13T23:31:33.000000Z" >foo-date-4.txt
svnadmin setrevprop $PWD/repos/foo -r 4 svn:date foo-date-4.txt

# Setup repository - create another suite.
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=allthebugs
description=Nom nom nom roses
owner=aphids
project=eat roses
title=Eat all the roses!
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info || exit 1
echo "2009-02-13T23:31:34.000000Z" >foo-date-5.txt
svnadmin setrevprop $PWD/repos/foo -r 5 svn:date foo-date-5.txt

# Setup repository - create another suite.
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
owner=bill
project=sonnet 54
title=The rose looks fair...
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info foo-aa002 || exit 1
echo "2009-02-13T23:31:35.000000Z" >foo-date-6.txt
svnadmin setrevprop $PWD/repos/foo -r 6 svn:date foo-date-6.txt

# Setup repository - create another suite.
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
owner=bill
project=sonnet 54
title=The rose looks fair but fairer we it deem for that sweet odour which doth in it live.
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info foo-aa003 || exit 1
echo "2009-02-13T23:31:36.000000Z" >foo-date-7.txt
svnadmin setrevprop $PWD/repos/foo -r 7 svn:date foo-date-7.txt

# Setup repository - create another suite.
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
owner=bill
project=sonnet 54
title=The rose looks fair but fairer we it deem for that sweet odour which doth in it live.
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info || exit 1
echo "2009-02-13T23:31:37.000000Z" >foo-date-8.txt
svnadmin setrevprop $PWD/repos/foo -r 8 svn:date foo-date-8.txt

# Setup repository - create another suite.
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
owner=bill
project=sonnet 54
title=This is becoming something of a thorny issue
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info foo-aa004 || exit 1
echo "2009-02-13T23:31:38.000000Z" >foo-date-9.txt
svnadmin setrevprop $PWD/repos/foo -r 8 svn:date foo-date-8.txt

# Setup db.
$ROSE_HOME/sbin/rosa db-create -q

#-------------------------------------------------------------------------------
# Run ws.
PORT="$((RANDOM + 10000))"
while port_is_busy "${PORT}"; do
    PORT="$((RANDOM + 10000))"
done
cat >'conf/opt/rose-port.conf' <<__ROSE_CONF__
[rosie-id]
prefix-ws.foo=http://${HOSTNAME}:${PORT}/foo
__ROSE_CONF__
rosie disco 'start' "${PORT}" \
    0<'/dev/null' 1>'rosie-disco.out' 2>'rosie-disco.err' &
ROSA_WS_PID="${!}"
T_INIT="$(date +%s)"
while ! port_is_busy "${PORT}" && (($(date +%s) < T_INIT + 60)); do
    sleep 1
done
if ! port_is_busy "${PORT}"; then
    exit 1
fi

#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-full
run_pass "$TEST_KEY" rosie graph --debug
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.filtered.out" <<__OUTPUT__
"foo-aa000" -> "foo-aa001" [
"foo-aa000" [label="foo-aa000"
"foo-aa001" [label="foo-aa001"
"foo-aa002" -> "foo-aa003" [
"foo-aa002" [label="foo-aa002"
"foo-aa003" -> "foo-aa004" [
"foo-aa003" [label="foo-aa003"
"foo-aa004" -> "foo-aa006" [
"foo-aa004" [label="foo-aa004"
"foo-aa006" [label="foo-aa006"
graph [rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-filter-id
run_pass "$TEST_KEY" rosie graph --debug foo-aa003
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.filtered.out" <<__OUTPUT__
"foo-aa002" -> "foo-aa003" [
"foo-aa002" [label="foo-aa002"
"foo-aa003" -> "foo-aa004" [
"foo-aa003" [label="foo-aa003", style=filled
"foo-aa004" -> "foo-aa006" [
"foo-aa004" [label="foo-aa004"
"foo-aa006" [label="foo-aa006"
graph [rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-filter-id-distance-1
run_pass "$TEST_KEY" rosie graph --debug --distance=1 foo-aa004
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.filtered.out" <<__OUTPUT__
"foo-aa003" -> "foo-aa004" [
"foo-aa003" [label="foo-aa003"
"foo-aa004" -> "foo-aa006" [
"foo-aa004" [label="foo-aa004", style=filled
"foo-aa006" [label="foo-aa006"
graph [rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-filter-id-distance-2
run_pass "$TEST_KEY" rosie graph --debug --distance=1 foo-aa002
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.filtered.out" <<__OUTPUT__
"foo-aa002" -> "foo-aa003" [
"foo-aa002" [label="foo-aa002", style=filled
"foo-aa003" [label="foo-aa003"
graph [rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-no-filter-id-distance
run_fail "$TEST_KEY" rosie graph --debug --distance=1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
Usage: rosie graph [OPTIONS] [ID]

rosie graph: error: distance option requires an ID
__ERROR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-property-owner
run_pass "$TEST_KEY" rosie graph --debug --property=owner
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.filtered.out" <<__OUTPUT__
"foo-aa000" -> "foo-aa001" [
"foo-aa000" [label="foo-aa000\niris"
"foo-aa001" [label="foo-aa001\nroses"
"foo-aa002" -> "foo-aa003" [
"foo-aa002" [label="foo-aa002\naphids"
"foo-aa003" -> "foo-aa004" [
"foo-aa003" [label="foo-aa003\nbill"
"foo-aa004" -> "foo-aa006" [
"foo-aa004" [label="foo-aa004\nbill"
"foo-aa006" [label="foo-aa006\nbill"
graph [rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-property-owner-project
run_pass "$TEST_KEY" rosie graph --debug --property=owner --property=project
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.filtered.out" <<__OUTPUT__
"foo-aa000" -> "foo-aa001" [
"foo-aa000" [label="foo-aa000\niris\neye pad"
"foo-aa001" [label="foo-aa001\nroses\npoetry"
"foo-aa002" -> "foo-aa003" [
"foo-aa002" [label="foo-aa002\naphids\neat roses"
"foo-aa003" -> "foo-aa004" [
"foo-aa003" [label="foo-aa003\nbill\nsonnet 54"
"foo-aa004" -> "foo-aa006" [
"foo-aa004" [label="foo-aa004\nbill\nsonnet 54"
"foo-aa006" [label="foo-aa006\nbill\nsonnet 54"
graph [rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-property-title
run_pass "$TEST_KEY" rosie graph --debug --property=title
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.filtered.out" <<__OUTPUT__
"foo-aa000" -> "foo-aa001" [
"foo-aa000" [label="foo-aa000\nShould have gone to ..."
"foo-aa001" [label="foo-aa001\nRoses are Red; Violets are Blue,..."
"foo-aa002" -> "foo-aa003" [
"foo-aa002" [label="foo-aa002\nEat all the roses!"
"foo-aa003" -> "foo-aa004" [
"foo-aa003" [label="foo-aa003\nThe rose looks fair..."
"foo-aa004" -> "foo-aa006" [
"foo-aa004" [label="foo-aa004\nThe rose looks fair but fairer we it deem for that sweet odour which\ndoth in it live."
"foo-aa006" [label="foo-aa006\nThis is becoming something of a thorny issue"
graph [rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-no-copy-tree
run_pass "$TEST_KEY" rosie graph --debug foo-aa005
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.filtered.out" <<__OUTPUT__
"foo-aa005" [label="foo-aa005", style=filled
graph [rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[WARN] foo-aa005: no copy relationships to other suites
__ERROR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-print-graph
run_pass "$TEST_KEY" rosie graph --text foo-aa003 -p owner
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
[parent] foo-aa002, aphids
[child1] foo-aa004, bill
[child2] foo-aa006, bill
__OUTPUT__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-print-graph-no-parent
run_pass "$TEST_KEY" rosie graph --text foo-aa000 -p owner -d 1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
[parent] None
[child1] foo-aa001, roses
__OUTPUT__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-print-graph-no-child
run_pass "$TEST_KEY" rosie graph --text foo-aa006 -p owner -d 1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
[parent] foo-aa004, bill
__OUTPUT__

#-------------------------------------------------------------------------------
kill "${ROSA_WS_PID}"
wait 2>'/dev/null'
rm -f ~/.metomi/rosie-disco-${HOSTNAME:-0.0.0.0}-${PORT}*
exit
