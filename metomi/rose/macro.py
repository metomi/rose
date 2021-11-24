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
"""
.. testsetup:: *

    import os
    from metomi.rose.macro import *

    def test_cleanup(stuff_to_remove):
        for item in stuff_to_remove:
            try:
                os.remove(item)
            except OSError:
                try:
                    os.rmdir(item)
                except OSError:
                    pass

Module to list or run available custom macros for a configuration.

It also stores macro base classes and macro library functions.

"""

import ast
import copy
from functools import cmp_to_key
import glob
from importlib.machinery import SourceFileLoader
import inspect
import os
import re
import sys
import traceback

import metomi.rose.config
from metomi.rose.config import ConfigNode
import metomi.rose.config_tree
import metomi.rose.formats.namelist
from metomi.rose.opt_parse import RoseOptionParser
import metomi.rose.reporter
import metomi.rose.resource
import metomi.rose.variable

ALLOWED_MACRO_CLASS_METHODS = [
    "transform",
    "validate",
    "downgrade",
    "upgrade",
    "report",
]
ERROR_LOAD_CONFIG_DIR = "{0}: not an application or suite directory.\n"
ERROR_LOAD_MACRO = "Could not load macro {0}: {1}"
ERROR_LOAD_METADATA = "Could not load metadata {0}\n"
ERROR_LOAD_CHOSEN_META_PATH = (
    "Could not find metadata for {0}, using {1}\n"
    "To suppress these warnings run 'rose edit --no-warn version'"
)
ERROR_LOAD_META_PATH = "Could not find metadata for {0}"
ERROR_LOAD_CONF_META_NODE = "Error: could not find meta flag"
ERROR_MACRO_CASE_MISMATCH = (
    "Error: case mismatch; \n {0} does not match {1},"
    " please only use lowercase."
)
ERROR_MACRO_NOT_FOUND = "Error: could not find macro {0}\n"
ERROR_NO_MACRO_HELP = "No help docstring provided, macro \"{0}\"."
ERROR_NO_MACROS = "Please specify a macro name.\n"
ERROR_RETURN_TYPE = "{0}: {1}: invalid returned type: {2}, expect {3}"
ERROR_RETURN_VALUE = "{0}: incorrect return value"
ERROR_RETURN_VALUE_STATE = "{0}: node.state: invalid returned value"
MACRO_DIRNAME = os.path.join(
    os.path.join("lib", "python"), metomi.rose.META_DIR_MACRO
)
ERROR_OUT_DIR_MULTIPLE_APPS = (
    "Cannot specify an output dir when running" " macro over multiple apps."
)
MACRO_EXT = ".py"
MACRO_OUTPUT_HELP = "    # {0}\n"
MACRO_OUTPUT_ID = "[{0}] {1}"
MACRO_OUTPUT_TRANSFORM_CHANGES = "{0}: changes: {1}\n"
MACRO_OUTPUT_VALIDATE_ISSUES = "{0}: issues: {1}\n"
MACRO_OUTPUT_WARNING_ISSUES = "{0}: warnings: {1}\n"
OPT_CONFIG_REPORT = "(opts={0})"
REC_MODIFIER = re.compile(r"\{.+\}")
REC_ID_STRIP_DUPL = re.compile(r"\([^()]+\)")
REC_ID_STRIP = re.compile(r'(?:\{.+\})?(?:\([^()]+\))?$')
REC_ID_ELEMENT = re.compile(r"\(([^()]+)\)$")
REC_ID_SINGLE_ELEMENT = re.compile(r"\((\d+)\)$")
ID_ELEMENT_FORMAT = "{0}({1})"
PROBLEM_ENTRY = "    {0}{1}={2}={3}\n        {4}\n"
PROMPT_ACCEPT_CHANGES = "Accept y/n (default n)? "
PROMPT_OK = "y"
SETTING_ID = "    {0}={1}={2}\n        {3}"
TRANSFORM_METHOD = "transform"
VALIDATE_METHOD = "validate"
REPORT_METHOD = "report"
VERBOSE_LIST = "{0} - ({1}) - {2}"


class MacroFinishNothingEvent(metomi.rose.reporter.Event):

    """Event reported when there have been no problems or changes."""

    LEVEL = metomi.rose.reporter.Event.VV

    def __str__(self):
        return "Configurations OK"


class MacroLoadError(Exception):

    """Raise this error if an exception occurs during macro import."""

    def __str__(self):
        return ERROR_LOAD_MACRO.format(self.args[0], self.args[1])


class MacroNotFoundError(NameError):

    """Raise this error if a macro name cannot be found."""

    def __str__(self):
        return ERROR_MACRO_NOT_FOUND.format(self.args[0])


class MacroTransformDumpEvent(metomi.rose.reporter.Event):

    """Event reported when a transformed configuration is dumped."""

    def __str__(self):
        if self.args[1] is None:
            return "M %s" % self.args[0]
        return "M %s -> %s" % (self.args[0], self.args[1])


class MacroReturnedCorruptConfigError(TypeError):

    """Raise this error if a macro's returned config is corrupt."""

    def __str__(self):
        return "Macro tried to corrupt the config: %s" % self.args[0]


class MacroValidateError(Exception):

    """Raise this error if validation parsing fails."""

    def __init__(self, *args):
        args = list(args)
        for i, arg in enumerate(args):
            if issubclass(type(arg), Exception):
                args[i] = str(type(arg)) + " " + str(arg)
        self.args_string = " ".join([str(a) for a in args])
        super(MacroValidateError, self).__init__()

    def __str__(self):
        return 'Could not perform validation: ' + self.args_string


class MetaConfigFlagMissingError(Exception):

    """Raise this error if there is no meta= flag."""

    def __str__(self):
        return ERROR_LOAD_CONF_META_NODE


