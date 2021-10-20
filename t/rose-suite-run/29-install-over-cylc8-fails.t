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
# Test that rose suite-run will not install a suite over the top of a cylc 8
# workflow installation.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
#-------------------------------------------------------------------------------
tests 10


mock_cylc8_install() {
    # Create a mocked up Cylc 8 Installed workflow.
    FLOW_NAME="${1:-}"
    UUID=$(uuidgen)
    WORKFLOW_NAME="rose-test-battery-${UUID::10}/${FLOW_NAME}"
    CYLC_RUN_DIR=$(cylc get-global-config -i '[hosts][localhost]run directory')
    INSTALLED_WORKFLOW_PATH="${CYLC_RUN_DIR}/${WORKFLOW_NAME}"
    mkdir -p "${INSTALLED_WORKFLOW_PATH}"
    export INSTALLED_WORKFLOW_PATH
}

# Create a Rose 1 Suite to try installing:
ROSE_1_SUITE_SRC="${PWD}/rose1-suite"
mkdir "${ROSE_1_SUITE_SRC}"
cat > "${ROSE_1_SUITE_SRC}/suite.rc" <<__HEREDOC__
[scheduling]
    initial cycle point = 1500
    [[dependencies]]
        [[[R1]]]
            graph = foo
[runtime]
    [[foo]]
        script = true
__HEREDOC__
touch "${ROSE_1_SUITE_SRC}/rose-suite.conf"


# Don't overwrite a Cylc 8 workflow installed in the top level dir.
# > cylc install simplest --flow-name s.6 --no-run-name
# |-- _cylc-install
# |-- flow.cylc
mock_cylc8_install
TEST_NAME="${TEST_KEY_BASE}-no-run-dir"
mkdir "${INSTALLED_WORKFLOW_PATH}/_cylc-install"
mkdir "${INSTALLED_WORKFLOW_PATH}/flow.cylc"
run_fail "${TEST_NAME}" rose suite-run -i -C "${ROSE_1_SUITE_SRC}" --name="$WORKFLOW_NAME"
file_grep "${TEST_NAME}-error" "already has a Cylc 8 workflow installed." "${TEST_NAME}.err"
rm -fr "$INSTALLED_WORKFLOW_PATH"

# Don't over-write a simply installed Cylc 8 workflow with numbered runs.
# > cylc install simplest
# |-- _cylc-install
# |-- run1
# |   |-- flow.cylc
mock_cylc8_install
mkdir "${INSTALLED_WORKFLOW_PATH}/_cylc-install"
mkdir -p "${INSTALLED_WORKFLOW_PATH}/run1/flow.cylc"
run_fail "${TEST_KEY_BASE}" rose suite-run -i -C "${ROSE_1_SUITE_SRC}" --name="$WORKFLOW_NAME"
file_grep "${TEST_KEY_BASE}-error" "already has a Cylc 8 workflow installed." "${TEST_KEY_BASE}.err"
rm -fr "$INSTALLED_WORKFLOW_PATH"

# Don't over-write a simply installed Cylc 8 workflow with named runs.
# > cylc install simplest --flow-name s.7 --run-name=bar
# |-- _cylc-install
# `-- bar
#     |-- flow.cylc
mock_cylc8_install
TEST_NAME="${TEST_KEY_BASE}--run-name"
mkdir "${INSTALLED_WORKFLOW_PATH}/_cylc-install"
mkdir -p "${INSTALLED_WORKFLOW_PATH}/foo/flow.cylc"
run_fail "${TEST_NAME}" rose suite-run -i -C "${ROSE_1_SUITE_SRC}" --name="$WORKFLOW_NAME"
file_grep "${TEST_NAME}-error" "already has a Cylc 8 workflow installed." "${TEST_NAME}.err"
rm -fr "$INSTALLED_WORKFLOW_PATH"

# Don't over-write a directory containing a Cylc 8 install
# > cylc install simplest --flow-name s.5/foo
# `-- foo
#     |-- _cylc-install
#     |-- run1
#     |   |-- flow.cylc
mock_cylc8_install
TEST_NAME="${TEST_KEY_BASE}-into-parent"
mkdir -p "${INSTALLED_WORKFLOW_PATH}/my_workflow/_cylc-install"
mkdir -p "${INSTALLED_WORKFLOW_PATH}/my_workflow/run1/flow.cylc"
run_fail "${TEST_NAME}" rose suite-run -i -C "${ROSE_1_SUITE_SRC}" --name="$WORKFLOW_NAME"
file_grep "${TEST_NAME}-error" "already has a Cylc 8 workflow installed." "${TEST_NAME}.err"
rm -fr "$INSTALLED_WORKFLOW_PATH"

# We want to rose suite-run install into a subdirectory of a Location with a
# Cylc-8 workflow:
# > cylc install simplest
# |-- _cylc-install
# |-- run1
# |   |-- flow.cylc
# |-- install/Rose1/suite/here
mock_cylc8_install
TEST_NAME="${TEST_KEY_BASE}-grandchild"
mkdir -p "${INSTALLED_WORKFLOW_PATH}/_cylc-install"
mkdir -p "${INSTALLED_WORKFLOW_PATH}/run1/flow.cylc"
run_fail "${TEST_NAME}" rose suite-run -i -C "${ROSE_1_SUITE_SRC}" \
    --name "${INSTALLED_WORKFLOW_PATH}baz"
echo "${ROSE_1_SUITE_SRC}" "${INSTALLED_WORKFLOW_PATH}/baz" >&2
file_grep "${TEST_NAME}-error" "already has a Cylc 8 workflow installed." "${TEST_NAME}.err"
rm -fr "$INSTALLED_WORKFLOW_PATH"
