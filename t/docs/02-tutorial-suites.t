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
# Run validation checks on tutorial suites located in etc/tutorial.
#
# Run `cylc validate -v -v` by default, to run different tests create a
# .validate file in the tests directory, each line will be passed to `run_pass`
# as a test. Use the `$TUT_DIR` environment variable to obtain the path to the
# `etc/tutorial/NAME` directory.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
skip_all "skipped: @TODO: Awaiting App upgrade to Python3"
#-------------------------------------------------------------------------------
# Generate list of tests.
TEST_KEYS=('')
TUT_DIRS=('')
TESTS=('')
TUTORIALS_PATH="${ROSE_HOME}/etc/tutorial"
for tutorial in $(ls -1 "${TUTORIALS_PATH}"); do
    tutorial_path="${TUTORIALS_PATH}/${tutorial}"
    validate_file="${tutorial_path}/.validate"
    if [[ -f "${tutorial_path}" ]]; then
        # Tutorial is a file, skip.
        continue
    fi
    if [[ -f "${validate_file}" ]]; then
        # Tutorial has a validate file - load tests.
        IFS=$'\n' TUT_TESTS=($(<"${validate_file}"))
        if [[ ${#TUT_TESTS[@]} == 0 ]]; then
            # Tutorial has an empty validate file - skip.
            continue
        fi
        TESTS=("${TESTS[@]}" "${TUT_TESTS[@]}")
        # Test names are TUTORIAL_NAME-TEST_NUMBER.
        for IND in $(seq 0 $(( ${#TUT_TESTS[@]} - 1 ))); do
            TEST_KEYS+=( "${tutorial}-$IND" )
            TUT_DIRS+=( "$tutorial_path" )
        done
    else
        # Tutorial has no validate file - run cylc validate.
        TESTS+=('cylc validate "'"${tutorial_path}/suite.rc"'"')
        TEST_KEYS+=("${tutorial}-0")
        TUT_DIRS+=( "$tutorial_path" )
        continue
    fi
done
tests $(( ( ${#TESTS[@]} - 1 ) * 2 ))
#-------------------------------------------------------------------------------
# Run the tests.
mkdir "${HOME}/cylc-run" -p
export REG_BASE=$(mktemp -d --tmpdir="${HOME}/cylc-run" |xargs basename)
for IND in $(seq 1 $(( ${#TEST_KEYS[@]} - 1 ))); do
    TEST_KEY="${TEST_KEY_BASE}-${TEST_KEYS[$IND]}"
    export TUT_DIR="${TUT_DIRS[$IND]}"
    export CYLC_RUN_DIR="${HOME}/cylc-run/"
    export REG="${REG_BASE}/$(basename $TUT_DIR)"
    run_pass "${TEST_KEY}" bash -c "${TESTS[$IND]}"
    file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" /dev/null
done
rm -rf "${HOME}/cylc-run/${REG_BASE}"
#-------------------------------------------------------------------------------
exit
