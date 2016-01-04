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
# Test "rose help" on alias commands.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 14
#-------------------------------------------------------------------------------
export PAGER=cat

cat >'rose-aliases.txt' <<'__TXT__'
config-edit edit
suite-gcontrol sgc
suite-hook task-hook
suite-log slv suite-log-view
__TXT__
cat >'rosie-aliases.txt' <<'__TXT__'
checkout co
create copy
__TXT__
#-------------------------------------------------------------------------------
for PREFIX in 'rose' 'rosie'; do
    while read; do
        COMMAND=$(cut -d' ' -f 1 <<<"${REPLY}")
        "${PREFIX}" help "${COMMAND}" >'help.txt'
        for COMMAND_ALIAS in $(cut -d' ' -f 2- <<<"${REPLY}"); do
            TEST_KEY="${TEST_KEY_BASE}-${COMMAND_ALIAS}"
            run_pass "${TEST_KEY}" "${PREFIX}" help "${COMMAND_ALIAS}"
            file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" 'help.txt'
        done
    done <"${PREFIX}-aliases.txt"
done
#-------------------------------------------------------------------------------
exit
