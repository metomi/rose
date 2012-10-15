# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) Crown copyright Met Office. All rights reserved.
#-----------------------------------------------------------------------------

import inspect

import rose.formats
import rose.macro


TRANSFORM_FUNC_NAME = "transform_config"
VALIDATE_FUNC_NAME = "validate_config"


class FormatChecker(rose.macro.MacroBase):

    """Validates against format specifications and conventions."""

    def validate(self, config, meta_config=None):
        """Return a list of errors, if any."""
        problem_list = []
        for attr_name in dir(rose.formats):
            if attr_name.startswith("_"):
                continue
            attr = getattr(rose.formats, attr_name)
            if inspect.ismodule(attr) and hasattr(attr, VALIDATE_FUNC_NAME):
                func = getattr(attr, VALIDATE_FUNC_NAME)
                if inspect.isfunction(func):
                    problem_list += func(config, meta_config,
                                         self.add_report)
        return problem_list


class FormatFixer(rose.macro.MacroBase):

    """Transforms a configuration based on format specifications."""

    def transform(self, config, meta_config=None):
        """Return a config and a list of changes, if any."""
        changes_list = []
        for attr_name in dir(rose.formats):
            if attr_name.startswith("_"):
                continue
            attr = getattr(rose.formats, attr_name)
            if inspect.ismodule(attr) and hasattr(attr, TRANSFORM_FUNC_NAME):
                func = getattr(attr, TRANSFORM_FUNC_NAME)
                if inspect.isfunction(func):
                    config, c_list = func(config, meta_config,
                                          self.add_report)
                    changes_list += c_list
        return config, changes_list
