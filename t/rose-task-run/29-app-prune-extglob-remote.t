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
# Test "rose_prune" built-in application, with bash extglob, using not glob.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

JOB_HOST_OPT=
if [[ "${TEST_KEY_BASE}" == *-remote ]]; then
    JOB_HOST=$(rose config --default= 't' 'job-host')
    if [[ -z "${JOB_HOST}" ]]; then
        skip_all '"[t]job-host" not defined'
    fi
    JOB_HOST="$(rose host-select -q "${JOB_HOST}")"
    if [[ -z "${JOB_HOST}" ]]; then
        skip_all '"[t]job-host" not available'
    fi
    JOB_HOST_OPT="-S JOB_HOST=\"${JOB_HOST}\""
fi

tests 3

export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
get_reg
TEST_KEY="${TEST_KEY_BASE}-install"
run_pass "${TEST_KEY}" \
    cylc install \
        -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
        --flow-name="${FLOW}" \
        --no-run-name
TEST_KEY="${TEST_KEY_BASE}-run"
run_pass "${TEST_KEY}" \
    cylc run \
        "${FLOW}" \
        --host='localhost' \
        ${JOB_HOST_OPT} \
        --no-detach \
        --debug
TEST_KEY="${TEST_KEY_BASE}-prune.log"
sed 's/[0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0-9]*/YYYY-MM-DDTHHMM/g'\
    "${FLOW_RUN_DIR}/prune.log" > stamp-removed.log
sed '/^\[INFO\] YYYY-MM-DDTHHMM export ROSE_TASK_CYCLE_TIME=/p;
    /^\[INFO\] YYYY-MM-DDTHHMM delete: /!d' \
    "stamp-removed.log" >'edited-prune.log'
file_cmp "${TEST_KEY}" 'edited-prune.log' <<__LOG__
[INFO] YYYY-MM-DDTHHMM export ROSE_TASK_CYCLE_TIME=20150101T0000Z
[INFO] YYYY-MM-DDTHHMM export ROSE_TASK_CYCLE_TIME=20150102T0000Z
[INFO] YYYY-MM-DDTHHMM delete: ${JOB_HOST}:work/20150101T0000Z/creator/red_dwarf.nl
[INFO] YYYY-MM-DDTHHMM delete: ${JOB_HOST}:work/20150101T0000Z/creator/rose-app-run.conf
[INFO] YYYY-MM-DDTHHMM export ROSE_TASK_CYCLE_TIME=20150103T0000Z
[INFO] YYYY-MM-DDTHHMM delete: ${JOB_HOST}:work/20150101T0000Z
[INFO] YYYY-MM-DDTHHMM delete: ${JOB_HOST}:work/20150102T0000Z/creator/red_dwarf.nl
[INFO] YYYY-MM-DDTHHMM delete: ${JOB_HOST}:work/20150102T0000Z/creator/rose-app-run.conf
[INFO] YYYY-MM-DDTHHMM delete: work/20150101T0000Z
__LOG__
#-------------------------------------------------------------------------------
purge
exit 0
