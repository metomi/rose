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
"""Simple INI-style configuration data model, loader and dumper.

Synopsis:

    import rose.config
    try:
        config = rose.config.load(file)
    except rose.config.SyntaxError:
        # ... do something to handle exception
    value = config.get([section, option])
    # ...

    config.set([section, option], value)
    # ...
    rose.config.dump(config, file)

Classes:
    ConfigNode - represents an individual node (setting or section).
    ConfigDumper - dumps a configuration to stdout or a file.
    ConfigLoader - loads a configuration into a Config instance.

Functions:
    dump - shorthand for ConfigDumper().dump
    load - shorthand for ConfigLoader().load

Limitations:
 * The loader does not handle trailing comments.

What about the standard library ConfigParser? Well, it is problematic:
 * The comment character and style is hard-coded.
 * The assignment character is hard-coded.
 * A duplicated section header causes an exception to be raised.
 * Option keys are transformed to lower case by default.
 * It is far too complicated and confusing.

"""

import copy
import os.path
import re
from rose.env import env_var_escape, env_var_process, UnboundEnvironmentVariableError
from rose.opt_parse import RoseOptionParser
from rose.resource import ResourceLocator
import string
import sys


CHAR_ASSIGN = "="
CHAR_COMMENT = "#"

REC_SETTING_ELEMENT = re.compile(r"^(.*?)\(?(\d+)\)?$")


class ConfigNode(object):

    """Represent a node in a configuration file."""

    STATE_NORMAL = ""
    STATE_USER_IGNORED = "!"
    STATE_SYST_IGNORED = "!!"

    def __init__(self, value=None, state=STATE_NORMAL, comments=None):
        if value is None:
            value = {}
        if comments is None:
            comments = []
        self.value = value
        #self.value = copy.deepcopy(value)
        self.state = state
        self.comments = comments

    def __repr__(self):
        return str({"value": self.value,
                    "state": self.state,
                    "comments": self.comments})

    __str__ = __repr__

    def __len__(self):
        return len(self.value)

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __delitem__(self, key):
        return self.value.pop(key)

    def __iter__(self, key):
        return self.value.items()

    def is_ignored(self):
        return self.state != self.STATE_NORMAL

    def walk(self, keys=[], no_ignore=False):
        """Return all keylist - sub-node pairs below keys.

        keys is a list defining a hierarchy of node.value
        'keys'. If an entry in keys is the null string,
        it is skipped.

        If a sub-node is at the top level, and does not
        contain any node children, a null string will be
        prepended to the returned keylist.

        """
        start_node = self.get(keys, no_ignore)
        stack = [(keys, start_node)]
        if start_node is None:
            stack = []
        while stack:
            node_keys, node = stack.pop(0)
            if isinstance(node.value, dict):
                for key in node.value.keys():
                    child_keys = node_keys + [key]
                    subnode = self.get(child_keys, no_ignore)
                    if subnode is not None:
                        stack.insert(0, (child_keys, subnode))
            if node_keys == keys:
                continue
            if len(node_keys) == 1 and not isinstance(node.value, dict):
                null_node_keys = [""] + node_keys
                yield (null_node_keys, node)
            else:
                yield (node_keys, node)

    def get(self, keys=[], no_ignore=False):
        """Return a node at the position of keys, if any.

        keys is a list defining a hierarchy of node.value
        'keys'. If an entry in keys is the null string,
        it is skipped.

        no_ignore switches on filtering nodes by their
        ignored status. If True, ignored nodes will not be
        returned. If False, ignored nodes will be returned.

        """
        if not keys:
            return self
        keys = list(keys)
        def filter_func(node):
            if no_ignore and node.state:
                return None
            return node
        node = filter_func(self)
        while node is not None and keys and keys[0] is not None:
            key = keys.pop(0)
            if not key:
                continue
            if isinstance(node.value, dict) and node.value.has_key(key):
                node = filter_func(node.value[key])
            else:
                node = None
        return node

    def get_value(self, keys=[], default=None):
        """Return the value of a normal node at the position of keys, if any.

        If the node does not exist or is ignored, return None.

        """
        return getattr(self.get(keys, no_ignore=True), "value", default)

    def set(self, keys=None, value=None, state=None, comments=None):
        """Set node properties at the position of keys, if any.

        keys is a list defining a hierarchy of node.value
        'keys'. If an entry in keys is the null string,
        it is skipped.

        value defines the node.value property at this position.

        state defines the node.state property at this position.

        comments defines the node.comments property at this position.        

        If value is None, the node is 'unset'.
        
        If state is None, the node.state property is unchanged.
        
        If comments is None, the node.comments property is unchanged.

        """
        if keys is None:
            keys = []
        else:
            keys = list(keys)
        if value is None:
            value = {}
        if not keys:
            return self
        node = self
        while keys and keys[0] is not None:
            key = keys.pop(0)
            if not key:
                continue
            if not isinstance(node.value, dict):
                node.value = {}
            if not node.value.has_key(key):
                node.value[key] = ConfigNode()
            node = node.value[key]
        node.value = value
        if state is not None:
            node.state = state
        if comments is not None:
            node.comments = comments
        return self

    def unset(self, keys=None):
        """Remove a node at this (keys) position, if any.

        keys is a list defining a hierarchy of node.value
        'keys'. If an entry in keys is the null string,
        it is skipped.

        """        
        if keys is None:
            return None
        keys = list(keys)
        key = keys.pop()
        try:
            return self.get(keys).value.pop(key)
        except:
            return None