class MacroBase:

    """Base class for macros for validating or transforming configurations.

    Synopsis:
        >>> import metomi.rose.macro
        ...
        >>> class SomeValidator(metomi.rose.macro.MacroBase):
        ...
        ...    '''Important: Add a docstring for your macro like this.
        ...
        ...    A macro class should implement one of the following methods:
        ...
        ...    '''
        ...
        ...    def validate(self, config, meta_config=None):
        ...        # Some check on config appends to self.reports using
        ...        # self.add_report.
        ...        return self.reports
        ...
        ...    def transform(self, config, meta_config=None):
        ...        # Some operation on config which calls self.add_report
        ...        # for each change.
        ...        return config, self.reports
        ...
        ...    def report(self, config, meta_config=None):
        ...        # Perform some analysis of the config but return nothing.
        ...        pass

        Keyword arguments can be used, ``rose macro`` will prompt the user to
        provide values for these arguments when the macro is run.

        >>> def validate(self, config, meta_config=None, answer=None):
        ...     # User will be prompted to provide a value for "answer".
        ...     return self.reports

        There is a special keyword argument called ``optional_config_name``
        which is set to the name of the optional configuration a macro is
        running on, or ``None`` if only the default configuration is being
        used.

        >>> def report(self, config, meta_config=None,
        ...            optional_config_name=None):
        ...     if optional_config_name:
        ...         print('Macro is being run using the "%s" '
        ...               'optional configuration' % optional_config_name)

    """

    def __init__(self):
        self.reports = []  # MacroReport instances for errors or changes

    def _get_section_option_from_id(self, var_id):
        """Return a configuration section and option from an id."""
        return get_section_option_from_id(var_id)

    def _get_id_from_section_option(self, section, option):
        """Return a variable id from a section and option."""
        return get_id_from_section_option(section, option)

    def _sorter(self, rep1, rep2):
        # Sort [section], [section, option], [section, None]
        id1 = self._get_id_from_section_option(rep1.section, rep1.option)
        id2 = self._get_id_from_section_option(rep2.section, rep2.option)
        if id1 == id2:
            # This logic replicates output of the deprecated Python2 `cmp`
            # builtin
            return (rep1.value > rep2.value) - (rep1.value < rep2.value)
        return metomi.rose.config.sort_settings(id1, id2)

    def _load_meta_config(
        self, config, meta=None, directory=None, config_type=None
    ):
        """Return a metadata configuration object."""
        if isinstance(meta, metomi.rose.config.ConfigNode):
            return meta
        return load_meta_config(config, directory, config_type=config_type)

    def get_metadata_for_config_id(self, setting_id, meta_config):
        """Return a dict of metadata properties and values for a setting id.

        Args:
            setting_id (str): The name of the setting to extract metadata for.
            meta_config (metomi.rose.config.ConfigNode): Config node containing
                the metadata to extract from.

        Return:
            dict: A dictionary containing metadata options.

        Example:
            >>> # Create a rose app.
            >>> with open('rose-app.conf', 'w+') as app_config:
            ...     _ = app_config.write('''
            ... [foo]
            ... bar=2
            ...     ''')
            >>> os.mkdir('meta')
            >>> with open('meta/rose-meta.conf', 'w+') as meta_config:
            ...     _ = meta_config.write('''
            ... [foo=bar]
            ... values = 1,2,3
            ...     ''')
            ...
            >>> # Load config.
            >>> app_conf, config_map, meta_config = load_conf_from_file(
            ...     '.', 'rose-app.conf')
            ...
            >>> # Extract metadata for foo=bar.
            >>> get_metadata_for_config_id('foo=bar', meta_config)
            {'values': '1,2,3', 'id': 'foo=bar'}

        .. testcleanup:: metomi.rose.macro.MacroBase.get_metadata_for_config_id

            test_cleanup(['rose-app.conf', 'meta/rose-meta.conf', 'meta'])
        """
        return get_metadata_for_config_id(setting_id, meta_config)

    def get_resource_path(self, filename=''):
        """Load the resource according to the path of the calling macro.

        The returned path will be based on the macro location under
        ``lib/python`` in the metadata directory.

        If the calling macro is ``lib/python/macro/levels.py``,
        and the filename is ``rules.json``, the returned path will be
        ``etc/macro/levels/rules.json``.

        Args:
            filename (str): The filename of the resource to request the path
                to.

        Return:
            str: The path to the requested resource.

        """
        last_frame = inspect.getouterframes(inspect.currentframe())[1]
        macro_path = os.path.abspath(inspect.getfile(last_frame[0]))
        macro_name = os.path.basename(macro_path).rpartition('.py')[0]
        macro_root_dir = os.path.dirname(macro_path)
        library_dir = os.path.dirname(os.path.dirname(macro_root_dir))
        root_dir = os.path.dirname(library_dir)
        # root_dir is the directory of the rose-meta.conf file.
        etc_path = os.path.join(root_dir, 'etc')
        resource_path = os.path.join(etc_path, 'macros')
        resource_path = os.path.join(resource_path, macro_name)
        resource_path = os.path.join(resource_path, filename)
        return resource_path

    def pretty_format_config(self, config):
        """Standardise the keys and values of a config node.

        Args:
            config (metomi.rose.config.ConfigNode): The config node to convert.

        """
        pretty_format_config(config)

    def standard_format_config(self, config):
        """Standardise any degenerate representations e.g. namelist repeats.

        Args:
            config (metomi.rose.config.ConfigNode): The config node to convert.

        """
        standard_format_config(config)

    def add_report(self, *args, **kwargs):
        """Add a metomi.rose.macro.MacroReport.

        See :class:`metomi.rose.macro.MacroReport` for details of arguments.

        Examples:
            >>> # An example validator macro which adds a report to the setting
            >>> # env=MY_FAVOURITE_STREAM_EDITOR.
            >>> class My_Macro(MacroBase):
            ...     def validate(self, config, meta_config=None):
            ...         editor_value = config.get(
            ...             ['env', 'MY_FAVOURITE_STREAM_EDITOR']).value
            ...         if editor_value != 'sed':
            ...             self.add_report(
            ...                 'env',                         # Section
            ...                 'MY_FAVOURITE_STREAM_EDITOR',  # Option
            ...                 editor_value,                  # Value
            ...                 'Should be "sed"!')            # Message
            ...         return self.reports

        """
        self.reports.append(MacroReport(*args, **kwargs))


class MacroBaseRoseEdit(MacroBase):

    """This class extends MacroBase to provide a non-ConfigNode API.

    In the following methods, config_data can be a
    metomi.rose.config.ConfigNode instance or a dictionary that
    looks like this:
    {"sections":
        {"namelist:foo": metomi.rose.section.Section instance,
         "env": metomi.rose.section.Section instance},
        "variables":
        {"namelist:foo": [metomi.rose.variable.Variable instance,
                          metomi.rose.variable.Variable instance],
         "env": [metomi.rose.variable.Variable instance]}
    }
    This makes it easy to interface with rose edit, which uses the
    latter data structure internally.

    """

    def _get_config_sections(self, config_data):
        """Return all sections within config_data."""
        sections = []
        if isinstance(config_data, metomi.rose.config.ConfigNode):
            for key, node in config_data.value.items():
                if isinstance(node.value, dict):
                    sections.append(key)
            if "" not in sections:
                sections.append("")
        else:
            for key in set(
                config_data["sections"].keys()
                + config_data["variables"].keys()
            ):
                sections.append(key)
        return sections

    def _get_config_section_options(self, config_data, section):
        """Return all options within a section in config_data."""
        if isinstance(config_data, metomi.rose.config.ConfigNode):
            names = []
            for keylist, _ in config_data.walk([section]):
                names.append(keylist[-1])
            return names
        else:
            return [v.name for v in config_data["variables"].get(section, [])]

    def _get_config_has_id(self, config_data, id_):
        """Return whether the config_data contains the id_."""
        section, option = self._get_section_option_from_id(id_)
        if isinstance(config_data, metomi.rose.config.ConfigNode):
            return config_data.get([section, option]) is not None
        if option is None:
            return section in config_data["sections"]
        return option in [
            v.name for v in config_data["variables"].get(section, [])
        ]

    def _get_config_id_state(self, config_data, id_):
        """Return the ConfigNode.STATE_* that applies to id_ or None."""
        section, option = self._get_section_option_from_id(id_)
        if isinstance(config_data, metomi.rose.config.ConfigNode):
            node = config_data.get([section, option])
            if node is None:
                return None
            return node.state
        ignored_reason = None
        if option is None:
            if section in config_data["sections"]:
                ignored_reason = config_data["sections"][
                    section
                ].ignored_reason
        else:
            for variable in config_data["variables"].get(section, []):
                if variable.name == option:
                    ignored_reason = variable.ignored_reason
                    break
        if ignored_reason is None:
            return None
        if metomi.rose.variable.IGNORED_BY_USER in ignored_reason:
            return metomi.rose.config.ConfigNode.STATE_USER_IGNORED
        if metomi.rose.variable.IGNORED_BY_SYSTEM in ignored_reason:
            return metomi.rose.config.ConfigNode.STATE_SYST_IGNORED
        return metomi.rose.config.ConfigNode.STATE_NORMAL

    def _get_config_id_value(self, config_data, id_):
        """Return a value (if any) for id_ in the config_data."""
        section, option = self._get_section_option_from_id(id_)
        if option is None:
            return None
        if isinstance(config_data, metomi.rose.config.ConfigNode):
            node = config_data.get([section, option])
            if node is None:
                return None
            return node.value
        for variable in config_data["variables"].get(section, []):
            if variable.name == option:
                return variable.value
        return None


class MacroValidatorCollection(MacroBase):

    """Collate several macros into one."""

    def __init__(self, *macros):
        self.macros = macros
        super(MacroValidatorCollection, self).__init__()

    def validate(self, config, meta_config):
        for macro_inst in self.macros:
            if not hasattr(macro_inst, VALIDATE_METHOD):
                continue
            macro_method = getattr(macro_inst, VALIDATE_METHOD)
            p_list = macro_method(config, meta_config)
            p_list.sort(key=cmp_to_key(self._sorter))
            self.reports += p_list
        return self.reports


class MacroTransformerCollection(MacroBase):

    """Collate several macros into one."""

    def __init__(self, *macros):
        self.macros = macros
        super(MacroTransformerCollection, self).__init__()

    def transform(self, config, meta_config=None):
        for macro_inst in self.macros:
            if not hasattr(macro_inst, TRANSFORM_METHOD):
                continue
            macro_method = getattr(macro_inst, TRANSFORM_METHOD)
            config, c_list = macro_method(config, meta_config)
            c_list.sort(key=cmp_to_key(self._sorter))
            self.reports += c_list
        return config, self.reports


class MacroReport:

    """Class to hold information about a macro issue.

    Arguments:
        section (str): The name of the section to attach this report to.
        option (str): The name of the option (within the section) to
            attach this report to.
        value (object): The value of the configuration associated with this
            report.
        info (str): Text information describing the nature of the report.
        is_warning (bool): If True then this report will be logged as a
            warning.

    Example:
        >>> report = MacroReport('env', 'WORLD', 'Earth',
        ...                      'World changed to Earth', True)

    """

    def __init__(
        self,
        section=None,
        option=None,
        value=None,
        info=None,
        is_warning=False,
    ):
        self.section = section
        self.option = option
        self.value = value
        self.info = info
        self.is_warning = is_warning

    def __repr__(self):
        return (
            "<MacroReport section=%s option=%s value=%s info=%s "
            + "is_warning=%s>"
        ) % (self.section, self.option, self.value, self.info, self.is_warning)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(
            (self.section, self.option, self.value, self.info, self.is_warning)
        )


def add_meta_paths():
    """Call add_site_meta_paths and add_env_meta_paths."""
    add_site_meta_paths()
    add_env_meta_paths()


def add_site_meta_paths():
    """Load any metadata paths specified in a user or site configuration."""
    conf = metomi.rose.resource.ResourceLocator.default().get_conf()
    path = conf.get_value(
        [metomi.rose.CONFIG_SECT_TOP, metomi.rose.CONFIG_OPT_META_PATH]
    )
    if path is not None:
        for path in path.split(os.pathsep):
            path = os.path.expanduser(os.path.expandvars(path))
            sys.path.insert(0, os.path.abspath(path))
    sys.path.append(
        str(metomi.rose.resource.ResourceLocator.default().locate('rose-meta'))
    )


def add_env_meta_paths():
    """Load the environment variable ROSE_META_PATH, if defined."""
    path = os.environ.get("ROSE_META_PATH")
    if path is not None:
        for path in path.split(os.pathsep):
            path = os.path.expanduser(os.path.expandvars(path))
            sys.path.insert(0, os.path.abspath(path))


def add_opt_meta_paths(meta_paths):
    """Load any metadata paths in a list of ":"-separated strings."""
    if meta_paths is not None:
        meta_paths.reverse()
        for child_paths in [arg.split(os.pathsep) for arg in meta_paths]:
            child_paths.reverse()
            for path in child_paths:
                path = os.path.expandvars(os.path.expanduser(path))
                sys.path.insert(0, os.path.abspath(path))


def get_section_option_from_id(var_id):
    """Return a configuration section and option from an id."""
    section_option = var_id.split(metomi.rose.CONFIG_DELIMITER, 1)
    if len(section_option) == 1:
        return var_id, None
    return section_option


def get_id_from_section_option(section, option):
    """Return a variable id from a section and option."""
    if option is None:
        return section
    return section + metomi.rose.CONFIG_DELIMITER + option


def load_meta_path(
    config=None,
    directory=None,
    is_upgrade=False,
    locator=None,
    opt_meta_paths=None,
    no_warn=None,
):
    """Retrieve the path to the configuration metadata directory.

    Arguments:
        config - a rose config, perhaps with a meta= or project= flag
        directory - the directory of the rose config file
        is_upgrade - if True, load the path in an upgrade-specific way
        locator - a metomi.rose.resource.ResourceLocator instance.

    Returns the path to(or None) and a warning message (or None).

    """
    if config is None:
        config = metomi.rose.config.ConfigNode()
    if no_warn is None:
        no_warn = []
    warning = None
    if directory is not None and not is_upgrade:
        config_meta_dir = os.path.join(directory, metomi.rose.CONFIG_META_DIR)
        meta_file = os.path.join(config_meta_dir, metomi.rose.META_CONFIG_NAME)
        if os.path.isfile(meta_file):
            return config_meta_dir, warning
    if locator is None:
        if opt_meta_paths:
            paths = opt_meta_paths + sys.path
        else:
            paths = sys.path
        locator = metomi.rose.resource.ResourceLocator(paths=paths)
    opt_node = config.get(
        [metomi.rose.CONFIG_SECT_TOP, metomi.rose.CONFIG_OPT_META_TYPE],
        no_ignore=True,
    )
    ignore_meta_error = opt_node is None
    if opt_node is None:
        opt_node = config.get(
            [metomi.rose.CONFIG_SECT_TOP, metomi.rose.CONFIG_OPT_PROJECT],
            no_ignore=True,
        )
    if opt_node is None or not opt_node.value:
        meta_keys = ["rose-all"]
    else:
        key = str(opt_node.value)
        split_key = key.split('/')
        if len(split_key) == 1:
            key = '/'.join([key, metomi.rose.META_DEFAULT_VN_DIR])
        meta_keys = [key]
        split_key = split_key if len(split_key) == 1 else split_key[:-1]
        if is_upgrade:
            meta_keys = ['/'.join(split_key)]
        else:
            default_key = '/'.join(
                split_key + [metomi.rose.META_DEFAULT_VN_DIR]
            )
            if default_key != key:
                meta_keys.append(default_key)
    for i, meta_key in enumerate(meta_keys):
        path = os.path.join(meta_key, metomi.rose.META_CONFIG_NAME)
        if is_upgrade:
            path = meta_key
        try:
            meta_path = str(locator.locate(path))
        except metomi.rose.resource.ResourceError:
            continue
        else:
            if not (ignore_meta_error or 'version' in no_warn) and i > 0:
                warning = ERROR_LOAD_CHOSEN_META_PATH.format(
                    meta_keys[0], meta_keys[i]
                )
            if is_upgrade:
                return meta_path, warning
            return os.path.dirname(meta_path), warning
    if not ignore_meta_error:
        warning = ERROR_LOAD_META_PATH.format(meta_keys[0])
    return None, warning


def load_meta_config_tree(
    config,
    directory=None,
    config_type=None,
    error_handler=None,
    ignore_meta_error=False,
    opt_meta_paths=None,
    no_warn=None,
):
    """Return the metadata config tree for a configuration."""
    if opt_meta_paths:
        paths = opt_meta_paths + sys.path
    else:
        paths = sys.path
    if error_handler is None:
        error_handler = _report_error
    meta_list = ["rose-all/" + metomi.rose.META_CONFIG_NAME]
    if config_type is not None:
        default_meta_dir = config_type.replace(".", "-")
        meta_list.append(default_meta_dir + "/" + metomi.rose.META_CONFIG_NAME)
    config_meta_path, warning = load_meta_path(
        config, directory, opt_meta_paths=opt_meta_paths, no_warn=no_warn
    )
    if warning is not None and not ignore_meta_error:
        error_handler(text=warning)
    locator = metomi.rose.resource.ResourceLocator(paths=paths)
    opt_node = config.get(
        [metomi.rose.CONFIG_SECT_TOP, metomi.rose.CONFIG_OPT_META_TYPE],
        no_ignore=True,
    )
    ignore_meta_error = ignore_meta_error or opt_node is None
    meta_config_tree = None
    meta_config = metomi.rose.config.ConfigNode()
    for meta_key in meta_list:
        try:
            meta_path = str(locator.locate(meta_key))
        except metomi.rose.resource.ResourceError:
            if not ignore_meta_error:
                error_handler(text=ERROR_LOAD_META_PATH.format(meta_key))
            continue
        try:
            meta_config_tree = metomi.rose.config_tree.ConfigTreeLoader().load(
                os.path.dirname(meta_path),
                metomi.rose.META_CONFIG_NAME,
                conf_dir_paths=list(paths),
                conf_node=meta_config,
            )
        except metomi.rose.config.ConfigSyntaxError as exc:
            error_handler(text=str(exc))
        else:
            meta_config = meta_config_tree.node
    if config_meta_path is None:
        return meta_config_tree
    # Try and get a proper non-default meta config tree.
    try:
        meta_config_tree = metomi.rose.config_tree.ConfigTreeLoader().load(
            config_meta_path,
            metomi.rose.META_CONFIG_NAME,
            conf_dir_paths=list(paths),
        )
    except metomi.rose.resource.ResourceError:
        if not ignore_meta_error:
            error_handler(text=ERROR_LOAD_META_PATH.format(meta_list))
    except metomi.rose.config.ConfigSyntaxError as exc:
        error_handler(text=str(exc))

    meta_config += meta_config_tree.node
    meta_config_tree.node = meta_config
    return meta_config_tree


def load_meta_config(
    config,
    directory=None,
    config_type=None,
    error_handler=None,
    ignore_meta_error=False,
):
    """Return the metadata config for a configuration."""
    config_tree = load_meta_config_tree(
        config,
        directory=directory,
        config_type=config_type,
        error_handler=error_handler,
        ignore_meta_error=ignore_meta_error,
    )
    return config_tree.node


def load_meta_macro_modules(meta_files, module_prefix=None):
    """Import metadata macros and return them in an array."""
    modules = []
    for meta_file in meta_files:
        meta_dir = os.path.dirname(meta_file)
        if not meta_dir.endswith(MACRO_DIRNAME) or not meta_file.endswith(
            MACRO_EXT
        ):
            continue
        sys.path.insert(0, meta_dir)
        macro_name = os.path.basename(meta_file).rpartition(MACRO_EXT)[0]
        if module_prefix is None:
            as_name = macro_name
        else:
            as_name = module_prefix + macro_name
        try:
            modules.append(SourceFileLoader(as_name, meta_file).load_module())
        except Exception:
            metomi.rose.reporter.Reporter()(
                MacroLoadError(meta_file, traceback.format_exc())
            )
        sys.path.pop(0)
    modules.sort(key=str)
    return modules


def get_macro_class_methods(macro_modules):
    """Return all macro methods in the modules."""
    macro_methods = []
    for macro_module in macro_modules:
        macro_name = macro_module.__name__
        contents = inspect.getmembers(macro_module)
        for obj_name, obj in contents:
            if not inspect.isclass(obj):
                continue
            for att_name in ALLOWED_MACRO_CLASS_METHODS:
                if hasattr(obj, att_name) and callable(getattr(obj, att_name)):
                    doc_string = obj.__doc__
                    macro_methods.append(
                        (macro_name, obj_name, att_name, doc_string)
                    )
    macro_methods.sort(key=lambda x: x[1])
    macro_methods.sort(key=lambda x: x[1])
    # This logic replicates output of the deprecated Python2 `cmp` builtin
    macro_methods.sort(
        key=cmp_to_key(lambda x, y: (y[2] > x[2]) - (y[2] < x[2]))
    )
    return macro_methods


def get_macros_for_config(
    config=None,
    config_directory=None,
    return_modules=False,
    include_system=False,
    include_custom=True,
    no_warn=False,
):
    """Driver function to return macro names for a config object.

    kwargs:
        config - The config to retrieve macros for as a
            metomi.rose.config.ConfigNode
        config_directory - The directory that the config file is located in.
        return_modules - If true then a list of macro modules is also returned.
        include_system - Include default rose macros?
        include_custom - Include non-default rose macros?
        no_warn - Output metadata warnings?
    """
    if config is None:
        config = ConfigNode()
    meta_config_tree = load_meta_config_tree(
        config, directory=config_directory, no_warn=no_warn
    )
    if meta_config_tree is None:
        return []
    modules = []
    if include_custom:  # Suite specified macros.
        meta_filepaths = [
            os.path.join(v, k) for k, v in meta_config_tree.files.items()
        ]
        modules.extend(load_meta_macro_modules(meta_filepaths))
    if include_system:  # Default macros.
        import metomi.rose.macros  # Done to avoid cyclic top-level imports.

        modules.append(metomi.rose.macros)
    if return_modules:
        return get_macro_class_methods(modules), modules
    return get_macro_class_methods(modules)


def check_config_integrity(app_config):
    """Verify that the configuration is sane - return an error otherwise."""
    try:
        keys_and_nodes = list(app_config.walk())
    except Exception as exc:
        return MacroReturnedCorruptConfigError(str(exc))
    keys_and_nodes.insert(0, ([], app_config))
    for keys, node in keys_and_nodes:
        if not isinstance(node, metomi.rose.config.ConfigNode):
            return MacroReturnedCorruptConfigError(
                ERROR_RETURN_TYPE.format(
                    node, "node", type(node), "rose.config.ConfigNode"
                )
            )
        if not isinstance(node.value, dict) and not isinstance(
            node.value, str
        ):
            return MacroReturnedCorruptConfigError(
                ERROR_RETURN_TYPE.format(
                    node.value,
                    "node.value",
                    type(node.value),
                    "dict, basestring",
                )
            )
        if not isinstance(node.state, str):
            return MacroReturnedCorruptConfigError(
                ERROR_RETURN_TYPE.format(
                    node.state, "node.state", type(node.state), "basestring"
                )
            )
        if node.state not in [
            metomi.rose.config.ConfigNode.STATE_NORMAL,
            metomi.rose.config.ConfigNode.STATE_SYST_IGNORED,
            metomi.rose.config.ConfigNode.STATE_USER_IGNORED,
        ]:
            return MacroReturnedCorruptConfigError(
                ERROR_RETURN_VALUE_STATE.format(node.state)
            )
        if not isinstance(node.comments, list):
            return MacroReturnedCorruptConfigError(
                ERROR_RETURN_TYPE.format(
                    node.comments, "node.comments", type(node.comments), "list"
                )
            )
        for comment in node.comments:
            if not isinstance(comment, str):
                return MacroReturnedCorruptConfigError(
                    ERROR_RETURN_TYPE.format(
                        comment, "comment", type(comment), "basestring"
                    )
                )
        for key in keys:
            if not isinstance(key, str):
                return MacroReturnedCorruptConfigError(
                    ERROR_RETURN_TYPE.format(
                        key, "key", type(key), "basestring"
                    )
                )


def report_config(
    app_config,
    meta_config,
    run_macro_list,
    modules,
    macro_info_tuples,
    opt_non_interactive=False,
    optional_config_name=None,
    optional_values=None,
    validate_mode=True,
):
    """Run report/validator custom macros on the config and return problems
    (in the case of validator macros)."""
    if optional_values is None:
        optional_values = {}
    macro_problem_map = {}
    if validate_mode:
        macro_method = VALIDATE_METHOD
    else:
        macro_method = REPORT_METHOD
    for module_name, class_name, method, _ in macro_info_tuples:
        macro_name = ".".join([module_name, class_name])
        if macro_name in run_macro_list and method == macro_method:
            for module in modules:
                if module.__name__ == module_name:
                    macro_inst = getattr(module, class_name)()
                    macro_meth = getattr(macro_inst, method)
                    break
            res = {}
            if not opt_non_interactive:
                arglist = inspect.getfullargspec(macro_meth).args
                defaultlist = inspect.getfullargspec(macro_meth).defaults
                optionals = {}
                while defaultlist is not None and len(defaultlist) > 0:
                    if arglist[-1] not in ["self", "config", "meta_config"]:
                        optionals[arglist[-1]] = defaultlist[-1]
                        arglist = arglist[0:-1]
                        defaultlist = defaultlist[0:-1]
                    else:
                        break
                if optionals:
                    update_optional_values(
                        res, optionals, optional_values, optional_config_name
                    )
            if validate_mode:
                problem_list = macro_meth(app_config, meta_config, **res)
                if not isinstance(problem_list, list):
                    raise ValueError(ERROR_RETURN_VALUE.format(macro_name))
                if problem_list:
                    macro_problem_map.update({macro_name: problem_list})
            else:
                macro_meth(app_config, meta_config, **res)
    if validate_mode:
        return macro_problem_map


def update_optional_values(
    res, optionals, optional_values, optional_config_name
):
    """Copy any relevant parameters into the 'res' dict."""
    if "optional_config_name" in optionals:
        res["optional_config_name"] = optional_config_name
        del optionals["optional_config_name"]
    for key in set(optionals) & set(optional_values):
        optionals[key] = optional_values[key]
        res[key] = optional_values[key]
    res.update(get_user_values(optionals, res.keys()))
    optional_values.update(res)


def transform_config(
    config,
    meta_config,
    transformer_macro,
    modules,
    macro_info_tuples,
    opt_non_interactive=False,
    optional_config_name=None,
    optional_values=None,
):
    """Run transformer custom macros on the config and return problems."""
    if optional_values is None:
        optional_values = {}
    for module_name, class_name, method, _ in macro_info_tuples:
        if method != TRANSFORM_METHOD:
            continue
        macro_name = ".".join([module_name, class_name])
        if macro_name != transformer_macro:
            continue
        for module in modules:
            if module.__name__ == module_name:
                macro_inst = getattr(module, class_name)()
                macro_method = getattr(macro_inst, method)
                break
        res = {}
        if not opt_non_interactive:
            arglist = inspect.getfullargspec(macro_method).args
            defaultlist = inspect.getfullargspec(macro_method).defaults
            optionals = {}
            while defaultlist is not None and len(defaultlist) > 0:
                if arglist[-1] not in ["self", "config", "meta_config"]:
                    optionals[arglist[-1]] = defaultlist[-1]
                    arglist = arglist[0:-1]
                    defaultlist = defaultlist[0:-1]
                else:
                    break
            if optionals:
                update_optional_values(
                    res, optionals, optional_values, optional_config_name
                )
        return macro_method(config, meta_config, **res)
    return config, []


def pretty_format_config(config, ignore_error=False):
    """Standardise the keys and values of a config node.

    Args:
        config (metomi.rose.config.ConfigNode): The Config node to convert.

    """
    for s_key, s_node in config.value.items():
        scheme = s_key
        if ":" in scheme:
            scheme = scheme.split(":", 1)[0]
        try:
            scheme_module = getattr(metomi.rose.formats, scheme)
            pretty_format_keys = getattr(scheme_module, "pretty_format_keys")
            pretty_format_value = getattr(scheme_module, "pretty_format_value")
        except AttributeError:
            continue
        for keylist, node in list(s_node.walk()):
            # FIXME: Surely, only the scheme knows how to split its array?
            values = metomi.rose.variable.array_split(node.value, ",")
            node.value = pretty_format_value(values)
            new_keylist = pretty_format_keys(keylist)
            if new_keylist != keylist:
                s_node.unset(keylist)
                s_node.set(new_keylist, node.value, node.state, node.comments)
                if ignore_error is False:
                    _report_error(
                        text=ERROR_MACRO_CASE_MISMATCH.format(
                            keylist[1], new_keylist[1]
                        )
                    )
                    sys.exit(0)


def standard_format_config(config):
    """Standardise any degenerate representations e.g. namelist repeats.

    Args:
        config (metomi.rose.config.ConfigNode): The config node to convert.

    """
    for keylist, node in config.walk():
        if len(keylist) == 2:
            scheme = keylist[0]
            if ":" in scheme:
                scheme = scheme.split(":", 1)[0]
            try:
                scheme_module = getattr(metomi.rose.formats, scheme)
                standard_format = getattr(scheme_module, "standard_format")
            except AttributeError:
                continue
            values = metomi.rose.variable.array_split(node.value, ",")
            node.value = standard_format(values)


def get_metadata_for_config_id(setting_id, meta_config):
    """Return a dict of metadata properties and values for a setting id.

    Args:
        setting_id (str): The name of the setting to extract metadata for.
        meta_config (metomi.rose.config.ConfigNode): Config node containing the
            metadata to extract from.

    Return:
        dict: A dictionary containing metadata options.

    Example:
        >>> # Create a rose app.
        >>> with open('rose-app.conf', 'w+') as app_config:
        ...     _ = app_config.write('''
        ... [foo]
        ... bar=2
        ...     ''')
        >>> os.mkdir('meta')
        >>> with open('meta/rose-meta.conf', 'w+') as meta_config:
        ...     _ = meta_config.write('''
        ... [foo=bar]
        ... values = 1,2,3
        ...     ''')
        ...
        >>> # Load config.
        >>> app_conf, config_map, meta_config = load_conf_from_file(
        ...     '.', 'rose-app.conf')
        ...
        >>> # Extract metadata for foo=bar.
        >>> get_metadata_for_config_id('foo=bar', meta_config)
        {'values': '1,2,3', 'id': 'foo=bar'}

        .. testcleanup:: metomi.rose.macro.get_metadata_for_config_id

            test_cleanup(['rose-app.conf', 'meta/rose-meta.conf', 'meta'])

    """
    metadata = {}
    if metomi.rose.CONFIG_DELIMITER in setting_id:
        option = setting_id.split(metomi.rose.CONFIG_DELIMITER, 1)[1]
        search_option = REC_ID_STRIP_DUPL.sub("", option)
    else:
        option = None
        search_option = None
    search_id = REC_ID_STRIP_DUPL.sub("", setting_id)
    no_modifier_id = REC_MODIFIER.sub("", search_id)
    if no_modifier_id != search_id:
        # There is a modifier e.g. namelist:foo{bar}.
        node = meta_config.get([no_modifier_id], no_ignore=True)
        # Get metadata for namelist:foo
        if node is not None:
            for opt, opt_node in node.value.items():
                if not opt_node.is_ignored():
                    metadata.update({opt: opt_node.value})
            if option is None and metomi.rose.META_PROP_TITLE in metadata:
                # Handle section modifier titles
                modifier = search_id.replace(no_modifier_id, "")
                metadata[metomi.rose.META_PROP_TITLE] += " " + modifier
            if (
                setting_id != search_id
                and metomi.rose.META_PROP_DUPLICATE in metadata
            ):
                # foo{bar}(1) cannot inherit duplicate from foo.
                metadata.pop(metomi.rose.META_PROP_DUPLICATE)
    node = meta_config.get([search_id], no_ignore=True)
    # If modifier, get metadata for namelist:foo{bar}
    if node is not None:
        for opt, opt_node in node.value.items():
            if not opt_node.is_ignored():
                metadata.update({opt: opt_node.value})
    if metomi.rose.META_PROP_TITLE in metadata:
        # Handle duplicate (indexed) settings sharing a title
        if option is None:
            if search_id != setting_id:
                # Handle duplicate sections titles
                metadata.pop(metomi.rose.META_PROP_TITLE)
        elif search_option != option:
            # Handle duplicate options titles
            index = option.replace(search_option, "")
            metadata[metomi.rose.META_PROP_TITLE] += " " + index
    if (
        metomi.rose.META_PROP_LENGTH in metadata
        and option is not None
        and search_option != option
        and REC_ID_SINGLE_ELEMENT.search(option)
    ):
        # Option is a single element in an array, not a slice.
        metadata.pop(metomi.rose.META_PROP_LENGTH)
    metadata.update({'id': setting_id})
    return metadata


def run_macros(
    config_map,
    meta_config,
    config_name,
    macro_names,
    opt_conf_dir=None,
    opt_fix=False,
    opt_non_interactive=False,
    opt_output_dir=None,
    opt_validate_all=False,
    opt_transform_all=False,
    verbosity=None,
    no_warn=False,
    default_only=False,
):
    """Run standard or custom macros for a configuration."""

    reporter = metomi.rose.reporter.Reporter(verbosity)

    macro_tuples, modules = get_macros_for_config(
        config_map[None],
        opt_conf_dir,
        return_modules=True,
        include_system=True,
        include_custom=not default_only,
        no_warn=no_warn,
    )

    # Add all macros to the run list as specified.
    methods = []
    if opt_validate_all:
        methods.append(VALIDATE_METHOD)
    if opt_transform_all or opt_fix:
        methods.append(TRANSFORM_METHOD)
    macros_by_type = {}
    for macro_method in methods:
        macros_by_type[macro_method] = []
        for module_name, class_name, method, _ in macro_tuples:
            if opt_fix and not opt_transform_all:
                # Only include internal transformer macros for
                # metomi.rose macro --fix.
                if module_name != metomi.rose.macros.__name__:
                    continue
            if method == macro_method:
                macro_name = ".".join([module_name, class_name])
                macros_by_type[macro_method].append(macro_name)
        if not macros_by_type[macro_method]:
            return True

    # List all macros if none are given.
    if not macro_names and not [
        macros_by_type[method] for method in macros_by_type
    ]:
        for module_name, class_name, method, help_ in macro_tuples:
            macro_name = ".".join([module_name, class_name])
            macro_id = MACRO_OUTPUT_ID.format(method.upper()[0], macro_name)
            if help_:
                reporter(macro_id + "\n", prefix="")
                for help_line in help_.split("\n"):
                    reporter(
                        MACRO_OUTPUT_HELP.format(help_line),
                        level=reporter.V,
                        prefix="",
                    )
            else:
                # No "help" docstring provided in macro.
                reporter(
                    ERROR_NO_MACRO_HELP.format(macro_name),
                    level=reporter.FAIL,
                    prefix=reporter.PREFIX_FAIL,
                )
                return False
        return True

    # Categorise macros given as arguments.
    macros_not_found = [m for m in macro_names]
    for module_name, class_name, method, _ in macro_tuples:
        this_macro_name = ".".join([module_name, class_name])
        this_macro_method_name = ".".join([this_macro_name, method])
        if this_macro_name in macro_names:
            macros_by_type.setdefault(method, [])
            macros_by_type[method].append(this_macro_name)
            if this_macro_name in macros_not_found:
                macros_not_found.remove(this_macro_name)
        elif this_macro_method_name in macro_names:
            macros_by_type.setdefault(method, [])
            macros_by_type[method].append(this_macro_name)
            if this_macro_method_name in macros_not_found:
                macros_not_found.remove(this_macro_method_name)
    for macro_name in macros_not_found:
        reporter(MacroNotFoundError(macro_name))
    if macros_not_found:
        return False

    ret_code = 0

    # Run any validator macros.
    if VALIDATE_METHOD in macros_by_type:
        new_combined_config_map = combine_opt_config_map(config_map)
        macro_config_problems_map = {}
        optional_values = {}
        for conf_key, config in new_combined_config_map.items():
            config_problems_map = report_config(
                config,
                meta_config,
                macros_by_type[VALIDATE_METHOD],
                modules,
                macro_tuples,
                opt_non_interactive,
                optional_config_name=conf_key,
                optional_values=optional_values,
                validate_mode=True,
            )
            if config_problems_map:
                ret_code = 1
            for macro, problem_list in config_problems_map.items():
                macro_config_problems_map.setdefault(macro, {})
                problem_list.sort(key=cmp_to_key(report_sort))
                macro_config_problems_map[macro][conf_key] = problem_list
        problem_macros = list(macro_config_problems_map)
        problem_macros.sort()
        for macro_name in problem_macros:
            config_problems_map = macro_config_problems_map[macro_name]
            method_id = VALIDATE_METHOD.upper()[0]
            macro_id = MACRO_OUTPUT_ID.format(method_id, macro_name)
            reporter(
                get_reports_as_text(
                    config_problems_map, macro_id, is_from_transform=False
                ),
                level=reporter.V,
                kind=reporter.KIND_ERR,
                prefix="",
            )

    # Run any report macros.
    if REPORT_METHOD in macros_by_type:
        new_combined_config_map = combine_opt_config_map(config_map)
        optional_values = {}
        for conf_key, config in new_combined_config_map.items():
            report_config(
                config,
                meta_config,
                macros_by_type[REPORT_METHOD],
                modules,
                macro_tuples,
                opt_non_interactive,
                optional_config_name=conf_key,
                optional_values=optional_values,
                validate_mode=False,
            )

    # Run any transform macros.
    no_changes = True
    if TRANSFORM_METHOD in macros_by_type:
        no_changes = no_changes and _run_transform_macros(
            macros_by_type[TRANSFORM_METHOD],
            config_name,
            config_map,
            meta_config,
            modules,
            macro_tuples,
            opt_non_interactive=opt_non_interactive,
            opt_conf_dir=opt_conf_dir,
            opt_output_dir=opt_output_dir,
            reporter=reporter,
        )

    if not ret_code and no_changes:
        reporter(MacroFinishNothingEvent())
    return ret_code == 0


def report_sort(report1, report2):
    """Sort MacroReport objects by section and option."""
    sect1 = report1.section
    sect2 = report2.section
    if sect1 == sect2:
        opt1 = report1.option
        opt2 = report2.option
        if opt1 is None or opt2 is None:
            # This logic replicates output of the deprecated Python2 `cmp`
            # builtin
            return (str(opt1) > str(opt2)) - (str(opt1) < str(opt2))
        return metomi.rose.config.sort_settings(opt1, opt2)
    return metomi.rose.config.sort_settings(sect1, sect2)


def get_reports_as_text(config_reports_map, macro_id, is_from_transform=False):
    """Translate reports into nicely formatted text."""
    text = ""

    config_warnings_list = []
    config_issues_list = []

    main_reports = set(config_reports_map.get(None, []))
    conf_keys = list(config_reports_map)
    conf_keys = sorted(conf_keys, key=lambda x: x is not None)
    for conf_key in conf_keys:
        reports = config_reports_map[conf_key]
        for rep in reports:  # MacroReport instance
            if conf_key is not None and rep in main_reports:
                # Don't repeat reports about the main configuration.
                continue
            if rep.is_warning:
                config_warnings_list.append((conf_key, rep))
            else:
                config_issues_list.append((conf_key, rep))

    if is_from_transform:
        header = MACRO_OUTPUT_TRANSFORM_CHANGES
    else:
        header = MACRO_OUTPUT_VALIDATE_ISSUES
    header = header.format(macro_id, len(config_issues_list))
    text = header

    for origin, rep in config_issues_list:
        origin_label = get_config_label(origin)
        out = PROBLEM_ENTRY.format(
            origin_label, rep.section, rep.option, rep.value, rep.info
        )
        text += out

    if config_warnings_list:
        header = MACRO_OUTPUT_WARNING_ISSUES
        header = header.format(macro_id, len(config_warnings_list))
        text += header

    for origin, rep in config_warnings_list:
        origin_label = get_config_label(origin)
        out = PROBLEM_ENTRY.format(
            origin_label, rep.section, rep.option, rep.value, rep.info
        )
        text += out
    return text


