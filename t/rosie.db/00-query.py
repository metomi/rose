#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------
"""Test the ability of the query parser to generate logical expressions."""

import ast
import sys
from rosie.db import DAO
from rosie.db_create import RosieDatabaseInitiator
from tempfile import NamedTemporaryFile


if __name__ == "__main__":
    f = NamedTemporaryFile()
    db_url = "sqlite:////" + f.name
    RosieDatabaseInitiator().create(db_url)
    dao = DAO(db_url)
    print str(dao.parse_filters_to_expr(ast.literal_eval(sys.argv[1])))
