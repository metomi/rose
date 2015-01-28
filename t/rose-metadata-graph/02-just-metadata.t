#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
# Test "rose metadata-graph" against just configuration metadata.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

python -c "import pygraphviz" 2>/dev/null || \
    skip_all 'pygraphviz not installed'

#-------------------------------------------------------------------------------
tests 3
#-------------------------------------------------------------------------------
# Check full graphing.
TEST_KEY=$TEST_KEY_BASE-ok-full
setup
init < $TEST_SOURCE_DIR/lib/rose-app.conf
init_meta < $TEST_SOURCE_DIR/lib/rose-meta.conf
META_CONFIG_PATH=$(cd ../config/meta && pwd -P)
run_pass "$TEST_KEY" rose metadata-graph --debug --config=../config/meta
# Sort and filter out non-essential properties from the output file.
LANG=C sort "$TEST_KEY.out" -o "$TEST_KEY.out"
sed -i -e 's/\(pos\|bb\|width\|height\|lp\)="[^"]*\("\|$\)//g;' \
       -e 's/[, ]*\]\?;\? *$//g; /^\t/!d;' "$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
		
	"env=CONTROL" -> "env=CONTROL=None" [color=grey
	"env=CONTROL" -> "env=CONTROL=bar" [color=grey
	"env=CONTROL" -> "env=CONTROL=baz" [color=grey
	"env=CONTROL" -> "env=CONTROL=foo" [color=grey
	"env=CONTROL" [
	"env=CONTROL=None" -> "env=DEPENDENT3" [color=grey
	"env=CONTROL=None" [label=None, shape=box, color=grey, style=filled
	"env=CONTROL=bar" -> "env=DEPENDENT1" [color=grey
	"env=CONTROL=bar" -> "env=DEPENDENT2" [color=grey
	"env=CONTROL=bar" -> "env=DEPENDENT_MISSING1" [color=grey
	"env=CONTROL=bar" [label=bar, shape=box, color=grey, style=filled
	"env=CONTROL=baz" -> "env=DEPENDENT1" [color=grey
	"env=CONTROL=baz" [label=baz, shape=box, color=grey, style=filled
	"env=CONTROL=foo" -> "env=DEPENDENT_MISSING1" [color=grey
	"env=CONTROL=foo" [label=foo, shape=box, color=grey, style=filled
	"env=CONTROL_NAMELIST_QUX" -> "env=CONTROL_NAMELIST_QUX=bar" [color=grey
	"env=CONTROL_NAMELIST_QUX" [
	"env=CONTROL_NAMELIST_QUX=bar" -> "namelist:qux" [color=grey
	"env=CONTROL_NAMELIST_QUX=bar" [label=bar, shape=box, color=grey, style=filled
	"env=CONTROL_NAMELIST_WIBBLE" -> "env=CONTROL_NAMELIST_WIBBLE=bar" [color=grey
	"env=CONTROL_NAMELIST_WIBBLE" [
	"env=CONTROL_NAMELIST_WIBBLE=bar" -> "namelist:wibble" [color=grey
	"env=CONTROL_NAMELIST_WIBBLE=bar" [label=bar, shape=box, color=grey, style=filled
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" -> "env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=grey
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" [
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" -> "namelist:wibble=wubble" [color=grey
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [label=bar, shape=box, color=grey, style=filled
	"env=DEPENDENT1" [
	"env=DEPENDENT2" [
	"env=DEPENDENT3" [
	"env=DEPENDENT_DEPENDENT1" [
	"env=DEPENDENT_MISSING1" -> "env=DEPENDENT_MISSING1=None" [color=grey
	"env=DEPENDENT_MISSING1" [
	"env=DEPENDENT_MISSING1=None" -> "env=DEPENDENT_DEPENDENT1" [color=grey
	"env=DEPENDENT_MISSING1=None" [label=None, shape=box, color=grey, style=filled
	"env=MISSING_VARIABLE" [
	"env=USER_IGNORED" [
	"namelist:qux" [shape=octagon
	"namelist:qux=wobble" -> "namelist:qux=wobble=.true." [color=grey
	"namelist:qux=wobble" [
	"namelist:qux=wobble=.true." -> "namelist:qux=wubble" [color=grey
	"namelist:qux=wobble=.true." [label=".true.", shape=box, color=grey, style=filled
	"namelist:qux=wubble" [
	"namelist:wibble" [shape=octagon
	"namelist:wibble=wobble" -> "namelist:wibble=wobble=.true." [color=grey
	"namelist:wibble=wobble" [
	"namelist:wibble=wobble=.true." -> "namelist:wibble=wubble" [color=grey
	"namelist:wibble=wobble=.true." [label=".true.", shape=box, color=grey, style=filled
	"namelist:wibble=wubble" [
	env [shape=octagon
	graph [label="$META_CONFIG_PATH", rankdir=LR
	graph [
	node [label="\N"
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
exit
