#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
#
# This file is part of Rose, a framework for scientific suites.
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
# Test rose_arch built-in application.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 21
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost
TEST_KEY=$TEST_KEY_BASE-suite-run-wait
TIMEOUT=$(($(date +%s) + 300)) # wait 5 minutes
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    fail "$TEST_KEY"
    exit 1
else
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
# Results
TEST_KEY="$TEST_KEY_BASE-find-foo"
(cd $SUITE_RUN_DIR; find foo -type f |sort) >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_SOURCE_DIR/$TEST_KEY.out"
for CYCLE in 2013010100 2013010112 2013010200; do
    TEST_KEY="$TEST_KEY_BASE-planet-n"
    tar -tzf $SUITE_RUN_DIR/foo/$CYCLE/hello/worlds/planet-n.tar.gz | sort \
        >"$TEST_KEY-$CYCLE.out"
    file_cmp "$TEST_KEY-$CYCLE.out" \
        "$TEST_KEY-$CYCLE.out" "$TEST_SOURCE_DIR/$TEST_KEY.out"
    TEST_KEY="$TEST_KEY_BASE-unknown-stuff"
    tar -tf $SUITE_RUN_DIR/foo/$CYCLE/hello/worlds/unknown/stuff.pax | sort \
        >"$TEST_KEY-$CYCLE.out"
    sed "s/\\\$CYCLE/$CYCLE/" "$TEST_SOURCE_DIR/$TEST_KEY.out" \
        >"$TEST_KEY-$CYCLE.out.expected"
    file_cmp "$TEST_KEY-$CYCLE.out" \
        "$TEST_KEY-$CYCLE.out" "$TEST_KEY-$CYCLE.out.expected"
    TEST_KEY="$TEST_KEY_BASE-db"
    for TRY in 1 2; do
        ACTUAL=$SUITE_RUN_DIR/work/archive.$CYCLE/rose-arch-db-$TRY.out
        file_cmp "$TEST_KEY-$CYCLE.out" \
            $ACTUAL "$TEST_SOURCE_DIR/$TEST_KEY-$CYCLE-$TRY.out"
    done
done
CYCLE=2013010112
TEST_KEY="$TEST_KEY_BASE-bad-archive-1"
FILE_PREFIX="$SUITE_RUN_DIR/log/job/archive_bad_"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}1.$CYCLE.1.err" <<'__ERR__'
[FAIL] [foo://2013010112/hello/worlds/planet-n.tar.gz]command-format=foo put %(target)s %(source)s: configuration value error: 'source'
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-2"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}2.$CYCLE.1.err" <<'__ERR__'
[FAIL] source=None: missing configuration error: 'source'
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-3"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}3.$CYCLE.1.err" <<'__ERR__'
[FAIL] source=$UNBOUND_PLANET-[1-9].txt: configuration value error: [UNDEFINED ENVIRONMENT VARIABLE] UNBOUND_PLANET
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-4"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}4.$CYCLE.1.err" <<'__ERR__'
[FAIL] [arch:$UNKNOWN_DARK_PLANETS.tar.gz]=: configuration value error: [UNDEFINED ENVIRONMENT VARIABLE] UNKNOWN_DARK_PLANETS
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-5"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}5.$CYCLE.1.err" <<'__ERR__'
[FAIL] [arch:inner.tar.gz]source=hello/mercurry.txt: configuration value error: [Errno 2] No such file or directory: 'hello/mercurry.txt'
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-6"
diff -u - "${FILE_PREFIX}6.$CYCLE.1.err" <<__ERR__
[FAIL] foo push foo://2013010112/hello/worlds/mars.txt.gz $SUITE_RUN_DIR/share/data/2013010112/hello/mars.txt # return-code=1, stderr=
[FAIL] foo: push: unknown action
__ERR__
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}6.$CYCLE.1.err" <<__ERR__
[FAIL] foo push foo://2013010112/hello/worlds/mars.txt.gz $SUITE_RUN_DIR/share/data/2013010112/hello/mars.txt # return-code=1, stderr=
[FAIL] foo: push: unknown action
__ERR__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
