#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2018 British Crown (Met Office) & Contributors.
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
# Test "rose metadata-check".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 2
#-------------------------------------------------------------------------------
# Check invalid syntax checking.
TEST_KEY=$TEST_KEY_BASE
setup
init <<__META_CONFIG__
[ns=foo]
title=namespace section
compulsory=true
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -v -C ../config
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__OUT__
[V] rose.metadata_check.MetadataChecker: issues: 1
    ns=foo=compulsory=true
        Invalid setting for namespace: compulsory
__OUT__
teardown
