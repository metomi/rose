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
# Test "rose macro" in built-in trigger changing mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[command]
default = main_command
alternate = alternate_command

[env]
USE_TRIGGERED_NAMELIST = true
USE_TRIGGERED_IGNORED_NAMELIST = false
TRIGGERED_IF_TRIGGERED_NAMELIST = 0
USE_TRIG_DUPL_NAMELIST_A = false
IS_COLD = false
IS_WET = true
!!USE_ICE = true

[file:file1]
source=namelist:nl1

[namelist:triggering_list]
A_trig_B = .true.
B_triglist_X_Y = .true.
X = 6
Y = 4

[namelist:triggering_dict]
A_trig_B_5_C_6 = 4
!!B = .false.
!!C = .false.
D_trig_E_1_2_F_2_3 = 2
E = .false.
F = .false.

[namelist:triggering_cascade]
A_trig_B_4_V_3 = 3
!!B_trig_C_1 = 1
!!C_trig_D_E = .false.
!!D_trig_F_3 = 2
!!E_trig_G_4 = 4
!!F = .false.
!!G = .false.
V_trig_W = .false.
W_trig_Z = .true.
X_trig_Z_1 = 0
Y_trig_Z_1 = 0
!!Z = .false.

[!namelist:ignored_namelist]
ign_normal_var = normal
!!ign_trig_var = 2
!ign_user_sw_var = 6

[namelist:ignored_error_namelist]
en_normal_var = normal
!!en_trig_comp_var = 2
!!en_trig_opt_var = 2
!!en_trig_i_err_comp_var = 2
!!en_trig_i_err_opt_var = 2
en_trig_e_err_comp_var = 2
en_trig_e_err_opt_var = 2
!!en_trig_nt_err_comp_var = 2
!!en_trig_nt_err_opt_var = 2
!en_user_sw_comp_var = 6
!en_user_sw_opt_var = 5

[namelist:near_cyclic_namelist]
switch = .false.
!!A = 2
!!B = 2
!!C = 2
!!D = 2
!!E = 2
!!F = 2

[namelist:triggered_namelist]
trigger_env_variable = normal
!!trig_var = 2
!user_sw_var = 6

[namelist:triggered_ignored_namelist]
normal_variable1 = normal
normal_variable2 = normal
normal_variable3 = normal
normal_variable4 = normal
normal_err_variable1 = normal
normal_err_variable2 = normal
normal_err_variable3 = normal
normal_err_variable4 = normal
abnormal_variable1 = abnormal
abnormal_variable2 = abnormal
abnormal_variable3 = abnormal
abnormal_variable4 = abnormal
abnormal_err_variable1 = abnormal
abnormal_err_variable2 = abnormal
abnormal_err_variable3 = abnormal
abnormal_err_variable4 = abnormal
!!trig_var1 = 2
!!trig_var2 = 2
!!trig_var3 = 2
!!trig_var4 = 2
ab_trig_var1 = 2
ab_trig_var2 = 2
ab_trig_var3 = 2
ab_trig_var4 = 2
!user_sw_var = 5

[namelist:trigger_logical_expression]
trig_X_if_not_2 = 2
X = .false.

[namelist:trig_dupl(1)]
A = 2
B = .false.
C = 2

[namelist:trig_dupl(2)]
A = 2
B = .true.
C = 2

[namelist:trig_not_dupl(1)]
A = 2
B = .false.
C = 2

[namelist:trig_absent]
no_value_triggered = .false.
one_value_triggered = .false.
two_values_triggered = .false.
__CONFIG__
#-------------------------------------------------------------------------------
tests 4
#-------------------------------------------------------------------------------
# Check trigger changing.
TEST_KEY=$TEST_KEY_BASE-change
setup
init_meta <<__META_CONFIG__

[env=USE_TRIGGERED_NAMELIST]
type = boolean
trigger = namelist:triggered_namelist: true

[env=TRIGGERED_IF_TRIGGERED_NAMELIST]
type = integer

[env=USE_TRIGGERED_IGNORED_NAMELIST]
type = boolean
trigger = namelist:triggered_ignored_namelist: true

[env=USE_TRIG_DUPL_NAMELIST_A]
type = boolean
trigger = namelist:trig_dupl=A: true

[env=IS_COLD]
type = boolean
trigger = env=USE_ICE: true
sort-key = ice

[env=IS_WET]
type = boolean
trigger = env=USE_ICE: true
sort-key = ice

[env=USE_ICE]
type = boolean
sort-key = ice

[namelist:triggering_list=A_trig_B]
type = logical
trigger = namelist:triggering_list=B_triglist_X_Y: .true.

