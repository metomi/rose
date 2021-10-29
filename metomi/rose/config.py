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
"""Simple INI-style configuration data model, loader and dumper.

.. testsetup:: *

    import os
    from metomi.rose.config import *

.. testcleanup:: metomi.rose.config

    try:
        os.remove('config.conf')
    except OSError:
        pass

Synopsis:
    >>> # Create a config file.
    >>> with open('config.conf', 'w+') as config_file:
    ...     _ = config_file.write('''
    ... [foo]
    ... bar=Bar
    ... !baz=Baz
    ...      ''')

    >>> # Load in a config file.
    >>> try:
    ...     config_node = load('config.conf')
    ... except ConfigSyntaxError:
    ...     # Handle exception.
    ...     pass

    >>> # Retrieve config settings.
    >>> config_node.get(['foo', 'bar'])
    {'value': 'Bar', 'state': '', 'comments': []}

    >>> # Set new config settings.
    >>> _ = config_node.set(['foo', 'new'], 'New')

    >>> # Overwrite existing config settings.
    >>> _ = config_node.set(['foo', 'baz'], state=ConfigNode.STATE_NORMAL,
    ...                     value='NewBaz')

    >>> # Write out config to a file.
    >>> dump(config_node, sys.stdout)
    [foo]
    bar=Bar
    baz=NewBaz
    new=New


Classes:
    .. autosummary::
        metomi.rose.config.ConfigNode
        metomi.rose.config.ConfigNodeDiff
        metomi.rose.config.ConfigDumper
        metomi.rose.config.ConfigLoader

Functions:
    .. autosummary::
       metomi.rose.config.load
       metomi.rose.config.dump

Limitations:
    - The loader does not handle trailing comments.

What about the standard library ConfigParser? Well, it is problematic:
    - The comment character and style is hard-coded.
    - The assignment character is hard-coded.
    - A duplicated section header causes an exception to be raised.
    - Option keys are transformed to lower case by default.
    - It is far too complicated and confusing.

"""

import copy
from functools import cmp_to_key
import os.path
import re
import shlex
import sys
from tempfile import NamedTemporaryFile, SpooledTemporaryFile

from metomi.rose.env import env_var_escape
from metomi.rose.unicode_utils import write_safely

CHAR_ASSIGN = "="
CHAR_COMMENT = "#"
CHAR_SECTION_OPEN = "["
CHAR_SECTION_CLOSE = "]"

OPT_CONFIG_DIR = "opt"
REC_SETTING_ELEMENT = re.compile(r"^(.+?)\(([^)]+)\)$")

STATE_SECT_IGNORED = "^"

OPT_CONFIG_SETTING_COMMENT = " setting from opt config \"%s\" (%s)"