def get_config_label(config_key):
    """Return an output-suitable representation of the config_key."""
    if not config_key:
        return ""
    return OPT_CONFIG_REPORT.format(config_key)


def handle_transform(
    config_map,
    new_config_map,
    change_map,
    macro_id,
    opt_conf_dir,
    opt_output_dir,
    opt_non_interactive,
    reporter,
):
    """Prompt the user to go ahead with macro changes and dump the output."""
    has_changes = False
    for change_list in change_map.values():
        for report in change_list:
            if not report.is_warning:
                has_changes = True
                break
        if has_changes:
            break
    reporter(
        get_reports_as_text(change_map, macro_id, is_from_transform=True),
        level=reporter.V,
        prefix="",
    )
    if has_changes and (opt_non_interactive or _get_user_accept()):
        for conf_key, config in new_config_map.items():
            dump_config(
                config, opt_conf_dir, opt_output_dir, conf_key=conf_key
            )
        if reporter is not None:
            reporter(
                MacroTransformDumpEvent(opt_conf_dir, opt_output_dir),
                level=reporter.VV,
            )
        return True
    return False


def combine_opt_config_map(config_map):
    """Combine optional configurations with a main configuration."""
    new_combined_config_map = {}
    main_config = config_map[None]
    for conf_key, config in config_map.items():
        if conf_key is None:
            new_combined_config_map[None] = copy.deepcopy(config)
            continue
        new_config = copy.deepcopy(main_config)
        for keylist, subnode in config.walk():
            old_subnode = new_config.get(keylist)
            if (
                isinstance(subnode.value, dict)
                and old_subnode is not None
                and isinstance(old_subnode.value, dict)
            ):
                old_subnode.state = subnode.state
                old_subnode.comments = subnode.comments
            else:
                new_config.set(
                    keylist,
                    value=copy.deepcopy(subnode.value),
                    state=subnode.state,
                    comments=subnode.comments,
                )
        new_combined_config_map[conf_key] = new_config
    return new_combined_config_map


def _run_transform_macros(
    macros,
    config_name,
    config_map,
    meta_config,
    modules,
    macro_tuples,
    opt_non_interactive=False,
    opt_conf_dir=None,
    opt_output_dir=None,
    reporter=None,
):
    no_changes = True
    combined_config_map = combine_opt_config_map(config_map)
    optional_values = {}
    for transformer_macro in macros:
        macro_function = lambda conf, meta, opt: transform_config(
            conf,
            meta,
            transformer_macro,
            modules,
            macro_tuples,
            opt_non_interactive,
            optional_config_name=opt,
            optional_values=optional_values,
        )
        new_config_map, changes_map = apply_macro_to_config_map(
            combined_config_map,
            meta_config,
            macro_function,
            macro_name=transformer_macro,
        )
        method_id = TRANSFORM_METHOD.upper()[0]
        macro_id = MACRO_OUTPUT_ID.format(method_id, transformer_macro)
        if handle_transform(
            config_map,
            new_config_map,
            changes_map,
            macro_id,
            opt_conf_dir,
            opt_output_dir,
            opt_non_interactive,
            reporter,
        ):
            combined_config_map = new_config_map
            no_changes = False
    return no_changes


def apply_macro_to_config_map(
    config_map, meta_config, macro_function, macro_name=None
):
    """Apply a transform macro function to a config_map."""
    new_config_map = {}
    changes_map = {}
    conf_keys = list(config_map)
    conf_keys = sorted(conf_keys, key=lambda x: x is not None)
    for conf_key in conf_keys:
        config = config_map[conf_key]
        macro_config = copy.deepcopy(config)
        return_value = macro_function(macro_config, meta_config, conf_key)
        err_bad_return_value = ERROR_RETURN_VALUE.format(macro_name)
        if not isinstance(return_value, tuple) or len(return_value) != 2:
            raise ValueError(err_bad_return_value)
        new_config, change_list = return_value
        if not isinstance(
            new_config, metomi.rose.config.ConfigNode
        ) or not isinstance(change_list, list):
            raise ValueError(err_bad_return_value)
        exception = check_config_integrity(new_config)
        if exception is not None:
            raise exception
        changes_map[conf_key] = change_list
        if conf_key is None:
            # Always the first item.
            new_config_map[conf_key] = new_config
        else:
            diff = new_config - new_config_map[None]
            new_opt_config = diff.get_as_opt_config()
            new_config_map[conf_key] = new_opt_config
    return new_config_map, changes_map


def _get_user_accept():
    try:
        user_input = input(PROMPT_ACCEPT_CHANGES)
    except EOFError:
        user_allowed_changes = False
    else:
        user_allowed_changes = user_input == PROMPT_OK
    return user_allowed_changes


def get_user_values(options, ignore=None):
    if ignore is None:
        ignore = []
    for key, val in options.items():
        if key in ignore:
            continue
        entered = False
        while not entered:
            try:
                user_input = input(
                    "Value for " + str(key) + " (default " + str(val) + "): "
                )
            except EOFError:
                user_input = ""
                entered = True
            if len(user_input) > 0:
                try:
                    options[key] = ast.literal_eval(user_input)
                    entered = True
                except (SyntaxError, ValueError):
                    metomi.rose.reporter.Reporter()(
                        "Invalid entry: Input should be a valid python "
                        "value.\nNote that strings should be quoted. "
                        "Please try again:\n",
                        kind=metomi.rose.reporter.Reporter.KIND_ERR,
                        level=metomi.rose.reporter.Reporter.FAIL,
                    )
            else:
                entered = True
    return options


def dump_config(
    config,
    opt_conf_dir,
    opt_output_dir=None,
    conf_key=None,
    name=metomi.rose.SUB_CONFIG_NAME,
):
    """Dump the config in a standard form."""
    config = copy.deepcopy(config)
    pretty_format_config(config)
    if opt_output_dir is None:
        directory = opt_conf_dir
    else:
        directory = opt_output_dir
    if conf_key is None:
        target_path = os.path.join(directory, name)
    else:
        source_root, source_ext = os.path.splitext(name)
        base = source_root + "-" + conf_key + source_ext
        target_path = os.path.join(
            directory, metomi.rose.config.OPT_CONFIG_DIR, base
        )
    metomi.rose.config.dump(config, target_path)


