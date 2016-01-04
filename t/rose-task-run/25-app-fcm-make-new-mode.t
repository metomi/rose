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
# * new mode, orig make only
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
tests 3
export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"

SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${SUITE_RUN_DIR}")"

# Add some garbage before running the suite
mkdir -p "${SUITE_RUN_DIR}/share/hello-make/junk2"
touch "${SUITE_RUN_DIR}/share/hello-make/junk1"

timeout 120 rose suite-run -q --debug \
    -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --host='localhost' -- --debug
#-------------------------------------------------------------------------------
file_cmp "${TEST_KEY_BASE}" "${SUITE_RUN_DIR}/share/hello.txt" <<__TXT__
${SUITE_RUN_DIR}/share/hello-make/build/bin/hello
Hello World!
__TXT__
file_grep "${TEST_KEY_BASE}-fcm-make.log" \
    '\[info\] mode=new' "${SUITE_RUN_DIR}/share/hello-make/fcm-make.log"
run_fail "${TEST_KEY_BASE}" ls \
    "${SUITE_RUN_DIR}/share/hello-make/junk1" \
    "${SUITE_RUN_DIR}/share/hello-make/junk2"
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
