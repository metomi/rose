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
# Test "rose suite-run" installation of share/cycle/ sub-directory.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

tests 2
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH="${PWD}/conf"
export ROOT_DIR_WORK="${PWD}"
mkdir -p 'conf'
cat >'conf/rose.conf' <<'__CONF__'
[rose-suite-run]
root-dir{share/cycle}=*=$ROOT_DIR_WORK
__CONF__

mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${SUITE_RUN_DIR}")"
rose suite-run --no-gcontrol -q \
    -n "${NAME}" -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" -- --debug >&2
ls -l
# Check contents of files written to ROSE_DATAC is going to $PWD/share/cycle/
for DATETIME in '20200101T0000Z' '20200101T0000Z'; do
    file_cmp "nl-${DATETIME}" \
        "${PWD}/cylc-run/${NAME}/share/cycle/${DATETIME}/share.nl" <<__NL__
&share_nl
date=${DATETIME},
index=ftse,
market=lse,
/
__NL__
done
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit
