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
# Test fcm_make built-in application:
# * fast dest root
#
# N.B. Test requires compatible versions of "rose" and "fcm make", as well as
#      "gfortran" being installed and available.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

if ! fcm help make 1>/dev/null 2>&1; then
    skip_all '"fcm make" unavailable'
fi
if ! gfortran --version 1>/dev/null 2>&1; then
    skip_all '"gfortran" unavailable'
fi
#-------------------------------------------------------------------------------
tests 7
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=
mkdir 'fast'
MTIME_OF_FAST_BEFORE=$(stat '-c%y' 'fast')
#-------------------------------------------------------------------------------
get_reg
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
        --flow-name="${FLOW}" \
        --no-run-name
run_pass "${TEST_KEY_BASE}-play" \
    timeout 120 \
        cylc play \
            "${FLOW}" \
            -s "FAST_DEST_ROOT='${PWD}/fast'" \
            --abort-if-any-task-fails \
            --host='localhost' \
            --no-detach \
            --debug
#-------------------------------------------------------------------------------
# Permission modes of make directory should be the same as a normal directory
mkdir "${FLOW_RUN_DIR}/share/hello-make-perm-mode-test"
run_pass "${TEST_KEY_BASE}-perm-mode" test \
    "$(stat -c'%a' "${FLOW_RUN_DIR}/share/hello-make-perm-mode-test")" = \
    "$(stat -c'%a' "${FLOW_RUN_DIR}/share/hello-make")"
rmdir "${FLOW_RUN_DIR}/share/hello-make-perm-mode-test"
# Executable runs OK
file_cmp "${TEST_KEY_BASE}" "${FLOW_RUN_DIR}/share/hello.txt" <<__TXT__
${FLOW_RUN_DIR}/share/hello-make/build/bin/hello
Hello World!
__TXT__
# Logs
HOST=$(hostname)
file_grep "${TEST_KEY_BASE}.log" \
    "\\[info\\] dest=${USER}@${HOST}:${PWD}/fast/hello-make.1.${FLOW//\//_}" \
    "${FLOW_RUN_DIR}/share/hello-make/fcm-make.log"
file_grep "${TEST_KEY_BASE}-bin.log" \
    "\\[info\\] dest=${USER}@${HOST}:${PWD}/fast/hello-make-bin.1.${FLOW//\//_}" \
    "${FLOW_RUN_DIR}/share/hello-make/fcm-make-bin.log"
# Prove that the fast directory has been modified
MTIME_OF_FAST_AFTER=$(stat '-c%y' 'fast')
run_pass "${TEST_KEY_BASE}-mtime-of-fast" \
    test "${MTIME_OF_FAST_BEFORE}" '!=' "${MTIME_OF_FAST_AFTER}"
#-------------------------------------------------------------------------------
purge
exit 0
