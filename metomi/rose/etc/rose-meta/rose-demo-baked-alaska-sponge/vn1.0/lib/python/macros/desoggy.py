# Copyright (C) British Crown (Met Office) & Contributors.
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
"""This module contains:

SpongeDeSoggifier, a rose transform macro.

"""

import metomi.rose.macro


class SpongeDeSoggifier(metomi.rose.macro.MacroBase):

    """De-soggifies the sponge."""

    SOGGY_FIX_TEXT = "de-soggified"

    def transform(self, config, meta_config=None):
        """Reduce the density of the sponge."""
        sponge_density = config.get_value(["env", "SPONGE_DENSITY"])
        if sponge_density is not None and float(sponge_density) > 0.5:
            # 1 g cm^-3 is pure water, so this is pretty soggy.
            config.set(["env", "SPONGE_DENSITY"], "0.3")
            self.add_report(
                "env", "SPONGE_DENSITY", "0.3", self.SOGGY_FIX_TEXT
            )
        return config, self.reports
