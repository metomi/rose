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
# Test "rose suite-run" when port file exists.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
#-------------------------------------------------------------------------------
tests 3
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
mkdir -p "${HOME}/.cylc/ports"
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rtb-suite-run-07.XXXXXX')"
NAME="$(basename "${SUITE_RUN_DIR}")"

PORT="$((${RANDOM} + 10000))"
while port_is_busy "${PORT}"; do
    PORT="$((${RANDOM} + 10000))"
done

HOST="$(hostname -f)"
cat >"${HOME}/.cylc/ports/${NAME}" <<__PORT_FILE__
${PORT}
${HOST}
__PORT_FILE__

TEST_KEY="${TEST_KEY_BASE}"
touch "${SUITE_RUN_DIR}/flag"
run_pass "${TEST_KEY}" \
    rose suite-run -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
    --name="${NAME}" --no-gcontrol -- --debug
file_grep "${TEST_KEY}.out" \
    "delete: ${HOME}/.cylc/ports/${NAME}" "${TEST_KEY}.out"
sed -i '/no HTTPS support/d' "${TEST_KEY}.err"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
