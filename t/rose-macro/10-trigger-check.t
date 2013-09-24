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
# Test "rose macro" in built-in trigger checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[namelist:near_cyclic_namelist]
switch = .false.
!!a = 2
!!b = 2
!!c = 2
!!d = 2
!!e = 2
!!f = 2

[namelist:dupl_nl(1)]
a = .true.

[namelist:subject_nl]
atrig = 2
btrig = 3
__CONFIG__
#-------------------------------------------------------------------------------
tests 15
#-------------------------------------------------------------------------------
# Check trigger checking - this is nearly cyclic but should be fine.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init_meta <<__META_CONFIG__
[namelist:near_cyclic_namelist=switch]
type = logical
trigger = namelist:near_cyclic_namelist=a: .true.

[namelist:near_cyclic_namelist=a]
trigger = namelist:near_cyclic_namelist=b;
          namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger = namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger = namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger = namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger = namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=f]

[namelist:dupl_nl]
duplicate = true
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check trigger checking - missing trigger in metadata.
TEST_KEY=$TEST_KEY_BASE-value-trigger-err-cyclic
setup
init_meta <<__META_CONFIG__
[namelist:near_cyclic_namelist=switch]
type = logical
trigger = namelist:near_cyclic_namelist=a: .true.

[namelist:near_cyclic_namelist=a]
trigger = namelist:near_cyclic_namelist=b;
          namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger = namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger = namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger = namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger = namelist:near_cyclic_namelist=f

[namelist:dupl_nl]
duplicate = true
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[V] rose.macros.DefaultValidators: issues: 1
    namelist:near_cyclic_namelist=f=2
        No metadata entry found
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check trigger checking - cyclic dependency.
TEST_KEY=$TEST_KEY_BASE-err-cyclic
setup
init_meta <<__META_CONFIG__
[namelist:near_cyclic_namelist=switch]
type = logical
trigger = namelist:near_cyclic_namelist=a: .true.

[namelist:near_cyclic_namelist=a]
trigger = namelist:near_cyclic_namelist=b;
          namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger = namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger = namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger = namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger = namelist:near_cyclic_namelist=f; namelist:near_cyclic_namelist=switch

[namelist:near_cyclic_namelist=f]

[namelist:dupl_nl]
duplicate = true
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[V] rose.macros.DefaultValidators: issues: 1
    namelist:near_cyclic_namelist=switch=.false.
        Cyclic dependency detected: namelist:near_cyclic_namelist=a to namelist:near_cyclic_namelist=switch
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check trigger checking - duplicate namelist external triggers.
TEST_KEY=$TEST_KEY_BASE-err-dupl-external
setup
init_meta <<__META_CONFIG__
[namelist:dupl_nl]
duplicate = true

[namelist:dupl_nl=a]
trigger = namelist:subject_nl=atrig: .true.
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[V] rose.macros.DefaultValidators: issues: 1
    namelist:dupl_nl=a=None
        Badly defined trigger - namelist:dupl_nl is 'duplicate'
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check trigger state checking.
TEST_KEY=$TEST_KEY_BASE-err-state
setup
init <<'__CONFIG__'
[command]
default = main_command
alternate = alternate_command

[env]
USE_TRIGGERED_NAMELIST = true
USE_TRIGGERED_IGNORED_NAMELIST = false
USE_ALREADY_TRIGGERED_IGNORED_NAMELIST = false
TRIGGERED_IF_TRIGGERED_NAMELIST = 0
USE_TRIG_DUPL_NAMELIST_A = false
IS_COLD = false
IS_WET = true
!!USE_ICE = true

[file:file1]
source=namelist:nl1

[namelist:triggering_list]
a_trig_b=.true.
b_triglist_x_y=.true.
x=6
y=4

[namelist:triggering_dict]
a_trig_b_5_c_6=4
!!b = .false.
!!c = .false.
d_trig_e_1_2_f_2_3=2
e=.false.
f=.false.

[namelist:triggering_cascade]
a_trig_b_4_v_3=3
!!b_trig_c_1 = 1
!!c_trig_d_e = .false.
!!d_trig_f_3 = 2
!!e_trig_g_4 = 4
!!f = .false.
!!g = .false.
v_trig_w=.false.
w_trig_z=.true.
x_trig_z_1=0
y_trig_z_1=0
!!z = .false.

