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
# Compatibility Mode Test
# Ensure that when Cylc Rose gets workflow config that
# compatibility run mode isn't changed.
# https://github.com/cylc/cylc-rose/issues/319
# To do this we check that the error for the fcm_make task derives
# from the platform for the fcm_make2 task is garbage,
# not from the config becoming illegal because compat mode has
# been switched off.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

tests 3
export ROSE_CONF_PATH=
get_reg

run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        --workflow-name="${FLOW}" \
        --no-run-name \
        "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}"

run_fail "${TEST_KEY_BASE}-play" \
    timeout 120 \
        cylc play \
            "${FLOW}" \
            --abort-if-any-task-fails \
            --host='localhost' \
            --no-detach \
            --debug

# It is a compat mode error.
# If we had turned compat mode off this would be a graphing error:
#   "Output fcm_make:failed can't be both required and optional"
file_grep "${TEST_KEY_BASE}-grep-failure" \
    'No matching platform "any_old_thing" found' \
    "${HOME}/cylc-run/${FLOW}/log/job/1/fcm_make/NN/job.err"

purge
exit 0
