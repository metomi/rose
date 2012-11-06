#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) Crown copyright Met Office. All rights reserved.
#-----------------------------------------------------------------------------

import rose.macro
import rose.variable


class FibonacciChecker(rose.macro.MacroBase):

    """Class to check if an array matches a Fibonacci sequence."""

    BAD_SEQUENCE = "not the Fibonacci sequence"

    def validate(self, config, meta_config):
        """Validate an array containing integer elements."""
        self.reports = []
        seq = [1, 1]
        problem_list = []
        section = "env"
        option = "INVALID_SEQUENCE"
        node = config.get([section, option])
        if node is None:
            return []
        value = node.value
        elems = rose.variable.array_split(value)
        if all([w.isdigit() for w in elems]) and len(elems) > 1:
            int_elems = [int(w) for w in elems]
            if len(int_elems) >= 2 and int_elems[:2] != seq:
                self._flag_problem(section, option, value)
            else:
                for i, element in enumerate(int_elems):
                    if i < 2:
                        continue
                    if element != int_elems[i - 1] + int_elems[i - 2]:
                        self.add_report(section, option, value,
                                        self.BAD_SEQUENCE)
                        break
        else:
            self.add_report(section, option, value,
                            self.BAD_SEQUENCE)
        return self.reports
