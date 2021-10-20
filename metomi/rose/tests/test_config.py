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
from io import StringIO
import os.path

import metomi.rose.config
import pytest


def test_init():
    """Test empty Config object."""
    conf = metomi.rose.config.ConfigNode()
    assert conf is not None
    assert conf.get([]) == conf
    assert not conf.get(["rubbish"])
    node = conf.get([])
    assert node.value == {}
    node = conf.get(["rubbish"])
    assert node is None
    assert conf.unset(["rubbish"]) is None


def test_set():
    """Test setting/unsetting value/ignored flag in a Config object."""
    conf = metomi.rose.config.ConfigNode()
    assert conf is not None
    assert conf.set([], {}) == conf
    conf.set(["", "top-option"], "rubbish")
    node = conf.get(["", "top-option"])
    assert (node.value, node.state) == ("rubbish", "")
    node = conf.get(["top-option"])
    assert (node.value, node.state) == ("rubbish", "")
    conf.set(["rubbish"], {})
    node = conf.get(["rubbish"])
    assert (node.value, node.state) == ({}, "")
    conf.set(["rubbish", "item"], "value")
    node = conf.get(["rubbish", "item"])
    assert (node.value, node.state) == ("value", "")
    assert conf.get(["rubbish", "item"]).value == "value"
    conf.get(["rubbish", "item"]).state = "!"
    node = conf.get(["rubbish", "item"], no_ignore=True)
    assert node is None
    assert conf.get(["rubbish", "item"]).value == "value"
    conf.get(["rubbish", "item"]).state = ""
    assert conf.get(["rubbish", "item"]) is not None
    assert conf.get(["rubbish", "item"]).value == "value"
    node = conf.unset(["rubbish", "item"])
    assert (node.value, node.state) == ("value", "")
    assert conf.unset(["rubbish", "item"]) is None
    conf.set(["rubbish", "item"], "value", "!!")
    node = conf.get(["rubbish", "item"])
    assert (node.value, node.state) == ("value", "!!")
    assert conf.unset(["rubbish"]) is not None
    conf.set(["rubbish"], {})
    node = conf.get(["rubbish"])
    assert (node.value, node.state) == ({}, "")
    conf.set(["rubbish", "item"], "value")
    node = conf.get(["rubbish", "item"])
    assert (node.value, node.state) == ("value", "")
    conf.get(["rubbish"]).state = "!"
    assert conf.get(["rubbish", "item"], True) is None


def test_iter():
    """Test the iterator"""
    conf = metomi.rose.config.ConfigNode()
    conf.set(["", "food"], "glorious")
    conf.set(["dinner", "starter"], "soup")
    conf.set(["dinner", "dessert"], "custard")
    assert list(iter(conf)) == ["food", "dinner"]
    end_node = conf.get(["", "food"])
    assert list(iter(end_node)) == []

    """Test usage of the metomi.rose.config.Dump object."""


def test_dump_empty():
    """Test dumping an empty configuration."""
    conf = metomi.rose.config.ConfigNode({})
    dumper = metomi.rose.config.ConfigDumper()
    target = StringIO()
    dumper.dump(conf, target)
    assert target.getvalue() == ""
    target.close()


def test_dump_normal():
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
    assert (
        target.getvalue()
        == """[egg]
boiled=false
fried=true
!!poached=true
!scrambled=false

[foo]
bar=BAR BAR
baz=BAZ
   = BAZ
"""
    )
    target.close()


def test_dump_root():
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
    assert (
        target.getvalue()
        == """#hello

bar=bar
#foo foo
#foo foo
foo=foo

[baz]
egg=egg
ham=ham
"""
    )
    target.close()


"""Test usage of the metomi.rose.config.Load object."""


def test_load_empty():
    """Test loading an empty configuration."""
    conf = metomi.rose.config.ConfigNode({})
    loader = metomi.rose.config.ConfigLoader()
    loader.load(os.path.devnull, conf)
    assert (conf.value, conf.state) == ({}, "")


def test_load_basic():
    """Test basic loading a configuration."""
    conf = metomi.rose.config.ConfigNode({})
    source = StringIO(
        """# test

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
"""
    )
    loader = metomi.rose.config.ConfigLoader()
    loader.load(source, conf)
    source.close()
    assert conf.comments == [" test"]
    for keys in [[], ["egg"], ["foo"]]:
        node = conf.get(keys)
        assert node is not None
        assert node.state == ""
    node = conf.get(["not-defined"])
    assert node is None
    for keys, value in [
        (["egg", "boiled"], "false"),
        (["egg", "fried"], "true"),
        (["egg", "scrambled"], "false"),
        (["foo", "bar"], "BAR BAR BAR"),
        (["foo", "baz"], "BAZ\nBAZ"),
        (["hello", "worlds"], "earth\n  moon\n  mars"),
    ]:
        node = conf.get(keys)
        assert (node.value, node.state) == (value, "")
    node = conf.get(["egg"])
    assert node.comments == ["eggy"]
    node = conf.get(["stuff"])
    assert node.value == "stuffing"
    node = conf.get(["hello", "name"], True)
    assert node is None
    node = conf.get(["hello", "name"])
    assert node.value == "fred"
    assert node.state == "!"
    node = conf.get(["hello", "greet"])
    assert node.value == "hi"
    assert node.state == "!!"


def test_load_bad_syntax():
    """Test loading a configuration with bad syntax present"""
    loader = metomi.rose.config.ConfigLoader()
    source = StringIO(
        """# test
foo=bar
baz
"""
    )
    with pytest.raises(metomi.rose.config.ConfigSyntaxError) as exc:
        loader.load(source)
    assert exc.value.code == 'BAD_SYNTAX'
    assert exc.value.line_num == 3


def test_load_info_config_bad_syntax():
    """Test loading a configuration in which sections are not allowed"""
    loader = metomi.rose.config.ConfigLoader(allow_sections=False)
    source = StringIO(
        """# test
stuff=stuffing
[egg]
boiled=false
"""
    )
    with pytest.raises(metomi.rose.config.ConfigSyntaxError) as exc:
        loader.load(source)
    assert exc.value.code == 'SECTIONS_NOT_ALLOWED'
    assert exc.value.line_num == 3
