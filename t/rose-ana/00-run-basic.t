#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
# Test fcm_make built-in application, basic usages.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
N_TESTS=13
tests $N_TESTS
#-------------------------------------------------------------------------------
# Run the suite.
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --debug
#-------------------------------------------------------------------------------
# Test the output
OUTPUT=$HOME/cylc-run/$NAME/log/job/1/rose_ana_t1/01/job.out
TEST_KEY=$TEST_KEY_BASE-exact_numeric_success
file_grep $TEST_KEY "[ OK ].*Semi-major Axis.*all: 0%:" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_numeric_fail
file_grep $TEST_KEY "[FAIL].*Orbital Period.*1: 5.234%" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_text_success
file_grep $TEST_KEY "[ OK ].*Atmosphere.*all: 0%" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_text_fail
file_grep $TEST_KEY "[FAIL].*Planet.*1: XX%.* (4 values)" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_percentage_success
file_grep $TEST_KEY "[ OK ].*Oxygen Partial Pressure.*all% <= 5%" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_percentage_fail
file_grep $TEST_KEY "[FAIL].*Ocean coverage.*35.3107344633% > 5%:.* (95.8) c.f. .* (70.8)" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_absolute_success
file_grep $TEST_KEY "[ OK ].*Surface Gravity.*all% <= 1.0:" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_absolute_fail
file_grep $TEST_KEY "[FAIL].*Rotation Period.*7.04623622489% > 0.05:.* (0.927) c.f. .* (0.99727)" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_list_success
file_grep $TEST_KEY "[ OK ].*Satellites Natural/Artificial.*all: 0%:" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_list_fail
file_grep $TEST_KEY "[FAIL].*Other Planets.*1: XX%:.* (4 values)" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_list_success
file_grep $TEST_KEY "[ OK ].*Periastron/Apastron.*all% <= 5%:" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_list_fail
file_grep $TEST_KEY "[FAIL].*Inclination/Axial Tilt.*285.744234801% > 5%:.* (value 1 of 2)" $OUTPUT
#-------------------------------------------------------------------------------
#Clean suite
rose suite-clean -q -y $NAME
#-------------------------------------------------------------------------------
exit 0