[namelist:triggering_list=B_triglist_X_Y]
type = logical
trigger = namelist:triggering_list=X; namelist:triggering_list=Y

[namelist:triggering_list=X]
type = integer

[namelist:triggering_list=Y]
type = integer

[namelist:triggering_dict=A_trig_B_5_C_6]
type = integer
trigger = namelist:triggering_dict=B: 5;
          namelist:triggering_dict=C: 6

[namelist:triggering_dict=B]
type = logical

[namelist:triggering_dict=C]
type = logical

[namelist:triggering_dict=D_trig_E_1_2_F_2_3]
type = integer
trigger = namelist:triggering_dict=E: 1, 2;
          namelist:triggering_dict=F: 2, 3;

[namelist:triggering_dict=E]
type = logical

[namelist:triggering_dict=F]
type = logical

[namelist:triggering_cascade=A_trig_B_4_V_3]
type = integer
trigger = namelist:triggering_cascade=B_trig_C_1: 4; namelist:triggering_cascade=V_trig_W: 3;

[namelist:triggering_cascade=B_trig_C_1]
type = integer
trigger = namelist:triggering_cascade=C_trig_D_E: 1

[namelist:triggering_cascade=C_trig_D_E]
type = logical
trigger = namelist:triggering_cascade=D_trig_F_3;
          namelist:triggering_cascade=E_trig_G_4

[namelist:triggering_cascade=D_trig_F_3]
type = integer
trigger = namelist:triggering_cascade=F: 3;

[namelist:triggering_cascade=E_trig_G_4]
type = integer
trigger = namelist:triggering_cascade=G: 4

[namelist:triggering_cascade=F]
type = logical

[namelist:triggering_cascade=G]
type = logical

[namelist:triggering_cascade=V_trig_W]
type = logical
trigger = namelist:triggering_cascade=W_trig_Z

[namelist:triggering_cascade=W_trig_Z]
type = logical
trigger = namelist:triggering_cascade=Z

[namelist:triggering_cascade=X_trig_Z_1]
type = integer
trigger = namelist:triggering_cascade=Z: 1

[namelist:triggering_cascade=Y_trig_Z_1]
type = integer
trigger = namelist:triggering_cascade=Z: 1

[namelist:triggering_cascade=Z]
type = logical

[namelist:near_cyclic_namelist=switch]
type = logical
trigger = namelist:near_cyclic_namelist=A: .true.

[namelist:near_cyclic_namelist=A]
trigger = namelist:near_cyclic_namelist=B;
          namelist:near_cyclic_namelist=C;
          namelist:near_cyclic_namelist=D

[namelist:near_cyclic_namelist=B]
trigger = namelist:near_cyclic_namelist=C;
          namelist:near_cyclic_namelist=D

[namelist:near_cyclic_namelist=C]
trigger = namelist:near_cyclic_namelist=D

[namelist:near_cyclic_namelist=D]
trigger = namelist:near_cyclic_namelist=E; namelist:near_cyclic_namelist=F

[namelist:near_cyclic_namelist=E]
trigger = namelist:near_cyclic_namelist=F
# trigger = namelist:near_cyclic_namelist=F; namelist:near_cyclic_namelist=switch

[namelist:near_cyclic_namelist=F]

[namelist:ignored_namelist=ign_normal_var]
values = normal, abnormal
trigger = namelist:ignored_namelist=ign_trig_var: abnormal

[namelist:ignored_namelist=ign_trig_var]
type = integer

[namelist:ignored_namelist=ign_user_sw_var]
type = integer

[namelist:ignored_error_namelist=en_normal_var]
values = normal, abnormal
trigger = namelist:ignored_error_namelist=en_trig_opt_var: abnormal;
          namelist:ignored_error_namelist=en_trig_comp_var: abnormal;
          namelist:ignored_error_namelist=en_trig_i_err_comp_var: normal;
          namelist:ignored_error_namelist=en_trig_i_err_opt_var: normal;
          namelist:ignored_error_namelist=en_trig_e_err_comp_var: abnormal;
          namelist:ignored_error_namelist=en_trig_e_err_opt_var: abnormal

[namelist:ignored_error_namelist=en_trig_opt_var]
type = integer

[namelist:ignored_error_namelist=en_trig_comp_var]
type = integer
compulsory = true

[namelist:ignored_error_namelist=en_trig_i_err_opt_var]
type = integer

[namelist:ignored_error_namelist=en_trig_i_err_comp_var]
type = integer
compulsory = true

[namelist:ignored_error_namelist=en_trig_e_err_opt_var]
type = integer

[namelist:ignored_error_namelist=en_trig_e_err_comp_var]
type = integer
compulsory = true

