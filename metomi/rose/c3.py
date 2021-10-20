#!/usr/bin/env python3
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
    results = {}  # {name: mro_list, ...}
    base_names_of = {}  # {name: base_names_list, ...}
    dependents_of = {}
    stack = [target_name]  # list of names not yet in results
    while target_name not in results:
        name = stack.pop()
        if name in results:
            continue
        base_names_of[name] = get_base_names(name, *args, **kwargs)
        if base_names_of[name]:
            # "name" has parents
            if all([n in results for n in base_names_of[name]]):
                # All parents resolved. Time to merge them.
                results[name] = [name]
                # Walk the mro of each parent, breadth 1st.
                # Generate a list of selection sequences.
                seqs = []
                queue = list(base_names_of[name])
                while queue:
                    base_name = queue.pop(0)
                    for i in range(len(results[base_name])):
                        res = results[base_name][i:]
                        if res not in seqs:
                            seqs.append(res)
                    for result in results[base_name][1:]:
                        if result not in queue:
                            queue.append(result)
                # A successful candidate is one that is no longer a parent in
                # any of the selection sequences.
                while seqs:
                    cand_name = None
                    for seq in seqs:
                        cand_name = seq[0]
                        if not any(cand_name in s[1:] for s in seqs):
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
                    if base_name not in results:
                        if base_name in dependents:
                            raise MROError(target_name)
                        dependents_of[base_name] = dependents
                        stack.append(base_name)
        else:
            # "name" has no parents
            results[name] = [name]
    return results[target_name]


class _Test:

    """Self tests. Print results in TAP format.

    Ordering obtained from http://www.python.org/download/releases/2.3/mro/.

    """

    def __init__(self):
        self.base_names_of = {}
        self.test_num = 0
        self.test_plan = "1..11"

    def get_base_names(self, name):
        """Return base names of name."""
        return self.base_names_of[name]

    def good(self, key, cond):
        """Print ok or not ok."""
        self.test_num += 1
        if cond:
            print("ok %d - %s" % (self.test_num, key))
        else:
            print("not ok %d - %s" % (self.test_num, key))

    def test(self, key, actual, expect):
        """Assert equal."""
        self.good(key, actual == expect)

    def run(self):
        """Run tests."""
        print(self.test_plan)

        # Test good cases
        self.base_names_of["O"] = []
        self.test("zero", mro("O", self.get_base_names), ["O"])

        self.base_names_of["A1"] = ["O"]
        self.base_names_of["A2"] = ["A1"]
        self.base_names_of["A3"] = ["A2"]
        self.test(
            "single", mro("A3", self.get_base_names), ["A3", "A2", "A1", "O"]
        )

        self.base_names_of["B1"] = ["O"]
        self.base_names_of["C1"] = ["O"]
        self.base_names_of["X"] = ["C1", "A1"]
        self.base_names_of["Y"] = ["C1", "B1"]
        self.base_names_of["Z"] = ["Y", "X"]
        self.test(
            "diamond-1",
            mro("Z", self.get_base_names),
            ["Z", "Y", "X", "C1", "B1", "A1", "O"],
        )

        self.base_names_of["P"] = ["C1", "A1"]
        self.base_names_of["Q"] = ["B1", "C1"]
        self.base_names_of["R"] = ["Q", "P"]
        self.test(
            "diamond-2",
            mro("R", self.get_base_names),
            ["R", "Q", "B1", "P", "C1", "A1", "O"],
        )

        self.base_names_of["P"] = ["A1", "A2"]
        self.test(
            "triangle", mro("P", self.get_base_names), ["P", "A2", "A1", "O"]
        )

        self.base_names_of["P"] = ["A1", "O"]
        self.test(
            "triangle-2", mro("P", self.get_base_names), ["P", "A1", "O"]
        )

        self.base_names_of["P"] = ["O", "A1"]
        self.test(
            "triangle-3", mro("P", self.get_base_names), ["P", "A1", "O"]
        )

        self.base_names_of["D1"] = ["O"]
        self.base_names_of["E1"] = ["O"]
        self.base_names_of["K"] = ["D1", "A1"]
        self.base_names_of["L"] = ["D1", "B1", "E1"]
        self.base_names_of["M"] = ["A1", "B1", "C1"]
        self.base_names_of["N"] = ["M", "L", "K"]
        self.test(
            "complex",
            mro("N", self.get_base_names),
            ["N", "M", "L", "K", "D1", "A1", "B1", "C1", "E1", "O"],
        )

        # Test bad cases
        self.base_names_of["CYCLIC"] = ["CYCLIC"]
        try:
            mro("CYCLIC", self.get_base_names)
        except MROError as exc:
            self.test("cyclic", str(exc), str(MROError("CYCLIC")))
        else:
            self.good("cyclic", False)

        self.base_names_of["CYCLIC1"] = ["CYCLIC3"]
        self.base_names_of["CYCLIC2"] = ["CYCLIC1"]
        self.base_names_of["CYCLIC3"] = ["CYCLIC2"]
        try:
            mro("CYCLIC3", self.get_base_names)
        except MROError as exc:
            self.test("cyclic3", str(exc), str(MROError("CYCLIC3")))
        else:
            self.good("cyclic3", False)

        self.base_names_of["A1B1"] = ["A1", "B1"]
        self.base_names_of["B1A1"] = ["B1", "A1"]
        self.base_names_of["BAD"] = ["A1B1", "B1A1"]
        try:
            mro("BAD", self.get_base_names)
        except MROError as exc:
            self.test("bad", str(exc), str(MROError("BAD")))
        else:
            self.good("bad", False)


if __name__ == "__main__":
    _Test().run()
