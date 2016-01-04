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
# Test "rose suite-run" in $HOME/cylc-run to ensure that insertion of jinja2
# variable declarations to "suite.rc" do not get repeated.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
N_TESTS=3
tests $N_TESTS
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
cat >$SUITE_RUN_DIR/rose-suite.conf <<__ROSE_SUITE_CONF__
[jinja2:suite.rc]
foo="food store"
bar="barley drink"
__ROSE_SUITE_CONF__
cat >"$SUITE_RUN_DIR/suite.rc" <<__SUITE_RC__
#!jinja2
{% set egg="egg sandwich" %}
{% set ham="hamburger" %}
[cylc]
UTC mode=True
[scheduling]
[[dependencies]]
graph=x
[runtime]
[[x]]
__SUITE_RC__
NAME=$(basename $SUITE_RUN_DIR)
CYLC_VERSION=$(cylc --version)
ROSE_ORIG_HOST=$(hostname)
ROSE_VERSION=$(rose --version | cut -d' ' -f2)
for I in $(seq 1 $N_TESTS); do
    rose suite-run -C$SUITE_RUN_DIR --name=$NAME -l -q --debug || break
    file_cmp "$TEST_KEY" "$SUITE_RUN_DIR/suite.rc" <<__SUITE_RC__
#!jinja2
{# Rose Configuration Insertion: Init #}
{% set CYLC_VERSION="$CYLC_VERSION" %}
{% set ROSE_ORIG_HOST="$ROSE_ORIG_HOST" %}
{% set ROSE_VERSION="$ROSE_VERSION" %}
{% set bar="barley drink" %}
{% set foo="food store" %}
{# Rose Configuration Insertion: Done #}
{% set egg="egg sandwich" %}
{% set ham="hamburger" %}
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
rose suite-clean -q -y $NAME --debug
exit 0
