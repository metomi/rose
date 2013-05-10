#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------

import os
from rose.c3 import mro, MROError
from rose.config import ConfigNode, ConfigLoader
import shlex


class ConfigTree(object):

    """Represent a (runtime) Rose configuration (directory) with inheritance.

    config_tree.node -- The ConfigNode object of the configuration tree.
    config_tree.files -- A dict of the files in the configuration tree
                         in {file-rel-path: config-dir, ...}
    config_tree.conf_dirs -- A lineralised list containing the source
                             directories of this configuration tree.
    """

    def __init__(self):
        self.node = ConfigNode()
        self.files = {} # {relative path: root, ...}
        self.conf_dirs = []


class ConfigTreeLoader(object):

    """Load a Rose configuration with inheritance."""

    def __init__(self, *args, **kwargs):
        self.node_loader = ConfigLoader(*args, **kwargs)

    def load(self, conf_dir, conf_name, conf_dir_paths=None, opt_keys=None):
        """Load a (runtime) configuration directory with inheritance.

        Return a ConfigTree object that represents the result.

        conf_dir -- The path to the configuration directory to load.
        conf_name -- The (base) name of the configuration file.
                     E.g. "rose-suite.conf".
        conf_dir_paths -- A list of directories to locate relative paths to
                          configurations.
        opt_keys -- Optional configuration keys.

        """

        if not conf_dir_paths:
            conf_dir_paths = []
        conf_dir = self._search(conf_dir, [os.getcwd()] + conf_dir_paths)
        nodes = {} # {conf_dir: node, ...}
        conf_file_name = os.path.join(conf_dir, conf_name)
        nodes[conf_dir] = self.node_loader.load_with_opts(
                conf_file_name, more_keys=opt_keys,
                ignore_missing_more_keys=True)

        config_tree = ConfigTree()
        config_tree.conf_dirs = mro(conf_dir, self._get_base_names, conf_name,
                                    conf_dir_paths, opt_keys, nodes)

        config_tree.node = ConfigNode()
        for t_conf_dir in config_tree.conf_dirs:
            node = nodes[t_conf_dir]
            for keys, sub_node in node.walk(no_ignore=True):
                if keys == ["", "import"]:
                    continue
                if config_tree.node.get_value(keys) is None:
                    config_tree.node.set(keys, sub_node.value)
            for dir_path, dir_names, file_names in os.walk(t_conf_dir):
                for file_name in file_names:
                    if file_name == conf_name:
                        continue
                    path = os.path.join(dir_path, file_name)
                    rel_path = os.path.relpath(path, t_conf_dir)
                    if not config_tree.files.has_key(rel_path):
                        config_tree.files[rel_path] = t_conf_dir

        return config_tree

    __call__ = load

    def _get_base_names(self, my_conf_dir, conf_name, conf_dir_paths, opt_keys,
                        nodes):
        values = shlex.split(nodes[my_conf_dir].get_value(["import"], ""))
        i_conf_dirs = []
        for value in values:
            i_conf_dir = self._search(
                    value, [os.path.dirname(my_conf_dir)] + conf_dir_paths)
            i_conf_file_name = os.path.join(i_conf_dir, conf_name)
            if nodes.get(i_conf_dir) is None:
                nodes[i_conf_dir] = self.node_loader.load_with_opts(
                        i_conf_file_name, more_keys=opt_keys,
                        ignore_missing_more_keys=True)
            i_conf_dirs.append(i_conf_dir)
        return i_conf_dirs

    def _search(self, conf_dir, conf_dir_paths):
        if os.path.isabs(conf_dir):
            return os.path.realpath(conf_dir)
        for conf_dir_path in conf_dir_paths:
            d = os.path.join(conf_dir_path, conf_dir)
            if os.path.isdir(d):
                return os.path.realpath(d)
        return os.path.realpath(os.path.join(conf_dir_paths[0], conf_dir))