def load_conf_from_file(conf_dir, config_file_path, mode="macro"):
    """Loads config data from the file config_file_path."""
    is_info_config = (
        os.path.basename(config_file_path) == metomi.rose.INFO_CONFIG_NAME
    )
    optional_keys = []
    optional_dir = os.path.join(conf_dir, metomi.rose.config.OPT_CONFIG_DIR)
    optional_glob = os.path.join(
        optional_dir, metomi.rose.GLOB_OPT_CONFIG_FILE
    )
    for path in glob.glob(optional_glob):
        filename = os.path.basename(path)
        # filename is a null string if path is to a directory.
        result = re.match(metomi.rose.RE_OPT_CONFIG_FILE, filename)
        if not result:
            continue
        optional_keys.append(result.group(1))

    # Load the configuration and the metadata macros.
    config_loader = metomi.rose.config.ConfigLoader()
    if is_info_config:
        optional_keys = None
    app_config, config_map = config_loader.load_with_opts(
        config_file_path, more_keys=optional_keys, return_config_map=True
    )
    standard_format_config(app_config)
    for _, config in config_map.items():
        standard_format_config(config)

    # Load meta config if it exists.
    meta_config = metomi.rose.config.ConfigNode()
    meta_path, warning = load_meta_path(app_config, conf_dir)

    if meta_path is None and not is_info_config:
        if mode == "macro":
            text = ERROR_LOAD_METADATA.format("")
            if warning:
                text = warning
            metomi.rose.reporter.Reporter()(
                text,
                kind=metomi.rose.reporter.Reporter.KIND_ERR,
                level=metomi.rose.reporter.Reporter.FAIL,
            )
            return None
    else:
        meta_config = load_meta_config(
            app_config,
            directory=conf_dir,
            config_type=os.path.basename(config_file_path),
            ignore_meta_error=True,
        )
    return app_config, config_map, meta_config


def parse_macro_args():
    """Parse options/arguments for rose macro and upgrade."""
    opt_parser = RoseOptionParser(
        usage='rose macro [OPTIONS] [MACRO_NAME ...]',
        description='''
List or run macros associated with a suite or application.

Macros are listed/run according to the config dir (`$PWD` unless
`--config=DIR` is set):

* If the config dir is an app directory (or is within an app directory)
  macros will be listed/run for the `rose-app.conf` file of that app.
* Otherwise macros will be listed/run for the `rose-suite.conf`,
  `rose-suite.info` and (unless `--suite-only` is set) all
  `rose-app.conf` files.

If a configuration contains optional configurations:

* For validator macros, validate the main configuration, then
  validate each main + optional configuration in turn.
* For transform macros, transform the main configuration, then
  transform each main + optional configuration, recreating each
  optional configuration as the diff vs the transformed main.
        ''',
        epilog='''
ARGUMENTS
    MACRO_NAME ...
        A list of macro names to run. If no macro names are specified and
        `--fix`, `--validate` are not used, list all available macros.
        Otherwise, run the specified macro names.

ENVIRONMENT VARIABLES
    optional ROSE_META_PATH
        Prepend `$ROSE_META_PATH` to the metadata search path.
        '''
    )
    opt_parser.add_my_options(
        "conf_dir",
        "meta_path",
        "non_interactive",
        "output_dir",
        "fix",
        "validate_all",
        "no_warn",
        "suite_only",
        "transform_all",
    )
    opt_parser.modify_option(
        'output_dir',
        help=(
            'The location of the output directory.'
            '\nOnly meaningful if there is at least one transformer in the'
            'argument list.'
        ),
    )

    opts, args = opt_parser.parse_args()
    if opts.validate_all and opts.output_dir:
        sys.stderr.write(opt_parser.get_usage())
        return None
    if opts.conf_dir is None:
        opts.conf_dir = os.getcwd()
    opts.conf_dir = os.path.abspath(opts.conf_dir)
    if opts.output_dir is not None:
        opts.output_dir = os.path.abspath(opts.output_dir)

    return opts, args


def _report_error(exception=None, text=""):
    """Report an error via metomi.rose.reporter utilities."""
    if text:
        text += "\n"
    if exception is not None:
        text += type(exception).__name__ + ": " + str(exception) + "\n"
    metomi.rose.reporter.Reporter()(
        text + "\n",
        kind=metomi.rose.reporter.Reporter.KIND_ERR,
        level=metomi.rose.reporter.Reporter.FAIL,
    )


def scan_rose_directory(conf_dir, suite_only=False):
    """Returns a list of rose config files found within the given
    conf_dir.

    * If the conf_dir is an application directory then return only the
      application configuration file
    * If the conf_dir is within the suite directory but above any application
      directory then return all application configs along with the suite and
      info configs.
    * Return None otherwise.

    Arguments:
        conf_dir - The directory to scan.
        suite_only - If True only return suite and info config files.
    """
    path = conf_dir
    while True:
        lstdir = set(os.listdir(path))
        if metomi.rose.TOP_CONFIG_NAME in lstdir:
            # We are in the suite directory.
            confs = []
            if not suite_only:
                # Add app/*/rose-app.conf files.
                confs = sorted(
                    glob.glob(
                        os.path.join(
                            path,
                            metomi.rose.SUB_CONFIGS_DIR,
                            '*',
                            metomi.rose.SUB_CONFIG_NAME,
                        )
                    )
                )
            # Add metomi.rose-suite.conf file.
            confs.append(os.path.join(path, metomi.rose.TOP_CONFIG_NAME))
            # Add metomi.rose-suite.info file.
            if metomi.rose.INFO_CONFIG_NAME in lstdir:
                confs.append(os.path.join(path, metomi.rose.INFO_CONFIG_NAME))
            return confs
        elif not suite_only and metomi.rose.SUB_CONFIG_NAME in lstdir:
            # We are in an app directory. Return only that app.
            return [os.path.join(path, metomi.rose.SUB_CONFIG_NAME)]
        # Go up a directory.
        path = os.path.dirname(path)
        if path == os.path.dirname(path):
            # We don't support suites located at the root!
            break
    return None


def main():
    """Run metomi.rose macro."""
    reporter = metomi.rose.reporter.Reporter()
    add_meta_paths()
    opts, args = parse_macro_args()

    # Get list of apps to evaluate.
    confs = scan_rose_directory(opts.conf_dir, suite_only=opts.suite_only)

    # Fail if no config files could be found.
    if not confs:
        reporter(
            ERROR_LOAD_CONFIG_DIR.format(opts.conf_dir),
            kind=metomi.rose.reporter.Reporter.KIND_ERR,
            level=metomi.rose.reporter.Reporter.FAIL,
        )
        sys.exit(1)

    # Fail if --output-dir specified and multiple config files found.
    if len(confs) > 1 and opts.output_dir:
        reporter(
            ERROR_OUT_DIR_MULTIPLE_APPS,
            kind=metomi.rose.reporter.Reporter.KIND_ERR,
            level=metomi.rose.reporter.Reporter.FAIL,
        )
        sys.exit(1)

    # Path manipulation.
    add_opt_meta_paths(opts.meta_path)

    # Run macros for each config.
    verbosity = 1 + opts.verbosity - opts.quietness
    ret = [True]
    for config_file_path in confs:
        # Macro info.
        conf_dir = os.path.dirname(config_file_path)
        cur_conf_type = os.path.basename(config_file_path)
        config_name = os.path.basename(conf_dir)
        os.chdir(conf_dir)

        # Load config.
        try:
            _, config_map, meta_config = load_conf_from_file(
                conf_dir, config_file_path
            )
        except TypeError:
            sys.exit(1)

        # Report which config we are currently working on.
        if len(confs) > 1:
            if cur_conf_type == metomi.rose.SUB_CONFIG_NAME:
                reporter(
                    os.path.join(
                        metomi.rose.SUB_CONFIGS_DIR, config_name, cur_conf_type
                    )
                )
            else:
                reporter(cur_conf_type)
            sys.stdout.flush()

        # Run macros.
        ret.append(
            run_macros(
                config_map,
                meta_config,
                config_name,
                list(args),
                conf_dir,
                opts.fix,
                opts.non_interactive,
                opts.output_dir,
                opts.validate_all,
                opts.transform_all,
                verbosity,
                no_warn=opts.no_warn,
                default_only=cur_conf_type == metomi.rose.INFO_CONFIG_NAME,
            )
        )

    # Fail if any macro failed.
    sys.exit(0 if all(ret) else 1)


if __name__ == "__main__":
    main()