class ConfigDumper(object):

    """Dumper of a ConfigNode object in Rose INI format."""

    def __init__(self, char_assign=CHAR_ASSIGN):
        """Initialise the configuration dumper utility.

        Arguments:
        char_assign -- the character to use to delimit a key=value assignment.

        """
        self.char_assign = char_assign

    def dump(self, root, target=sys.stdout, sort_sections=None,
             sort_option_items=None, env_escape_ok=False):
        """Format a ConfigNode object and write result to target.

        Arguments:
        root -- the root node, a ConfigNode object.
        target -- an open file handle or a string containing a
        file path. If not specified, the result is written to
        sys.stdout.
        sort_sections -- an optional argument that should be a function
        for sorting a list of section keys.
        sort_option_items -- an optional argument that should be a
        function for sorting a list of option (key, value) tuples.
        in string values.
        env_escape_ok -- an optional argument to indicate that $NAME
        and ${NAME} syntax in values should be escaped.

        """
        if sort_sections is None:
            sort_sections = sort_settings
        if sort_option_items is None:
            sort_option_items = sort_settings
        f = target
        if not hasattr(target, "write") or not hasattr(target, "close"):
            target_dir = os.path.dirname(target)
            if not target_dir:
                target_dir = "."
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)
            f = open(target, "w")
        blank = ""
        if root.comments:
            for comment in root.comments:
                f.write(self._comment_format(comment))
            blank = "\n"
        root_keys = root.value.keys()
        root_keys.sort(sort_sections)
        root_option_keys = []
        section_keys = []
        for key in root_keys:
            if isinstance(root.value[key].value, str):
                root_option_keys.append(key)
            else:
                section_keys.append(key)
        if root_option_keys:
            f.write(blank)
            blank = "\n"
            for key in root_option_keys:
                self._string_node_dump(key, root.value[key], f, env_escape_ok)
        for section_key in section_keys:
            section_node = root.value[section_key]
            f.write(blank)
            blank = "\n"
            for comment in section_node.comments:
                f.write(self._comment_format(comment))
            f.write("[%s%s]\n" % (section_node.state, section_key))
            keys = section_node.value.keys()
            keys.sort(sort_option_items)
            for key in keys:
                value = section_node.value[key]
                self._string_node_dump(key, value, f, env_escape_ok)
        if f is not target:
            f.close()

    def _string_node_dump(self, key, node, f, env_escape_ok):
        state = node.state
        values = node.value.split("\n")
        for comment in node.comments:
            f.write(self._comment_format(comment))
        value0 = values.pop(0)
        if env_escape_ok:
            value0 = env_var_escape(value0)
        f.write(state + key + self.char_assign + value0)
        f.write("\n")
        if values:
            indent = " " * len(state + key)
            for v in values:
                if env_escape_ok:
                    v = env_var_escape(v)
                f.write(indent + self.char_assign + v + "\n")

    def _comment_format(self, comment):
        return "#%s\n" % (comment)


class ConfigLoader(object):

    """Loader of an INI format configuration into a Config object."""

    RE_SECTION = re.compile(r"^\s*\[(?P<state>!?!?)(?P<section>[^\]]*)\]\s*$")

    def __init__(self, char_assign=CHAR_ASSIGN, char_comment=CHAR_COMMENT):
        """Initialise the configuration utility.

        Arguments:
        char_comment -- the character to indicate the start of a
        comment.
        char_assign -- the character to use to delimit a key=value
        assignment.

        """
        self.char_assign = char_assign
        self.char_comment = char_comment
        self.re_option = re.compile(
            r"^(?P<state>!?!?)(?P<option>[^\s"
            + char_assign
            + r"]+)\s*"
            + char_assign
            + r"\s*(?P<value>.*)$")

    def load(self, source, node=None):
        """Read a source configuration file.

        Arguments:
        source -- an open file handle or a string for a file path.
        node --- a ConfigNode object if specified, otherwise created.

        Return the node.
        
        """
        f = source
        file_name = source
        if isinstance(source, str):
            f = open(source, "r")
        else:
            try:
                file_name = f.name
            except AttributeError:
                file_name = "<???>"
        if node is None:
            node = ConfigNode()
        keys = []
        TYPE_SECTION = "TYPE_SECTION"
        TYPE_OPTION = "TYPE_OPTION"
        type = None
        comments = None
        line_num = 0
        # Note: "for line in f:" hangs for sys.stdin
        while True:
            line = f.readline()
            if not line:
                break
            line_num += 1
            # White space and comments
            if line.isspace():
                comments = []
                continue
            elif line.lstrip().startswith(self.char_comment):
                if comments is None:
                    node.comments.append(self._comment_strip(line))
                else:
                    comments.append(self._comment_strip(line))
                continue
            # Handle option continuation.
            if type == TYPE_OPTION and line[0].isspace():
                value = node.get(keys[:]).value
                value_cont = line.strip()
                if value_cont.startswith(self.char_assign):
                    value_cont = value_cont[1:]
                node.set(keys[:], value + "\n" + value_cont)
                continue
            # Match a section header?
            match = self.RE_SECTION.match(line)
            if match:
                section, state = match.group("section", "state")
                if type == TYPE_OPTION:
                    keys.pop()
                if keys:
                    keys.pop()
                if section:
                    keys.append(section)
                    type = TYPE_SECTION
                else:
                    keys = []
                    type = None
                section_node = node.get(keys[:])
                if section_node is None:
                    node.set(keys[:], {}, state, comments)
                else:
                    section_node.state = state
                    if comments:
                        section_node.comments += comments
                comments = []
                continue
            # Match the start of an option setting
            match = self.re_option.match(line)
            if not match:
                raise SyntaxError(file_name, line_num, line)
            option, value, state = match.group("option", "value", "state")
            if type == TYPE_OPTION:
                keys.pop()
            keys.append(option)
            type = TYPE_OPTION
            value = value.strip()
            node.set(keys[:], value.strip(), state, comments)
            comments = []
        if f is not source:
            f.close()
        return node

    def _comment_strip(self, line):
        return line.strip()[1:]


