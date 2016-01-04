#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
#
# This file is part of Rose,a framework for scientific suites.
#
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation,either version 3 of the License,or
# (at your option) any later version.
#
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not,see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
# Test "rose config-dump".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Mixed string-integer section indices.
TEST_KEY=$TEST_KEY_BASE-basic
setup
cat > f1 <<'__CONF__'
[namelist:Bacon_and_Beans]
recipe='Fry ',6,'slices of bacon until nearly crispy then cut them up',' then chop ',1,' large onion and fry it with the bacon ', ' then add baked beans, mixed herbs, smoked paprika, chilli powder, and pepper and serve with ', ' a few ', ' slices of toast '

[namelist:morse]
Signal='dot', 'dash', 'dash', 'dot', 'pause','dot', 'dot', 'pause','dash', 'dot', 'pause','dash', 'long pause','dot', 'dash', 'dot', 'dot', 'pause','dot', 'pause','dot', 'dash', 'dash', 'pause','dot', 'dot', 'pause','dot', 'dot', 'dot'

[namelist:sequences]
fibonacci=0, 1, 1, 2, 3, 5, 8, 13, 21, 34,55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657, 46368, 75025, 121393, 196418, 317811, 514229, 832040, 1346269, 2178309, 3524578, 5702887, 9227465, 14930352, 24157817, 39088169
happy=1, 7, 10, 13, 19, 23, 28, 31, 32, 44, 49, 68, 70, 79, 82, 86, 91, 94, 97, 100, 103, 109, 129, 130, 133, 139, 167, 176, 188, 190, 192, 193, 203, 208, 219, 226, 230, 236, 239, 262, 263, 280, 291, 293, 301, 302,
 =310, 313, 319, 320, 326, 329, 331, 338, 356, 362, 365, 367, 368, 376, 379, 383, 386, 391, 392, 397, 404, 409, 440, 446, 464, 469, 478, 487, 490, 496, 536, 556, 563, 565, 566, 608, 617, 622, 623, 632, 635, 637, 638, 644, 649, 653, 655, 656, 665, 671, 673, 680, 683, 694, 700, 709, 716, 736, 739, 748, 761, 763, 784, 790, 793, 802, 806,
 =818, 820, 833, 836, 847, 860, 863, 874, 881, 888, 899, 901,
 =904, 907, 910, 912, 913, 921, 923, 931, 932, 937, 940, 946, 964, 970, 973, 989, 998, 1000
perfect=6,
 28,
 496,
 8128,
 33550336, 8589869056, 137438691328
powers_of_one=1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
__CONF__
cp f1 rose-app.conf
run_pass "$TEST_KEY" rose config-dump
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] M rose-app.conf
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
cat > f2 <<'__CONF__'
[namelist:Bacon_and_Beans]
recipe='Fry ',6,
      ='slices of bacon until nearly crispy then cut them up',
      =' then chop ',1,' large onion and fry it with the bacon ',
      =' then add baked beans, mixed herbs, smoked paprika, chilli powder, and pepper and serve with ',
      =' a few ',' slices of toast '

[namelist:morse]
signal='dot','dash','dash','dot','pause','dot','dot','pause',
      ='dash','dot','pause','dash','long pause','dot','dash','dot',
      ='dot','pause','dot','pause','dot','dash','dash','pause',
      ='dot','dot','pause','dot','dot','dot'

[namelist:sequences]
fibonacci=0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,
         =4181,6765,10946,17711,28657,46368,75025,121393,196418,
         =317811,514229,832040,1346269,2178309,3524578,5702887,
         =9227465,14930352,24157817,39088169
happy=1,7,10,13,19,23,28,31,32,44,49,68,70,79,82,86,91,94,97,100,
     =103,109,129,130,133,139,167,176,188,190,192,193,203,208,219,
     =226,230,236,239,262,263,280,291,293,301,302,310,313,319,320,
     =326,329,331,338,356,362,365,367,368,376,379,383,386,391,392,
     =397,404,409,440,446,464,469,478,487,490,496,536,556,563,565,
     =566,608,617,622,623,632,635,637,638,644,649,653,655,656,665,
     =671,673,680,683,694,700,709,716,736,739,748,761,763,784,790,
     =793,802,806,818,820,833,836,847,860,863,874,881,888,899,901,
     =904,907,910,912,913,921,923,931,932,937,940,946,964,970,973,
     =989,998,1000
perfect=6,28,496,8128,33550336,8589869056,137438691328
powers_of_one=54*1
__CONF__
file_cmp "$TEST_KEY.f2" f2 rose-app.conf
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-basic-metadata
rm -f 'rose-app.conf'
cat > f3 <<'__CONF__'
[namelist:sequences=fibonacci]
help=Here are some values in the sequence:
    =0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,4181,6765,10946,17711,28657,46368,75025,121393,196418,
    =317811,514229,832040,1346269,2178309,3524578,5702887,
    =9227465,14930352,24157817,39088169
__CONF__
cp f3 rose-meta.conf
run_pass "$TEST_KEY" rose config-dump
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.f3" f3 rose-meta.conf
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-basic-metadata-subdir
rm -f 'rose-app.conf'
cat > f4 <<'__CONF__'
[namelist:sequences=fibonacci]
help=Here are some values in the sequence:
    =0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,4181,6765,10946,17711,28657,46368,75025,121393,196418,
    =317811,514229,832040,1346269,2178309,3524578,5702887,
    =9227465,14930352,24157817,39088169
__CONF__
mkdir meta
cp f4 meta/rose-meta.conf
run_pass "$TEST_KEY" rose config-dump
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.f3" f4 rose-meta.conf
teardown
#-------------------------------------------------------------------------------
exit 0
