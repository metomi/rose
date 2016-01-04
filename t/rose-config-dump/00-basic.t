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
# Test "rose config-dump".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 22
#-------------------------------------------------------------------------------
# Basic usage, empty directory.
TEST_KEY=$TEST_KEY_BASE-basic-empty
setup
run_pass "$TEST_KEY" rose config-dump
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Basic usage, empty files in directory.
TEST_KEY=$TEST_KEY_BASE-basic-empty-files
setup
touch rose-suite.conf
mkdir app
mkdir app/{foo,bar,baz}
touch app/{foo,bar,baz}/rose-app.conf
run_pass "$TEST_KEY" rose config-dump --no-pretty
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Basic usage, standard files in directory.
TEST_KEY=$TEST_KEY_BASE-basic-ok-files
setup
cat > f1 <<'__CONF__'
# More comments

# File 1
[file:1]
mode=auto
source=foo bar baz

# File 2
[file:2]
source=namelist:egg namelist:ham namelist:bacon
__CONF__
cat > f2 <<'__CONF__'
# HEAD comments

meta=my-foo/HEAD

[command]
default=foo
__CONF__
cat > f3 <<'__CONF__'
# HEADER comments

meta=my-bar/HEAD

[command]
default=bar

[env]
PUB=bar
STCIK=bar
__CONF__
cat > f4 <<'__CONF__'
# Root comments

meta=my-baz/HEAD

[command]
default=baz

[env]
DID_YOU_MEAN=bus
__CONF__
cp f1 rose-suite.conf
mkdir app
mkdir app/{foo,bar,baz}
touch app/{foo,bar,baz}/rose-app.conf
cp f2 app/foo/rose-app.conf
cp f3 app/bar/rose-app.conf
cp f4 app/baz/rose-app.conf
run_pass "$TEST_KEY" rose config-dump
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.f1" f1 rose-suite.conf
file_cmp "$TEST_KEY.f2" f2 app/foo/rose-app.conf
file_cmp "$TEST_KEY.f3" f3 app/bar/rose-app.conf
file_cmp "$TEST_KEY.f4" f4 app/baz/rose-app.conf
teardown
#-------------------------------------------------------------------------------
# Basic usage, non-standard files in directory.
TEST_KEY=$TEST_KEY_BASE-basic-files
setup
cat > f1 <<'__CONF__'
# More comments

# File 1
[file:1]
mode=auto
source=foo bar baz

# File 2
[file:2]
source=egg ham bacon
__CONF__
cat > f2 <<'__CONF__'
# HEAD comments

meta=my-foo/HEAD

[command]
default=foo
__CONF__
cat > f3 <<'__CONF__'
# HEADER comments

meta=my-bar/HEAD

[command]
default=bar

[env]
PUB=bar
# sticky stuffs
STCIK=bar
__CONF__
cat > f4 <<'__CONF__'
# Root comments

meta=my-baz/HEAD

[command]
default=baz

[env]
DID_YOU_MEAN=bus
__CONF__
cp f1 rose-suite.conf
cat >rose-suite.conf <<'__CONF__'
# More comments

# File 1
[file:1]
mode=auto
source=foo bar baz

# File 2
[file:2]
source=egg ham bacon

# more comments at the end

__CONF__
mkdir app
mkdir app/{foo,bar,baz}
touch app/{foo,bar,baz}/rose-app.conf
cp f2 app/foo/rose-app.conf
cat >app/bar/rose-app.conf <<'__CONF__'
# HEADER comments

[env]

# sticky stuffs
STCIK=bar

[command]
default=bar

[env]
PUB=bar

[]
meta=my-bar/HEAD
__CONF__
cp f4 app/baz/rose-app.conf
stat -c%a rose-suite.conf >"$TEST_KEY.suite.stat"
stat -c%a app/bar/rose-app.conf >"$TEST_KEY.app-bar.stat"
run_pass "$TEST_KEY" rose config-dump --no-pretty
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] M rose-suite.conf
[INFO] M app/bar/rose-app.conf
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.f1" f1 rose-suite.conf
file_cmp "$TEST_KEY.suite.stat" "$TEST_KEY.suite.stat" \
    <<<$(stat -c%a rose-suite.conf)
file_cmp "$TEST_KEY.app-bar.stat" "$TEST_KEY.app-bar.stat" \
    <<<$(stat -c%a app/bar/rose-app.conf)
file_cmp "$TEST_KEY.f2" f2 app/foo/rose-app.conf
file_cmp "$TEST_KEY.f3" f3 app/bar/rose-app.conf
file_cmp "$TEST_KEY.f4" f4 app/baz/rose-app.conf
teardown
#-------------------------------------------------------------------------------
exit 0