[!namelist:ignored_namelist]
ign_normal_var=normal
!!ign_trig_var = 2
!ign_user_sw_var = 6

[namelist:ignored_error_namelist]
en_normal_var=normal
!!en_trig_comp_var = 2
!!en_trig_opt_var = 2
!!en_trig_i_err_comp_var = 2
!!en_trig_i_err_opt_var = 2
en_trig_e_err_comp_var=2
en_trig_e_err_opt_var=2
!!en_trig_nt_err_comp_var = 2
!!en_trig_nt_err_opt_var = 2
!en_user_sw_comp_var = 6
!en_user_sw_opt_var = 5

[namelist:near_cyclic_namelist]
switch=.false.
!!a = 2
!!b = 2
!!c = 2
!!d = 2
!!e = 2
!!f = 2

[namelist:triggered_namelist]
trigger_env_variable=normal
!!trig_var = 2
!user_sw_var = 6

[!!namelist:already_triggered_ignored_namelist]
normal_variable1=normal
normal_variable2=normal
normal_variable3=normal
normal_variable4=normal
normal_err_variable1=normal
normal_err_variable2=normal
normal_err_variable3=normal
normal_err_variable4=normal
abnormal_variable1=abnormal
abnormal_variable2=abnormal
abnormal_variable3=abnormal
abnormal_variable4=abnormal
abnormal_err_variable1=abnormal
abnormal_err_variable2=abnormal
abnormal_err_variable3=abnormal
abnormal_err_variable4=abnormal
!!trig_var1 = 2
!!trig_var2 = 2
!!trig_var3 = 2
!!trig_var4 = 2
trig_var_err1=2
trig_var_err2=2
trig_var_err3=2
trig_var_err4=2
ab_trig_var1=2
ab_trig_var2=2
ab_trig_var3=2
ab_trig_var4=2
!!ab_trig_var_err1 = 2
!!ab_trig_var_err2 = 2
!!ab_trig_var_err3 = 2
!!ab_trig_var_err4 = 2
!user_sw_var = 5

[namelist:triggered_ignored_namelist]
normal_variable1=normal
normal_variable2=normal
normal_variable3=normal
normal_variable4=normal
normal_err_variable1=normal
normal_err_variable2=normal
normal_err_variable3=normal
normal_err_variable4=normal
abnormal_variable1=abnormal
abnormal_variable2=abnormal
abnormal_variable3=abnormal
abnormal_variable4=abnormal
abnormal_err_variable1=abnormal
abnormal_err_variable2=abnormal
abnormal_err_variable3=abnormal
abnormal_err_variable4=abnormal
!!trig_var1 = 2
!!trig_var2 = 2
!!trig_var3 = 2
!!trig_var4 = 2
trig_var_err1=2
trig_var_err2=2
trig_var_err3=2
trig_var_err4=2
ab_trig_var1=2
ab_trig_var2=2
ab_trig_var3=2
ab_trig_var4=2
!!ab_trig_var_err1 = 2
!!ab_trig_var_err2 = 2
!!ab_trig_var_err3 = 2
!!ab_trig_var_err4 = 2
!user_sw_var = 5

[namelist:trigger_logical_expression]
trig_x_if_not_2=2
x=.false.

[namelist:trig_dupl(1)]
a=2
b=.false.
c=2

[namelist:trig_dupl(2)]
a=2
b=.true.
c=2

[namelist:trig_not_dupl(1)]
a=2
b=.false.
c=2

[namelist:trig_absent]
no_value_triggered=.false.
one_value_triggered=.false.
two_values_triggered=.false.
__CONFIG__
init_meta <<__META_CONFIG__

[env=USE_TRIGGERED_NAMELIST]
type=boolean
trigger=namelist:triggered_namelist: true

[env=TRIGGERED_IF_TRIGGERED_NAMELIST]
type=integer

[env=USE_TRIGGERED_IGNORED_NAMELIST]
type=boolean
trigger=namelist:triggered_ignored_namelist: true

