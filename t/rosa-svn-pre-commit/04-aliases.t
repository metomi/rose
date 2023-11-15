#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2020 British Crown (Met Office) & Contributors.
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
# Tests for "rosa svn-pre-commit" with username aliasing behaviour.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_PATH=
mkdir conf
cat >conf/rose.conf <<'__ROSE_CONF__'
[rosa-svn-pre-commit]
super-users=rosie
__ROSE_CONF__
#-------------------------------------------------------------------------------
tests 73
#-------------------------------------------------------------------------------
mkdir repos
svnadmin create repos/foo
SVN_URL=file://$PWD/repos/foo
cat >repos/foo/hooks/pre-commit <<__PRE_COMMIT__
#!/bin/bash
export ROSE_CONF_PATH=$PWD/conf
exec $ROSE_HOME/sbin/rosa svn-pre-commit "\$@"
__PRE_COMMIT__
chmod +x repos/foo/hooks/pre-commit
export LANG=C
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-good-1
cat >rose-suite.info <<__ROSE_SUITE_INFO__
access-list=frank dave
owner=daisy
project=rose
title=${TEST_KEY}
__ROSE_SUITE_INFO__
run_pass "$TEST_KEY" \
    svn import rose-suite.info -q -m 't' --non-interactive \
    $SVN_URL/a/a/0/0/0/trunk/rose-suite.info
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   a/
A   a/a/
A   a/a/0/
A   a/a/0/0/
A   a/a/0/0/0/
A   a/a/0/0/0/trunk/
A   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-good-1
svn checkout -q $SVN_URL/a/a/0/0/0/trunk/ aa000/
echo "vehicle=bicycle" >>aa000/rose-suite.info
REV1=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY" svn commit -q -m 't' --username=daisy aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn update -q aa000
REV2=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY.rev" bash -c "(( $REV2 > $REV1 ))"
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
U   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-bad-1
svn update -q aa000
echo "subtitle=answer" >>aa000/rose-suite.info
run_fail "$TEST_KEY" svn commit -q -m 't' --username=hal aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
svn: E165001: Commit failed (details follow):
svn: E165001: Commit blocked by pre-commit hook (exit code 1) with output:
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.info: User not in access list

__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-bad-2
svn update -q aa000
run_fail "$TEST_KEY" svn commit -q -m 't' --username=daisynew aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
svn: E165001: Commit failed (details follow):
svn: E165001: Commit blocked by pre-commit hook (exit code 1) with output:
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.info: User not in access list

__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-alias-ok-1
cat >rose-suite.info <<__ROSE_SUITE_INFO__
owner=rosie_member0
project=Rosie admin
title=${TEST_KEY}
__ROSE_SUITE_INFO__
run_pass "$TEST_KEY" \
    svn import rose-suite.info -q -m 't' --non-interactive \
    $SVN_URL/R/O/S/I/E/trunk/rose-suite.info
svn checkout -q $SVN_URL/R/O/S/I/E/trunk/ ROSIE/
cat >ROSIE/author_aliases <<'__TEXT__'
daisynew:daisy
franknew:frank
davenew:dave
__TEXT__
svn add -q ROSIE/author_aliases
run_pass "$TEST_KEY" svn commit -q -m 't' --username=rosie_member0 ROSIE/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   R/O/S/I/E/trunk/author_aliases
__CHANGED__
rm -rf ROSIE
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-with-alias-good-1
svn update -q aa000
svn revert -R aa000
echo "vehicle=carriage" >>aa000/rose-suite.info
REV1=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY" svn commit -q -m 't' --username=daisynew aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn update -q aa000
REV2=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY.rev" bash -c "(( $REV2 > $REV1 ))"
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
U   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-with-alias-good-2
svn update -q aa000
sed -i "s/owner=daisy/owner=daisynew/" aa000/rose-suite.info
sed -i "s/access-list=frank dave/access-list=franknew davenew/" aa000/rose-suite.info
touch aa000/extra-stuff
svn add aa000/extra-stuff
REV1=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY" svn commit -q -m 't' --username=daisynew aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn update -q aa000
REV2=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY.rev" bash -c "(( $REV2 > $REV1 ))"
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   a/a/0/0/0/trunk/extra-stuff
U   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-with-alias-bad-1
echo "references=stretched" >>aa000/rose-suite.info
run_fail "$TEST_KEY" svn commit -q -m 't' --username=hal aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
svn: E165001: Commit failed (details follow):
svn: E165001: Commit blocked by pre-commit hook (exit code 1) with output:
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.info: User not in access list