[namelist:ignored_error_namelist=en_trig_nt_err_opt_var]
type = integer

[namelist:ignored_error_namelist=en_trig_nt_err_comp_var]
type = integer
compulsory = true

[namelist:ignored_error_namelist=en_user_sw_comp_var]
type = integer
compulsory = true

[namelist:ignored_error_namelist=en_user_sw_opt_var]
type = integer

[namelist:triggered_namelist]

[namelist:triggered_namelist=trigger_env_variable]
values = normal, abnormal
trigger = env=TRIGGERED_IF_TRIGGERED_NAMELIST

[namelist:triggered_namelist=trig_var]
type = integer

[namelist:triggered_namelist=user_sw_var]
type = integer

[namelist:triggered_ignored_namelist]

[namelist:triggered_ignored_namelist=normal_variable1]
values = normal, abnormal
trigger = namelist:triggered_ignored_namelist=trig_var1: abnormal

[namelist:triggered_ignored_namelist=normal_variable2]
values = normal, abnormal
trigger = namelist:triggered_ignored_namelist=trig_var2: abnormal

[namelist:triggered_ignored_namelist=normal_variable3]
values = normal, abnormal
trigger = namelist:triggered_ignored_namelist=trig_var3: abnormal

[namelist:triggered_ignored_namelist=normal_variable4]
values = normal, abnormal
trigger = namelist:triggered_ignored_namelist=trig_var4: abnormal

[namelist:triggered_ignored_namelist=abnormal_variable1]
values = normal, abnormal
trigger = namelist:triggered_ignored_namelist=ab_trig_var1: abnormal

[namelist:triggered_ignored_namelist=abnormal_variable2]
values = normal, abnormal
trigger = namelist:triggered_ignored_namelist=ab_trig_var2: abnormal

[namelist:triggered_ignored_namelist=abnormal_variable3]
values = normal, abnormal
trigger = namelist:triggered_ignored_namelist=ab_trig_var3: abnormal

[namelist:triggered_ignored_namelist=abnormal_variable4]
values = normal, abnormal
trigger = namelist:triggered_ignored_namelist=ab_trig_var4: abnormal

[namelist:triggered_ignored_namelist=trig_var1]
type = integer

[namelist:triggered_ignored_namelist=trig_var2]
type = integer

[namelist:triggered_ignored_namelist=trig_var3]
type = integer

[namelist:triggered_ignored_namelist=trig_var4]
type = integer

[namelist:triggered_ignored_namelist=ab_trig_var1]
type = integer

[namelist:triggered_ignored_namelist=ab_trig_var2]
type = integer

[namelist:triggered_ignored_namelist=ab_trig_var3]
type = integer

[namelist:triggered_ignored_namelist=ab_trig_var4]
type = integer

[namelist:triggered_ignored_namelist=user_sw_var]
type = integer

[namelist:trigger_logical_expression]
help = This tests the 'this % 2 == 1' type of expression

[namelist:trigger_logical_expression=trig_X_if_not_2]
type = integer
sort-key = 0
trigger = namelist:trigger_logical_expression=X: this != 2

[namelist:trigger_logical_expression=X]
type = logical

[namelist:trigger_env_var]
help = This tests triggering from variables containing environment variables

[namelist:not_trig_dupl=B]
trigger = namelist:not_trig_dupl=C: .true.

[namelist:trig_dupl]
duplicate = true

[namelist:trig_dupl=A]
type = integer

[namelist:trig_dupl=B]
type = logical
trigger = namelist:trig_dupl=C: .true.

[namelist:trig_dupl=C]
type = integer
description = This should be triggered on/off depending on B

[namelist:trig_absent=no_value]
type = integer
trigger = namelist:trig_absent=no_value_triggered

[namelist:trig_absent=no_value_triggered]

[namelist:trig_absent=one_value]
type = integer
trigger = namelist:trig_absent=one_value_triggered: 1

[namelist:trig_absent=one_value_triggered]

[namelist:trig_absent=two_values]
type = integer
trigger = namelist:trig_absent=two_values_triggered: 1, 2

