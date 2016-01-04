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
# Test rose_arch built-in application.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 48
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --debug
#-------------------------------------------------------------------------------
# Results, good ones
TEST_KEY="$TEST_KEY_BASE-find-foo"
(cd $SUITE_RUN_DIR; find foo -type f | LANG=C sort) >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_SOURCE_DIR/$TEST_KEY.out" "$TEST_KEY.out"
for CYCLE in 2013010100 2013010112 2013010200; do
    TEST_KEY="$TEST_KEY_BASE-$CYCLE.out"
    sed '/^\[INFO\] [=!+]/!d;
         s/\(t(init)=\)[^Z]*Z/\1YYYY-mm-DDTHH:MM:SSZ/;
         s/\(dt(\(tran\|arch\))=\)[^s]*s/\1SSSSs/g' \
         $SUITE_RUN_DIR/log/job/$CYCLE/archive/0*/job.out >"$TEST_KEY"
    file_cmp "$TEST_KEY" "$TEST_KEY" $TEST_SOURCE_DIR/$TEST_KEY_BASE-$CYCLE.out
    TEST_KEY="$TEST_KEY_BASE-planet-n"
    tar -tzf $SUITE_RUN_DIR/foo/$CYCLE/hello/worlds/planet-n.tar.gz | \
        LANG=C sort >"$TEST_KEY-$CYCLE.out"
    file_cmp "$TEST_KEY-$CYCLE.out" \
        "$TEST_KEY-$CYCLE.out" "$TEST_SOURCE_DIR/$TEST_KEY.out"
    TEST_KEY="$TEST_KEY_BASE-unknown-stuff"
    tar -tf $SUITE_RUN_DIR/foo/$CYCLE/hello/worlds/unknown/stuff.pax | \
        LANG=C sort >"$TEST_KEY-$CYCLE.out"
    sed "s/\\\$CYCLE/$CYCLE/" "$TEST_SOURCE_DIR/$TEST_KEY.out" \
        >"$TEST_KEY-$CYCLE.out.expected"
    file_cmp "$TEST_KEY-$CYCLE.out" \
        "$TEST_KEY-$CYCLE.out" "$TEST_KEY-$CYCLE.out.expected"
    TEST_KEY="$TEST_KEY_BASE-db"
    for TRY in 1 2; do
        FILE=$SUITE_RUN_DIR/work/$CYCLE/archive/rose-arch-db-$TRY.out
        sed "s?\\\$ROSE_DATAC?$SUITE_RUN_DIR/share/cycle/$CYCLE?" \
            "$TEST_SOURCE_DIR/$TEST_KEY-$CYCLE-$TRY.out" >$FILE.expected
        file_cmp "$TEST_KEY-$CYCLE.out" $FILE.expected $FILE
    done
    for KEY in dark-matter.txt jupiter.txt try.nl uranus.txt; do
        TEST_KEY="$TEST_KEY_BASE-$CYCLE-grep-$KEY-foo-log-2"
        file_grep "$TEST_KEY" $KEY $SUITE_RUN_DIR/foo.log.$CYCLE.2
    done
    if test $(wc -l <$SUITE_RUN_DIR/foo.log.$CYCLE.2) -eq 4; then
        pass "$TEST_KEY_BASE-$CYCLE-foo-log-2-wc-l"
    else
        fail "$TEST_KEY_BASE-$CYCLE-foo-log-2-wc-l"
    fi
    TEST_KEY="$TEST_KEY_BASE-$CYCLE-neptune-1.txt"
    file_cmp "$TEST_KEY" \
        $SUITE_RUN_DIR/foo/$CYCLE/hello/worlds/neptune-1.txt <<__TXT__
[$CYCLE] Greet Triton
__TXT__
    TEST_KEY="$TEST_KEY_BASE-$CYCLE-jupiter-moons.tar.gz"
    tar -xzf $SUITE_RUN_DIR/foo/$CYCLE/hello/worlds/jupiter-moons.tar.gz -O \
        >"$TEST_KEY.out"
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__TXT__
[$CYCLE] Greet Io
__TXT__
done
#-------------------------------------------------------------------------------
# Results, bad ones
CYCLE=2013010112
TEST_KEY="$TEST_KEY_BASE-bad-archive-1"
FILE_PREFIX="$SUITE_RUN_DIR/log/job/$CYCLE/archive_bad_"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}1/01/job.err" <<'__ERR__'
[FAIL] foo://2013010112/hello/worlds/planet-n.tar.gz: bad command-format: foo put %(target)s %(source)s: KeyError: 'source'
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-2"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}2/01/job.err" <<'__ERR__'
[FAIL] source=None: missing configuration error: 'source'
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-3"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}3/01/job.err" <<'__ERR__'
[FAIL] source=$UNBOUND_PLANET-[1-9].txt: configuration value error: [UNDEFINED ENVIRONMENT VARIABLE] UNBOUND_PLANET
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-4"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}4/01/job.err" <<'__ERR__'
[FAIL] [arch:$UNKNOWN_DARK_PLANETS.tar.gz]=: configuration value error: [UNDEFINED ENVIRONMENT VARIABLE] UNKNOWN_DARK_PLANETS
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-5"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}5/01/job.err" <<__ERR__
[FAIL] [arch:inner.tar.gz]source=hello/mercurry.txt: configuration value error: [Errno 2] No such file or directory: '$SUITE_RUN_DIR/share/cycle/2013010112/hello/mercurry.txt'
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-6"
file_cmp "$TEST_KEY.err" "${FILE_PREFIX}6/01/job.err" <<__ERR__
[FAIL] foo push foo://2013010112/hello/worlds/mars.txt.gz $SUITE_RUN_DIR/share/cycle/2013010112/hello/mars.txt # return-code=1, stderr=
[FAIL] foo: push: unknown action
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-7"
file_cmp "$TEST_KEY.err" "$SUITE_RUN_DIR/log/job/$CYCLE/archive_bad_7/01/job.err" <<'__ERR__'
[FAIL] foo://2013010112/planet-n.tar.gz: bad rename-format: %(planet?maybedwarfplanet???)s: KeyError: 'planet?maybedwarfplanet???'
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-8"
file_cmp "$TEST_KEY.err" "$SUITE_RUN_DIR/log/job/$CYCLE/archive_bad_8/01/job.err" <<'__ERR__'
[FAIL] foo://2013010112/planet-n.tar.gz: bad rename-parser: planet-(?P<planet>[MVEJSUN]\w+.txt: error: unbalanced parenthesis
__ERR__
TEST_KEY="$TEST_KEY_BASE-bad-archive-9"
sed '/^\[INFO\] [=!+]/!d;
     s/\(t(init)=\)[^Z]*Z/\1YYYY-mm-DDTHH:MM:SSZ/;
     s/\(dt(\(tran\|arch\))=\)[^s]*s/\1SSSSs/g' \
    "$SUITE_RUN_DIR/log/job/$CYCLE/archive_bad_9/01/job.out" >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" \
    "$TEST_SOURCE_DIR/$TEST_KEY_BASE-bad-9.out" "$TEST_KEY.out"
sed 's?\(hello/planet-5.txt\) .*\(/hello/planet-5.txt\)?\1 \2?' \
    "$SUITE_RUN_DIR/log/job/$CYCLE/archive_bad_9/01/job.err" >"$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] my-bad-command $SUITE_RUN_DIR/share/cycle/2013010112/hello/planet-5.txt /hello/planet-5.txt # return-code=1, stderr=
[FAIL] [my-bad-command] $SUITE_RUN_DIR/share/cycle/2013010112/hello/planet-5.txt /hello/planet-5.txt
__ERR__

#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