__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-with-alias-access-list-good-1
# Restore the state without aliases.
svn update -q aa000
sed -i "s/new//g" aa000/rose-suite.info
REV1=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY-setup" svn commit -q -m 't' --username=daisynew aa000
file_cmp "$TEST_KEY-setup.out" "$TEST_KEY-setup.out" </dev/null
file_cmp "$TEST_KEY-setup.err" "$TEST_KEY-setup.err" </dev/null
svn update -q aa000
REV2=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY-setup.rev" bash -c "(( $REV2 > $REV1 ))"
svnlook changed repos/foo >"$TEST_KEY-setup.changed"
file_cmp "$TEST_KEY-setup.changed" "$TEST_KEY-setup.changed" <<'__CHANGED__'
U   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
# Now change the owner and access-list but only to aliases.
sed -i "s/owner=daisy/owner=daisynew/" aa000/rose-suite.info
sed -i "s/access-list=frank dave/access-list=franknew davenew/" aa000/rose-suite.info
REV1=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY" svn commit -q -m 't' --username=franknew aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn update -q aa000
REV2=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY.rev" bash -c "(( $REV2 > $REV1 ))"
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
U   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-with-alias-access-list-bad-1
# Restore the state without aliases.
svn update -q aa000
sed -i "s/new//g" aa000/rose-suite.info
REV1=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY-setup" svn commit -q -m 't' --username=daisynew aa000
file_cmp "$TEST_KEY-setup.out" "$TEST_KEY-setup.out" </dev/null
file_cmp "$TEST_KEY-setup.err" "$TEST_KEY-setup.err" </dev/null
svn update -q aa000
REV2=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY-setup.rev" bash -c "(( $REV2 > $REV1 ))"
svnlook changed repos/foo >"$TEST_KEY-setup.changed"
file_cmp "$TEST_KEY-setup.changed" "$TEST_KEY-setup.changed" <<'__CHANGED__'
U   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
# Access-list user trying to change the owner, should be blocked.
sed -i "s/owner=daisy/owner=franknew/" aa000/rose-suite.info
sed -i "s/access-list=frank dave/access-list=franknew davenew/" aa000/rose-suite.info
REV1=$(svn info --show-item revision aa000/)
run_fail "$TEST_KEY" svn commit -q -m 't' --username=franknew aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
svn: E165001: Commit failed (details follow):
svn: E165001: Commit blocked by pre-commit hook (exit code 1) with output:
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.info: owner=franknew

__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-with-alias-access-list-bad-2
svn revert -q -R aa000
# Access-list user trying to change the access-list, should be blocked.
sed -i "s/owner=daisy/owner=daisynew/" aa000/rose-suite.info
sed -i "s/access-list=frank dave/access-list=franknew davenew heywood/" aa000/rose-suite.info
REV1=$(svn info --show-item revision aa000/)
run_fail "$TEST_KEY" svn commit -q -m 't' --username=franknew aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
svn: E165001: Commit failed (details follow):
svn: E165001: Commit blocked by pre-commit hook (exit code 1) with output:
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.info: owner=daisynew

__ERR__
svn revert -q -R aa000
svn update -q aa000
REV2=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY.rev" bash -c "(( $REV2 == $REV1 ))"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-delete-alias-ok
svn checkout -q $SVN_URL/R/O/S/I/E/trunk/ ROSIE/
svn delete ROSIE/author_aliases
run_pass "$TEST_KEY" svn commit -q -m 't' --username=rosie ROSIE
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
D   R/O/S/I/E/trunk/author_aliases
__CHANGED__
rm -rf ROSIE
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-no-alias-ok
svn update -q aa000
echo "plant=flower" >>aa000/rose-suite.info
REV1=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY" svn commit -q -m 't' --username=daisy aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn update -q aa000
REV2=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY.rev" bash -c "(( $REV2 > $REV1 ))"
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
U   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-single-alias-ok-1
svn checkout -q $SVN_URL/R/O/S/I/E/trunk ROSIE/
cat >ROSIE/author_aliases <<'__TEXT__'
daisynew2:daisy
__TEXT__
svn add -q ROSIE/author_aliases
run_pass "$TEST_KEY" svn commit -q -m 't' --username=rosie_member0 ROSIE
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   R/O/S/I/E/trunk/author_aliases
__CHANGED__
rm -rf ROSIE
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-with-single-alias-good-1
svn update -q aa000
echo "bicycle_for=two" >>aa000/rose-suite.info
REV1=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY" svn commit -q -m 't' --username=daisynew2 aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn update -q aa000
REV2=$(svn info --show-item revision aa000/)
run_pass "$TEST_KEY.rev" bash -c "(( $REV2 > $REV1 ))"
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
U   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
exit 0