class SyntaxError(Exception):

    """Exception raised for syntax error loading a configuration file."""

    def __init__(self, file_name, line_number, line, e=None):
        e_string = ""
        if e:
            e_string = "%s:" % (e)
        else:
            e_string = "[SYNTAX ERROR]"
        self.message = (
            "%s %s:%d:\n%s"
            % (e_string, file_name, line_number, line)
        )
        Exception.__init__(self, self.message)

    def __repr__(self):
        return self.message

    __str__ = __repr__


_DEFAULT_CONFIG_NODE = None
def default_node(reset=False):
    """Return a node to represent the default (i.e. site/user) configuration.
    Load the configuration on 1st call only, unless "reset" is True.
    """
    global _DEFAULT_CONFIG_NODE
    if _DEFAULT_CONFIG_NODE is None or reset:
        _DEFAULT_CONFIG_NODE = ConfigNode()
        res_loc = ResourceLocator.default()
        files = [os.path.join(res_loc.get_util_home(), "etc", "rose.conf"),
                 os.path.join(os.path.expanduser("~"), ".metomi", "rose.conf")]
        for file in files:
            if os.path.isfile(file) and os.access(file, os.R_OK):
                load(file, _DEFAULT_CONFIG_NODE)
    return _DEFAULT_CONFIG_NODE


def dump(root, target=sys.stdout, sort_sections=None, sort_option_items=None,
         env_escape_ok=False):
    """See ConfigDumper.dump for detail."""
    d = ConfigDumper()
    return d.dump(root, target, sort_sections, sort_option_items, env_escape_ok)


def load(source, root=None):
    """See ConfigLoader.load for detail."""
    return ConfigLoader().load(source, root)


def sort_settings(setting_1, setting_2):
    match_1 = REC_SETTING_ELEMENT.match(setting_1)
    match_2 = REC_SETTING_ELEMENT.match(setting_2)
    if match_1 and match_2:
        text_1, num_1 = match_1.groups()
        text_2, num_2 = match_2.groups()
        if text_1 == text_2:
            return cmp(int(num_1), int(num_2))
    return cmp(setting_1, setting_2)


def main():
    """Implement the "rose config" command."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("default", "files", "keys", "no_ignore")
    opts, args = opt_parser.parse_args()
    try:
        if opts.files:
            root_node = ConfigNode()
            for file in opts.files:
                if file == "-":
                    load(sys.stdin, root_node)
                    sys.stdin.close()
                else:
                    load(file, root_node)
        else:
            root_node = default_node()
    except SyntaxError as e:
        sys.exit(repr(e))
    if opts.quietness:
        if root_node.get(args, opts.no_ignore) is None:
            sys.exit(1)
    elif opts.keys_mode:
        try:
            keys = root_node.get(args, opts.no_ignore).value.keys()
        except:
            sys.exit(1)
        keys.sort()
        for key in keys:
            print key
    elif len(args) == 0:
        dump(root_node)
    else:
        node = root_node.get(args, opts.no_ignore)
        if node is not None and isinstance(node.value, dict):
            keys = node.value.keys()
            keys.sort()
            for key in keys:
                node_of_key = node.get([key], opts.no_ignore)
                value = node_of_key.value
                state = node_of_key.state
                string = "%s%s=%s" % (state, key, value)
                lines = string.splitlines()
                print lines[0]
                i_equal = len(state + key) + 1
                for line in lines[1:]:
                    print " " * i_equal + line
        else:
            if node is None:
                if opts.default is None:
                    sys.exit(1)
                print opts.default
            else:
                print node.value


if __name__ == "__main__":
    main()