[env=USE_ALREADY_TRIGGERED_IGNORED_NAMELIST]
type=boolean
trigger=namelist:already_triggered_ignored_namelist: true

[env=USE_TRIG_DUPL_NAMELIST_A]
type=boolean
trigger=namelist:trig_dupl=a: true

[env=IS_COLD]
type=boolean
trigger=env=USE_ICE: true
sort-key = ice

[env=IS_WET]
type=boolean
trigger=env=USE_ICE: true
sort-key = ice

[env=USE_ICE]
type=boolean
sort-key = ice

[namelist:triggering_list=a_trig_b]
type=logical
trigger=namelist:triggering_list=b_triglist_x_y: .true.

[namelist:triggering_list=b_triglist_x_y]
type=logical
trigger=namelist:triggering_list=x; namelist:triggering_list=y

[namelist:triggering_list=x]
type=integer

[namelist:triggering_list=y]
type=integer

[namelist:triggering_dict=a_trig_b_5_c_6]
type=integer
trigger=namelist:triggering_dict=b: 5;
          namelist:triggering_dict=c: 6

[namelist:triggering_dict=b]
type=logical

[namelist:triggering_dict=c]
type=logical

[namelist:triggering_dict=d_trig_e_1_2_f_2_3]
type=integer
trigger=namelist:triggering_dict=e: 1, 2;
          namelist:triggering_dict=f: 2, 3;

[namelist:triggering_dict=e]
type=logical

[namelist:triggering_dict=f]
type=logical

[namelist:triggering_cascade=a_trig_b_4_v_3]
type=integer
trigger=namelist:triggering_cascade=b_trig_c_1: 4; namelist:triggering_cascade=v_trig_w: 3;

[namelist:triggering_cascade=b_trig_c_1]
type=integer
trigger=namelist:triggering_cascade=c_trig_d_e: 1

[namelist:triggering_cascade=c_trig_d_e]
type=logical
trigger=namelist:triggering_cascade=d_trig_f_3;
        namelist:triggering_cascade=e_trig_g_4

[namelist:triggering_cascade=d_trig_f_3]
type=integer
trigger=namelist:triggering_cascade=f: 3;

[namelist:triggering_cascade=e_trig_g_4]
type=integer
trigger=namelist:triggering_cascade=g: 4

[namelist:triggering_cascade=f]
type=logical

[namelist:triggering_cascade=g]
type=logical

[namelist:triggering_cascade=v_trig_w]
type=logical
trigger=namelist:triggering_cascade=w_trig_z

[namelist:triggering_cascade=w_trig_z]
type=logical
trigger=namelist:triggering_cascade=z

[namelist:triggering_cascade=x_trig_z_1]
type=integer
trigger=namelist:triggering_cascade=z: 1

[namelist:triggering_cascade=y_trig_z_1]
type=integer
trigger=namelist:triggering_cascade=z: 1

[namelist:triggering_cascade=z]
type=logical

[namelist:near_cyclic_namelist=switch]
type=logical
trigger=namelist:near_cyclic_namelist=a: .true.

[namelist:near_cyclic_namelist=a]
trigger=namelist:near_cyclic_namelist=b;
        namelist:near_cyclic_namelist=c;
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger=namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger=namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger=namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger=namelist:near_cyclic_namelist=f
# trigger = namelist:near_cyclic_namelist=f; namelist:near_cyclic_namelist=switch

[namelist:near_cyclic_namelist=f]

[namelist:ignored_namelist=ign_normal_var]
values=normal, abnormal
trigger=namelist:ignored_namelist=ign_trig_var: abnormal

[namelist:ignored_namelist=ign_trig_var]
type=integer

[namelist:ignored_namelist=ign_user_sw_var]
type=integer

[namelist:ignored_error_namelist=en_normal_var]
values=normal, abnormal
trigger=namelist:ignored_error_namelist=en_trig_opt_var: abnormal;
        namelist:ignored_error_namelist=en_trig_comp_var: abnormal;
        namelist:ignored_error_namelist=en_trig_i_err_comp_var: normal;
        namelist:ignored_error_namelist=en_trig_i_err_opt_var: normal;
        namelist:ignored_error_namelist=en_trig_e_err_comp_var: abnormal;
        namelist:ignored_error_namelist=en_trig_e_err_opt_var: abnormal

