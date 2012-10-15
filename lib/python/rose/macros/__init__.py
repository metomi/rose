# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
"""
Module to contain internal system macros for operating on a configuration.
"""

import inspect

import rose.macro
import compulsory
import duplicate
import format
import rule
import trigger
import value


MODULES = [compulsory, duplicate, format, rule, trigger, value]


class DefaultTransforms(rose.macro.MacroBase):

    """Runs all the default fixers, such as trigger fixing."""

    def transform(self, config, meta_config=None):
        """Apply transforms within the macros package."""
        change_list = []
        get_id = self._get_id_from_section_option
        macro_info_tuples = rose.macro.get_macro_class_methods(MODULES)
        for module_name, class_name, method, help in macro_info_tuples:
            if method != rose.macro.TRANSFORM_METHOD:
                    continue
            macro_name = ".".join([module_name, class_name])
            for module in MODULES:
                if module.__name__ == module_name:
                    macro_inst = getattr(module, class_name)()
                    macro_method = getattr(macro_inst, method)
                    break
            config, c_list = macro_method(config, meta_config)
            c_list.sort(self._sorter)
            change_list += c_list
        return config, change_list


class DefaultValidators(rose.macro.MacroBase):

    """Runs all the default checks, such as compulsory checking."""

    def validate(self, config, meta_config):
        """Apply validators within the macros package."""
        problem_list = []
        macro_info_tuples = rose.macro.get_macro_class_methods(MODULES)
        for module_name, class_name, method, help in macro_info_tuples:
            macro_name = ".".join([module_name, class_name])
            if method == rose.macro.VALIDATE_METHOD:
                for module in MODULES:
                    if module.__name__ == module_name:
                        macro_inst = getattr(module, class_name)()
                        macro_meth = getattr(macro_inst, method)
                        break
                p_list = macro_meth(config, meta_config)
                p_list.sort(self._sorter)
                problem_list += p_list
        return problem_list 
