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
# Test "rose suite-run --restart" does not re-initialise run directory,
# on remote host.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

T_HOST=$(rose config --default= t job-host)
T_HOST_RUN_ROOT=$(rose config --default= t job-host-run-root)
if [[ -z "$T_HOST" || -z "$T_HOST_RUN_ROOT" ]]; then
    skip_all '"[t]job-host" or "[t]job-host-run-root" not defined'
fi
T_HOST=$(rose host-select -q $T_HOST)
#-------------------------------------------------------------------------------
SSH='ssh -oBatchMode=yes'
function ssh_mkdtemp() {
    local T_HOST=$1
    $SSH $T_HOST python3 - <<'__PYTHON__'
import os
from tempfile import mkdtemp
print mkdtemp(dir=os.path.expanduser("~"), prefix="rose-")
__PYTHON__
}

T_HOST_ROSE_HOME=$(ssh_mkdtemp $T_HOST)
rsync -a --exclude=*.pyc $ROSE_HOME/* $T_HOST:$T_HOST_ROSE_HOME/

mkdir -p 'conf'
cat >'conf/rose.conf' <<__CONF__
[rose-suite-run]
remote-no-login-shell=${T_HOST}=true
remote-rose-bin=${T_HOST}=${T_HOST_ROSE_HOME}/bin/rose
__CONF__
export ROSE_CONF_PATH="${PWD}/conf"

tests 3

cp -r $TEST_SOURCE_DIR/$TEST_KEY_BASE src
cat >'src/rose-suite.conf' <<__CONF__
[jinja2:suite.rc]
T_HOST="$T_HOST"
__CONF__
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -n $NAME --no-gcontrol -C src -- --no-detach --debug
cat >'src/rose-suite.conf' <<__CONF__
root-dir=$T_HOST=$T_HOST_RUN_ROOT
[jinja2:suite.rc]
T_HOST="$T_HOST"
__CONF__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-restart"
run_pass "$TEST_KEY" \
    rose suite-run -q -n $NAME --no-gcontrol -C src --restart \
    -- --no-detach --debug
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-dir"
run_pass "$TEST_KEY" ssh -oBatchMode=yes $T_HOST test -d "cylc-run/$NAME" 
TEST_KEY="$TEST_KEY_BASE-symlink"
run_fail "$TEST_KEY" ssh -oBatchMode=yes $T_HOST test -L "cylc-run/$NAME" 
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
$SSH $T_HOST "rm -fr '$T_HOST_ROSE_HOME'"
exit
