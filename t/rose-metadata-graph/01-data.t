#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
# Test "rose macro" in built-in trigger checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

python -c "import pygraphviz" 2>/dev/null || \
    skip_all 'pygraphviz not installed'

init <<'__CONFIG__'
[env]
!USER_IGNORED=0
CONTROL=foo
!!DEPENDENT1=bar
!!DEPENDENT2=baz
DEPENDENT3=foo
!!DEPENDENT_DEPENDENT1=qux
CONTROL_NAMELIST_QUX=foo
CONTROL_NAMELIST_WIBBLE=bar
CONTROL_NAMELIST_WIBBLE_WUBBLE=foo

[!!namelist:qux]
wobble=.false.
!!wubble=.true.

[namelist:wibble]
wobble=.true.
!!wubble=.true.
__CONFIG__
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Check trigger checking - this is nearly cyclic but should be fine.
TEST_KEY=$TEST_KEY_BASE-ok-full
setup
init_meta <<'__META_CONFIG__'
[env]

[env=CONTROL]

trigger=env=DEPENDENT1: bar, baz;
        env=DEPENDENT2: bar;
        env=DEPENDENT3;
        env=DEPENDENT_MISSING1: foo, bar;
values=foo,bar

[env=CONTROL_NAMELIST_QUX]
trigger=namelist:qux: bar;
values=foo,bar

[env=CONTROL_NAMELIST_WIBBLE]
trigger=namelist:wibble: bar;
values=foo,bar

[env=CONTROL_NAMELIST_WIBBLE_WUBBLE]
trigger=namelist:wibble=wubble: bar;

[env=DEPENDENT1]

[env=DEPENDENT2]

[env=DEPENDENT3]

[env=DEPENDENT_MISSING1]
trigger=env=DEPENDENT_DEPENDENT1

[env=DEPENDENT_DEPENDENT1]

[env=USER_IGNORED]
type=integer

[env=MISSING_VARIABLE]

[namelist:wibble]

[namelist:wibble=wobble]
trigger=namelist:wibble=wubble: .true.
type=logical

[namelist:wibble=wubble]
type=logical

[namelist:qux]

[namelist:qux=wobble]
trigger=namelist:qux=wubble: .true.
type=logical

[namelist:qux=wubble]
type=logical
__META_CONFIG__
CONFIG_PATH=$(cd ../config && pwd -P)
run_pass "$TEST_KEY" rose metadata-graph --debug --config=../config
sort "$TEST_KEY.out" -o "$TEST_KEY.out"
sed -i -e 's/\(pos\|bb\|width\|height\|lp\)="[^"]*\("\|$\)//g;' \
       -e 's/[, ]*\]\?;\? *$//g; /^\t/!d;' "$TEST_KEY.out"
