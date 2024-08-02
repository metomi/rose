# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2020 British Crown (Met Office) & Contributors.
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
"""This holds some shared functionality between stash and stash_add."""


def get_stash_section_meta(stash_meta_lookup, stash_section,
                           stash_item, stash_description):
    """Return a dictionary of metadata properties for this stash record."""
    try:
        stash_code = 1000 * int(stash_section) + int(stash_item)
    except (TypeError, ValueError):
        return {}
    meta_key = "code(%d)" % stash_code
    return stash_meta_lookup.get(meta_key, {})
