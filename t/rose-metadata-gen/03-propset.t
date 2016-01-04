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
# Test "rose metadata-gen" properties setting.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<__CONFIG__
[namelist:testnl1]
my_char = 'Character string'
my_char_array = 'a', 'b', 'c'
my_int = 1
my_int_array_long = 1, 2, 3, 4, 5, 6
my_raw = Raw string
my_real = 1.0
my_real_array = 1.0, 2.0, 3.0
my_logical = .false.
my_logical_array = .false., .true., .false.
my_derived = 'String', 1.0, 2, .false.
my_derived_array = 'String1', 1.0, 2, .false., 'String2', 3.0, 4, .true.
__CONFIG__
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Compulsory property set.
TEST_KEY=$TEST_KEY_BASE-compulsory-true
setup
run_pass "$TEST_KEY" rose metadata-gen --config=../config compulsory=true
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.conf" ../config/meta/rose-meta.conf - <<'__CONTENT__'
[namelist:testnl1]
compulsory=true

[namelist:testnl1=my_char]
compulsory=true

[namelist:testnl1=my_char_array]
compulsory=true

[namelist:testnl1=my_derived]
compulsory=true

[namelist:testnl1=my_derived_array]
compulsory=true

[namelist:testnl1=my_int]
compulsory=true

[namelist:testnl1=my_int_array_long]
compulsory=true

[namelist:testnl1=my_logical]
compulsory=true

[namelist:testnl1=my_logical_array]
compulsory=true

[namelist:testnl1=my_raw]
compulsory=true

[namelist:testnl1=my_real]
compulsory=true

[namelist:testnl1=my_real_array]
compulsory=true
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Null title property set.
TEST_KEY=$TEST_KEY_BASE-title-null
setup
run_pass "$TEST_KEY" rose metadata-gen --config=../config title
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.conf" ../config/meta/rose-meta.conf - <<'__CONTENT__'
[namelist:testnl1]
title=

[namelist:testnl1=my_char]
title=

[namelist:testnl1=my_char_array]
title=

[namelist:testnl1=my_derived]
title=

[namelist:testnl1=my_derived_array]
title=

[namelist:testnl1=my_int]
title=

[namelist:testnl1=my_int_array_long]
title=

[namelist:testnl1=my_logical]
title=

[namelist:testnl1=my_logical_array]
title=

[namelist:testnl1=my_raw]
title=

[namelist:testnl1=my_real]
title=

[namelist:testnl1=my_real_array]
title=
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Many properties set.
TEST_KEY=$TEST_KEY_BASE-many-props
setup
run_pass "$TEST_KEY" rose metadata-gen --config=../config description=favourite help= url=google.com title type
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.conf" ../config/meta/rose-meta.conf - <<'__CONTENT__'
[namelist:testnl1]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_char]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_char_array]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_derived]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_derived_array]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_int]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_int_array_long]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_logical]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_logical_array]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_raw]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_real]
description=favourite
help=
title=
type=
url=google.com

[namelist:testnl1=my_real_array]
description=favourite
help=
title=
type=
url=google.com
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
