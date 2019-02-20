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
# Test "rose suite-run", match TIMESTAMP of local and remote log.TIMESTAMP/
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
skip_all "@TODO: Awaiting App upgrade to Python3"
JOB_HOST="$(rose config --default= 't' 'job-host')"
if [[ -n "${JOB_HOST}" ]]; then
    JOB_HOST="$(rose host-select -q "${JOB_HOST}")"
fi
if [[ -z "${JOB_HOST}" ]]; then
    skip_all '"[t]job-host" not defined'
fi
tests 3
export ROSE_CONF_PATH="${PWD}/conf"
export PATH="${PWD}/bin:${PATH}"
mkdir 'bin' 'conf'
cat >'bin/myssh' <<'__BASH__'
#!/bin/bash
# Make sure that local and remote log cannot be created in the same second
sleep 1
# Print arguments to log file
echo "$@" >"$(dirname "$0")/../myssh.log"
# Invoke real SSH
exec ssh "$@"
__BASH__
chmod +x 'bin/myssh'
cat >'conf/rose.conf' <<'__CONF__'
[external]
ssh=myssh -oBatchMode=yes -oConnectTimeout=10
__CONF__
rsync -a "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}/" '.'
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename ${SUITE_RUN_DIR})"
run_pass "${TEST_KEY_BASE}" \
    rose suite-run --debug --name="${NAME}" --no-gcontrol \
    -S "HOST=\"${JOB_HOST}\"" -- --no-detach
NOW_STR="$(sed 's/^.*now-str=\([^,]*\),\?.*$/\1/' 'myssh.log')"
run_pass "${TEST_KEY_BASE}-log-timestamp-local" \
    test -d "${SUITE_RUN_DIR}/log.${NOW_STR}"
run_pass "${TEST_KEY_BASE}-log-timestamp-remote" \
    ssh -n -oBatchMode='yes' "${JOB_HOST}" \
    "test -d cylc-run/${NAME}/log.${NOW_STR}"
rose suite-clean -q -y "${NAME}"
exit 0