[namelist:trig_absent=two_values_triggered]
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --non-interactive --config=../config rose.macros.DefaultTransforms
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[T] rose.macros.DefaultTransforms: changes: 21
    namelist:ignored_error_namelist=en_trig_e_err_comp_var=2
        enabled      -> trig-ignored
    namelist:ignored_error_namelist=en_trig_e_err_opt_var=2
        enabled      -> trig-ignored
    namelist:ignored_error_namelist=en_trig_i_err_comp_var=2
        trig-ignored -> enabled     
    namelist:ignored_error_namelist=en_trig_i_err_opt_var=2
        trig-ignored -> enabled     
    namelist:ignored_error_namelist=en_trig_nt_err_comp_var=2
        trig-ignored -> enabled     
    namelist:ignored_error_namelist=en_trig_nt_err_opt_var=2
        trig-ignored -> enabled     
    namelist:ignored_error_namelist=en_user_sw_comp_var=6
        user-ignored -> enabled     
    namelist:ignored_error_namelist=en_user_sw_opt_var=5
        user-ignored -> enabled     
    namelist:ignored_namelist=None=None
        user-ignored -> enabled     
    namelist:ignored_namelist=ign_user_sw_var=6
        user-ignored -> enabled     
    namelist:trig_absent=no_value_triggered=.false.
        enabled      -> trig-ignored
    namelist:trig_absent=one_value_triggered=.false.
        enabled      -> trig-ignored
    namelist:trig_absent=two_values_triggered=.false.
        enabled      -> trig-ignored
    namelist:trig_dupl(1)=A=2
        enabled      -> trig-ignored
    namelist:trig_dupl(1)=C=2
        enabled      -> trig-ignored
    namelist:trig_dupl(2)=A=2
        enabled      -> trig-ignored
    namelist:trigger_logical_expression=X=.false.
        enabled      -> trig-ignored
    namelist:triggered_ignored_namelist=None=None
        enabled      -> trig-ignored
    namelist:triggered_ignored_namelist=user_sw_var=5
        user-ignored -> enabled     
    namelist:triggered_namelist=trig_var=2
        trig-ignored -> enabled     
    namelist:triggered_namelist=user_sw_var=6
        user-ignored -> enabled     
__CONTENT__
file_cmp ../config/rose-app.conf ../config/rose-app.conf <<'__CONTENT__'
[command]
alternate=alternate_command
default=main_command

[env]
IS_COLD=false
IS_WET=true
TRIGGERED_IF_TRIGGERED_NAMELIST=0
!!USE_ICE=true
USE_TRIGGERED_IGNORED_NAMELIST=false
USE_TRIGGERED_NAMELIST=true
USE_TRIG_DUPL_NAMELIST_A=false

[file:file1]
source=namelist:nl1

[namelist:ignored_error_namelist]
en_normal_var=normal
!!en_trig_comp_var=2
!!en_trig_e_err_comp_var=2
!!en_trig_e_err_opt_var=2
en_trig_i_err_comp_var=2
en_trig_i_err_opt_var=2
en_trig_nt_err_comp_var=2
en_trig_nt_err_opt_var=2
!!en_trig_opt_var=2
en_user_sw_comp_var=6
en_user_sw_opt_var=5

[namelist:ignored_namelist]
ign_normal_var=normal
!!ign_trig_var=2
ign_user_sw_var=6

[namelist:near_cyclic_namelist]
!!A=2
!!B=2
!!C=2
!!D=2
!!E=2
!!F=2
switch=.false.

[namelist:trig_absent]
!!no_value_triggered=.false.
!!one_value_triggered=.false.
!!two_values_triggered=.false.

[namelist:trig_dupl(1)]
!!A=2
B=.false.
!!C=2

[namelist:trig_dupl(2)]
!!A=2
B=.true.
C=2

[namelist:trig_not_dupl(1)]
A=2
B=.false.
C=2

[namelist:trigger_logical_expression]
!!X=.false.
trig_X_if_not_2=2

[!!namelist:triggered_ignored_namelist]
normal_variable1=normal
normal_variable2=normal
normal_variable3=normal
normal_variable4=normal
abnormal_variable1=abnormal
abnormal_variable2=abnormal
abnormal_variable3=abnormal
abnormal_variable4=abnormal
!!trig_var1=2
!!trig_var2=2
!!trig_var3=2
!!trig_var4=2
ab_trig_var1=2
ab_trig_var2=2
ab_trig_var3=2
ab_trig_var4=2
user_sw_var=5

[namelist:triggered_namelist]
trig_var=2
trigger_env_variable=normal
user_sw_var=6

[namelist:triggering_cascade]
A_trig_B_4_V_3=3
!!B_trig_C_1=1
!!C_trig_D_E=.false.
!!D_trig_F_3=2
!!E_trig_G_4=4
!!F=.false.
!!G=.false.
V_trig_W=.false.
W_trig_Z=.true.
X_trig_Z_1=0
Y_trig_Z_1=0
!!Z=.false.

[namelist:triggering_dict]
A_trig_B_5_C_6=4
!!B=.false.
!!C=.false.
D_trig_E_1_2_F_2_3=2
E=.false.
F=.false.

[namelist:triggering_list]
A_trig_B=.true.
B_triglist_X_Y=.true.
X=6
Y=4
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