class ConfigNode:

    """Represent a node in a configuration file.

    Nodes are stored hierarchically, for instance the following config
        [foo]
        bar = Bar

    When loaded by ConfigNode.load(file) would result in three levels of
    ConfigNodes, the first representing "root" (i.e. the top level of the
    config), one representing the config section "foo" and one representing the
    setting "bar".

    Examples:
        >>> # Create a new ConfigNode.
        >>> config_node = ConfigNode()

        >>> # Add sub-nodes.
        >>> _ = config_node.set(keys=['foo', 'bar'], value='Bar')
        >>> _ = config_node.set(keys=['foo', 'baz'], value='Baz')
        >>> config_node # doctest: +NORMALIZE_WHITESPACE
        {'value': {'foo': {'value': {'bar': {'value': 'Bar',
                                             'state': '', 'comments': []},
                                     'baz': {'value': 'Baz',
                                             'state': '', 'comments': []}},
                           'state': '', 'comments': []}},
         'state': '', 'comments': []}

        >>> # Set the state of a node.
        >>> _ = config_node.set(keys=['foo', 'bar'],
        ...                     state=ConfigNode.STATE_USER_IGNORED)

        >>> # Get the value of the node at a position.
        >>> config_node.get_value(keys=['foo', 'baz'])
        'Baz'

        >>> # Walk over the hierarchical structure of a node.
        >>> [keys for keys, sub_node in config_node.walk()]
        [['foo'], ['foo', 'baz'], ['foo', 'bar']]

        >>> # Walk over the config skipping ignored sections.
        >>> [keys for keys, sub_node in config_node.walk(no_ignore=True)]
        [['foo'], ['foo', 'baz']]

        >>> # Add two ConfigNode instances to create a new "merged" node.
        >>> another_config_node = ConfigNode()
        >>> _ = another_config_node.set(keys=['new'], value='New')
        >>> new_config_node = config_node + another_config_node
        >>> [keys for keys, sub_node in new_config_node.walk()]
        [['', 'new'], ['foo'], ['foo', 'baz'], ['foo', 'bar']]

    """

    __slots__ = ["value", "state", "comments"]

    STATE_NORMAL = ""
    """The default state of a ConfigNode."""
    STATE_USER_IGNORED = "!"
    """ConfigNode state if it has been specifically ignored in the config."""
    STATE_SYST_IGNORED = "!!"
    """ConfigNode state if a metadata opperation has logically ignored the
    config."""

    def __init__(self, value=None, state=STATE_NORMAL, comments=None):
        if value is None:
            value = {}
        if comments is None:
            comments = []
        self.value = value
        self.state = state
        self.comments = comments

    def __repr__(self):
        return str(
            {
                "value": self.value,
                "state": self.state,
                "comments": self.comments,
            }
        )

    __str__ = __repr__

    def __len__(self):
        return len(self.value)

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __delitem__(self, key):
        return self.value.pop(key)

    def __iter__(self):
        if isinstance(self.value, dict):
            for key in self.value.keys():
                yield key

    def __eq__(self, other):
        if self is other:
            return True
        try:
            for keys_1, node_1 in self.walk(no_ignore=True):
                node_2 = other.get(keys_1, no_ignore=True)
                if (
                    type(node_1) != type(node_2)
                    or (
                        not isinstance(node_1.value, dict)
                        and node_1.value != node_2.value
                    )
                    or node_1.comments != node_2.comments
                ):
                    return False
            for keys_2, node_2 in other.walk(no_ignore=True):
                if self.get(keys_2, no_ignore=True) is None:
                    return False
        except AttributeError:  # Should handle "other is None"
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_ignored(self):
        """Return True if current node is in the "ignored" state."""
        return self.state != self.STATE_NORMAL

    def walk(self, keys=None, no_ignore=False):
        """Return all keylist - sub-node pairs below keys.

        Args:
            keys (list): A list defining a hierarchy of node.value 'keys'.
                If an entry in keys is the null string, it is skipped.
            no_ignore (bool): If True any ignored nodes will be skipped.

        Yields:
            tuple - (keys, sub_node)
                - keys (list) - A list defining a hierarchy of node.value
                  'keys'. If a sub-node is at the top level, and does not
                  contain any node children, a null string will be
                  prepended to the returned keylist.
                - sub_node (ConfigNode) - The config node at the position of
                  keys.

        Examples:
            >>> config_node = ConfigNode()
            >>> _ = config_node.set(['foo', 'bar'], 'Bar')
            >>> _ = config_node.set(['foo', 'baz'], 'Baz',
            ...                     state=ConfigNode.STATE_USER_IGNORED)

            >>> # Walk over the full hierarchy.
            >>> [keys for keys, sub_node in config_node.walk()]
            [['foo'], ['foo', 'baz'], ['foo', 'bar']]

            >>> # Walk over one branch of the hierarchy
            >>> [keys for keys, sub_node in config_node.walk(keys=['foo'])]
            [['foo', 'baz'], ['foo', 'bar']]

            >>> # Skip over ignored nodes.
            >>> [keys for keys, sub_node in config_node.walk(no_ignore=True)]
            [['foo'], ['foo', 'bar']]

            >>> # Invalid/non-existent keys.
            >>> [keys for keys, sub_node in config_node.walk(
            ...     keys=['elephant'])]
            []

        """
        if keys is None:
            keys = []
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

    def get(self, keys=None, no_ignore=False):
        """Return a node at the position of keys, if any.

        Args:
            keys (list): A list defining a hierarchy of
                node.value 'keys'. If an entry in keys is the null
                string, it is skipped.
            no_ignore (bool): If True any ignored nodes will
                not be returned.

        Returns:
            ConfigNode: The config node located at the position of keys or
            None.

        Examples:
            >>> # Create ConfigNode.
            >>> config_node = ConfigNode()
            >>> _ = config_node.set(['foo', 'bar'], 'Bar')
            >>> _ = config_node.set(['foo', 'baz'], 'Baz',
            ...     state=ConfigNode.STATE_USER_IGNORED)

            >>> # A ConfigNode containing sub-nodes.
            >>> config_node.get(keys=['foo']) # doctest: +NORMALIZE_WHITESPACE
            {'value': {'bar': {'value': 'Bar', 'state': '', 'comments': []},
                       'baz': {'value': 'Baz', 'state': '!', 'comments': []}},
             'state': '', 'comments': []}

            >>> # A bottom level sub-node.
            >>> config_node.get(keys=['foo', 'bar'])
            {'value': 'Bar', 'state': '', 'comments': []}

            >>> # Skip ignored nodes.
            >>> print(config_node.get(keys=['foo', 'baz'], no_ignore=True))
            None

        """
        if not keys:
            return self
        keys = list(keys)
        node = self.get_filter(no_ignore)
        while node is not None and keys and keys[0] is not None:
            key = keys.pop(0)
            if not key:
                continue
            if isinstance(node.value, dict) and key in node.value:
                node = node.value[key].get_filter(no_ignore)
            else:
                node = None
        return node

    def get_filter(self, no_ignore):
        """Return this ConfigNode unless no_ignore and node is ignored.

        Args:
            no_ignore (bool): If True only return this node if it is not
                ignored.

        Returns:
            ConfigNode: This ConfigNode unless no_ignore and node is ignored.

        Examples:
            >>> config_node = ConfigNode(value=42)
            >>> config_node.get_filter(False)
            {'value': 42, 'state': '', 'comments': []}
            >>> config_node.get_filter(True)
            {'value': 42, 'state': '', 'comments': []}

            >>> config_node = ConfigNode(value=42,
            ...                      state=ConfigNode.STATE_USER_IGNORED)
            >>> config_node.get_filter(False)
            {'value': 42, 'state': '!', 'comments': []}
            >>> print(config_node.get_filter(True))
            None


        """
        if no_ignore and self.state:
            return None
        return self

    def get_value(self, keys=None, default=None):
        """Return the value of a normal node at the position of keys, if any.

        If the node does not exist or is ignored, return None.

        Args:
            keys (list): A list defining a hierarchy of node.value
                'keys'. If an entry in keys is the null string, it is skipped.
            default (object): Return default if the value is not set.

        Returns:
            object: The value of this ConfigNode at the position of keys or
            default if not set.

        Examples:
            >>> # Create ConfigNode.
            >>> config_node = ConfigNode(value=42)
            >>> _ = config_node.set(['foo'], 'foo')
            >>> _ = config_node.set(['foo', 'bar'], 'Bar')

            >>> # Get value without specifying keys returns the value of the
            >>> # root ConfigNode (which in this case is a dict of its
            >>> # sub-nodes).
            >>> config_node.get_value() # doctest: +NORMALIZE_WHITESPACE
            {'foo': {'value': {'bar': {'value': 'Bar', 'state': '',
                                       'comments': []}},
                     'state': '', 'comments': []}}

            >>> # Intermediate level ConfigNode.
            >>> config_node.get_value(keys=['foo'])
            {'bar': {'value': 'Bar', 'state': '', 'comments': []}}

            >>> # Bottom level ConfigNode.
            >>> config_node.get_value(keys=['foo', 'bar'])
            'Bar'

            >>> # If there is no node located at the position of keys or if
            >>> # that node is unset then the default value is returned.
            >>> config_node.get_value(keys=['foo', 'bar', 'baz'],
            ...                       default=True)
            True
        """
        return getattr(self.get(keys, no_ignore=True), "value", default)

    def set(self, keys=None, value=None, state=None, comments=None):
        """Set node properties at the position of keys, if any.

        Arguments:
            keys (list): A list defining a hierarchy of node.value 'keys'.
                If an entry in keys is the null string, it is skipped.
            value (object): The node.value property to set at this position.
            state (str): The node.state property to set at this position.
                If None, the node.state property is unchanged.
            comments (str): The node.comments property to set at this position.
                If None, the node.comments property is unchanged.

        Returns:
            ConfigNode: This config node.

        Examples:
            >>> # Create ConfigNode.
            >>> config_node = ConfigNode()
            >>> config_node
            {'value': {}, 'state': '', 'comments': []}

            >>> # Add a sub-node at the position 'foo' with the comment 'Info'.
            >>> config_node.set(keys=['foo'], comments='Info')
            ... # doctest: +NORMALIZE_WHITESPACE
            {'value': {'foo': {'value': {}, 'state': '', 'comments': 'Info'}},
             'state': '', 'comments': []}

            >>> # Set the value for the sub-node at the position
            >>> # 'foo' to 'Foo'.
            >>> config_node.set(keys=['foo'], value='Foo')
            ... # doctest: +NORMALIZE_WHITESPACE
            {'value': {'foo': {'value': 'Foo', 'state': '',
                               'comments': 'Info'}},
             'state': '', 'comments': []}

            >>> # Set the value of the ConfigNode to True, this overwrites all
            >>> # sub-nodes!
            >>> config_node.set(keys=[''], value=True)
            {'value': True, 'state': '', 'comments': []}

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
            if key not in node.value:
                node.value[key] = ConfigNode()
            node = node.value[key]
        node.value = value
        if state is not None:
            node.state = state
        if comments is not None:
            node.comments = comments
        return self

    def unset(self, keys=None):
        """Remove a node at the position of keys, if any.

        Args:
            keys (list): A list defining a hierarchy of node.value 'keys'.
                If an entry in keys is the null string, it is skipped.

        Returns:
            ConfigNode: The ConfigNode instance that was removed, else None.

        Examples:
            >>> # Create ConfigNode.
            >>> config_node = ConfigNode()
            >>> _ = config_node.set(keys=['foo'], value='Foo')

            >>> # Unset without providing any keys does nothing.
            >>> print(config_node.unset())
            None

            >>> # Unset with invalid keys does nothing.
            >>> print(config_node.unset(keys=['bar']))
            None

            >>> # Unset with valid keys removes the node from the node.
            >>> config_node.unset(keys=['foo'])
            {'value': 'Foo', 'state': '', 'comments': []}

            >>> config_node
            {'value': {}, 'state': '', 'comments': []}

        """
        if keys is None:
            return None
        keys = list(keys)
        key = keys.pop()
        while keys and key is None:
            key = keys.pop()
        try:
            return self.get(keys).value.pop(key)
        except (KeyError, AttributeError):
            return None

    def add(self, config_diff):
        """Apply a ConfigNodeDiff object to self.

        Args:
            config_diff (ConfigNodeDiff): A diff to apply to this ConfigNode.

        Examples:
            >>> # Create ConfigNode
            >>> config_node = ConfigNode()
            >>> _ = config_node.set(keys=['foo', 'bar'], value='Bar')
            >>> [keys for keys, sub_node in config_node.walk()]
            [['foo'], ['foo', 'bar']]

            >>> # Create ConfigNodeDiff
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_added_setting(keys=['foo', 'baz'],
            ...                                    data='Baz')

            >>> # Apply ConfigNodeDiff to ConfigNode
            >>> config_node.add(config_node_diff)
            >>> [keys for keys, sub_node in config_node.walk()]
            [['foo'], ['foo', 'baz'], ['foo', 'bar']]
        """
        for added_key, added_data in config_diff.get_added():
            value, state, comments = added_data
            self.set(
                keys=added_key, value=value, state=state, comments=comments
            )
        for modified_key, modified_data in config_diff.get_modified():
            # Should we check that the original data matches what we have?
            orig_value = modified_data[0][0]
            value, state, comments = modified_data[1]
            if orig_value is None and value is None:
                # A section - be careful not to change an existing node value.
                subnode = self.get(keys=modified_key)
                if subnode is None:
                    self.set(keys=modified_key, state=state, comments=comments)
                else:
                    subnode.state = state
                    subnode.comments = comments
            else:
                self.set(
                    keys=modified_key,
                    value=value,
                    state=state,
                    comments=comments,
                )
        for removed_key, _ in config_diff.get_removed():
            self.unset(keys=removed_key)

    def __add__(self, config_diff):
        """Return a new node by applying a node or diff to self.

        Create a new node by applying either a ConfigNodeDiff or ConfigNode
        instance to this ConfigNode.

        Arguments:
            config_diff - Either a ConfigNodeDiff or a ConfigNode.

        Returns:
            node - The new ConfigNode.

        Examples:
            >>> # Add one ConfigNode to another ConfigNode
            >>> config_node_1 = ConfigNode()
            >>> _ = config_node_1.set(keys=['foo'], value='Foo')
            >>> config_node_2 = ConfigNode()
            >>> _ = config_node_2.set(keys=['bar'], value='Bar')
            >>> new_config_node = config_node_1 + config_node_2
            >>> [keys for keys, sub_node in new_config_node.walk()]
            [['', 'bar'], ['', 'foo']]

            >>> # Add a ConfigNodeDiff to a ConfigNode
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_added_setting(keys=['baz'], data='Baz')
            >>> new_config_node = config_node_1 + config_node_diff
            >>> [keys for keys, sub_node in new_config_node.walk()]
            [['', 'baz'], ['', 'foo']]

        """
        if isinstance(config_diff, ConfigNode):
            config_node = config_diff
            config_diff = ConfigNodeDiff()
            config_diff.set_from_configs(self, config_node)
            config_diff.delete_removed()  # Don't delete anything.
        new_node = copy.deepcopy(self)
        new_node.add(config_diff)
        return new_node

    def __sub__(self, other_config_node):
        """Produce a ConfigNodeDiff from another ConfigNode.

        Arguments:
            other_config_node (ConfigNode):
                The ConfigNode to be applied to this ConfigNode
                to produce the ConfigNodeDiff.

        Returns:
            config_diff - A ConfigNodeDiff instance.

        Examples:
            >>> # Create a ConfigNodeDiff from two ConfigNodes
            >>> config_node_1 = ConfigNode()
            >>> _ = config_node_1.set(keys=['foo'], value='Foo')
            >>> config_node_2 = ConfigNode()
            >>> _ = config_node_2.set(keys=['bar'], value='Bar')
            >>> config_node_diff = config_node_1 - config_node_2

            >>> config_node_diff.get_added()
            [(('', 'foo'), ('Foo', '', []))]

            >>> config_node_diff.get_removed()
            [(('', 'bar'), ('Bar', '', []))]

        """
        diff = ConfigNodeDiff()
        diff.set_from_configs(other_config_node, self)
        return diff

    def __getstate__(self):
        """Avoid pickling the STATE constants within a deepcopy.

        This avoids a read-only error and allows __slots__ compatibility.

        """
        return {
            "state": self.state,
            "value": self.value,
            "comments": self.comments,
        }

    def __setstate__(self, state):
        """Read in the results of __getstate__."""
        self.state = state["state"]
        self.value = state["value"]
        self.comments = state["comments"]


class ConfigNodeDiff:

    """Represent differences between two ConfigNode instances.

    Examples:
        >>> # Create a new ConfigNodeDiff.
        >>> config_node_diff = ConfigNodeDiff()
        >>> config_node_diff.set_added_setting(keys=['bar'],
        ...                                    data=('Bar', None, None,))

        >>> # Create a new ConfigNode.
        >>> config_node = ConfigNode()
        >>> _ = config_node.set(keys=['baz'], value='Baz')

        >>> # Apply the diff to the node.
        >>> config_node.add(config_node_diff)
        >>> [(keys, sub_node.get_value()) for keys, sub_node in
        ...  config_node.walk()]
        [(['', 'bar'], 'Bar'), (['', 'baz'], 'Baz')]

        >>> # Create a ConfigNodeDiff by comparing two ConfigNodes.
        >>> another_config_node = ConfigNode()
        >>> _ = another_config_node.set(keys=['bar'], value='NewBar')
        >>> _ = another_config_node.set(keys=['new'], value='New')
        >>> config_node_diff = ConfigNodeDiff()
        >>> config_node_diff.set_from_configs(config_node,
        ...                                   another_config_node)
        >>> config_node_diff.get_added()
        [(('', 'new'), ('New', '', []))]
        >>> config_node_diff.get_removed()
        [(('', 'baz'), ('Baz', '', []))]
        >>> config_node_diff.get_modified()
        [(('', 'bar'), (('Bar', '', []), ('NewBar', '', [])))]

        >>> # Inverse a ConfigNodeDiff.
        >>> reversed_diff = config_node_diff.get_reversed()
        >>> reversed_diff.get_added()
        [(('', 'baz'), ('Baz', '', []))]

    """

    KEY_ADDED = "added"
    KEY_MODIFIED = "modified"
    KEY_REMOVED = "removed"

    def __init__(self):
        self._data = {
            self.KEY_ADDED: {},
            self.KEY_REMOVED: {},
            self.KEY_MODIFIED: {},
        }

    def set_from_configs(self, config_node_1, config_node_2):
        """Create diff data from two ConfigNode instances.

        Args:
            config_node_1 (ConfigNode): The node for which to base the diff
                off of.
            config_node_2 (ConfigNode): The "new" node the changes of which
                this diff will "apply".

        Example:
            >>> # Create two ConfigNode instances to compare.
            >>> config_node_1 = ConfigNode()
            >>> _ = config_node_1.set(keys=['foo'])
            >>> config_node_2 = ConfigNode()
            >>> _ = config_node_2.set(keys=['bar'])

            >>> # Create a ConfigNodeDiff instance.
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_from_configs(config_node_1, config_node_2)
            >>> config_node_diff.get_added()
            [(('bar',), (None, '', []))]
            >>> config_node_diff.get_removed()
            [(('foo',), (None, '', []))]

        """
        settings_1 = {}
        settings_2 = {}
        for config_node, settings in [
            (config_node_1, settings_1),
            (config_node_2, settings_2),
        ]:
            for keys, node in config_node.walk():
                value = node.value
                if isinstance(node.value, dict):
                    value = None
                settings[tuple(keys)] = (value, node.state, node.comments)
        for keys in set(settings_2) - set(settings_1):
            self.set_added_setting(keys, settings_2[keys])
        for keys in set(settings_1) - set(settings_2):
            self.set_removed_setting(keys, settings_1[keys])
        for keys in set(settings_1).intersection(set(settings_2)):
            if settings_1[keys] != settings_2[keys]:
                self.set_modified_setting(
                    keys, settings_1[keys], settings_2[keys]
                )

    def get_as_opt_config(self):
        """Return a ConfigNode such that main + new_node = main + diff.

        Add all the added settings, add all the modified settings,
        add all the removed settings as user-ignored.

        Returns:
            ConfigNode: A new ConfigNode instance.

        Example:
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_added_setting(['foo'],
            ...                                    ('Foo', None, None,))
            >>> config_node_diff.set_removed_setting(['bar'],
            ...                                      ('Bar', None, None,))
            >>> config_node = config_node_diff.get_as_opt_config()
            >>> list(config_node.walk()) # doctest: +NORMALIZE_WHITESPACE
            [(['', 'bar'], {'value': 'Bar', 'state': '!', 'comments': []}),
             (['', 'foo'], {'value': 'Foo', 'state': '', 'comments': []})]

        """
        node = ConfigNode()
        for keys, old_and_new_info in self.get_modified():
            value, state, comments = old_and_new_info[1]
            node.set(keys, value=value, state=state, comments=comments)
        for keys, info in self.get_added():
            value, state, comments = info
            node.set(keys, value=value, state=state, comments=comments)
        for keys, info in self.get_removed():
            # Need to add as user-ignored.
            value, state, comments = info
            node.set(
                keys,
                value=value,
                state=node.STATE_USER_IGNORED,
                comments=comments,
            )
        return node

    def set_added_setting(self, keys, data):
        """Set a config setting to be "added" in this ConfigNodeDiff.

        Args:
            keys (list, tuple):
                The position of the setting to add.
            data (tuple):
                A tuple of the form
                ``(value: object, state: string, comments: string)``
                for the setting to add.

        Examples:
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_added_setting(['foo'],
            ...                                    ('Foo', None, None,))
            >>> config_node_diff.set_added_setting(
            ...     ['bar'],
            ...     ('Bar', ConfigNode.STATE_USER_IGNORED, 'Some Info',))

            >>> config_node = ConfigNode()
            >>> config_node.add(config_node_diff)

            >>> list(config_node.walk()) # doctest: +NORMALIZE_WHITESPACE
            [(['', 'foo'], {'value': 'Foo', 'state': '', 'comments': []}),
             (['', 'bar'],
              {'value': 'Bar', 'state': '!', 'comments': 'Some Info'})]

        """
        keys = tuple(keys)
        self._data[self.KEY_ADDED][keys] = data

    def set_modified_setting(self, keys, old_data, data):
        """Set a config setting to be "modified" in this ConfigNodeDiff.

        If a property in both the old_data and data (new data) are both set to
        None then no change will be made to any pre-existing value.

        Args:
            keys (list, tuple):
                The position of the setting to add.
            old_data (tuple):
                A tuple ``(value: object, state: str, comments: str)``
                for the "current" properties of the setting to modify.
            data (object):
                A tuple ``(value: object, state: str, comments: str)``
                for "new" properties to change this setting to.

        Examples:
            >>> # Create a ConfigNodeDiff.
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_modified_setting(
            ...     ['foo'], ('Foo', None, None), ('New Foo', None, None))

            >>> # Create a ConfigNode.
            >>> config_node = ConfigNode()
            >>> _ = config_node.set(keys=['foo'], value='Foo',
            ...                     comments='Some Info')

            >>> # Apply the ConfigNodeDiff to the ConfigNode
            >>> config_node.add(config_node_diff)
            >>> config_node.get(keys=['foo'])
            {'value': 'New Foo', 'state': '', 'comments': 'Some Info'}

        """
        keys = tuple(keys)
        self._data[self.KEY_MODIFIED][keys] = (old_data, data)

    def set_removed_setting(self, keys, data):
        """Set a config setting to be "removed" in this ConfigNodeDiff.

        Arguments:
            keys (list):
                The position of the setting to add.
            data (tuple):
                A tuple ``(value: object, state: str, comments: str)`` of the
                properties for the setting to remove.

        Example:
            >>> # Create a ConfigNodeDiff.
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_removed_setting(['foo'], ('X', 'Y', 'Z'))

            >>> # Create a ConfigNode.
            >>> config_node = ConfigNode()
            >>> _ = config_node.set(keys=['foo'], value='Foo',
            ...                     comments='Some Info')

            >>> # Apply the ConfigNodeDiff to the ConfigNode
            >>> config_node.add(config_node_diff)
            >>> print(config_node.get(keys=['foo']))
            None

        """
        keys = tuple(keys)
        self._data[self.KEY_REMOVED][keys] = data

    def get_added(self):
        """Return a list of tuples of added keys with their data.

        The data is a tuple of value, state, comments, where value is
        set to None for sections.

        Returns:
            list: A list of the form [(keys, data), ...]
                - keys - The position of an added setting.
                - data - Tuple of the form (value, state, comments) of the
                  properties of the added setting.

        Examples:
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_added_setting(['foo'],
            ...                                    ('Foo', None, None))
            >>> config_node_diff.get_added()
            [(('foo',), ('Foo', None, None))]

        """
        return sorted(self._data[self.KEY_ADDED].items())

    def get_modified(self):
        """Return a dict of altered keys with before and after data.

        The data is a list of two tuples (before and after) of value,
        state, comments, where value is set to None for sections.

        Returns:
            list: A list of the form [(keys, data), ...]:
                - keys - The position of an added setting.
                - data - Tuple of the form (value, state, comments) for the
                  properties of the setting before the modification.
                - old_data - The same tuple as data but representing the
                  properties of the setting after the modification.

        Examples:
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_modified_setting(
            ...     ['foo'], ('Foo', None, None), ('New Foo', None, None))
            >>> config_node_diff.get_modified()
            [(('foo',), (('Foo', None, None), ('New Foo', None, None)))]

        """
        return sorted(self._data[self.KEY_MODIFIED].items())

    def get_removed(self):
        """Return a dict of removed keys with their data.

        The data is a tuple of value, state, comments, where value is
        set to None for sections.

        Returns:
            list: A list of the form ``[(keys, data), ...]``:
               - keys - The position of an added setting.
               - data - Tuple of the form (value, state, comments) of the
                 properties of the removed setting.

        Examples:
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_removed_setting(keys=['foo'],
            ...                                      data=('foo', None, None))
            >>> config_node_diff.get_removed()
            [(('foo',), ('foo', None, None))]

        """
        return sorted(self._data[self.KEY_REMOVED].items())

    def get_all_keys(self):
        """Return all keys affected by this ConfigNodeDiff.

        Returns:
            list: A list containing any keys affected by this diff as tuples,
            e.g. ('foo', 'bar').

        Examples:
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_added_setting(['foo'],('foo', None, None))
            >>> config_node_diff.set_removed_setting(['bar'],
            ...                                      ('bar', None, None))
            >>> config_node_diff.get_all_keys()
            [('bar',), ('foo',)]
        """
        return sorted(
            set(self._data[self.KEY_ADDED])
            | set(self._data[self.KEY_MODIFIED])
            | set(self._data[self.KEY_REMOVED])
        )

    def get_reversed(self):
        """Return an inverse (add->remove, etc) copy of this ConfigNodeDiff.

        Returns:
            ConfigNodeDiff: A new ConfigNodeDiff instance.

        Examples:
            >>> # Create ConfigNodeDiff instance.
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_added_setting(['foo'],('foo', None, None))
            >>> config_node_diff.set_removed_setting(['bar'],
            ...                                      ('bar', None, None))

            >>> # Generate reversed diff.
            >>> reversed_diff = config_node_diff.get_reversed()
            >>> reversed_diff.get_added()
            [(('bar',), ('bar', None, None))]
            >>> reversed_diff.get_removed()
            [(('foo',), ('foo', None, None))]
        """
        rev_diff = ConfigNodeDiff()
        for keys, data in self.get_removed():
            rev_diff.set_added_setting(keys, data)
        for keys, data in self.get_modified():
            rev_diff.set_modified_setting(keys, data[1], data[0])
        for keys, data in self.get_added():
            rev_diff.set_removed_setting(keys, data)
        return rev_diff

    def delete_removed(self):
        """Deletes all 'removed' keys from this ConfigNodeDiff.

        Examples:
            >>> config_node_diff = ConfigNodeDiff()
            >>> config_node_diff.set_removed_setting(['foo'],
            ...                                      ('foo', None, None))
            >>> config_node_diff.delete_removed()
            >>> config_node_diff.get_removed()
            []
        """
        self._data[self.KEY_REMOVED] = {}


class ConfigDumper:

    """Dumper of a ConfigNode object in Rose INI format.

    Examples:
        >>> config_node = ConfigNode()
        >>> _ = config_node.set(keys=['foo', 'bar'], value='Bar')
        >>> _ = config_node.set(keys=['foo', 'baz'], value='Baz',
        ...                     comments=['Currently ignored!'],
        ...                     state=ConfigNode.STATE_USER_IGNORED)
        >>> dumper = ConfigDumper()
        >>> dumper(config_node, sys.stdout)
        [foo]
        bar=Bar
        #Currently ignored!
        !baz=Baz
    """

    def __init__(self, char_assign=CHAR_ASSIGN):
        """Initialise the configuration dumper utility.

        Arguments:
        char_assign -- the character to use to delimit a key=value assignment.

        """
        self.char_assign = char_assign

    def dump(
        self,
        root,
        target=sys.stdout,
        sort_sections=None,
        sort_option_items=None,
        env_escape_ok=False,
        concat_mode=False,
    ):
        """Format a ConfigNode object and write result to target.

        Args:
            root (ConfigNode): The root config node.
            target (object): An open file handle or a string containing a
                file path. If not specified, the result is written to
                sys.stdout.
            sort_sections (Callable): An optional argument that should be
                a function for sorting a list of section keys.
            sort_option_items (Callable): An optional argument that
                should be a function for sorting a list of option (key, value)
                tuples in string values.
            env_escape_ok (bool): An optional argument to indicate
                that $NAME and ${NAME} syntax in values should be escaped.
            concat_mode (bool): Switch on concatenation mode. If
                True, add [] before root level options.

        """
        if sort_sections is None:
            sort_sections = sort_settings
        if sort_option_items is None:
            sort_option_items = sort_settings
        handle = target
        if not hasattr(target, "write") or not hasattr(target, "close"):
            target_dir = os.path.dirname(target)
            if not target_dir:
                target_dir = "."
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)
            handle = NamedTemporaryFile(
                mode='w',
                prefix=os.path.basename(target),
                dir=target_dir,
                delete=False,
            )
        blank = ""
        if root.comments:
            for comment in root.comments:
                write_safely(self._comment_format(comment), handle)
            blank = "\n"
        root_keys = list(root.value.keys())
        root_keys.sort(key=cmp_to_key(sort_sections))
        root_option_keys = []
        section_keys = []
        for key in root_keys:
            if isinstance(root.value[key].value, str):
                root_option_keys.append(key)
            else:
                section_keys.append(key)
        if root_option_keys:
            write_safely(blank, handle)
            blank = "\n"
            if concat_mode:
                handle.write(CHAR_SECTION_OPEN + CHAR_SECTION_CLOSE + "\n")
            for key in root_option_keys:
                self._string_node_dump(
                    key, root.value[key], handle, env_escape_ok
                )
        for section_key in section_keys:
            section_node = root.value[section_key]
            write_safely(blank, handle)
            blank = "\n"
            for comment in section_node.comments:
                write_safely(self._comment_format(comment), handle)
            write_safely(
                "%(open)s%(state)s%(key)s%(close)s\n"
                % {
                    "open": CHAR_SECTION_OPEN,
                    "state": section_node.state,
                    "key": section_key,
                    "close": CHAR_SECTION_CLOSE,
                },
                handle,
            )
            keys = list(section_node.value.keys())
            keys.sort(key=cmp_to_key(sort_option_items))
            for key in keys:
                value = section_node.value[key]
                self._string_node_dump(key, value, handle, env_escape_ok)
        if handle is not target:
            handle.close()
            if not os.path.exists(target):
                open(target, "a").close()
            os.chmod(handle.name, os.stat(target).st_mode)
            os.rename(handle.name, target)

    __call__ = dump

    def _string_node_dump(self, key, node, handle, env_escape_ok):
        """Helper for self.dump().

        Return text representation of a string node.

        """
        state = node.state
        try:
            values = node.value.decode().split("\n")
        except AttributeError:
            values = node.value.split("\n")
        for comment in node.comments:
            write_safely(self._comment_format(comment), handle)
        value0 = values.pop(0)
        if env_escape_ok:
            value0 = env_var_escape(value0)
        write_safely(state + key + self.char_assign + value0, handle)
        write_safely("\n", handle)
        if values:
            indent = " " * len(state + key)
            for value in values:
                if env_escape_ok:
                    value = env_var_escape(value)
                write_safely(indent + self.char_assign + value + "\n", handle)

    @classmethod
    def _comment_format(cls, comment):
        """Return text representation of a configuration comment."""
        return "#%s\n" % (comment)


class ConfigLoader:

    """Loader of an INI format configuration into a ConfigNode object.

    Example:
        >>> with open('config.conf', 'w+') as config_file:
        ...     _ = config_file.write('''
        ... [foo]
        ... !bar=Bar
        ... baz=Baz
        ...     ''')
        >>> loader = ConfigLoader()
        >>> try:
        ...     config_node = loader.load('config.conf')
        ... except ConfigSyntaxError:
        ...     raise  # Handle exception.
        >>> config_node.get(keys=['foo', 'bar'])
        {'value': 'Bar', 'state': '!', 'comments': []}
    """

    RE_SECTION = re.compile(
        r"^(?P<head>\s*\[(?P<state>!?!?))(?P<section>.*)\]\s*$"
    )
    RE_OPT_DEFINE = re.compile(r"\A(?:\[([^\]]+)\])?([^=]+)?(?:=(.*))?\Z")
    TYPE_SECTION = "TYPE_SECTION"
    TYPE_OPTION = "TYPE_OPTION"
    UNKNOWN_NAME = "<???>"

    def __init__(
        self,
        char_assign=CHAR_ASSIGN,
        char_comment=CHAR_COMMENT,
        allow_sections=True,
    ):
        """Initialise the configuration utility.

        Arguments:
            char_assign (str): the character to use to delimit a key=value
                assignment.
            char_comment (str): the character to indicate the start of a
                comment.
            allow_sections (bool): whether to permit sections in the config.

        """
        self.char_assign = char_assign
        self.char_comment = char_comment
        self.allow_sections = allow_sections
        self.re_option = re.compile(
            r"^(?P<state>!?!?)(?P<option>[^\s"
            + char_assign
            + r"]+)\s*"
            + char_assign
            + r"\s*(?P<value>.*)$"
        )

    @staticmethod
    def can_miss_opt_conf_key(key):
        """Return KEY if key is a string like "(KEY)", None otherwise."""
        if key.startswith("(") and key.endswith(")"):
            return key[1:-1]
        else:
            return

    def load_with_opts(
        self,
        source,
        node=None,
        more_keys=None,
        used_keys=None,
        return_config_map=False,
        mark_opt_confs=False,
        defines=None,
    ):
        """Read a source configuration file with optional configurations.

        Arguments:
            source (str): A file path.
            node (ConfigNode): A ConfigNode object if specified,
                otherwise one is created.
            more_keys (list): A list of additional optional
                configuration names. If source is "rose-${TYPE}.conf", the
                file of each name should be "opt/rose-${TYPE}-${NAME}.conf".
            used_keys (list): If defined, it should be a list for
                this method to  append to. The key of each successfully loaded
                optional configuration will be appended to the list (unless the
                key is already in the list). Missing optional configurations
                that are specified in more_keys will not raise an error.
                If not defined, any missing optional configuration will
                trigger an OSError.
            mark_opt_configs (bool): if True, add comments above any
                settings which have been loaded from an optional config.
            return_config_map (bool): If True, construct and return
                a dict (config_map) containing config names vs their uncombined
                nodes. Optional configurations use their opt keys as keys, and
                the main configuration uses 'None'.
            defines (list): A list of [SECTION]KEY=VALUE overrides.

        Returns:
            tuple: node or (node, config_map):
                - node - The loaded configuration as a ConfigNode.
                - config_map - A dictionary containing opt_conf_key: ConfigNode
                  pairs. Only returned if return_config_map is True.

        Examples:
            .. testcleanup:: metomi.rose.config.ConfigLoader.load_with_opts

                try:
                    os.remove('config.conf')
                    os.remove('opt/config-foo.conf')
                    os.rmdir('opt')
                except OSError:
                    pass

            >>> # Write config file.
            >>> with open('config.conf', 'w+') as config_file:
            ...     _ = config_file.write('''
            ... [foo]
            ... bar=Bar
            ...     ''')
            >>> # Write optional config file (foo).
            >>> os.mkdir('opt')
            >>> with open('opt/config-foo.conf', 'w+') as opt_config_file:
            ...     _ = opt_config_file.write('''
            ... [foo]
            ... bar=Baz
            ...     ''')

            >>> loader = ConfigLoader()
            >>> config_node, config_map = loader.load_with_opts(
            ...     'config.conf', more_keys=['foo'], return_config_map=True)
            >>> config_node.get_value(keys=['foo', 'bar'])
            'Baz'

            >>> original_config_node = config_map[None]
            >>> original_config_node.get_value(keys=['foo', 'bar'])
            'Bar'

            >>> optional_config_node = config_map['foo']
            >>> optional_config_node.get_value(keys=['foo', 'bar'])
            'Baz'

        """
        node = self.load(source, node)
        if defines is not None:
            node = self.load(defines, node)  # enable opts override
        if return_config_map:
            config_map = {None: copy.deepcopy(node)}
        opt_conf_keys_node = node.unset(["opts"])
        if opt_conf_keys_node is None or opt_conf_keys_node.is_ignored():
            opt_conf_keys = []
        else:
            opt_conf_keys = shlex.split(opt_conf_keys_node.value)
        if more_keys:
            opt_conf_keys += more_keys
        if not opt_conf_keys:
            if return_config_map:
                return node, config_map
            return node
        source_dir = os.path.dirname(source)
        source_root, source_ext = os.path.splitext(os.path.basename(source))
        for opt_conf_key in opt_conf_keys:
            can_miss_opt_conf_key = self.can_miss_opt_conf_key(opt_conf_key)
            if can_miss_opt_conf_key:
                key = can_miss_opt_conf_key
            else:
                key = opt_conf_key
            opt_conf_file_name_base = source_root + "-" + key + source_ext
            opt_conf_file_name = os.path.join(
                source_dir, OPT_CONFIG_DIR, opt_conf_file_name_base
            )
            try:
                if mark_opt_confs:
                    self.load(
                        opt_conf_file_name,
                        node,
                        default_comments=[
                            OPT_CONFIG_SETTING_COMMENT
                            % (
                                key,
                                opt_conf_file_name,
                            )
                        ],
                    )
                else:
                    self.load(opt_conf_file_name, node)
            except IOError:
                if can_miss_opt_conf_key or (
                    used_keys is not None and opt_conf_key in more_keys
                ):
                    continue
                raise
            else:
                if used_keys is not None and key not in used_keys:
                    used_keys.append(key)
                if return_config_map:
                    config_map[key] = self.load(opt_conf_file_name)
        if defines is not None:
            node = self.load(defines, node)
        if return_config_map:
            return node, config_map
        return node

    def load(self, source, node=None, default_comments=None):
        """Read a source configuration file.

        Arguments:
            source (str): An open file handle, a string for a file path or
                a list of [SECTION]KEY=VALUE items.
            node (ConfigNode): A ConfigNode object if specified, otherwise
                created.

        Returns:
            ConfigNode: A new ConfigNode object.

        Examples:
            >>> # Create example config file.
            >>> with open('config.conf', 'w+') as config_file:
            ...     _ = config_file.write('''
            ... [foo]
            ... # Some comment
            ... !bar=Bar
            ...     ''')

            >>> # Load config file.
            >>> loader = ConfigLoader()
            >>> try:
            ...     config_node = loader.load('config.conf')
            ... except ConfigSyntaxError:
            ...     raise  # Handle exception.
            >>> config_node.get(keys=['foo', 'bar'])
            {'value': 'Bar', 'state': '!', 'comments': [' Some comment']}

        """
        if node is None:
            node = ConfigNode()
        handle, file_name = self._get_file_and_name(source)
        if isinstance(file_name, int):  # Probably a temporary file
            file_name = ""
        keys = []  # Currently position under root node
        type_ = None  # Type of current node, section or option?
        comments = None  # Comments associated with next node
        line_num = 0
        # Note: "for line in handle:" hangs for sys.stdin
        while True:
            line = handle.readline()
            if isinstance(line, bytes):
                try:
                    line = line.decode()
                except UnicodeDecodeError as exc:
                    raise ConfigDecodeError(source, exc)
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
            if type_ == self.TYPE_OPTION and line[0].isspace():
                value = node.get(keys[:]).value
                value_cont = line.strip()
                if value_cont.startswith(self.char_assign):
                    value_cont = value_cont[1:]
                node.set(keys[:], value + "\n" + value_cont)
                continue
            # Match a section header?
            match = self.RE_SECTION.match(line)
            if match:
                if self.allow_sections:
                    head, section, state = match.group(
                        "head", "section", "state"
                    )
                    bad_index = self._check_section_value(section)
                    if bad_index > -1:
                        raise ConfigSyntaxError(
                            ConfigSyntaxError.BAD_CHAR,
                            file_name,
                            line_num,
                            len(head) + bad_index,
                            line,
                        )
                    # Find position under root node
                    if type_ == self.TYPE_OPTION:
                        keys.pop()
                    if keys:
                        keys.pop()
                    section = section.strip()
                    if section:
                        keys.append(section)
                        type_ = self.TYPE_SECTION
                    else:
                        keys = []
                        type_ = None
                    section_node = node.get(keys[:])
                    if section_node is None:
                        node.set(keys[:], {}, state, comments)
                    else:
                        section_node.state = state
                        if comments:
                            section_node.comments += comments
                    comments = []
                    continue
                else:
                    raise ConfigSyntaxError(
                        ConfigSyntaxError.SECTIONS_NOT_ALLOWED,
                        file_name,
                        line_num,
                        0,
                        line,
                    )
            # Match the start of an option setting?
            match = self.re_option.match(line)
            if not match:
                if self.allow_sections:
                    err = ConfigSyntaxError.BAD_SYNTAX
                else:
                    err = ConfigSyntaxError.BAD_SYNTAX_NO_SECTIONS
                raise ConfigSyntaxError(err, file_name, line_num, 0, line)
            option, value, state = match.group("option", "value", "state")
            if type_ == self.TYPE_OPTION:
                keys.pop()
            keys.append(option)
            type_ = self.TYPE_OPTION
            value = value.strip()
            if comments is not None and default_comments is not None:
                comments += default_comments
            node.set(keys[:], value.strip(), state, comments)
            comments = []
        return node

    __call__ = load

    @classmethod
    def _check_section_value(cls, section):
        """Check value of section title for bad braces."""
        # Square braces
        for char in CHAR_SECTION_OPEN, CHAR_SECTION_CLOSE:
            bad_index = section.find(char)
            if bad_index > -1:
                return bad_index
        # Don't check string with environment variable substitution syntax
        if "${" in section:
            return -1
        # Check only section values with schemes
        scheme, _, path = section.partition(":")
        if not path:
            return -1
        # Check brackets and curly braces
        index_of = {}
        for char in "{}()":
            index_of[char] = -1
            pos = 0
            while pos < len(path):
                index = path.find(char, pos)
                if index > -1 and pos > 0:
                    # 2nd occurrence of char
                    return len(scheme) + index + 1
                elif index > -1:
                    index_of[char] = index
                    pos = index + 1
                else:
                    break
        for sym_open, sym_close in ["{}", "()"]:
            if index_of[sym_close] == -1 and index_of[sym_open] == -1:
                continue
            elif index_of[sym_close] == -1:
                # has open, but no close
                return len(section)
            elif (
                index_of[sym_open] == -1
                or index_of[sym_close] < index_of[sym_open]
            ):
                # has close, but no open
                # or close before open
                return len(scheme) + index_of[sym_close] + 1
        # Curly braces should be placed before brackets
        if index_of["("] > -1:
            if index_of["{"] > index_of["("]:
                return len(scheme) + index_of["{"] + 1
            elif index_of["}"] > index_of["("]:
                return len(scheme) + index_of["("] + 1
        return -1

    @classmethod
    def _comment_strip(cls, line):
        """Strip comment character and whitespace from a comment."""
        return line.strip()[1:]

    def _get_file_and_name(self, file_):
        """Return file handle and file name of "file_"."""
        if hasattr(file_, "readline"):
            try:
                file_name = file_.name
            except AttributeError:
                file_name = self.UNKNOWN_NAME
        elif isinstance(file_, str):
            file_name = os.path.abspath(file_)
            file_ = open(file_name, "rb")
        else:
            defines = file_
            file_ = SpooledTemporaryFile()
            file_name = self.UNKNOWN_NAME
            for define in defines:
                sect, key, value = self.RE_OPT_DEFINE.match(define).groups()
                if sect is None:
                    sect = ""
                if value is None:
                    value = ""
                file_.write(("[%s]\n" % sect).encode())
                if key is not None:
                    file_.write(("%s=%s\n" % (key, value)).encode())
            file_.seek(0)
        return (file_, file_name)


class ConfigError(Exception):
    """Base class for config errors."""


class ConfigSyntaxError(ConfigError):

    """Exception raised for syntax error loading a configuration file.

    Attributes:
        exc.code: Error code. Can be one of:
            ConfigSyntaxError.BAD_CHAR (bad characters in a name)
            ConfigSyntaxError.BAD_SYNTAX (general syntax error)
        exc.file_name: The name of the file that triggers the error.
        exc.line_num: The line number (from 1) in the file with the error.
        exc.col_num: The column number (from 0) in the line with the error.
        exc.line: The content of the line that contains the error.

    Examples:
        >>> with open('config.conf', 'w+') as config_file:
        ...     _ = config_file.write('[foo][foo]')
        >>> loader = ConfigLoader()
        >>> try:
        ...     loader.load('config.conf')
        ... except ConfigSyntaxError as exc:
        ...     print('Error (%s) in file "%s" at %s:%s' % (
        ...         exc.code, exc.file_name, exc.line_num, exc.col_num))
        ... # doctest: +ELLIPSIS
        Error (BAD_CHAR) in file "..." at 1:5

    """

    BAD_CHAR = "BAD_CHAR"
    BAD_SYNTAX = "BAD_SYNTAX"
    BAD_SYNTAX_NO_SECTIONS = "BAD_SYNTAX_NO_SECTIONS"
    SECTIONS_NOT_ALLOWED = "SECTIONS_NOT_ALLOWED"

    MESSAGES = {
        BAD_CHAR: 'unexpected character or end of value',
        BAD_SYNTAX: 'expecting "[SECTION]" or "KEY=VALUE"',
        BAD_SYNTAX_NO_SECTIONS: 'expecting "KEY=VALUE"',
        SECTIONS_NOT_ALLOWED: 'sections not permitted in this configuration',
    }

    def __init__(self, code, file_name, line_num, col_num, line):
        Exception.__init__(self, code, file_name, line_num, col_num, line)
        self.code = code
        self.file_name = file_name
        self.line_num = line_num
        self.col_num = col_num
        self.line = line

    def __str__(self):
        msg = self.MESSAGES[self.code]
        return (
            f"{self.file_name}(line {self.line_num}): {msg}\n"
            f"{self.line}{' ' * self.col_num}^"
        )


class ConfigDecodeError(ConfigError):
    """Exception that should be raised when loading a configuration file that
    is not encoded in a UTF-8 compatible charset.

    Args:
        path (str): Path to the config file
        unicode_decode_err (UnicodeDecodeError): The original exception raised
            when doing bytes.decode()
    """

    MESSAGE = (
        'Configuration files must be encoded in UTF-8 (or a subset of UTF-8)'
    )

    def __init__(self, path, unicode_decode_err):
        self.path = path
        self.err = unicode_decode_err

    def __str__(self):
        return f"{self.MESSAGE}. {self.path}: {self.err}"


def dump(
    root,
    target=sys.stdout,
    sort_sections=None,
    sort_option_items=None,
    env_escape_ok=False,
):
    """Shorthand for :py:func:`ConfigDumper.dump`."""
    return ConfigDumper()(
        root, target, sort_sections, sort_option_items, env_escape_ok
    )


def load(source, root=None):
    """Shorthand for :py:func:`ConfigLoader.load`."""
    return ConfigLoader()(source, root)


def sort_element(elem_1, elem_2):
    """Sort pieces of text, numerically if possible."""
    if elem_1.isdigit() and elem_2.isdigit():
        # This logic replicates output of the deprecated Python2 `cmp` builtin
        return (int(elem_1) > int(elem_2)) - (int(elem_1) < int(elem_2))
    elif elem_1.isdigit():
        return -1
    elif elem_2.isdigit():
        return 1
    else:
        return (elem_1 > elem_2) - (elem_1 < elem_2)


def sort_settings(setting_1, setting_2):
    """Sort sections and options, by numeric element if possible."""
    if not isinstance(setting_1, str) or not isinstance(setting_2, str):
        # This logic replicates output of the deprecated Python2 `cmp` builtin
        return (setting_1 > setting_2) - (setting_1 < setting_2)
    match_1 = REC_SETTING_ELEMENT.match(setting_1)
    match_2 = REC_SETTING_ELEMENT.match(setting_2)
    if match_1 and match_2:
        text_1, num_1 = match_1.groups()
        text_2, num_2 = match_2.groups()
        if text_1 == text_2:
            return sort_element(num_1, num_2)
    # This logic replicates output of the deprecated Python2 `cmp` builtin
    return (setting_1 > setting_2) - (setting_1 < setting_2)
