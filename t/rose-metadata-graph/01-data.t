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
# Rose is distributed in the hope that it will be useful
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
# Test "rose metadata-graph" against configuration and configuration metadata.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header_extra
. $(dirname $0)/test_header

python3 -c "import pygraphviz" 2>/dev/null || \
    skip_all '"pygraphviz" not installed'
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Check full graphing of our example configuration & configuration metadata.
TEST_KEY=$TEST_KEY_BASE-ok-full
setup
init < $TEST_SOURCE_DIR/lib/rose-app.conf
init_meta < $TEST_SOURCE_DIR/lib/rose-meta.conf
CONFIG_PATH=$(cd ../config && pwd -P)
run_pass "$TEST_KEY" rose metadata-graph --debug --config=../config
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
sort "$TEST_KEY.filtered.out" >"$TEST_KEY.filtered.out.sorted" 
sort >"$TEST_KEY.filtered.out.expected" <<__OUTPUT__
"env=CONTROL" -> "env=CONTROL=None" [color=green, label=foo
"env=CONTROL" -> "env=CONTROL=bar" [color=red, label=foo
"env=CONTROL" -> "env=CONTROL=baz" [color=red, label=foo
"env=CONTROL" -> "env=CONTROL=foo" [color=green, label=foo
"env=CONTROL" [color=green
"env=CONTROL=None" -> "env=DEPENDENT3" [color=green
"env=CONTROL=None" [color=green, label=None, shape=box, style=filled
"env=CONTROL=bar" -> "env=DEPENDENT1" [color=red
"env=CONTROL=bar" -> "env=DEPENDENT2" [color=red
"env=CONTROL=bar" -> "env=DEPENDENT_MISSING1" [arrowhead=empty, color=red
"env=CONTROL=bar" [color=red, label=bar, shape=box, style=filled
"env=CONTROL=baz" -> "env=DEPENDENT1" [color=red
"env=CONTROL=baz" [color=red, label=baz, shape=box, style=filled
"env=CONTROL=foo" -> "env=DEPENDENT_MISSING1" [color=green
"env=CONTROL=foo" [color=green, label=foo, shape=box, style=filled
"env=CONTROL_NAMELIST_QUX" -> "env=CONTROL_NAMELIST_QUX=bar" [color=red, label=foo
"env=CONTROL_NAMELIST_QUX" [color=green
"env=CONTROL_NAMELIST_QUX=bar" -> "namelist:qux" [color=red
"env=CONTROL_NAMELIST_QUX=bar" [color=red, label=bar, shape=box, style=filled
"env=CONTROL_NAMELIST_WIBBLE" -> "env=CONTROL_NAMELIST_WIBBLE=bar" [color=green, label=bar
"env=CONTROL_NAMELIST_WIBBLE" [color=green
"env=CONTROL_NAMELIST_WIBBLE=bar" -> "namelist:wibble" [color=green
"env=CONTROL_NAMELIST_WIBBLE=bar" [color=green, label=bar, shape=box, style=filled
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" -> "env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=red, label=foo
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" [color=green
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" -> "namelist:wibble=wubble" [color=red
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=red, label=bar, shape=box, style=filled
"env=DEPENDENT1" [color=red, label="!!env=DEPENDENT1"
"env=DEPENDENT2" [color=red, label="!!env=DEPENDENT2"
"env=DEPENDENT3" [color=green
"env=DEPENDENT_DEPENDENT1" [color=red, label="!!env=DEPENDENT_DEPENDENT1"
"env=DEPENDENT_MISSING1" -> "env=DEPENDENT_MISSING1=None" [color=grey
"env=DEPENDENT_MISSING1" [color=grey
"env=DEPENDENT_MISSING1=None" -> "env=DEPENDENT_DEPENDENT1" [color=grey
"env=DEPENDENT_MISSING1=None" [color=grey, label=None, shape=box, style=filled
"env=MISSING_VARIABLE" [color=grey
"env=USER_IGNORED" [color=orange, label="!env=USER_IGNORED"
"namelist:qux" [color=red, label="!!namelist:qux", shape=octagon
"namelist:qux=wobble" -> "namelist:qux=wobble=.true." [color=red, label=".false."
"namelist:qux=wobble" [color=red, label="^namelist:qux=wobble"
"namelist:qux=wobble=.true." -> "namelist:qux=wubble" [color=red
"namelist:qux=wobble=.true." [color=red, label=".true.", shape=box, style=filled
"namelist:qux=wubble" [color=red, label="^!!namelist:qux=wubble"
"namelist:wibble" [color=green, shape=octagon
"namelist:wibble=wobble" -> "namelist:wibble=wobble=.true." [color=green, label=".true."
"namelist:wibble=wobble" [color=green
"namelist:wibble=wobble=.true." -> "namelist:wibble=wubble" [color=green
"namelist:wibble=wobble=.true." [color=green, label=".true.", shape=box, style=filled
"namelist:wibble=wubble" [color=red, label="!!namelist:wibble=wubble"
env [color=green, shape=octagon
graph [label="$CONFIG_PATH", rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.out" \
    "$TEST_KEY.filtered.out.sorted" "$TEST_KEY.filtered.out.expected"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Check specific section graphing.
TEST_KEY=$TEST_KEY_BASE-ok-sub-section
run_pass "$TEST_KEY" rose metadata-graph --debug --config=../config namelist:qux
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
sort "$TEST_KEY.filtered.out" >"$TEST_KEY.filtered.out.sorted" 
sort >"$TEST_KEY.filtered.out.expected" <<__OUTPUT__
"env=CONTROL_NAMELIST_QUX" -> "env=CONTROL_NAMELIST_QUX=bar" [color=red, label=foo
"env=CONTROL_NAMELIST_QUX" [color=green, shape=rectangle
"env=CONTROL_NAMELIST_QUX=bar" -> "namelist:qux" [color=red
"env=CONTROL_NAMELIST_QUX=bar" [color=red, label=bar, shape=box, style=filled
"namelist:qux" [color=red, label="!!namelist:qux", shape=octagon
"namelist:qux=wobble" -> "namelist:qux=wobble=.true." [color=red, label=".false."
"namelist:qux=wobble" [color=red, label="^namelist:qux=wobble"
"namelist:qux=wobble=.true." -> "namelist:qux=wubble" [color=red
"namelist:qux=wobble=.true." [color=red, label=".true.", shape=box, style=filled
"namelist:qux=wubble" [color=red, label="^!!namelist:qux=wubble"
graph [label="$CONFIG_PATH: namelist:qux", rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.out" \
    "$TEST_KEY.filtered.out.sorted" "$TEST_KEY.filtered.out.expected"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Check specific property graphing.
TEST_KEY=$TEST_KEY_BASE-ok-property
run_pass "$TEST_KEY" rose metadata-graph --debug --config=../config \
    --property=trigger
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
sort "$TEST_KEY.filtered.out" >"$TEST_KEY.filtered.out.sorted" 
sort >"$TEST_KEY.filtered.out.expected" <<__OUTPUT__
"env=CONTROL" -> "env=CONTROL=None" [color=green, label=foo
"env=CONTROL" -> "env=CONTROL=bar" [color=red, label=foo
"env=CONTROL" -> "env=CONTROL=baz" [color=red, label=foo
"env=CONTROL" -> "env=CONTROL=foo" [color=green, label=foo
"env=CONTROL" [color=green
"env=CONTROL=None" -> "env=DEPENDENT3" [color=green
"env=CONTROL=None" [color=green, label=None, shape=box, style=filled
"env=CONTROL=bar" -> "env=DEPENDENT1" [color=red
"env=CONTROL=bar" -> "env=DEPENDENT2" [color=red
"env=CONTROL=bar" -> "env=DEPENDENT_MISSING1" [arrowhead=empty, color=red
"env=CONTROL=bar" [color=red, label=bar, shape=box, style=filled
"env=CONTROL=baz" -> "env=DEPENDENT1" [color=red
"env=CONTROL=baz" [color=red, label=baz, shape=box, style=filled
"env=CONTROL=foo" -> "env=DEPENDENT_MISSING1" [color=green
"env=CONTROL=foo" [color=green, label=foo, shape=box, style=filled
"env=CONTROL_NAMELIST_QUX" -> "env=CONTROL_NAMELIST_QUX=bar" [color=red, label=foo
"env=CONTROL_NAMELIST_QUX" [color=green
"env=CONTROL_NAMELIST_QUX=bar" -> "namelist:qux" [color=red
"env=CONTROL_NAMELIST_QUX=bar" [color=red, label=bar, shape=box, style=filled
"env=CONTROL_NAMELIST_WIBBLE" -> "env=CONTROL_NAMELIST_WIBBLE=bar" [color=green, label=bar
"env=CONTROL_NAMELIST_WIBBLE" [color=green
"env=CONTROL_NAMELIST_WIBBLE=bar" -> "namelist:wibble" [color=green
"env=CONTROL_NAMELIST_WIBBLE=bar" [color=green, label=bar, shape=box, style=filled
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" -> "env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=red, label=foo
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" [color=green
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" -> "namelist:wibble=wubble" [color=red
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=red, label=bar, shape=box, style=filled
"env=DEPENDENT1" [color=red, label="!!env=DEPENDENT1"
"env=DEPENDENT2" [color=red, label="!!env=DEPENDENT2"
"env=DEPENDENT3" [color=green
"env=DEPENDENT_DEPENDENT1" [color=red, label="!!env=DEPENDENT_DEPENDENT1"
"env=DEPENDENT_MISSING1" -> "env=DEPENDENT_MISSING1=None" [color=grey
"env=DEPENDENT_MISSING1" [color=grey
"env=DEPENDENT_MISSING1=None" -> "env=DEPENDENT_DEPENDENT1" [color=grey
"env=DEPENDENT_MISSING1=None" [color=grey, label=None, shape=box, style=filled
"env=MISSING_VARIABLE" [color=grey
"env=USER_IGNORED" [color=orange, label="!env=USER_IGNORED"
"namelist:qux" [color=red, label="!!namelist:qux", shape=octagon
"namelist:qux=wobble" -> "namelist:qux=wobble=.true." [color=red, label=".false."
"namelist:qux=wobble" [color=red, label="^namelist:qux=wobble"
"namelist:qux=wobble=.true." -> "namelist:qux=wubble" [color=red
"namelist:qux=wobble=.true." [color=red, label=".true.", shape=box, style=filled
"namelist:qux=wubble" [color=red, label="^!!namelist:qux=wubble"
"namelist:wibble" [color=green, shape=octagon
"namelist:wibble=wobble" -> "namelist:wibble=wobble=.true." [color=green, label=".true."
"namelist:wibble=wobble" [color=green
"namelist:wibble=wobble=.true." -> "namelist:wibble=wubble" [color=green
"namelist:wibble=wobble=.true." [color=green, label=".true.", shape=box, style=filled
"namelist:wibble=wubble" [color=red, label="!!namelist:wibble=wubble"
env [color=green, shape=octagon
graph [label="$CONFIG_PATH (trigger)", rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.out" \
    "$TEST_KEY.filtered.out.sorted" "$TEST_KEY.filtered.out.expected"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Check specific section and specific property graphing.
TEST_KEY=$TEST_KEY_BASE-ok-property-sub-section
run_pass "$TEST_KEY" rose metadata-graph --debug --config=../config \
    --property=trigger env
filter_graphviz <"$TEST_KEY.out" >"$TEST_KEY.filtered.out"
sort "$TEST_KEY.filtered.out" >"$TEST_KEY.filtered.out.sorted" 
sort >"$TEST_KEY.filtered.out.expected" <<__OUTPUT__
"env=CONTROL" -> "env=CONTROL=None" [color=green, label=foo
"env=CONTROL" -> "env=CONTROL=bar" [color=red, label=foo
"env=CONTROL" -> "env=CONTROL=baz" [color=red, label=foo
"env=CONTROL" -> "env=CONTROL=foo" [color=green, label=foo
"env=CONTROL" [color=green
"env=CONTROL=None" -> "env=DEPENDENT3" [color=green
"env=CONTROL=None" [color=green, label=None, shape=box, style=filled
"env=CONTROL=bar" -> "env=DEPENDENT1" [color=red
"env=CONTROL=bar" -> "env=DEPENDENT2" [color=red
"env=CONTROL=bar" -> "env=DEPENDENT_MISSING1" [arrowhead=empty, color=red
"env=CONTROL=bar" [color=red, label=bar, shape=box, style=filled
"env=CONTROL=baz" -> "env=DEPENDENT1" [color=red
"env=CONTROL=baz" [color=red, label=baz, shape=box, style=filled
"env=CONTROL=foo" -> "env=DEPENDENT_MISSING1" [color=green
"env=CONTROL=foo" [color=green, label=foo, shape=box, style=filled
"env=CONTROL_NAMELIST_QUX" -> "env=CONTROL_NAMELIST_QUX=bar" [color=red, label=foo
"env=CONTROL_NAMELIST_QUX" [color=green
"env=CONTROL_NAMELIST_QUX=bar" -> "namelist:qux" [color=red
"env=CONTROL_NAMELIST_QUX=bar" [color=red, label=bar, shape=box, style=filled
"env=CONTROL_NAMELIST_WIBBLE" -> "env=CONTROL_NAMELIST_WIBBLE=bar" [color=green, label=bar
"env=CONTROL_NAMELIST_WIBBLE" [color=green
"env=CONTROL_NAMELIST_WIBBLE=bar" -> "namelist:wibble" [color=green
"env=CONTROL_NAMELIST_WIBBLE=bar" [color=green, label=bar, shape=box, style=filled
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" -> "env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=red, label=foo
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" [color=green
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" -> "namelist:wibble=wubble" [color=red
"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=red, label=bar, shape=box, style=filled
"env=DEPENDENT1" [color=red, label="!!env=DEPENDENT1"
"env=DEPENDENT2" [color=red, label="!!env=DEPENDENT2"
"env=DEPENDENT3" [color=green
"env=DEPENDENT_DEPENDENT1" [color=red, label="!!env=DEPENDENT_DEPENDENT1"
"env=DEPENDENT_MISSING1" -> "env=DEPENDENT_MISSING1=None" [color=grey
"env=DEPENDENT_MISSING1" [color=grey
"env=DEPENDENT_MISSING1=None" -> "env=DEPENDENT_DEPENDENT1" [color=grey
"env=DEPENDENT_MISSING1=None" [color=grey, label=None, shape=box, style=filled
"env=MISSING_VARIABLE" [color=grey
"env=USER_IGNORED" [color=orange, label="!env=USER_IGNORED"
"namelist:qux" [color=red, label="!!namelist:qux", shape=rectangle
"namelist:wibble" [color=green, shape=rectangle
"namelist:wibble=wubble" [color=red, label="!!namelist:wibble=wubble", shape=rectangle
env [color=green, shape=octagon
graph [label="$CONFIG_PATH: env (trigger)", rankdir=LR
node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.out" \
    "$TEST_KEY.filtered.out.sorted" "$TEST_KEY.filtered.out.expected"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
exit
