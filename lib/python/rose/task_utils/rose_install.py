# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
"""Task utility: install files in a given location of a suite."""

from rose.run import TaskUtilBase

class RoseInstallTaskUtil(TaskUtilBase):

    """Install files in a given location."""

    SCHEME = "rose_install"

    def can_handle(self, key):
        return key.startswith(self.SCHEME)

    def run_impl_main(self, config, opts, args, uuid, work_files):
        pass
