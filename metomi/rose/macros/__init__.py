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
"""
Module to contain internal system macros for operating on a configuration.
"""

import metomi.rose.macro
from . import compulsory
from . import duplicate
from . import format
from . import rule
from . import trigger
from . import value


MODULES = [compulsory, duplicate, format, rule, trigger, value]


class DefaultTransforms(metomi.rose.macro.MacroTransformerCollection):

    """Runs all the default fixers, such as trigger fixing."""

    def __init__(self):
        macros = []
        macro_info_tuples = metomi.rose.macro.get_macro_class_methods(MODULES)
        for module_name, class_name, method, _ in macro_info_tuples:
            if method == metomi.rose.macro.TRANSFORM_METHOD:
                for module in MODULES:
                    if module.__name__ == module_name:
                        macro_inst = getattr(module, class_name)()
                        macros.append(macro_inst)
        super(DefaultTransforms, self).__init__(*macros)


class DefaultValidators(metomi.rose.macro.MacroValidatorCollection):

    """Runs all the default checks, such as compulsory checking."""

    def __init__(self):
        macros = []
        macro_info_tuples = metomi.rose.macro.get_macro_class_methods(MODULES)
        for module_name, class_name, method, _ in macro_info_tuples:
            if method == metomi.rose.macro.VALIDATE_METHOD:
                for module in MODULES:
                    if module.__name__ == module_name:
                        macro_inst = getattr(module, class_name)()
                        macros.append(macro_inst)
        super(DefaultValidators, self).__init__(*macros)
