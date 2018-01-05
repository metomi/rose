#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
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
#-------------------------------------------------------------------------------
# Generate list of tests.
TEST_KEYS=('')
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
        DIR=$(sed 's/\//\\\//g' <<< "${tutorial_path}")
        CMD='sed '"'"'s/$TUT_DIR/'"${DIR}"'/g'"' "'"'"${validate_file}"'"'
        IFS=$'\n' command eval 'TUT_TESTS=($('"${CMD}"'))'
        if [[ ${#TUT_TESTS[@]} == 0 ]]; then
            # Tutorial has an empty validate file - skip.
            continue
        fi
        TESTS=("${TESTS[@]}" "${TUT_TESTS[@]}")
        # Test names are TUTORIAL_NAME-TEST_NUMBER.
        for IND in $(seq 0 $(( ${#TUT_TESTS[@]} - 1 ))); do
            TEST_KEYS+=( "${tutorial}-$IND" )
        done
    else
        # Tutorial has no validate file - run cylc validate.
        TESTS+=('cylc validate "'"${tutorial_path}/suite.rc"'"')
        TEST_KEYS+=("${tutorial}-0")
        continue
    fi
done
tests $(( ( ${#TESTS[@]} - 1 ) * 2 ))
#-------------------------------------------------------------------------------
# Run the tests.
for IND in $(seq 1 $(( ${#TEST_KEYS[@]} - 1 ))); do
    TEST_KEY="${TEST_KEY_BASE}-${TEST_KEYS[$IND]}"
    run_pass "${TEST_KEY}" eval "${TESTS[$IND]}"
    file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" /dev/null
done
#-------------------------------------------------------------------------------
exit 0