[namelist:ignored_error_namelist=en_trig_opt_var]
type=integer

[namelist:ignored_error_namelist=en_trig_comp_var]
type=integer
compulsory=true

[namelist:ignored_error_namelist=en_trig_i_err_opt_var]
type=integer

[namelist:ignored_error_namelist=en_trig_i_err_comp_var]
type=integer
compulsory=true

[namelist:ignored_error_namelist=en_trig_e_err_opt_var]
type=integer

[namelist:ignored_error_namelist=en_trig_e_err_comp_var]
type=integer
compulsory=true

[namelist:ignored_error_namelist=en_trig_nt_err_opt_var]
type=integer

[namelist:ignored_error_namelist=en_trig_nt_err_comp_var]
type=integer
compulsory=true

[namelist:ignored_error_namelist=en_user_sw_comp_var]
type=integer
compulsory=true

[namelist:ignored_error_namelist=en_user_sw_opt_var]
type=integer

[namelist:triggered_namelist]

[namelist:triggered_namelist=trigger_env_variable]
values=normal, abnormal
trigger=env=TRIGGERED_IF_TRIGGERED_NAMELIST

[namelist:triggered_namelist=trig_var]
type=integer

[namelist:triggered_namelist=user_sw_var]
type=integer

[namelist:triggered_ignored_namelist]

[namelist:triggered_ignored_namelist=normal_variable1]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=trig_var1: normal

[namelist:triggered_ignored_namelist=normal_variable2]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=trig_var2: normal

[namelist:triggered_ignored_namelist=normal_variable3]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=trig_var3: normal

[namelist:triggered_ignored_namelist=normal_variable4]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=trig_var4: normal

[namelist:triggered_ignored_namelist=normal_variable_err1]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=trig_var_err1: normal

[namelist:triggered_ignored_namelist=normal_variable_err2]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=trig_var_err2: normal

[namelist:triggered_ignored_namelist=normal_variable_err3]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=trig_var_err3: normal

[namelist:triggered_ignored_namelist=normal_variable_err4]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=trig_var_err4: normal

[namelist:triggered_ignored_namelist=abnormal_variable1]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=ab_trig_var1: normal

[namelist:triggered_ignored_namelist=abnormal_variable2]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=ab_trig_var2: normal

[namelist:triggered_ignored_namelist=abnormal_variable3]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=ab_trig_var3: normal

[namelist:triggered_ignored_namelist=abnormal_variable4]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=ab_trig_var4: normal

[namelist:triggered_ignored_namelist=abnormal_variable_err1]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=ab_trig_var_err1: normal

[namelist:triggered_ignored_namelist=abnormal_variable_err2]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=ab_trig_var_err2: normal

[namelist:triggered_ignored_namelist=abnormal_variable_err3]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=ab_trig_var_err3: normal

[namelist:triggered_ignored_namelist=abnormal_variable_err4]
values=normal, abnormal
trigger=namelist:triggered_ignored_namelist=ab_trig_var_err4: normal

[namelist:triggered_ignored_namelist=trig_var1]
type=integer

[namelist:triggered_ignored_namelist=trig_var2]
type=integer

[namelist:triggered_ignored_namelist=trig_var3]
type=integer

[namelist:triggered_ignored_namelist=trig_var4]
type=integer

[namelist:triggered_ignored_namelist=trig_var_err1]
type=integer

[namelist:triggered_ignored_namelist=trig_var_err2]
type=integer

[namelist:triggered_ignored_namelist=trig_var_err3]
type=integer

[namelist:triggered_ignored_namelist=trig_var_err4]
type=integer

[namelist:triggered_ignored_namelist=ab_trig_var1]
type=integer

[namelist:triggered_ignored_namelist=ab_trig_var2]
type=integer

[namelist:triggered_ignored_namelist=ab_trig_var3]
type=integer

[namelist:triggered_ignored_namelist=ab_trig_var4]
type=integer

[namelist:triggered_ignored_namelist=ab_trig_var_err1]
type=integer

[namelist:triggered_ignored_namelist=ab_trig_var_err2]
type=integer

[namelist:triggered_ignored_namelist=ab_trig_var_err3]
type=integer

