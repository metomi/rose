# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
#
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
import os.path
import metomi.rose.config
from io import StringIO
import unittest


class TestConfigData(unittest.TestCase):
    """Test usage of the metomi.rose.config.ConfigNode object."""

    def test_init(self):
        """Test empty Config object."""
        conf = metomi.rose.config.ConfigNode()
        self.assertFalse(conf is None)
        self.assertEqual(conf.get([]), conf)
        self.assertFalse(conf.get(["rubbish"]))
        node = conf.get([])
        self.assertEqual(node.value, {})
        node = conf.get(["rubbish"])
        self.assertTrue(node is None)
        self.assertTrue(conf.unset(["rubbish"]) is None)

    def test_set(self):
        """Test setting/unsetting value/ignored flag in a Config object."""
        conf = metomi.rose.config.ConfigNode()
        self.assertFalse(conf is None)
        self.assertEqual(conf.set([], {}), conf)
        conf.set(["", "top-option"], "rubbish")
        node = conf.get(["", "top-option"])
        self.assertEqual((node.value, node.state), ("rubbish", ""))
        node = conf.get(["top-option"])
        self.assertEqual((node.value, node.state), ("rubbish", ""))
        conf.set(["rubbish"], {})
        node = conf.get(["rubbish"])
        self.assertEqual((node.value, node.state), ({}, ""))
        conf.set(["rubbish", "item"], "value")
        node = conf.get(["rubbish", "item"])
        self.assertEqual((node.value, node.state), ("value", ""))
        self.assertEqual(conf.get(["rubbish", "item"]).value, "value")
        conf.get(["rubbish", "item"]).state = "!"
        node = conf.get(["rubbish", "item"], no_ignore=True)
        self.assertTrue(node is None)
        self.assertEqual(conf.get(["rubbish", "item"]).value, "value")
        conf.get(["rubbish", "item"]).state = ""
        self.assertTrue(conf.get(["rubbish", "item"]) is not None)
        self.assertEqual(conf.get(["rubbish", "item"]).value, "value")
        node = conf.unset(["rubbish", "item"])
        self.assertEqual((node.value, node.state), ("value", ""))
        self.assertEqual(conf.unset(["rubbish", "item"]), None)
        conf.set(["rubbish", "item"], "value", "!!")
        node = conf.get(["rubbish", "item"])
        self.assertEqual((node.value, node.state), ("value", "!!"))
        self.assertTrue(conf.unset(["rubbish"]) is not None)
        conf.set(["rubbish"], {})
        node = conf.get(["rubbish"])
        self.assertEqual((node.value, node.state), ({}, ""))
        conf.set(["rubbish", "item"], "value")
        node = conf.get(["rubbish", "item"])
        self.assertEqual((node.value, node.state), ("value", ""))
        conf.get(["rubbish"]).state = "!"
        self.assertTrue(conf.get(["rubbish", "item"], True) is None)

    def test_iter(self):
        """Test the iterator"""
        conf = metomi.rose.config.ConfigNode()
        conf.set(["", "food"], "glorious")
        conf.set(["dinner", "starter"], "soup")
        conf.set(["dinner", "dessert"], "custard")
        self.assertEqual(list(iter(conf)), ["food", "dinner"])
        end_node = conf.get(["", "food"])
        self.assertEqual(list(iter(end_node)), [])


class TestConfigDump(unittest.TestCase):
    """Test usage of the metomi.rose.config.Dump object."""

    def test_dump_empty(self):
        """Test dumping an empty configuration."""
        conf = metomi.rose.config.ConfigNode({})
        dumper = metomi.rose.config.ConfigDumper()
        target = StringIO()
        dumper.dump(conf, target)
        self.assertEqual(target.getvalue(), "")
        target.close()

    def test_dump_normal(self):
        """Test normal dumping a configuration."""
        conf = metomi.rose.config.ConfigNode({})
        conf.set(["foo"], {})
        conf.set(["foo", "bar"], "BAR BAR")
        conf.set(["foo", "baz"], "BAZ\n BAZ")
        conf.set(["egg"], {})
        conf.set(["egg", "fried"], "true")
        conf.set(["egg", "boiled"], "false")
        conf.set(["egg", "scrambled"], "false", "!")
        conf.set(["egg", "poached"], "true", "!!")
        dumper = metomi.rose.config.ConfigDumper()
        target = StringIO()
        dumper.dump(conf, target)
        self.assertEqual(target.getvalue(), """[egg]
boiled=false
fried=true
!!poached=true
!scrambled=false

[foo]
bar=BAR BAR
baz=BAZ
   = BAZ
""")
        target.close()

    def test_dump_root(self):
        """Test dumping of a configuration with root settings."""
        conf = metomi.rose.config.ConfigNode({}, comments=["hello"])
        conf.set(["foo"], "foo", comments=["foo foo", "foo foo"])
        conf.set(["bar"], "bar")
        conf.set(["baz"], {})
        conf.set(["baz", "egg"], "egg")
        conf.set(["baz", "ham"], "ham")
        dumper = metomi.rose.config.ConfigDumper()
        target = StringIO()
        dumper.dump(conf, target)
        self.assertEqual(target.getvalue(), """#hello

bar=bar
#foo foo
#foo foo
foo=foo

[baz]
egg=egg
ham=ham
""")
        target.close()


class TestConfigLoad(unittest.TestCase):
    """Test usage of the metomi.rose.config.Load object."""

    def test_load_empty(self):
        """Test loading an empty configuration."""
        conf = metomi.rose.config.ConfigNode({})
        loader = metomi.rose.config.ConfigLoader()
        loader.load(os.path.devnull, conf)
        self.assertEqual((conf.value, conf.state), ({}, ""))

    def test_load_basic(self):
        """Test basic loading a configuration."""
        conf = metomi.rose.config.ConfigNode({})
        source = StringIO("""# test

stuff=stuffing

#eggy
[egg]
boiled=false
fried=true
scrambled=false

[foo]
bar=BAR BAR
baz=BAZ
    BAZ

[hello]
!name = fred
!!greet = hi
worlds=earth
      =  moon
      =  mars

[foo]
bar=BAR BAR BAR
""")
        loader = metomi.rose.config.ConfigLoader()
        loader.load(source, conf)
        source.close()
        self.assertEqual(conf.comments, [" test"])
        for keys in [[], ["egg"], ["foo"]]:
            node = conf.get(keys)
            self.assertFalse(node is None)
            self.assertEqual(node.state, "")
        node = conf.get(["not-defined"])
        self.assertTrue(node is None)
        for keys, value in [(["egg", "boiled"], "false"),
                            (["egg", "fried"], "true"),
                            (["egg", "scrambled"], "false"),
                            (["foo", "bar"], "BAR BAR BAR"),
                            (["foo", "baz"], "BAZ\nBAZ"),
                            (["hello", "worlds"], "earth\n  moon\n  mars")]:
            node = conf.get(keys)
            self.assertEqual((node.value, node.state), (value, ""))
        node = conf.get(["egg"])
        self.assertEqual(node.comments, ["eggy"])
        node = conf.get(["stuff"])
        self.assertEqual(node.value, "stuffing")
        node = conf.get(["hello", "name"], True)
        self.assertTrue(node is None)
        node = conf.get(["hello", "name"])
        self.assertEqual(node.value, "fred")
        self.assertEqual(node.state, "!")
        node = conf.get(["hello", "greet"])
        self.assertEqual(node.value, "hi")
        self.assertEqual(node.state, "!!")


if __name__ == "__main__":
    unittest.main()
