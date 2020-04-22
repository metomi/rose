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
# Test "rose_prune" built-in application:
# Prune only host relevant to the relevant cycle.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

JOB_HOSTS="$(rose config --default= 't' 'job-hosts')"
JOB_HOST_1="$(awk '{print $1}' <<<"${JOB_HOSTS}")"
JOB_HOST_2="$(awk '{print $2}' <<<"${JOB_HOSTS}")"
if [[ -z "${JOB_HOST_1}" || -z "${JOB_HOST_2}" ]]; then
    skip_all '"[t]job-hosts-sharing-fs" not defined with 2 host names'
fi

tests 3

export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"
RUND="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${RUND}")"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
run_pass "${TEST_KEY}" \
    rose suite-run -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --host='localhost' --debug \
    -S "JOB_HOST_1=\"${JOB_HOST_1}\"" -S "JOB_HOST_2=\"${JOB_HOST_2}\"" \
    -- --no-detach --debug

TEST_KEY="${TEST_KEY_BASE}-prune.log"
run_pass "${TEST_KEY}-ssh-1" \
    grep -q "ssh .* ${JOB_HOST_1} .* share/cycle/19700101T0000Z;" \
    "${RUND}/prune.log"
run_fail "${TEST_KEY}-ssh-2" \
    grep -q "ssh .* ${JOB_HOST_2} .* share/cycle/19700101T0000Z;" \
    "${RUND}/prune.log"
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
