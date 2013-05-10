#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------
"""Implement the C3 linearisation algorithm.

See http://www.python.org/download/releases/2.3/mro/ for detail.

"""


class MROError(Exception):

   """Cannot resolve MRO."""

   def __str__(self):
       return "%s: cannot resolve MRO" % self.args[0]


def mro(target_name, get_base_names, *args, **kwargs):
    """Resolve MRO for an item.

    target_name -- The name of the target item.
    get_base_names -- A callable to return the base names of an item. It should
                      have the interface:
                      [base1, ...] = get_base_names(name, *args, **kwargs)
    *args and **kwargs -- Optional arguments for get_base_names.

    Return a list e.g. [target_name, name, ...] with the correct method
    resolution order.

    """
    results = {} # {name: mro_list, ...}
    base_names_of = {} # {name: base_names_list, ...}
    dependents_of = {}
    stack = [target_name] # list of names not yet in results
    while results.get(target_name) is None:
        name = stack.pop()
        if results.get(name) is not None:
            continue
        base_names_of[name] = get_base_names(name, *args, **kwargs)
        if base_names_of[name]:
            # "name" has parents
            if all([results.get(n) is not None for n in base_names_of[name]]):
                # All parents resolved. Time to merge them.
                results[name] = [name]
                # Walk the mro of each parent, breadth 1st.
                # Generate a list of selection sequences.
                seqs = []
                q = list(base_names_of[name]) # queue
                while q:
                    base_name = q.pop(0)
                    for i in range(len(results[base_name])):
                        r = results[base_name][i:]
                        if r not in seqs:
                            seqs.append(r)
                    for result in results[base_name][1:]:
                        if result not in q:
                            q.append(result)
                # A successful candidate is one that is no longer a parent in
                # any of the selection sequences.
                while seqs:
                    cand_name = None
                    for seq in seqs:
                        cand_name = seq[0]
                        if not any([cand_name in s[1:] for s in seqs]):
                            results[name].append(cand_name)
                            break
                        cand_name = None
                    if cand_name is None:
                        raise MROError(target_name)
                    for seq in list(seqs):
                        if cand_name == seq[0]:
                            seqs.remove(seq)
            else:
                # Some parents not resolved.
                # Put "name" and unresolved parents in stack.
                stack.append(name)
                dependents = dependents_of.get(name, []) + [name]
                for base_name in base_names_of[name]:
                    if results.get(base_name) is None:
                        if base_name in dependents:
                            raise MROError(target_name)
                        dependents_of[base_name] = dependents
                        stack.append(base_name)
        else:
            # "name" has no parents
            results[name] = [name]
    return results[target_name]


if __name__ == "__main__":

    """Self tests. Print results in TAP format.

    Ordering obtained from http://www.python.org/download/releases/2.3/mro/.

    """

    base_names_of = {}

    def get_base_names(name):
        global base_names_of
        return base_names_of[name]

    n = 0
    def ok(key, cond):
        global n
        n += 1
        if cond:
            print "ok %d - %s" % (n, key)
        else:
            print "not ok %d - %s" % (n, key)

    def test(key, actual, expect):
        ok(key, actual == expect)

    print "1..9"

    # Test good cases
    base_names_of["O"] = []
    test("zero", mro("O", get_base_names), ["O"])

    base_names_of["A1"] = ["O"]
    base_names_of["A2"] = ["A1"]
    base_names_of["A3"] = ["A2"]
    test("single", mro("A3", get_base_names), ["A3", "A2", "A1", "O"])

    base_names_of["B1"] = ["O"]
    base_names_of["C1"] = ["O"]
    base_names_of["X"] = ["C1", "A1"]
    base_names_of["Y"] = ["C1", "B1"]
    base_names_of["Z"] = ["Y", "X"]
    test("diamond-1",
       mro("Z", get_base_names),
       ["Z", "Y", "X", "C1", "B1", "A1", "O"])

    base_names_of["P"] = ["C1", "A1"]
    base_names_of["Q"] = ["B1", "C1"]
    base_names_of["R"] = ["Q", "P"]
    test("diamond-2",
       mro("R", get_base_names),
       ["R", "Q", "B1", "P", "C1", "A1", "O"])

    base_names_of["P"] = ["A1", "A2"]
    test("triangle", mro("P", get_base_names), ["P", "A2", "A1", "O"])

    base_names_of["D1"] = ["O"]
    base_names_of["E1"] = ["O"]
    base_names_of["K"] = ["D1", "A1"]
    base_names_of["L"] = ["D1", "B1", "E1"]
    base_names_of["M"] = ["A1", "B1", "C1"]
    base_names_of["N"] = ["M", "L", "K"]
    test("complex",
       mro("N", get_base_names),
       ["N", "M", "L", "K", "D1", "A1", "B1", "C1", "E1", "O"])

    # Test bad cases
    base_names_of["CYCLIC"] = ["CYCLIC"]
    try:
        mro("CYCLIC", get_base_names)
    except MROError as e:
        test("cyclic", str(e), str(MROError("CYCLIC")))
    else:
        ok("cyclic", False)

    base_names_of["CYCLIC1"] = ["CYCLIC3"]
    base_names_of["CYCLIC2"] = ["CYCLIC1"]
    base_names_of["CYCLIC3"] = ["CYCLIC2"]
    try:
        mro("CYCLIC3", get_base_names)
    except MROError as e:
        test("cyclic3", str(e), str(MROError("CYCLIC3")))
    else:
        ok("cyclic3", False)

    base_names_of["A1B1"] = ["A1", "B1"]
    base_names_of["B1A1"] = ["B1", "A1"]
    base_names_of["BAD"] = ["A1B1", "B1A1"]
    try:
        mro("BAD", get_base_names)
    except MROError as e:
        test("bad", str(e), str(MROError("BAD")))
    else:
        ok("bad", False)
