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

tests 2

export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR=$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')
NAME="$(basename "${SUITE_RUN_DIR}")"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
run_pass "${TEST_KEY}" \
    rose suite-run -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --host='localhost' ${JOB_HOST_OPT} -- --debug

TEST_KEY="${TEST_KEY_BASE}-prune.log"
sed '/^\[INFO\] export ROSE_TASK_CYCLE_TIME=/p;/^\[INFO\] delete: /!d' \
    "${SUITE_RUN_DIR}/prune.log" >'edited-prune.log'
file_cmp "${TEST_KEY}" 'edited-prune.log' <<__LOG__
[INFO] export ROSE_TASK_CYCLE_TIME=20150101T0000Z
[INFO] export ROSE_TASK_CYCLE_TIME=20150102T0000Z
[INFO] delete: ${JOB_HOST}:work/20150101T0000Z/creator/red_dwarf.nl
[INFO] delete: ${JOB_HOST}:work/20150101T0000Z/creator/rose-app-run.conf
[INFO] export ROSE_TASK_CYCLE_TIME=20150103T0000Z
[INFO] delete: ${JOB_HOST}:work/20150101T0000Z
[INFO] delete: ${JOB_HOST}:work/20150102T0000Z/creator/red_dwarf.nl
[INFO] delete: ${JOB_HOST}:work/20150102T0000Z/creator/rose-app-run.conf
[INFO] delete: work/20150101T0000Z
__LOG__
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