file_xxdiff "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
		
	"env=CONTROL" -> "env=CONTROL=None" [color=green, label=foo
	"env=CONTROL" -> "env=CONTROL=bar" [color=red, label=foo
	"env=CONTROL" -> "env=CONTROL=baz" [color=red, label=foo
	"env=CONTROL" -> "env=CONTROL=foo" [color=green, label=foo
	"env=CONTROL" [color=green
	"env=CONTROL=None" -> "env=DEPENDENT3" [color=green
	"env=CONTROL=None" [label=None, color=green, shape=box, style=filled
	"env=CONTROL=bar" -> "env=DEPENDENT1" [color=red
	"env=CONTROL=bar" -> "env=DEPENDENT2" [color=red
	"env=CONTROL=bar" -> "env=DEPENDENT_MISSING1" [color=red, arrowhead=empty
	"env=CONTROL=bar" [label=bar, color=red, shape=box, style=filled
	"env=CONTROL=baz" -> "env=DEPENDENT1" [color=red
	"env=CONTROL=baz" [label=baz, color=red, shape=box, style=filled
	"env=CONTROL=foo" -> "env=DEPENDENT_MISSING1" [color=green
	"env=CONTROL=foo" [label=foo, color=green, shape=box, style=filled
	"env=CONTROL_NAMELIST_QUX" -> "env=CONTROL_NAMELIST_QUX=bar" [color=red, label=foo
	"env=CONTROL_NAMELIST_QUX" [color=green
	"env=CONTROL_NAMELIST_QUX=bar" -> "namelist:qux" [color=red
	"env=CONTROL_NAMELIST_QUX=bar" [label=bar, color=red, shape=box, style=filled
	"env=CONTROL_NAMELIST_WIBBLE" -> "env=CONTROL_NAMELIST_WIBBLE=bar" [color=green, label=bar
	"env=CONTROL_NAMELIST_WIBBLE" [color=green
	"env=CONTROL_NAMELIST_WIBBLE=bar" -> "namelist:wibble" [color=green
	"env=CONTROL_NAMELIST_WIBBLE=bar" [label=bar, color=green, shape=box, style=filled
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" -> "env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=red, label=foo
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" [color=green
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" -> "namelist:wibble=wubble" [color=red
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [label=bar, color=red, shape=box, style=filled
	"env=DEPENDENT1" [label="!!env=DEPENDENT1", color=red
	"env=DEPENDENT2" [label="!!env=DEPENDENT2", color=red
	"env=DEPENDENT3" [color=green
	"env=DEPENDENT_DEPENDENT1" [label="!!env=DEPENDENT_DEPENDENT1", color=red
	"env=DEPENDENT_MISSING1" -> "env=DEPENDENT_MISSING1=None" [color=grey
	"env=DEPENDENT_MISSING1" [color=grey
	"env=DEPENDENT_MISSING1=None" -> "env=DEPENDENT_DEPENDENT1" [color=grey
	"env=DEPENDENT_MISSING1=None" [label=None, color=grey, shape=box, style=filled
	"env=MISSING_VARIABLE" [color=grey
	"env=USER_IGNORED" [label="!env=USER_IGNORED", color=orange
	"namelist:qux" [label="!!namelist:qux", color=red, shape=octagon
	"namelist:qux=wobble" -> "namelist:qux=wobble=.true." [color=red, label=".false."
	"namelist:qux=wobble" [label="^namelist:qux=wobble", color=red
	"namelist:qux=wobble=.true." -> "namelist:qux=wubble" [color=red
	"namelist:qux=wobble=.true." [label=".true.", color=red, shape=box, style=filled
	"namelist:qux=wubble" [label="^!!namelist:qux=wubble", color=red
	"namelist:wibble" [color=green, shape=octagon
	"namelist:wibble=wobble" -> "namelist:wibble=wobble=.true." [color=green, label=".true."
	"namelist:wibble=wobble" [color=green
	"namelist:wibble=wobble=.true." -> "namelist:wibble=wubble" [color=green
	"namelist:wibble=wobble=.true." [label=".true.", color=green, shape=box, style=filled
	"namelist:wibble=wubble" [label="!!namelist:wibble=wubble", color=red
	env [color=green, shape=octagon
	graph [label="$CONFIG_PATH", rankdir=LR
	graph [
	node [label="\N"
__OUTPUT__
file_xxdiff "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ok-sub-section
run_pass "$TEST_KEY" rose metadata-graph --debug --config=../config namelist:qux
sort "$TEST_KEY.out" -o "$TEST_KEY.out"
sed -i -e 's/\(pos\|bb\|width\|height\|lp\)="[^"]*\("\|$\)//g;' \
       -e 's/[, ]*\]\?;\? *$//g; /^\t/!d;' "$TEST_KEY.out"
file_xxdiff "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
		
	"env=CONTROL_NAMELIST_QUX" -> "env=CONTROL_NAMELIST_QUX=bar" [color=red, label=foo
	"env=CONTROL_NAMELIST_QUX" [color=green, shape=rectangle
	"env=CONTROL_NAMELIST_QUX=bar" -> "namelist:qux" [color=red
	"env=CONTROL_NAMELIST_QUX=bar" [label=bar, color=red, shape=box, style=filled
	"namelist:qux" [label="!!namelist:qux", color=red, shape=octagon
	"namelist:qux=wobble" -> "namelist:qux=wobble=.true." [color=red, label=".false."
	"namelist:qux=wobble" [label="^namelist:qux=wobble", color=red
	"namelist:qux=wobble=.true." -> "namelist:qux=wubble" [color=red
	"namelist:qux=wobble=.true." [label=".true.", color=red, shape=box, style=filled
	"namelist:qux=wubble" [label="^!!namelist:qux=wubble", color=red
	graph [label="$CONFIG_PATH: namelist:qux", rankdir=LR
	graph [
	node [label="\N"
__OUTPUT__
file_xxdiff "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ok-property
run_pass "$TEST_KEY" rose metadata-graph --debug --config=../config \
    --property=trigger
sort "$TEST_KEY.out" -o "$TEST_KEY.out"
sed -i -e 's/\(pos\|bb\|width\|height\|lp\)="[^"]*\("\|$\)//g;' \
       -e 's/[, ]*\]\?;\? *$//g; /^\t/!d;' "$TEST_KEY.out"
file_xxdiff "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
		
	"env=CONTROL" -> "env=CONTROL=None" [color=green, label=foo
	"env=CONTROL" -> "env=CONTROL=bar" [color=red, label=foo
	"env=CONTROL" -> "env=CONTROL=baz" [color=red, label=foo
	"env=CONTROL" -> "env=CONTROL=foo" [color=green, label=foo
	"env=CONTROL" [color=green
	"env=CONTROL=None" -> "env=DEPENDENT3" [color=green
	"env=CONTROL=None" [label=None, color=green, shape=box, style=filled
	"env=CONTROL=bar" -> "env=DEPENDENT1" [color=red
	"env=CONTROL=bar" -> "env=DEPENDENT2" [color=red
	"env=CONTROL=bar" -> "env=DEPENDENT_MISSING1" [color=red, arrowhead=empty
	"env=CONTROL=bar" [label=bar, color=red, shape=box, style=filled
	"env=CONTROL=baz" -> "env=DEPENDENT1" [color=red
	"env=CONTROL=baz" [label=baz, color=red, shape=box, style=filled
	"env=CONTROL=foo" -> "env=DEPENDENT_MISSING1" [color=green
	"env=CONTROL=foo" [label=foo, color=green, shape=box, style=filled
	"env=CONTROL_NAMELIST_QUX" -> "env=CONTROL_NAMELIST_QUX=bar" [color=red, label=foo
	"env=CONTROL_NAMELIST_QUX" [color=green
	"env=CONTROL_NAMELIST_QUX=bar" -> "namelist:qux" [color=red
	"env=CONTROL_NAMELIST_QUX=bar" [label=bar, color=red, shape=box, style=filled
	"env=CONTROL_NAMELIST_WIBBLE" -> "env=CONTROL_NAMELIST_WIBBLE=bar" [color=green, label=bar
	"env=CONTROL_NAMELIST_WIBBLE" [color=green
	"env=CONTROL_NAMELIST_WIBBLE=bar" -> "namelist:wibble" [color=green
	"env=CONTROL_NAMELIST_WIBBLE=bar" [label=bar, color=green, shape=box, style=filled
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" -> "env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=red, label=foo
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" [color=green
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" -> "namelist:wibble=wubble" [color=red
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [label=bar, color=red, shape=box, style=filled
	"env=DEPENDENT1" [label="!!env=DEPENDENT1", color=red
	"env=DEPENDENT2" [label="!!env=DEPENDENT2", color=red
	"env=DEPENDENT3" [color=green
	"env=DEPENDENT_DEPENDENT1" [label="!!env=DEPENDENT_DEPENDENT1", color=red
	"env=DEPENDENT_MISSING1" -> "env=DEPENDENT_MISSING1=None" [color=grey
	"env=DEPENDENT_MISSING1" [color=grey
	"env=DEPENDENT_MISSING1=None" -> "env=DEPENDENT_DEPENDENT1" [color=grey
	"env=DEPENDENT_MISSING1=None" [label=None, color=grey, shape=box, style=filled
	"env=MISSING_VARIABLE" [color=grey
	"env=USER_IGNORED" [label="!env=USER_IGNORED", color=orange
	"namelist:qux" [label="!!namelist:qux", color=red, shape=octagon
	"namelist:qux=wobble" -> "namelist:qux=wobble=.true." [color=red, label=".false."
	"namelist:qux=wobble" [label="^namelist:qux=wobble", color=red
	"namelist:qux=wobble=.true." -> "namelist:qux=wubble" [color=red
	"namelist:qux=wobble=.true." [label=".true.", color=red, shape=box, style=filled
	"namelist:qux=wubble" [label="^!!namelist:qux=wubble", color=red
	"namelist:wibble" [color=green, shape=octagon
	"namelist:wibble=wobble" -> "namelist:wibble=wobble=.true." [color=green, label=".true."
	"namelist:wibble=wobble" [color=green
	"namelist:wibble=wobble=.true." -> "namelist:wibble=wubble" [color=green
	"namelist:wibble=wobble=.true." [label=".true.", color=green, shape=box, style=filled
	"namelist:wibble=wubble" [label="!!namelist:wibble=wubble", color=red
	env [color=green, shape=octagon
	graph [label="$CONFIG_PATH (trigger)", rankdir=LR
	graph [
	node [label="\N"
__OUTPUT__
file_xxdiff "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ok-property-sub-section
run_pass "$TEST_KEY" rose metadata-graph --debug --config=../config \
    --property=trigger env
sort "$TEST_KEY.out" -o "$TEST_KEY.out"
sed -i -e 's/\(pos\|bb\|width\|height\|lp\)="[^"]*\("\|$\)//g;' \
       -e 's/[, ]*\]\?;\? *$//g; /^\t/!d;' "$TEST_KEY.out"
file_xxdiff "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
		
	"env=CONTROL" -> "env=CONTROL=None" [color=green, label=foo
	"env=CONTROL" -> "env=CONTROL=bar" [color=red, label=foo
	"env=CONTROL" -> "env=CONTROL=baz" [color=red, label=foo
	"env=CONTROL" -> "env=CONTROL=foo" [color=green, label=foo
	"env=CONTROL" [color=green
	"env=CONTROL=None" -> "env=DEPENDENT3" [color=green
	"env=CONTROL=None" [label=None, color=green, shape=box, style=filled
	"env=CONTROL=bar" -> "env=DEPENDENT1" [color=red
	"env=CONTROL=bar" -> "env=DEPENDENT2" [color=red
	"env=CONTROL=bar" -> "env=DEPENDENT_MISSING1" [color=red, arrowhead=empty
	"env=CONTROL=bar" [label=bar, color=red, shape=box, style=filled
	"env=CONTROL=baz" -> "env=DEPENDENT1" [color=red
	"env=CONTROL=baz" [label=baz, color=red, shape=box, style=filled
	"env=CONTROL=foo" -> "env=DEPENDENT_MISSING1" [color=green
	"env=CONTROL=foo" [label=foo, color=green, shape=box, style=filled
	"env=CONTROL_NAMELIST_QUX" -> "env=CONTROL_NAMELIST_QUX=bar" [color=red, label=foo
	"env=CONTROL_NAMELIST_QUX" [color=green
	"env=CONTROL_NAMELIST_QUX=bar" -> "namelist:qux" [color=red
	"env=CONTROL_NAMELIST_QUX=bar" [label=bar, color=red, shape=box, style=filled
	"env=CONTROL_NAMELIST_WIBBLE" -> "env=CONTROL_NAMELIST_WIBBLE=bar" [color=green, label=bar
	"env=CONTROL_NAMELIST_WIBBLE" [color=green
	"env=CONTROL_NAMELIST_WIBBLE=bar" -> "namelist:wibble" [color=green
	"env=CONTROL_NAMELIST_WIBBLE=bar" [label=bar, color=green, shape=box, style=filled
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" -> "env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [color=red, label=foo
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE" [color=green
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" -> "namelist:wibble=wubble" [color=red
	"env=CONTROL_NAMELIST_WIBBLE_WUBBLE=bar" [label=bar, color=red, shape=box, style=filled
	"env=DEPENDENT1" [label="!!env=DEPENDENT1", color=red
	"env=DEPENDENT2" [label="!!env=DEPENDENT2", color=red
	"env=DEPENDENT3" [color=green
	"env=DEPENDENT_DEPENDENT1" [label="!!env=DEPENDENT_DEPENDENT1", color=red
	"env=DEPENDENT_MISSING1" -> "env=DEPENDENT_MISSING1=None" [color=grey
	"env=DEPENDENT_MISSING1" [color=grey
	"env=DEPENDENT_MISSING1=None" -> "env=DEPENDENT_DEPENDENT1" [color=grey
	"env=DEPENDENT_MISSING1=None" [label=None, color=grey, shape=box, style=filled
	"env=MISSING_VARIABLE" [color=grey
	"env=USER_IGNORED" [label="!env=USER_IGNORED", color=orange
	"namelist:qux" [label="!!namelist:qux", color=red, shape=rectangle
	"namelist:wibble" [color=green, shape=rectangle
	"namelist:wibble=wubble" [label="!!namelist:wibble=wubble", color=red, shape=rectangle
	env [color=green, shape=octagon
	graph [label="$CONFIG_PATH: env (trigger)", rankdir=LR
	graph [
	node [label="\N"
__OUTPUT__
file_xxdiff "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
exit
