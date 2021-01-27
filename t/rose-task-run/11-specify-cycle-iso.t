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
# Test "rose task-run" and "rose task-env": specify cycle.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

export ROSE_CONF_PATH=

#-------------------------------------------------------------------------------
# Run the suite.
tests 3
TEST_KEY=$TEST_KEY_BASE
get_reg
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        -C "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --flow-name="$FLOW" \
        --no-run-name
run_pass "${TEST_KEY_BASE}-run" \
    cylc run \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
file_cmp "$TEST_KEY" "$FLOW_RUN_DIR/file" <<<'20121231T1200Z'
cylc clean "$FLOW"
exit 0
