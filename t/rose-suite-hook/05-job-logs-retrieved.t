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
# Test "rose suite-hook", remote job, but the logs of some jobs have already
# been retrieved.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
HOST="$(rose config 't' 'job-host')"
if [[ -z $HOST ]]; then
    skip_all '"[t]job-host" not defined'
fi
HOST="$(rose host-select -q "${HOST}")"
export ROSE_CONF_PATH="${TEST_SOURCE_DIR}/${TEST_KEY_BASE}/conf"

tests 7

#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
SUITE_RUN_DIR="$(mktemp -d --tmpdir=${HOME}/cylc-run 'rose-test-battery.XXXXXX')"
NAME="$(basename "${SUITE_RUN_DIR}")"
export PATH="${TEST_SOURCE_DIR}/${TEST_KEY_BASE}/bin:${PATH}"
export TEST_DIR
rose suite-run -q -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --host='localhost' -S "HOST=\"${HOST}\"" -- --debug

#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-log"
cd "${SUITE_RUN_DIR}/log/job"
for TASK in 'task-1' 'task-2'; do
    file_test "${TEST_KEY}-${TASK}-out" "1/${TASK}/01/job.out"
    file_test "${TEST_KEY}-${TASK}-err" "1/${TASK}/01/job.err"
    file_cmp "${TEST_KEY}-${TASK}.txt" "1/${TASK}/01/job.txt" <<__CONTENT__
Hello from ${TASK}.1
__CONTENT__
done
cd "${OLDPWD}"

sqlite3 "${SUITE_RUN_DIR}/log/rose-job-logs.db" \
    'SELECT cycle,task,path FROM log_files ORDER BY cycle,task,path;' \
    >'rose-job-logs.db.out'
file_cmp "${TEST_KEY}-rose-job-logs-db" 'rose-job-logs.db.out' <<'__DB__'
1|task-1|log/job/1/task-1/01/job
1|task-1|log/job/1/task-1/01/job-activity.log
1|task-1|log/job/1/task-1/01/job.err
1|task-1|log/job/1/task-1/01/job.out
1|task-1|log/job/1/task-1/01/job.txt
1|task-2|log/job/1/task-2/01/job
1|task-2|log/job/1/task-2/01/job-activity.log
1|task-2|log/job/1/task-2/01/job.err
1|task-2|log/job/1/task-2/01/job.out
1|task-2|log/job/1/task-2/01/job.txt
__DB__

#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
