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
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
# Test the rose CLI bash completion script.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 209
setup
#-------------------------------------------------------------------------------
# Source the script.
. $ROSE_HOME/etc/rose-bash-completion || exit 1
#-------------------------------------------------------------------------------
# List Rose subcommands.
TEST_KEY=$TEST_KEY_BASE-rose-subcommands
COMP_WORDS=( rose "")
COMP_CWORD=1
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_test "$TEST_KEY.reply" "rose help"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List Rosie subcommands.
TEST_KEY=$TEST_KEY_BASE-rosie-subcommands
COMP_WORDS=( rosie "")
COMP_CWORD=1
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_test "$TEST_KEY.reply" "rosie help"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List partial subcommands.
TEST_KEY=$TEST_KEY_BASE-rose-subcommands-app
COMP_WORDS=( rose app- )
COMP_CWORD=1
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply-run" "app-run"
compreply_grep "$TEST_KEY.reply-upgrade" "app-upgrade"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Stop completing subcommands.
TEST_KEY=$TEST_KEY_BASE-rose-subcommands-app-run
COMP_WORDS=( rose app-run )
COMP_CWORD=1
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" </dev/null
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List options for "rose app-run".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-options
COMP_WORDS=( rose app-run "" )
COMP_CWORD=2
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
--app-mode=
--config=
-C
--command-key=
-c
--define=
-D
--install-only
-i
--new
-N
--no-overwrite
--opt-conf-key=
-O
--quiet
-q
--verbose
-v
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List options for "rose app-run --app".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-options-app-
COMP_WORDS=( rose app-run --app- )
COMP_CWORD=2
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
--app-mode=
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rose app-run --app-mode=".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-options-app-mode
COMP_WORDS=( rose app-run --app-mode = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
fcm_make
rose_ana
rose_arch
rose_prune
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rose app-run --app-mode ".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-options-app-mode-no-equals
COMP_WORDS=( rose app-run --app-mode "" )
COMP_CWORD=3
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
fcm_make
rose_ana
rose_arch
rose_prune
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rose app-run --app-mode=fcm_make ".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-app-mode-options
COMP_WORDS=( rose app-run --app-mode = fcm_make "" )
COMP_CWORD=5
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
--app-mode=
--config=
-C
--command-key=
-c
--define=
-D
--install-only
-i
--new
-N
--no-overwrite
--opt-conf-key=
-O
--quiet
-q
--verbose
-v
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rose app-run --app-mode=fcm_make --config=".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-config
COMP_WORDS=( rose app-run --app-mode = fcm_make --config = "" )
COMP_CWORD=7
COMPREPLY=
run_pass "$TEST_KEY" _rose
# Bash should take over here - no reply from our function.
compreply_cmp "$TEST_KEY.reply" </dev/null
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose app-run --app-mode=fcm_make --config=../config/ -c ".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-c
setup
init <<'__CONFIG__'
[command]
command1=sleep 1
command2=sleep 2
command3=sleep 3
__CONFIG__
COMP_WORDS=( rose app-run --app-mode = fcm_make --config = ../config -c "" )
COMP_CWORD=9
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
command1
command2
command3
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rose app-run --app-mode=fcm_make --config=../config/ --command-key= ".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-command-key
init <<'__CONFIG__'
[command]
command1=sleep 1
command2=sleep 2
command3=sleep 3
__CONFIG__
COMP_WORDS=( rose app-run --app-mode = fcm_make --config = ../config --command-key = "" )
COMP_CWORD=10
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
command1
command2
command3
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose app-run -q --app-mode=fcm_make --config=../config/ -O ".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-o
setup
init </dev/null
init_opt_app foo
init_opt_app bar
COMP_WORDS=( rose app-run --app-mode = fcm_make --config = ../config/ -O "" )
COMP_CWORD=9
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
bar
foo
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose app-run -q --app-mode=fcm_make --config=../config/ --opt-conf-key= ".
TEST_KEY=$TEST_KEY_BASE-rose-app-run-opt-conf-key
setup
init </dev/null
init_opt_app foo
init_opt_app bar
COMP_WORDS=( rose app-run --app-mode = fcm_make --config = ../config/ --opt-conf-key = "" )
COMP_CWORD=10
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
bar
foo
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose app-upgrade ".
TEST_KEY=$TEST_KEY_BASE-rose-app-upgrade
setup
init <<'__CONFIG__'
meta=jupiter_moons/io

[env]
SEMI_MAJOR_AXIS_M=4.2e8
__CONFIG__
init_upgrade_meta jupiter_moons io europa ganymede callisto
init_upgrade_macro jupiter_moons <<'__MACRO__'
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import rose.upgrade


class UpgradeIotoEuropa(rose.upgrade.MacroUpgrade):

    """Upgrade from Io to Europa."""

    BEFORE_TAG = "io"
    AFTER_TAG = "europa"

    def upgrade(self, config, meta_config=None):
        self.change_setting_value(config, ["env", "SEMI_MAJOR_AXIS_M"], "6.7e8")
        return config, self.reports


class UpgradeEuropatoGanymede(rose.upgrade.MacroUpgrade):

    """Upgrade from Europa to Ganymede."""

    BEFORE_TAG = "europa"
    AFTER_TAG = "ganymede"

    def upgrade(self, config, meta_config=None):
        self.change_setting_value(config, ["env", "SEMI_MAJOR_AXIS_M"], "1.0e9")
        return config, self.reports


class UpgradeGanymedetoCallisto(rose.upgrade.MacroUpgrade):

    """Upgrade from Ganymede to Callisto."""

    BEFORE_TAG = "ganymede"
    AFTER_TAG = "callisto"

    def upgrade(self, config, meta_config=None):
        self.change_setting_value(config, ["env", "SEMI_MAJOR_AXIS_M"], "1.9e9")
        return config, self.reports


class UpgradeCallistotoThemisto(rose.upgrade.MacroUpgrade):

    """Upgrade from Callisto to Themisto."""

    BEFORE_TAG = "callisto"
    AFTER_TAG = "themisto"

    def upgrade(self, config, meta_config=None):
        self.change_setting_value(config, ["env", "SEMI_MAJOR_AXIS_M"], "7.4e9")
        return config, self.reports
__MACRO__
COMP_WORDS=( rose app-upgrade --config = $TEST_DIR/config --meta-path = $TEST_DIR/rose-meta "" )
COMP_CWORD=8
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply1" '^io$'
compreply_grep "$TEST_KEY.reply2" '^europa$'
compreply_grep "$TEST_KEY.reply3" '^ganymede$'
compreply_grep "$TEST_KEY.reply4" '^callisto$'
compreply_grep "$TEST_KEY.reply5" '^--config=$'
compreply_grep "$TEST_KEY.reply6" '^--meta-path=$'
compreply_grep "$TEST_KEY.reply7" '^-a$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rose app-upgrade -a ".
TEST_KEY=$TEST_KEY=$TEST_KEY_BASE-rose-app-upgrade-a
COMP_WORDS=( rose app-upgrade -a --config = $TEST_DIR/config --meta-path = $TEST_DIR/rose-meta "" )
COMP_CWORD=9
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply1" '^io$'
compreply_grep "$TEST_KEY.reply2" '^europa$'
compreply_grep "$TEST_KEY.reply3" '^ganymede$'
compreply_grep "$TEST_KEY.reply4" '^callisto$'
compreply_grep "$TEST_KEY.reply5" '^themisto$'
compreply_grep "$TEST_KEY.reply6" '^--config=$'
compreply_grep "$TEST_KEY.reply7" '^--meta-path=$'
compreply_grep "$TEST_KEY.reply8" '^-a$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose host-select -q --rank-method= ".
setup
TEST_KEY=$TEST_KEY_BASE-rose-host-select-q-rank-method
COMP_WORDS=( rose host-select -q --rank-method = "" )
COMP_CWORD=5
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
load
fs
mem
random
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List arguments for "rose macro -C ../config/ ".
TEST_KEY=$TEST_KEY_BASE-rose-macro-C-args
setup
init </dev/null
COMP_WORDS=( rose macro -C ../config "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply1" '^rose.macros.DefaultTransforms$'
compreply_grep "$TEST_KEY.reply2" '^rose.macros.DefaultValidators$'
compreply_grep "$TEST_KEY.reply3" '^--config=$'
compreply_grep "$TEST_KEY.reply4" '^-C$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List arguments for "rose macro --meta-path=../config/etc/rose-meta/ -C ../config/ ".
TEST_KEY=$TEST_KEY_BASE-rose-macro-meta-path-C-args
setup
init <<'__CONFIG__'
meta=beef/HEAD
__CONFIG__
init_macro beef burger.py <<'__MACRO__'
import rose.macro


class BeefBurgerTransformer(rose.macro.MacroBase):

    """Test class to change the value of a boolean environment variable."""

    WARNING_CHANGED_VALUE = "{0} -> {1}"

    def transform(self, config, meta_config=None):
        """Add more beef."""
        config.set(["env", "BEEF_AMOUNT"], "lots")
        self.add_report(["env", "BEEF_AMOUNT"], "lots",
                        info="Mmmmm.... lots of beef")
        return config, self.reports
__MACRO__
COMP_WORDS=( rose macro --meta-path = ../config/etc/rose-meta -C ../config "" )
COMP_CWORD=7
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply1" '^rose.macros.DefaultTransforms$'
compreply_grep "$TEST_KEY.reply2" '^rose.macros.DefaultValidators$'
compreply_grep "$TEST_KEY.reply3" '^burger.BeefBurgerTransformer$'
compreply_grep "$TEST_KEY.reply4" '^--config=$'
compreply_grep "$TEST_KEY.reply5" '^-C$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List arguments for "rose macro -M ../config/etc/rose-meta/ -C ../config/ ".
TEST_KEY=$TEST_KEY_BASE-rose-macro-M-C-args
COMP_WORDS=( rose macro -M ../config/etc/rose-meta -C ../config "" )
COMP_CWORD=6
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply1" '^rose.macros.DefaultTransforms$'
compreply_grep "$TEST_KEY.reply2" '^rose.macros.DefaultValidators$'
compreply_grep "$TEST_KEY.reply3" '^burger.BeefBurgerTransformer$'
compreply_grep "$TEST_KEY.reply4" '^--config=$'
compreply_grep "$TEST_KEY.reply5" '^-C$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List arguments for "rose metadata-graph -C ../config".
TEST_KEY=$TEST_KEY_BASE-rose-metadata-graph-C-config-args
setup
init <<'__CONFIG__'
[env]

[namelist:foo]

[namelist:bar]
__CONFIG__
init_meta <<'__META__'
[env]

[namelist:qux]

[namelist:wibble]

[namelist:wibble=foo]
__META__
COMP_WORDS=( rose metadata-graph -C ../config "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply1" '^env$'
compreply_grep "$TEST_KEY.reply2" '^namelist:qux$'
compreply_grep "$TEST_KEY.reply3" '^namelist:wibble$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List arguments for "rose metadata-graph -C ../config/meta/".
TEST_KEY=$TEST_KEY_BASE-rose-metadata-graph-C-meta-config-args
COMP_WORDS=( rose metadata-graph -C ../config/meta "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply1" '^env$'
compreply_grep "$TEST_KEY.reply2" '^namelist:qux$'
compreply_grep "$TEST_KEY.reply3" '^namelist:wibble$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option args for "rose metadata-graph -C ../config/meta --property=".
TEST_KEY=$TEST_KEY_BASE-rose-metadata-graph-C-config-property
COMP_WORDS=( rose metadata-graph -C ../config/meta --property = "" )
COMP_CWORD=6
COMPREPLY=
run_pass "$TEST_KEY" _rose
printf "%s\n" "${COMPREPLY[@]}" >/dev/tty
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
trigger
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose stem --group= ".
TEST_KEY=$TEST_KEY_BASE-rose-stem-group
setup
init_rose_stem_meta <<'__META__'
[jinja2:suite.rc=RUN_NAMES]
widget[rose-config-edit]=rose.config_editor.valuewidget.choice.ChoicesValueWidget
                        =--all-group=all --editable --format=python --guess-groups
                        =--choices=all,many,lots --choices=more,extra
                        = --choices=superfluous task_1 task_2
                        = task_3
                        =task_4
                        = task_5 task_6
                        =task_6 task_7
                        =task_8
__META__
cd $TEST_DIR/config
COMP_WORDS=( rose stem --group = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
cd $TEST_DIR/run
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
all
many
lots
more
extra
superfluous
task_1
task_2
task_3
task_4
task_5
task_6
task_6
task_7
task_8
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_DIR/config/$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_DIR/config/$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rose stem --task= ".
TEST_KEY=$TEST_KEY_BASE-rose-stem-task
COMP_WORDS=( rose stem -C $TEST_DIR/config/ --task = "" )
COMP_CWORD=6
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
all
many
lots
more
extra
superfluous
task_1
task_2
task_3
task_4
task_5
task_6
task_6
task_7
task_8
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose suite-hook --mail-cc= ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-hook-mail-cc
setup
COMP_WORDS=( rose suite-hook --mail-cc = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
getent aliases | cut -f1 -d" " | sort | uniq > ok_users
compreply_cmp "$TEST_KEY.reply" < ok_users
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose suite-log --user= ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-log-user
setup
COMP_WORDS=( rose suite-log --user = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
getent aliases | cut -f1 -d" " | sort | uniq > ok_users
compreply_cmp "$TEST_KEY.reply" < ok_users
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose suite-run --host= ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-run-host
setup
cat >rose.conf <<'__CONF__'
[rose-host-select]
group{quark}=up down strange charm bottom top

[rose-suite-run]
hosts=quark
__CONF__
export ROSE_CONF_PATH=$PWD
COMP_WORDS=( rose suite-run --host = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
up
down
strange
charm
bottom
top
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
unset ROSE_CONF_PATH
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose suite-run --opt-conf-key= ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-run-opt-conf-key
setup
init_suite </dev/null
init_opt_suite penthouse
init_opt_suite honeymoon
COMP_WORDS=( rose suite-run --config = ../config --opt-conf-key = "" )
COMP_CWORD=7
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
honeymoon
penthouse
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose suite-run -O ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-run-O
setup
init_suite </dev/null
init_opt_suite penthouse
init_opt_suite honeymoon
COMP_WORDS=( rose suite-run --config = ../config -O "" )
COMP_CWORD=6
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
honeymoon
penthouse
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "cd SUITE_DIR; rose suite-run -O ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-run-O-pwd
setup
init_suite </dev/null
init_opt_suite penthouse
init_opt_suite honeymoon
COMP_WORDS=( rose suite-run -O "" )
COMP_CWORD=3
COMPREPLY=
cd $TEST_DIR/config
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
honeymoon
penthouse
__REPLY__
cd $TEST_DIR/run
file_cmp "$TEST_KEY.out" "$TEST_DIR/config/$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_DIR/config/$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose suite-run --run= ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-run-run
setup
COMP_WORDS=( rose suite-run --run = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
reload
restart
run
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose suite-run --run= ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-run-run
setup
COMP_WORDS=( rose suite-run --run = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
reload
restart
run
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rose suite-shutdown --host= ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-shutdown-host
cat >rose.conf <<'__CONF__'
[rose-host-select]
group{quark}=up down strange charm bottom top

[rose-suite-run]
hosts=quark
__CONF__
export ROSE_CONF_PATH=$PWD
COMP_WORDS=( rose suite-shutdown --host = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
up
down
strange
charm
bottom
top
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
unset ROSE_CONF_PATH
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose suite-stop --host= ".
TEST_KEY=$TEST_KEY_BASE-rose-suite-stop-host
setup
cat >rose.conf <<'__CONF__'
[rose-host-select]
group{quark}=up down strange charm bottom top

[rose-suite-run]
hosts=quark
__CONF__
export ROSE_CONF_PATH=$PWD
COMP_WORDS=( rose suite-stop --host = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
up
down
strange
charm
bottom
top
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
unset ROSE_CONF_PATH
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose task-run --app-mode=".
TEST_KEY=$TEST_KEY_BASE-rose-task-run-options-app-
setup
COMP_WORDS=( rose task-run --app-mode = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
fcm_make
rose_ana
rose_arch
rose_prune
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose task-run --app-mode=fcm_make --config=../config/ -c ".
TEST_KEY=$TEST_KEY_BASE-rose-task-run-c
setup
init <<'__CONFIG__'
[command]
command1=sleep 1
command2=sleep 2
command3=sleep 3
__CONFIG__
COMP_WORDS=( rose task-run --app-mode = fcm_make --config = ../config/ -c "" )
COMP_CWORD=9
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
command1
command2
command3
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose task-run --app-mode=fcm_make --config=../config/ --command-key= ".
TEST_KEY=$TEST_KEY_BASE-rose-task-run-command-key
setup
init <<'__CONFIG__'
[command]
command1=sleep 1
command2=sleep 2
command3=sleep 3
__CONFIG__
COMP_WORDS=( rose task-run --app-mode = fcm_make --config = ../config/ --command-key = "" )
COMP_CWORD=10
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
command1
command2
command3
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose task-run -q --app-mode=fcm_make --config=../config/ -O ".
TEST_KEY=$TEST_KEY_BASE-rose-task-run-o
setup
init </dev/null
init_opt_app foo
init_opt_app bar
COMP_WORDS=( rose task-run --app-mode = fcm_make --config = ../config/ -O "" )
COMP_CWORD=9
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
bar
foo
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rose task-run -q --app-mode=fcm_make --config=../config/ --opt-conf-key= ".
TEST_KEY=$TEST_KEY_BASE-rose-task-run-opt-conf-key
setup
init </dev/null
init_opt_app foo
init_opt_app bar
COMP_WORDS=( rose task-run --app-mode = fcm_make --config = ../config/ --opt-conf-key = "" )
COMP_CWORD=10
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
bar
foo
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List arguments for "rose test-battery ".
TEST_KEY=$TEST_KEY_BASE-rose-test-battery
setup
COMP_WORDS=( rose test-battery "" )
COMP_CWORD=2
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply" "^rose-cli-bash-completion$"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# List option arguments for "rosie create --prefix= ".
TEST_KEY=$TEST_KEY_BASE-rosie-create-prefix
setup
cat >rose.conf <<'__CONF__'
[rosie-id]
prefix-default=electron
prefix-location.electron=svn://host/roses_electron_svn
prefix-location.muon=svn://host/roses_muon_svn
prefix-location.tau=svn://host/roses_tau_svn
prefix-web.electron=http://host/projects/roses_electron/intertrac/source:
prefix-web.muon=http://host/projects/roses_muon/intertrac/source:
prefix-web.tau=http://host/projects/roses_tau/intertrac/source:
prefix-ws.electron=http://host/rosie/electron
prefix-ws.muon=http://host/rosie/muon
prefix-ws.tau=http://host/rosie/tau
__CONF__
export ROSE_CONF_PATH=$PWD
COMP_WORDS=( rosie create --prefix = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
electron
muon
tau
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rosie go --prefix= ".
TEST_KEY=$TEST_KEY_BASE-rosie-go-prefix
COMP_WORDS=( rosie go --prefix = "" )
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
electron
muon
tau
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rosie lookup --prefix= ".
TEST_KEY=$TEST_KEY_BASE-rosie-lookup-prefix
COMP_WORDS=( rosie lookup --prefix = "" )
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
electron
muon
tau
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# List option arguments for "rosie ls --prefix= ".
TEST_KEY=$TEST_KEY_BASE-rosie-ls-prefix
COMP_WORDS=( rosie ls --prefix = "" )
run_pass "$TEST_KEY" _rose
compreply_cmp "$TEST_KEY.reply" <<'__REPLY__'
electron
muon
tau
__REPLY__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