[namelist:triggered_ignored_namelist=ab_trig_var_err4]
type=integer

[namelist:triggered_ignored_namelist=user_sw_var]
type=integer

[namelist:already_triggered_ignored_namelist]

[namelist:already_triggered_ignored_namelist=normal_variable1]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=trig_var1: normal

[namelist:already_triggered_ignored_namelist=normal_variable2]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=trig_var2: normal

[namelist:already_triggered_ignored_namelist=normal_variable3]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=trig_var3: normal

[namelist:already_triggered_ignored_namelist=normal_variable4]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=trig_var4: normal

[namelist:already_triggered_ignored_namelist=normal_variable_err1]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=trig_var_err1: normal

[namelist:already_triggered_ignored_namelist=normal_variable_err2]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=trig_var_err2: normal

[namelist:already_triggered_ignored_namelist=normal_variable_err3]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=trig_var_err3: normal

[namelist:already_triggered_ignored_namelist=normal_variable_err4]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=trig_var_err4: normal

[namelist:already_triggered_ignored_namelist=abnormal_variable1]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=ab_trig_var1: normal

[namelist:already_triggered_ignored_namelist=abnormal_variable2]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=ab_trig_var2: normal

[namelist:already_triggered_ignored_namelist=abnormal_variable3]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=ab_trig_var3: normal

[namelist:already_triggered_ignored_namelist=abnormal_variable4]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=ab_trig_var4: normal

[namelist:already_triggered_ignored_namelist=abnormal_variable_err1]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=ab_trig_var_err1: normal

[namelist:already_triggered_ignored_namelist=abnormal_variable_err2]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=ab_trig_var_err2: normal

[namelist:already_triggered_ignored_namelist=abnormal_variable_err3]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=ab_trig_var_err3: normal

[namelist:already_triggered_ignored_namelist=abnormal_variable_err4]
values=normal, abnormal
trigger=namelist:already_triggered_ignored_namelist=ab_trig_var_err4: normal

[namelist:already_triggered_ignored_namelist=trig_var1]
type=integer

[namelist:already_triggered_ignored_namelist=trig_var2]
type=integer

[namelist:already_triggered_ignored_namelist=trig_var3]
type=integer

[namelist:already_triggered_ignored_namelist=trig_var4]
type=integer

[namelist:already_triggered_ignored_namelist=trig_var_err1]
type=integer

[namelist:already_triggered_ignored_namelist=trig_var_err2]
type=integer

[namelist:already_triggered_ignored_namelist=trig_var_err3]
type=integer

[namelist:already_triggered_ignored_namelist=trig_var_err4]
type=integer

[namelist:already_triggered_ignored_namelist=ab_trig_var1]
type=integer

[namelist:already_triggered_ignored_namelist=ab_trig_var2]
type=integer

[namelist:already_triggered_ignored_namelist=ab_trig_var3]
type=integer

[namelist:already_triggered_ignored_namelist=ab_trig_var4]
type=integer

[namelist:already_triggered_ignored_namelist=ab_trig_var_err1]
type=integer

[namelist:already_triggered_ignored_namelist=ab_trig_var_err2]
type=integer

[namelist:already_triggered_ignored_namelist=ab_trig_var_err3]
type=integer

[namelist:already_triggered_ignored_namelist=ab_trig_var_err4]
type=integer

[namelist:already_triggered_ignored_namelist=user_sw_var]
type=integer

[namelist:trigger_logical_expression]
help=This tests the 'this % 2 == 1' type of expression

[namelist:trigger_logical_expression=trig_x_if_not_2]
type=integer
sort-key = 0
trigger=namelist:trigger_logical_expression=x: this != 2

[namelist:trigger_logical_expression=x]
type=logical

[namelist:trigger_env_var]
help=This tests triggering from variables containing environment variables

[namelist:not_trig_dupl=b]
trigger=namelist:not_trig_dupl=c: .true.

[namelist:not_trig_dupl=c]
type=integer
description=This should be triggered on/off depending on b

[namelist:trig_dupl]
duplicate=true

[namelist:trig_dupl=a]
type=integer

[namelist:trig_dupl=b]
type=logical
trigger=namelist:trig_dupl=c: .true.

[namelist:trig_dupl=c]
type=integer
description=This should be triggered on/off depending on b

