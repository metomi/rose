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
"""Rose configuration directory inheritance."""

from io import StringIO
import os
import shlex
from shutil import rmtree
from tempfile import mkdtemp

from metomi.rose.c3 import mro
from metomi.rose.config import ConfigDumper, ConfigLoader, ConfigNode


class BadOptionalConfigurationKeysError(Exception):

    """A error raised when bad optional configuration keys are specified."""

    def __str__(self):
        return "Bad optional configuration key(s): " + ", ".join(self.args[0])


class ConfigTree:

    """A run time Rose configuration with linearised inheritance.

    conf_tree.node -- The ConfigNode object of the configuration tree.
    conf_tree.files -- A dict of the top files in the configuration tree
                       in {rel_path: conf_dir_0, ...}
    conf_tree.files_locs -- A dict of all files in the configuration tree
                            in {rel_path: [config_dir_0, ...], ...}
    conf_tree.conf_dirs -- A lineralised list containing the source
                           directories of this configuration tree.
    """

    def __init__(self):
        self.node = ConfigNode()
        self.files = {}  # {rel path: root, ...}
        self.file_locs = {}  # {rel path: [root0, ...], ...}
        self.conf_dirs = []

    def get_file_name_of(self, key):
        """Return the full name of the file indexed by "key".

        A short hand of:
        os.path.join(conf_tree.files[key], key)

        """
        return os.path.join(self.files[key], key)

    def get_file_locs_of(self, key):
        """Return the full names of all files indexed by "key".

        Short hand for:
        [os.path.join(file_loc, key) for file_loc in conf_tree.file_locs[key]]

        """
        return [
            os.path.join(file_loc, key) for file_loc in self.file_locs[key]
        ]


class ConfigTreeLoader:

    """Load a Rose configuration with inheritance."""

    def __init__(self, *args, **kwargs):
        self.node_loader = ConfigLoader(*args, **kwargs)

    def load(
        self,
        conf_dir,
        conf_name,
        conf_dir_paths=None,
        opt_keys=None,
        conf_node=None,
        no_ignore=False,
        defines=None,
    ):
        """Load a (runtime) configuration directory with inheritance.

        Return a ConfigTree object that represents the result.

        conf_dir -- The path to the configuration directory to load.
        conf_name -- The (base) name of the configuration file.
                     E.g. "rose-suite.conf".
        conf_dir_paths -- A list of directories to locate relative paths to
                          configurations.
        opt_keys -- Optional configuration keys.
        conf_node -- A metomi.rose.config.ConfigNode to extend, or None to use
                     a fresh one.
        no_ignore -- If True, skip loading ignored config settings.
        defines -- A list of [SECTION]KEY=VALUE overrides.

        """

        if not conf_dir_paths:
            conf_dir_paths = []
        conf_dir = self._search(conf_dir, [os.getcwd()] + conf_dir_paths)
        nodes = {}  # {conf_dir: node, ...}
        conf_file_name = os.path.join(conf_dir, conf_name)
        used_keys = []
        nodes[conf_dir] = self.node_loader.load_with_opts(
            conf_file_name,
            more_keys=opt_keys,
            used_keys=used_keys,
            defines=defines,
        )

        conf_tree = ConfigTree()
        conf_tree.conf_dirs = mro(
            conf_dir,
            self._get_base_names,
            conf_name,
            conf_dir_paths,
            opt_keys,
            used_keys,
            nodes,
        )

        if opt_keys:
            bad_keys = []
            for opt_key in opt_keys:
                if (
                    opt_key not in used_keys
                    and not self.node_loader.can_miss_opt_conf_key(opt_key)
                ):
                    bad_keys.append(opt_key)
            if bad_keys:
                raise BadOptionalConfigurationKeysError(bad_keys)

        if conf_node is None:
            conf_tree.node = ConfigNode()
        else:
            conf_tree.node = conf_node
        for t_conf_dir in conf_tree.conf_dirs:
            node = nodes[t_conf_dir]
            for keys, sub_node in node.walk(no_ignore=no_ignore):
                if keys == ["", "import"]:
                    continue
                if conf_tree.node.get(keys) is None:
                    conf_tree.node.set(
                        keys, sub_node.value, sub_node.state, sub_node.comments
                    )
            for dir_path, dir_names, file_names in os.walk(t_conf_dir):
                names = [dir_ for dir_ in dir_names if dir_.startswith(".")]
                for name in names:
                    dir_names.remove(name)
                for file_name in file_names:
                    if file_name == conf_name or file_name.startswith("."):
                        continue
                    path = os.path.join(dir_path, file_name)
                    rel_path = os.path.relpath(path, t_conf_dir)
                    if rel_path not in conf_tree.files:
                        conf_tree.files[rel_path] = t_conf_dir
                    if rel_path not in conf_tree.file_locs:
                        conf_tree.file_locs[rel_path] = []
                    conf_tree.file_locs[rel_path].append(t_conf_dir)

        return conf_tree

    __call__ = load

    def _get_base_names(
        self,
        my_conf_dir,
        conf_name,
        conf_dir_paths,
        opt_keys,
        used_keys,
        nodes,
    ):
        """Return a list of configuration directories to import."""
        values = shlex.split(nodes[my_conf_dir].get_value(["import"], ""))
        i_conf_dirs = []
        for value in values:
            i_conf_dir = self._search(
                value, [os.path.dirname(my_conf_dir)] + conf_dir_paths
            )
            i_conf_file_name = os.path.join(i_conf_dir, conf_name)
            if nodes.get(i_conf_dir) is None:
                nodes[i_conf_dir] = self.node_loader.load_with_opts(
                    i_conf_file_name, more_keys=opt_keys, used_keys=used_keys
                )
            i_conf_dirs.append(i_conf_dir)
        return i_conf_dirs

    @classmethod
    def _search(cls, conf_dir, conf_dir_paths):
        """Search for named a configuration directory from a list of paths."""
        if os.path.isabs(conf_dir):
            return os.path.abspath(conf_dir)
        for conf_dir_path in conf_dir_paths:
            dir_ = os.path.join(conf_dir_path, conf_dir)
            if os.path.isdir(dir_):
                return os.path.abspath(dir_)
        return os.path.abspath(os.path.join(conf_dir_paths[0], conf_dir))


