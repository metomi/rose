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


from metomi.rose.config import ConfigNode
from metomi.rose.macros.trigger import TriggerMacro


def test_trigger_file():
    config = ConfigNode()
    meta = ConfigNode()

    # populate the config and meta nodes
    config.set(keys=['command', 'default'], value='true')
    config.set(keys=['file:foo', 'source'], value='namelist:foo')
    config.set(keys=['namelist:foo', 'switch'], value='.false.')
    meta.set(keys=['file:foo'])
    meta.set(keys=['namelist:foo=switch', 'type'], value='logical')
    meta.set(keys=['namelist:foo=switch', 'trigger'], value='file:foo: .true.')

    _, reports = TriggerMacro().transform(config, meta)
    assert reports[0].info == 'enabled      -> trig-ignored'
