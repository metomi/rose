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
# Test "rose suite-run" with "site=SITE" setting in site/user conf.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
skip_all "TEST-DISABLED: Awaiting App upgrade to Python3"

N_TESTS=3
tests "${N_TESTS}"
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH="${PWD}/conf"
export ROOT_DIR_WORK="${PWD}"
mkdir -p 'conf'
cat >'conf/rose.conf' <<'__CONF__'
site=my-site
__CONF__

#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
touch "${SUITE_RUN_DIR}/rose-suite.conf"
cat >"$SUITE_RUN_DIR/suite.rc" <<'__SUITE_RC__'
#!jinja2
[cylc]
UTC mode=True
[scheduling]
[[dependencies]]
graph=x
[runtime]
[[x]]
__SUITE_RC__
NAME="$(basename "${SUITE_RUN_DIR}")"
CYLC_VERSION="$(cylc --version)"
ROSE_ORIG_HOST="$(hostname)"
ROSE_VERSION="$(rose --version | cut -d' ' -f2)"
for I in $(seq 1 "${N_TESTS}"); do
    rose suite-run -C"${SUITE_RUN_DIR}" --name="${NAME}" -l -q --debug || break
    file_cmp "${TEST_KEY}-${I}" "${SUITE_RUN_DIR}/suite.rc" <<__SUITE_RC__
#!jinja2
{# Rose Configuration Insertion: Init #}
{% set CYLC_VERSION="${CYLC_VERSION}" %}
{% set ROSE_ORIG_HOST="${ROSE_ORIG_HOST}" %}
{% set ROSE_SITE="my-site" %}
{% set ROSE_VERSION="${ROSE_VERSION}" %}
[cylc]
    [[environment]]
        CYLC_VERSION=${CYLC_VERSION}
        ROSE_ORIG_HOST=${ROSE_ORIG_HOST}
        ROSE_SITE=my-site
        ROSE_VERSION=${ROSE_VERSION}
{# Rose Configuration Insertion: Done #}
[cylc]
UTC mode=True
[scheduling]
[[dependencies]]
graph=x
[runtime]
[[x]]
__SUITE_RC__
done
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit
