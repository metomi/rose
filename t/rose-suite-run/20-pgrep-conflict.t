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
# Test "rose suite-run" when similarly-named suites are running.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
set -eu
#-------------------------------------------------------------------------------
tests 20
#-------------------------------------------------------------------------------
cat >$TEST_DIR/cylc-run <<'__PYTHON__'
#!/usr/bin/env python
import time
time.sleep(60)
__PYTHON__
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery-XXXXXX')
NAME=$(basename "${SUITE_RUN_DIR}")
#-------------------------------------------------------------------------------
# Check that "rose suite-run" fails if a "python cylc-run SUITE" process is
# running.

# Recent version of "pgrep" has introduced a "-a" option, which does what "-l"
# used to do. Unfortunately, "-l" no longer does what it used to, so the output
# from our call to "pgrep -l" no longer looks the same. We should fix this in
# our lib, but it is really hard, because we may be running "pgrep" via SSH,
# and it does not even have a "--version" option. In the mean time, the easiest
# thing to allow these tests to pass is to have different expectation for the
# output depending on whether the "-a" option is available or not.
IS_NEW_PGREP=false
if pgrep -a 'bash' 1>'/dev/null' 2>&1; then
    IS_NEW_PGREP=true
fi
for ARG in '' '--hold'; do
    TEST_KEY="${TEST_KEY_BASE}-self-check${ARG}"
    python "${TEST_DIR}/cylc-run" "${NAME}" ${ARG} 1>'/dev/null' 2>&1 &
    FAKE_SUITE_PID=$!
    run_fail "${TEST_KEY}" rose suite-run -q --no-gcontrol \
        -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" -- --debug
    ARG_STR=
    if [[ -n "${ARG}" ]]; then
        ARG_STR=" ${ARG}"
    fi
    if "${IS_NEW_PGREP}"; then
        file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] Suite "${NAME}" may still be running.
[FAIL] Host "localhost" has process:
[FAIL]     ${FAKE_SUITE_PID} python
[FAIL] Try "rose suite-shutdown --name=${NAME}" first?
__ERR__
    else
        file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] Suite "${NAME}" may still be running.
[FAIL] Host "localhost" has process:
[FAIL]     ${FAKE_SUITE_PID} python ${TEST_DIR}/cylc-run ${NAME}${ARG_STR}
[FAIL] Try "rose suite-shutdown --name=${NAME}" first?
__ERR__
    fi
    disown "${FAKE_SUITE_PID}" 2>'/dev/null'  # Don't report stuff on kill
    kill "${FAKE_SUITE_PID}" 2>'/dev/null' || true
done
#-------------------------------------------------------------------------------
# Check that "rose suite-run" does not fail while suites with similar names are
# running.
for ALT_NAME in \
    "foo${NAME}" \
    "foo-${NAME}" \
    "foo_${NAME}" \
    "${NAME}bar" \
    "${NAME}-bar" \
    "${NAME}_bar" \
    "${NAME}." \
    ".${NAME}"
do
    for ARG in '' '--hold'; do
        TEST_KEY="${TEST_KEY_BASE}-alt-name-${ALT_NAME}${ARG}"
        python "${TEST_DIR}/cylc-run" "${ALT_NAME}" ${ARG} 1>'/dev/null' 2>&1 &
        FAKE_SUITE_PID=$!
        run_pass "${TEST_KEY}" rose suite-run -q --no-gcontrol \
            -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" -- --debug
        disown "${FAKE_SUITE_PID}" 2>'/dev/null'
        kill "${FAKE_SUITE_PID}" 2>'/dev/null' || true
    done
done
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
