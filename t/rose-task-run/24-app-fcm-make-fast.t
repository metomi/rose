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
tests 5
export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"
mkdir 'fast'
MTIME_OF_FAST_BEFORE=$(stat '-c%y' 'fast')
#-------------------------------------------------------------------------------
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${SUITE_RUN_DIR}")"
timeout 120 rose suite-run -q --debug \
    -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --host='localhost' -S "FAST_DEST_ROOT=\"${PWD}/fast\"" \
    -- --debug
#-------------------------------------------------------------------------------
# Permission modes of make directory should be the same as a normal directory
mkdir "${SUITE_RUN_DIR}/share/hello-make-perm-mode-test"
run_pass "${TEST_KEY_BASE}-perm-mode" test \
    "$(stat -c'%a' "${SUITE_RUN_DIR}/share/hello-make-perm-mode-test")" = \
    "$(stat -c'%a' "${SUITE_RUN_DIR}/share/hello-make")"
rmdir "${SUITE_RUN_DIR}/share/hello-make-perm-mode-test"
# Executable runs OK
file_cmp "${TEST_KEY_BASE}" "${SUITE_RUN_DIR}/share/hello.txt" <<__TXT__
${SUITE_RUN_DIR}/share/hello-make/build/bin/hello
Hello World!
__TXT__
# Logs
HOST=$(hostname)
file_grep "${TEST_KEY_BASE}.log" \
    "\\[info\\] dest=${USER}@${HOST}:${PWD}/fast/hello-make.1.${NAME}" \
    "${SUITE_RUN_DIR}/share/hello-make/fcm-make.log"
file_grep "${TEST_KEY_BASE}-bin.log" \
    "\\[info\\] dest=${USER}@${HOST}:${PWD}/fast/hello-make-bin.1.${NAME}" \
    "${SUITE_RUN_DIR}/share/hello-make/fcm-make-bin.log"
# Prove that the fast directory has been modified
MTIME_OF_FAST_AFTER=$(stat '-c%y' 'fast')
run_pass "${TEST_KEY_BASE}-mtime-of-fast" \
    test "${MTIME_OF_FAST_BEFORE}" '!=' "${MTIME_OF_FAST_AFTER}"
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