[namelist:trig_absent=no_value]
type=integer
trigger=namelist:trig_absent=no_value_triggered

[namelist:trig_absent=no_value_triggered]

[namelist:trig_absent=one_value]
type=integer
trigger=namelist:trig_absent=one_value_triggered: 1

[namelist:trig_absent=one_value_triggered]

[namelist:trig_absent=two_values]
type=integer
trigger=namelist:trig_absent=two_values_triggered: 1, 2

[namelist:trig_absent=two_values_triggered]
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --non-interactive --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 39
    namelist:already_triggered_ignored_namelist=ab_trig_var1=2
        State should be trig-ignored
    namelist:already_triggered_ignored_namelist=ab_trig_var2=2
        State should be trig-ignored
    namelist:already_triggered_ignored_namelist=ab_trig_var3=2
        State should be trig-ignored
    namelist:already_triggered_ignored_namelist=ab_trig_var4=2
        State should be trig-ignored
    namelist:already_triggered_ignored_namelist=trig_var_err1=2
        State should be trig-ignored
    namelist:already_triggered_ignored_namelist=trig_var_err2=2
        State should be trig-ignored
    namelist:already_triggered_ignored_namelist=trig_var_err3=2
        State should be trig-ignored
    namelist:already_triggered_ignored_namelist=trig_var_err4=2
        State should be trig-ignored
    namelist:already_triggered_ignored_namelist=user_sw_var=5
        State should be enabled
    namelist:ignored_error_namelist=en_trig_e_err_comp_var=2
        State should be trig-ignored
    namelist:ignored_error_namelist=en_trig_e_err_opt_var=2
        State should be trig-ignored
    namelist:ignored_error_namelist=en_trig_i_err_comp_var=2
        State should be enabled
    namelist:ignored_error_namelist=en_trig_i_err_opt_var=2
        State should be enabled
    namelist:ignored_error_namelist=en_trig_nt_err_comp_var=2
        State should be enabled
    namelist:ignored_error_namelist=en_trig_nt_err_opt_var=2
        State should be enabled
    namelist:ignored_error_namelist=en_user_sw_comp_var=6
        Compulsory settings should not be user-ignored.
    namelist:ignored_error_namelist=en_user_sw_comp_var=6
        State should be enabled
    namelist:ignored_error_namelist=en_user_sw_opt_var=5
        State should be enabled
    namelist:ignored_namelist=None=None
        State should be enabled
    namelist:ignored_namelist=ign_user_sw_var=6
        State should be enabled
    namelist:trig_absent=no_value_triggered=.false.
        State should be trig-ignored
    namelist:trig_absent=one_value_triggered=.false.
        State should be trig-ignored
    namelist:trig_absent=two_values_triggered=.false.
        State should be trig-ignored
    namelist:trig_dupl(1)=a=2
        State should be trig-ignored
    namelist:trig_dupl(1)=c=2
        State should be trig-ignored
    namelist:trig_dupl(2)=a=2
        State should be trig-ignored
    namelist:trigger_logical_expression=x=.false.
        State should be trig-ignored
    namelist:triggered_ignored_namelist=None=None
        State should be trig-ignored
    namelist:triggered_ignored_namelist=ab_trig_var1=2
        State should be trig-ignored
    namelist:triggered_ignored_namelist=ab_trig_var2=2
        State should be trig-ignored
    namelist:triggered_ignored_namelist=ab_trig_var3=2
        State should be trig-ignored
    namelist:triggered_ignored_namelist=ab_trig_var4=2
        State should be trig-ignored
    namelist:triggered_ignored_namelist=trig_var_err1=2
        State should be trig-ignored
    namelist:triggered_ignored_namelist=trig_var_err2=2
        State should be trig-ignored
    namelist:triggered_ignored_namelist=trig_var_err3=2
        State should be trig-ignored
    namelist:triggered_ignored_namelist=trig_var_err4=2
        State should be trig-ignored
    namelist:triggered_ignored_namelist=user_sw_var=5
        State should be enabled
    namelist:triggered_namelist=trig_var=2
        State should be enabled
    namelist:triggered_namelist=user_sw_var=6
        State should be enabled
__CONTENT__
exit