class _Test:

    """Self tests. Print results in TAP format."""

    def __init__(self):
        self.config_tree_loader = ConfigTreeLoader()
        self.config_dumper = ConfigDumper()
        self.test_num = 0
        self.test_plan = "1..13"

    def test(self, key, actual, expect):
        """Test if actual == expect."""
        self.test_num += 1
        if actual == expect:
            print("ok %d - %s" % (self.test_num, key))
        else:
            print("not ok %d - %s" % (self.test_num, key))

    def test1(self):
        """Test: configuration file only."""
        os.mkdir("t1")
        handle = open("t1/rose-t.conf", "w")
        handle.write(
            r"""title=breakfast
type=fried up

[bacon]
number=2
type=streaky

[egg]
number=2
type=fried
"""
        )
        handle.close()
        conf_tree = self.config_tree_loader("t1", "rose-t.conf")

        string_io = StringIO()
        self.config_dumper(conf_tree.node, string_io)
        self.test(
            "t1.node",
            string_io.getvalue(),
            r"""title=breakfast
type=fried up

[bacon]
number=2
type=streaky

[egg]
number=2
type=fried
""",
        )
        string_io.close()
        self.test("t1.files", conf_tree.files, {})
        conf_dir = os.path.join(os.getcwd(), "t1")
        self.test("t1.conf_dirs", conf_tree.conf_dirs, [conf_dir])

    def test2(self):
        """Test: configuration file and some other files."""
        os.mkdir("t2")
        handle = open("t2/rose-t.conf", "w")
        handle.write(
            r"""title=all day breakfast

[sausage]
number=3
type=pork and apple

[toast]
butter=yes
number=2
type=brown

[tomato]
number=1
type=grilled
"""
        )
        handle.close()
        os.mkdir("t2/bin")
        handle = open("t2/bin/make-breakfast", "w")
        handle.write(
            r"""#!/bin/sh
echo "Making breakfast $@"
"""
        )
        handle.close()
        os.chmod("t2/bin/make-breakfast", 0o755)
        os.mkdir("t2/etc")
        for key, val in (
            ("sausage", "10 fat sausages"),
            ("bread", "slice bread"),
            ("tomato", "a red tomato"),
        ):
            handle = open(os.path.join("t2/etc", key), "w")
            handle.write(val + "\n")
            handle.close()
        conf_tree = self.config_tree_loader("t2", "rose-t.conf")

        string_io = StringIO()
        self.config_dumper(conf_tree.node, string_io)
        self.test(
            "t2.node",
            string_io.getvalue(),
            r"""title=all day breakfast

[sausage]
number=3
type=pork and apple

[toast]
butter=yes
number=2
type=brown

[tomato]
number=1
type=grilled
""",
        )
        string_io.close()
        conf_dir = os.path.join(os.getcwd(), "t2")
        self.test(
            "t2.files",
            conf_tree.files,
            {
                "bin/make-breakfast": conf_dir,
                "etc/sausage": conf_dir,
                "etc/bread": conf_dir,
                "etc/tomato": conf_dir,
            },
        )
        self.test("t2.conf_dirs", conf_tree.conf_dirs, [conf_dir])

    def test3(self):
        """Test: configuration that imports t1 and t2."""
        os.mkdir("t3")
        handle = open("t3/rose-t.conf", "w")
        handle.write(
            r"""import=t2 t1
size=large
"""
        )
        handle.close()
        os.mkdir("t3/etc")
        handle = open("t3/etc/bread", "w")
        handle.write("50/50 slice bread\n")
        handle.close()
        conf_tree = self.config_tree_loader("t3", "rose-t.conf")

        string_io = StringIO()
        self.config_dumper(conf_tree.node, string_io)
        self.test(
            "t3.node",
            string_io.getvalue(),
            r"""size=large
title=all day breakfast
type=fried up

[bacon]
number=2
type=streaky

[egg]
number=2
type=fried

[sausage]
number=3
type=pork and apple

[toast]
butter=yes
number=2
type=brown

[tomato]
number=1
type=grilled
""",
        )
        string_io.close()
        t3_conf_dir = os.path.join(os.getcwd(), "t3")
        t2_conf_dir = os.path.join(os.getcwd(), "t2")
        t1_conf_dir = os.path.join(os.getcwd(), "t1")
        self.test(
            "t3.files",
            conf_tree.files,
            {
                "bin/make-breakfast": t2_conf_dir,
                "etc/sausage": t2_conf_dir,
                "etc/bread": t3_conf_dir,
                "etc/tomato": t2_conf_dir,
            },
        )
        self.test(
            "t3.conf_dirs",
            conf_tree.conf_dirs,
            [t3_conf_dir, t2_conf_dir, t1_conf_dir],
        )

    def test3_opt(self):
        """Test: configuration that imports t1 and t2, with opt conf."""
        os.mkdir("t1/opt")
        handle = open("t1/opt/rose-t-go-large.conf", "w")
        handle.write(
            r"""[bacon]
number=4

[egg]
number=3
"""
        )
        handle.close()
        os.mkdir("t3/opt")
        handle = open("t3/opt/rose-t-go-large.conf", "w")
        handle.write(
            r"""[bean]
type=baked
"""
        )
        handle.close()
        conf_tree = self.config_tree_loader(
            "t3", "rose-t.conf", opt_keys=["go-large"]
        )

        string_io = StringIO()
        self.config_dumper(conf_tree.node, string_io)
        self.test(
            "t3_opt.node",
            string_io.getvalue(),
            r"""size=large
title=all day breakfast
type=fried up

[bacon]
number=4
type=streaky

[bean]
type=baked

[egg]
number=3
type=fried

[sausage]
number=3
type=pork and apple

[toast]
butter=yes
number=2
type=brown

[tomato]
number=1
type=grilled
""",
        )
        string_io.close()

    def test4(self):
        """Test: as t3, but use an alternate path."""
        os.chdir("../b")
        os.mkdir("t4")
        handle = open("t4/rose-t.conf", "w")
        handle.write(
            r"""import=t2 t1
size=large
"""
        )
        handle.close()
        os.mkdir("t4/etc")
        handle = open("t4/etc/bread", "w")
        handle.write("50/50 slice bread\n")
        handle.close()
        conf_tree = self.config_tree_loader(
            "t4", "rose-t.conf", conf_dir_paths=["../a"]
        )

        string_io = StringIO()
        self.config_dumper(conf_tree.node, string_io)
        self.test(
            "t4.node",
            string_io.getvalue(),
            r"""size=large
title=all day breakfast
type=fried up

[bacon]
number=2
type=streaky

[egg]
number=2
type=fried

[sausage]
number=3
type=pork and apple

[toast]
butter=yes
number=2
type=brown

[tomato]
number=1
type=grilled
""",
        )
        string_io.close()
        t4_conf_dir = os.path.join(os.getcwd(), "t4")
        os.chdir("../a")
        t2_conf_dir = os.path.join(os.getcwd(), "t2")
        t1_conf_dir = os.path.join(os.getcwd(), "t1")
        self.test(
            "t4.files",
            conf_tree.files,
            {
                "bin/make-breakfast": t2_conf_dir,
                "etc/sausage": t2_conf_dir,
                "etc/bread": t4_conf_dir,
                "etc/tomato": t2_conf_dir,
                "opt/rose-t-go-large.conf": t1_conf_dir,
            },
        )
        self.test(
            "t4.conf_dirs",
            conf_tree.conf_dirs,
            [t4_conf_dir, t2_conf_dir, t1_conf_dir],
        )

    def run(self):
        """Run the tests."""
        print(self.test_plan)

        cwd = os.getcwd()
        work_dir = mkdtemp()
        a_dir = os.path.join(work_dir, "a")
        b_dir = os.path.join(work_dir, "b")
        os.mkdir(a_dir)
        os.mkdir(b_dir)
        os.chdir(a_dir)
        try:
            self.test1()
            self.test2()
            self.test3()
            self.test3_opt()
            self.test4()
        finally:
            os.chdir(cwd)
            rmtree(work_dir)


if __name__ == "__main__":
    # These modules are only required for running the self tests.
    _Test().run()