class _Test(object):

    """Self tests. Print results in TAP format."""

    def __init__(self):
        self.config_tree_loader = ConfigTreeLoader()
        self.config_dumper = ConfigDumper()
        self.test_num = 0
        self.test_plan = "1..13"

    def ok(self, key, cond):
        self.test_num += 1
        if cond:
            print "ok %d - %s" % (self.test_num, key)
        else:
            print "not ok %d - %s" % (self.test_num, key)

    def test(self, key, actual, expect):
        self.ok(key, actual == expect)

    def t1(self):
        """Test: configuration file only."""
        os.mkdir("t1")
        f = open("t1/rose-t.conf", "wb")
        f.write(r"""title=breakfast
type=fried up

[bacon]
number=2
type=streaky

[egg]
number=2
type=fried
""")
        f.close()
        config_tree = self.config_tree_loader("t1", "rose-t.conf")

        string_io = StringIO()
        self.config_dumper(config_tree.node, string_io)
        self.test("t1.node", string_io.getvalue(), r"""title=breakfast
type=fried up

[bacon]
number=2
type=streaky

[egg]
number=2
type=fried
""")
        string_io.close()
        self.test("t1.files", config_tree.files, {})
        conf_dir = os.path.join(os.getcwd(), "t1")
        self.test("t1.conf_dirs", config_tree.conf_dirs, [conf_dir])

    def t2(self):
        """Test: configuration file and some other files."""
        os.mkdir("t2")
        f = open("t2/rose-t.conf", "wb")
        f.write(r"""title=all day breakfast

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
""")
        f.close()
        os.mkdir("t2/bin")
        f = open("t2/bin/make-breakfast", "wb")
        f.write(r"""#!/bin/sh
echo "Making breakfast $@"
""")
        f.close()
        os.chmod("t2/bin/make-breakfast", 0755)
        os.mkdir("t2/etc")
        for k, v in (("sausage", "10 fat sausages"),
                     ("bread", "slice bread"),
                     ("tomato", "a red tomato")):
            f = open(os.path.join("t2/etc", k), "wb")
            f.write(v + "\n")
            f.close()
        config_tree = self.config_tree_loader("t2", "rose-t.conf")

        string_io = StringIO()
        self.config_dumper(config_tree.node, string_io)
        self.test("t2.node", string_io.getvalue(), r"""title=all day breakfast

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
""")
        string_io.close()
        conf_dir = os.path.join(os.getcwd(), "t2")
        self.test("t2.files", config_tree.files,
                  {"bin/make-breakfast": conf_dir,
                   "etc/sausage": conf_dir,
                   "etc/bread": conf_dir,
                   "etc/tomato": conf_dir})
        self.test("t2.conf_dirs", config_tree.conf_dirs, [conf_dir])

    def t3(self):
        """Test: configuration that imports t1 and t2."""
        os.mkdir("t3")
        f = open("t3/rose-t.conf", "wb")
        f.write(r"""import=t2 t1
size=large
""")
        f.close()
        os.mkdir("t3/etc")
        f = open("t3/etc/bread", "wb")
        f.write("50/50 slice bread\n")
        f.close()
        config_tree = self.config_tree_loader("t3", "rose-t.conf")

        string_io = StringIO()
        self.config_dumper(config_tree.node, string_io)
        self.test("t3.node", string_io.getvalue(), r"""size=large
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
""")
        string_io.close()
        t3_conf_dir = os.path.join(os.getcwd(), "t3")
        t2_conf_dir = os.path.join(os.getcwd(), "t2")
        t1_conf_dir = os.path.join(os.getcwd(), "t1")
        self.test("t3.files", config_tree.files,
                  {"bin/make-breakfast": t2_conf_dir,
                   "etc/sausage": t2_conf_dir,
                   "etc/bread": t3_conf_dir,
                   "etc/tomato": t2_conf_dir})
        self.test("t3.conf_dirs", config_tree.conf_dirs,
             [t3_conf_dir, t2_conf_dir, t1_conf_dir])

    def t3_opt(self):
        """Test: configuration that imports t1 and t2, with opt conf."""
        os.mkdir("t1/opt")
        f = open("t1/opt/rose-t-go-large.conf", "wb")
        f.write(r"""[bacon]
number=4

[egg]
number=3
""")
        f.close()
        os.mkdir("t3/opt")
        f = open("t3/opt/rose-t-go-large.conf", "wb")
        f.write(r"""[bean]
type=baked
""")
        f.close()
        config_tree = self.config_tree_loader("t3", "rose-t.conf",
                                         opt_keys=["go-large"])

        string_io = StringIO()
        self.config_dumper(config_tree.node, string_io)
        self.test("t3_opt.node", string_io.getvalue(), r"""size=large
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
""")
        string_io.close()

    def t4(self):
        """Test: as t3, but use an alternate path."""
        os.chdir("../b")
        os.mkdir("t4")
        f = open("t4/rose-t.conf", "wb")
        f.write(r"""import=t2 t1
size=large
""")
        f.close()
        os.mkdir("t4/etc")
        f = open("t4/etc/bread", "wb")
        f.write("50/50 slice bread\n")
        f.close()
        config_tree = self.config_tree_loader("t4", "rose-t.conf",
                                         conf_dir_paths=["../a"])

        string_io = StringIO()
        self.config_dumper(config_tree.node, string_io)
        self.test("t4.node", string_io.getvalue(), r"""size=large
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
""")
        string_io.close()
        t4_conf_dir = os.path.join(os.getcwd(), "t4")
        os.chdir("../a")
        t2_conf_dir = os.path.join(os.getcwd(), "t2")
        t1_conf_dir = os.path.join(os.getcwd(), "t1")
        self.test("t4.files", config_tree.files,
             {"bin/make-breakfast": t2_conf_dir,
              "etc/sausage": t2_conf_dir,
              "etc/bread": t4_conf_dir,
              "etc/tomato": t2_conf_dir,
              "opt/rose-t-go-large.conf": t1_conf_dir})
        self.test("t4.conf_dirs", config_tree.conf_dirs,
             [t4_conf_dir, t2_conf_dir, t1_conf_dir])

    def run(self):
        print self.test_plan

        cwd = os.getcwd()
        work_dir = mkdtemp()
        a_dir = os.path.join(work_dir, "a")
        b_dir = os.path.join(work_dir, "b")
        os.mkdir(a_dir)
        os.mkdir(b_dir)
        os.chdir(a_dir)
        try:
            self.t1()
            self.t2()
            self.t3()
            self.t3_opt()
            self.t4()
        finally:
            os.chdir(cwd)
            rmtree(work_dir)


if __name__ == "__main__":
    # These modules are only required for running the self tests.
    from rose.config import ConfigDumper
    from StringIO import StringIO
    from shutil import rmtree
    from tempfile import mkdtemp
    _Test().run()
