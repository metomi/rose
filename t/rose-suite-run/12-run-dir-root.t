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
# Test "rose suite-run", modification of the suite run root directory.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
if [[ -z ${TMPDIR:-} || -z ${USER:-} || $TMPDIR/$USER == $HOME ]]; then
    skip_all '"TMPDIR" or "USER" not defined or "TMPDIR"/"USER" is "HOME"'
fi
#-------------------------------------------------------------------------------
N_TESTS=7
tests $N_TESTS
#-------------------------------------------------------------------------------
cp -r $TEST_SOURCE_DIR/$TEST_KEY_BASE/* .
cat >rose-suite.conf <<__CONF__
root-dir=*=\$TMPDIR/\$USER
__CONF__
JOB_HOST=$(rose config 't' 'job-host')
JOB_HOST_RUN_ROOT=$(rose config 't' 'job-host-run-root')
JOB_HOST_OPT=
if [[ -n $JOB_HOST && -n $JOB_HOST_RUN_ROOT ]]; then
    export JOB_HOST=$(rose host-select -q $JOB_HOST)
    export JOB_HOST_RUN_ROOT
    JOB_HOST_OPT='-O job-host'
    mkdir opt
    cat >opt/rose-suite-job-host.conf <<__CONF__
root-dir=$JOB_HOST=$JOB_HOST_RUN_ROOT
        =*=\$TMPDIR/\$USER

[jinja2:suite.rc]
JOB_HOST="$JOB_HOST"
__CONF__
fi
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-install
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" rose suite-run -n $NAME -i --no-gcontrol $JOB_HOST_OPT
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-locs"
rose config -f $SUITE_RUN_DIR/log/rose-suite-run.locs localhost root-dir \
    >"$TEST_KEY.localhost"
file_cmp "$TEST_KEY.localhost" "$TEST_KEY.localhost" <<<'$TMPDIR/$USER'
if [[ -n $JOB_HOST_OPT ]]; then
    rose config -f $SUITE_RUN_DIR/log/rose-suite-run.locs $JOB_HOST root-dir \
        >"$TEST_KEY.$JOB_HOST"
    file_cmp "$TEST_KEY.$JOB_HOST" "$TEST_KEY.$JOB_HOST" <<<$JOB_HOST_RUN_ROOT
else
    skip 1 "[t]job-host not defined"
fi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-root-symlink"
if [[ $(readlink $HOME/cylc-run/$NAME) == $TMPDIR/$USER/cylc-run/$NAME ]]; then
    pass "$TEST_KEY.localhost"
else
    fail "$TEST_KEY.localhost"
fi
if [[ -n $JOB_HOST_OPT ]]; then
    RUN_ROOT=$(ssh $JOB_HOST "bash -l -c echo\\ \\$JOB_HOST_RUN_ROOT" | tail -1)
    RUN_DIR=$(ssh $JOB_HOST "bash -l -c readlink\\ ~/cylc-run/$NAME" | tail -1)
    if [[ $RUN_DIR == $RUN_ROOT/cylc-run/$NAME ]]; then
        pass "$TEST_KEY.$JOB_HOST"
    else
        fail "$TEST_KEY.$JOB_HOST"
    fi
else
    skip 1 "[t]job-host not defined"
fi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-clean"
run_pass "$TEST_KEY" rose suite-clean -y $NAME
if [[ -e $HOME/cylc-run/$NAME || -e $TMPDIR/$USER/cylc-run/$NAME ]]; then
    fail "$TEST_KEY.localhost"
else
    pass "$TEST_KEY.localhost"
fi
#-------------------------------------------------------------------------------
exit 0
