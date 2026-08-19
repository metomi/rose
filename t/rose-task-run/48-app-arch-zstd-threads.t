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
# Test "rose_arch" built-in application, multi-threaded zstd compression.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

if ! command -v zstd 1>'/dev/null' 2>&1; then
    skip_all '"zstd" unavailable'
fi
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Run the workflow, and wait for it to complete
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=

get_reg
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
        --workflow-name="${FLOW}" \
        --no-run-name
run_pass "${TEST_KEY_BASE}-play" \
    cylc play \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-job.status"
file_grep "${TEST_KEY}-archive-01" \
    'CYLC_JOB_EXIT=SUCCEEDED' \
    "${FLOW_RUN_DIR}/log/job/1/archive/01/job.status"

ARCHIVE_D="${FLOW_RUN_DIR}/share/backup/archive.d"

TEST_KEY="${TEST_KEY_BASE}-find"
(cd "${FLOW_RUN_DIR}/share/backup" && find . -type f) | LANG=C sort \
    >"${TEST_KEY}.out"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__FIND__'
./archive.d/2016.txt.zst
./archive.d/whatever.tar.zst
__FIND__

# "compress-threads=4"
TEST_KEY="${TEST_KEY_BASE}-2016.txt.zst"
zstd -dc "${ARCHIVE_D}/2016.txt.zst" >"${TEST_KEY}.out"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__OUT__'
MMXVI
__OUT__

# "compress-threads=0", i.e. one thread per available CPU
TEST_KEY="${TEST_KEY_BASE}-whatever.tar.zst"
zstd -dc "${ARCHIVE_D}/whatever.tar.zst" | tar -tf - | LANG=C sort \
    >"${TEST_KEY}.out"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__OUT__'
whatever/idontcare.txt
whatever/youmayberight.txt
__OUT__
#-------------------------------------------------------------------------------
purge
exit 0
