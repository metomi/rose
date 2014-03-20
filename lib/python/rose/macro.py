# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
#-----------------------------------------------------------------------------
"""
Module to list or run available custom macros for a configuration.

It also stores macro base classes and macro library functions.

"""

import ast
import copy
import imp
import inspect
import os
import re
import sys
import traceback

import rose.config
import rose.formats.namelist
from rose.opt_parse import RoseOptionParser
import rose.reporter
import rose.resource
import rose.variable


ALLOWED_MACRO_CLASS_METHODS = ["transform", "validate",
                               "downgrade", "upgrade"]
ERROR_LOAD_CONFIG_DIR = "{0}: not an application directory.\n"
ERROR_LOAD_MACRO = "Could not load macro {0}: {1}"
ERROR_LOAD_METADATA = "Could not load metadata {0}\n"
ERROR_LOAD_CHOSEN_META_PATH = "Could not find metadata for {0}, using {1}\n"
ERROR_LOAD_META_PATH = "Could not find metadata for {0}"
ERROR_LOAD_CONF_META_NODE = "Error: could not find meta flag"
ERROR_MACRO_NOT_FOUND = "Error: could not find macro {0}\n"
ERROR_NO_MACROS = "Please specify a macro name.\n"
ERROR_RETURN_TYPE = "{0}: {1}: invalid returned type: {2}, expect {3}"
ERROR_RETURN_VALUE = "{0}: incorrect return value"
ERROR_RETURN_VALUE_STATE = "{0}: node.state: invalid returned value"
MACRO_DIRNAME = os.path.join(os.path.join("lib", "python"),
                             rose.META_DIR_MACRO)
MACRO_EXT = ".py"
MACRO_OUTPUT_HELP = "    # {0}\n"
MACRO_OUTPUT_ID = "[{0}] {1}"
MACRO_OUTPUT_TRANSFORM_CHANGES = "{0}: changes: {1}\n"
MACRO_OUTPUT_VALIDATE_ISSUES = "{0}: issues: {1}\n"
MACRO_OUTPUT_WARNING_ISSUES = "{0}: warnings: {1}\n"
REC_MODIFIER = re.compile(r"\{.+\}")
REC_ID_STRIP_DUPL = re.compile(r"\([:, \w]+\)")
REC_ID_STRIP = re.compile('(?:\{.+\})?(?:\([:, \w]+\))?$')
REC_ID_ELEMENT = re.compile(r"\(([:, \w]+)\)$")
REC_ID_SINGLE_ELEMENT = re.compile(r"\((\d+)\)$")
ID_ELEMENT_FORMAT = "{0}({1})"
PROBLEM_ENTRY = "    {0}={1}={2}\n        {3}\n"
PROMPT_ACCEPT_CHANGES = "Accept y/n (default n)? "
PROMPT_OK = "y"
SETTING_ID = "    {0}={1}={2}\n        {3}"
TRANSFORM_METHOD = "transform"
VALIDATE_METHOD = "validate"
VERBOSE_LIST = "{0} - ({1}) - {2}"


class MacroFinishNothingEvent(rose.reporter.Event):

    """Event reported when there have been no problems or changes."""

    LEVEL = rose.reporter.Event.VV

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


class MacroTransformDumpEvent(rose.reporter.Event):

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


class MacroBase(object):

    """Base class for macros for validating or transforming configurations."""

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
            return cmp(rep1.value, rep2.value)
        return rose.config.sort_settings(id1, id2)

    def _load_meta_config(self, config, meta=None, directory=None,
                          config_type=None):
        """Return a metadata configuration object."""
        if isinstance(meta, rose.config.ConfigNode):
            return meta
        return load_meta_config(config, directory, config_type=config_type)

    def get_metadata_for_config_id(self, setting_id, meta_config):
        return get_metadata_for_config_id(setting_id, meta_config)

    def get_resource_path(self, filename=''):
        """Load the resource according to the path of the calling macro.

        The returned path will be based on the macro location under
        lib/python in the metadata directory.

        If the calling macro is lib/python/macro/levels.py,
        and the filename is 'rules.json', the returned path will be
        etc/macro/levels/rules.json .

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
        """Pretty-format the configuration values."""
        pretty_format_config(config)

    def standard_format_config(self, config):
        """Standardise configuration syntax."""
        standard_format_config(config)

    def add_report(self, *args, **kwargs):
        self.reports.append(MacroReport(*args, **kwargs))


class MacroBaseRoseEdit(MacroBase):

    """This class extends MacroBase to provide a non-ConfigNode API.

    In the following methods, config_data can be a
    rose.config.ConfigNode instance or a dictionary that
    looks like this:
    {"sections":
        {"namelist:foo": rose.section.Section instance,
         "env": rose.section.Section instance},
        "variables":
        {"namelist:foo": [rose.variable.Variable instance,
                          rose.variable.Variable instance],
         "env": [rose.variable.Variable instance]}
    }
    This makes it easy to interface with rose edit, which uses the
    latter data structure internally.

    """

    def _get_config_sections(self, config_data):
        """Return all sections within config_data."""
        sections = []
        if isinstance(config_data, rose.config.ConfigNode):
            for key, node in config_data.value.items():
                if isinstance(node.value, dict):
                    sections.append(key)
                elif "" not in sections:
                    sections.append("")
        else:
            for key in set(config_data["sections"].keys() +
                           config_data["variables"].keys()):
                sections.append(key)
        return sections

    def _get_config_section_options(self, config_data, section):
        """Return all options within a section in config_data."""
        if isinstance(config_data, rose.config.ConfigNode):
            names = []
            for keylist, node in config_data.walk([section]):
                names.append(keylist[-1])
            return names
        else:
            return [v.name for v in config_data["variables"].get(section, [])]
        return []

    def _get_config_has_id(self, config_data, id_):
        """Return whether the config_data contains the id_."""
        section, option = self._get_section_option_from_id(id_)
        if isinstance(config_data, rose.config.ConfigNode):
            return (config_data.get([section, option]) is not None)
        if option is None:
            return section in config_data["sections"]
        return option in [v.name for v in
                          config_data["variables"].get(section, [])]

    def _get_config_id_state(self, config_data, id_):
        """Return the ConfigNode.STATE_* that applies to id_ or None."""
        section, option = self._get_section_option_from_id(id_)
        if isinstance(config_data, rose.config.ConfigNode):
            node = config_data.get([section, option])
            if node is None:
                return None
            return node.state
        ignored_reason = None
        if option is None:
            if section in config_data["sections"]:
                 ignored_reason = (
                     config_data["sections"][section].ignored_reason)
        else:
            for variable in config_data["variables"].get(section, []):
                if variable.name == option:
                    ignored_reason = variable.ignored_reason
                    break
        if ignored_reason is None:
            return None
        if rose.variable.IGNORED_BY_USER in ignored_reason:
            return rose.config.ConfigNode.STATE_USER_IGNORED
        if rose.variable.IGNORED_BY_SYSTEM in ignored_reason:
            return rose.config.ConfigNode.STATE_SYST_IGNORED
        return rose.config.ConfigNode.STATE_NORMAL

    def _get_config_id_value(self, config_data, id_):
        """Return a value (if any) for id_ in the config_data."""
        section, option = self._get_section_option_from_id(id_)
        if option is None:
            return None
        if isinstance(config_data, rose.config.ConfigNode):
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
            p_list.sort(self._sorter)
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
            c_list.sort(self._sorter)
            self.reports += c_list
        return config, self.reports


class MacroReport(object):

    """Class to hold information about a macro issue."""

    def __init__(self, section=None, option=None, value=None,
                 info=None, is_warning=False):
        self.section = section
        self.option = option
        self.value = value
        self.info = info
        self.is_warning = is_warning


def add_site_meta_paths():
    """Load any metadata paths specified in a user or site configuration."""
    conf = rose.resource.ResourceLocator.default().get_conf()
    path = conf.get_value([rose.CONFIG_SECT_TOP, rose.CONFIG_OPT_META_PATH])
    if path is not None:
        for path in path.split(os.pathsep):
            path = os.path.expanduser(os.path.expandvars(path))
            sys.path.insert(0, os.path.abspath(path))
    sys.path.append(os.path.join(os.getenv("ROSE_HOME"), "etc/rose-meta"))


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
    section_option = var_id.split(rose.CONFIG_DELIMITER, 1)
    if len(section_option) == 1:
        return var_id, None
    return section_option


def get_id_from_section_option(section, option):
    """Return a variable id from a section and option."""
    if option is None:
        return section
    return section + rose.CONFIG_DELIMITER + option


def load_meta_path(config=None, directory=None, is_upgrade=False,
                   locator=None):
    """Retrieve the path to the configuration metadata directory.

    Arguments:
        config - a rose config, perhaps with a meta= or project= flag
        directory - the directory of the rose config file
        is_upgrade - if True, load the path in an upgrade-specific way
        locator - a rose.resource.ResourceLocator instance.

    Returns the path to(or None) and a warning message (or None).

    """
    if config is None:
        config = rose.config.ConfigNode()
    warning = None
    if directory is not None and not is_upgrade:
        config_meta_dir = os.path.join(directory, rose.CONFIG_META_DIR)
        meta_file = os.path.join(config_meta_dir, rose.META_CONFIG_NAME)
        if os.path.isfile(meta_file):
            return config_meta_dir, warning
    if locator is None:
        locator = rose.resource.ResourceLocator(paths=sys.path)
    opt_node = config.get([rose.CONFIG_SECT_TOP,
                           rose.CONFIG_OPT_META_TYPE], no_ignore=True)
    ignore_meta_error = opt_node is None
    if opt_node is None:
        opt_node = config.get([rose.CONFIG_SECT_TOP,
                               rose.CONFIG_OPT_PROJECT], no_ignore=True)
    if opt_node is None or not opt_node.value:
        meta_keys = ["rose-all"]
    else:
        key = opt_node.value
        if "/" not in key:
            key = key + "/" + rose.META_DEFAULT_VN_DIR
        meta_keys = [key]
        if is_upgrade:
            meta_keys = [key.split("/")[0]]
        else:
            default_key = (key.rsplit("/", 1)[0] + "/" +
                           rose.META_DEFAULT_VN_DIR)
            if default_key != key:
                meta_keys.append(default_key)
    for i, meta_key in enumerate(meta_keys):
        path = os.path.join(meta_key, rose.META_CONFIG_NAME)
        if is_upgrade:
            path = meta_key
        try:
            meta_path = locator.locate(path)
        except rose.resource.ResourceError:
            continue
        else:
            if not ignore_meta_error and i > 0:
                warning = ERROR_LOAD_CHOSEN_META_PATH.format(meta_keys[0],
                                                             meta_keys[i])
            if is_upgrade:
                return meta_path, warning
            return os.path.dirname(meta_path), warning
    if not ignore_meta_error:
        warning = ERROR_LOAD_META_PATH.format(meta_keys[0])
    return None, warning


def load_meta_config(config, directory=None, config_type=None,
                     error_handler=None, ignore_meta_error=False):
    """Return the metadata config for a configuration."""
    if error_handler is None:
        error_handler = _report_error
    meta_config = rose.config.ConfigNode()
    meta_list = ["rose-all/" + rose.META_CONFIG_NAME]
    if config_type is not None:
        default_meta_dir = config_type.replace(".", "-")
        meta_list.append(default_meta_dir + "/" + rose.META_CONFIG_NAME)
    config_meta_path, warning = load_meta_path(config, directory)
    if warning is not None and not ignore_meta_error:
        error_handler(text=warning)
    if config_meta_path is not None:
        path = os.path.join(config_meta_path, rose.META_CONFIG_NAME)
        if path not in meta_list:
            meta_list.append(path)
    locator = rose.resource.ResourceLocator(paths=sys.path)
    opt_node = config.get([rose.CONFIG_SECT_TOP,
                           rose.CONFIG_OPT_META_TYPE], no_ignore=True)
    ignore_meta_error = ignore_meta_error or opt_node is None
    config_loader = rose.config.ConfigLoader()
    for meta_key in meta_list:
        try:
            meta_path = locator.locate(meta_key)
        except rose.resource.ResourceError as e:
            if not ignore_meta_error:
                error_handler(text=ERROR_LOAD_META_PATH.format(meta_key))
        else:
            try:
                config_loader.load_with_opts(meta_path, meta_config)
            except rose.config.ConfigSyntaxError as e:
                error_handler(text=str(e))
    return meta_config


def load_meta_macro_modules(meta_files, module_prefix=None):
    """Import metadata macros and return them in an array."""
    modules = []
    for meta_file in meta_files:
        meta_dir = os.path.dirname(meta_file)
        if (not meta_dir.endswith(MACRO_DIRNAME) or
            not meta_file.endswith(MACRO_EXT)):
            continue
        macro_name = os.path.basename(meta_file).rpartition(MACRO_EXT)[0]
        if module_prefix is None:
            as_name = macro_name
        else:
            as_name = module_prefix + macro_name
        try:
            modules.append(imp.load_source(as_name, meta_file))
        except Exception:
            rose.reporter.Reporter()(
                MacroLoadError(meta_file, traceback.format_exc()))
    modules.sort()
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
                if (hasattr(obj, att_name) and
                    callable(getattr(obj, att_name))):
                    doc_string = obj.__doc__
                    macro_methods.append((macro_name, obj_name, att_name,
                                          doc_string))
    macro_methods.sort(lambda x, y: cmp(x[1], y[1]))
    macro_methods.sort(lambda x, y: cmp(x[0], y[0]))
    macro_methods.sort(lambda x, y: cmp(y[2], x[2]))
    return macro_methods


def get_macros_for_config(app_config=None,
                          config_directory=None,
                          return_modules=False,
                          include_system=False):
    """Driver function to return macro names for a config object."""
    if app_config is None:
        app_config = rose.config.ConfigNode()
    meta_path, warning = load_meta_path(app_config, config_directory)
    if meta_path is None:
        sys.exit(ERROR_LOAD_METADATA.format(""))
    meta_filepaths = []
    for dirpath, dirnames, filenames in os.walk(meta_path):
        if "/.svn" in dirpath:
            continue
        for fname in filenames:
            meta_filepaths.append(os.path.join(dirpath, fname))
    modules = load_meta_macro_modules(meta_filepaths)
    if include_system:
        import rose.macros  # Done to avoid cyclic top-level imports.
        modules.append(rose.macros)
    if return_modules:
        return get_macro_class_methods(modules), modules
    return get_macro_class_methods(modules)


def check_config_integrity(app_config):
    """Verify that the configuration is sane - return an error otherwise."""
    try:
        keys_and_nodes = list(app_config.walk())
    except Exception as e:
        return MacroReturnedCorruptConfigError(str(e))
    keys_and_nodes.insert(0, ([], app_config))
    for keys, node in keys_and_nodes:
        if not isinstance(node, rose.config.ConfigNode):
            return MacroReturnedCorruptConfigError(ERROR_RETURN_TYPE.format(
                node, "node", type(node), "rose.config.ConfigNode"))
        if (not isinstance(node.value, dict) and
            not isinstance(node.value, basestring)):
            return MacroReturnedCorruptConfigError(ERROR_RETURN_TYPE.format(
                node.value, "node.value", type(node.value),
                "dict, basestring"
            ))
        if not isinstance(node.state, basestring):
            return MacroReturnedCorruptConfigError(ERROR_RETURN_TYPE.format(
                node.state, "node.state", type(node.state), "basestring"))
        if node.state not in [rose.config.ConfigNode.STATE_NORMAL,
                              rose.config.ConfigNode.STATE_SYST_IGNORED,
                              rose.config.ConfigNode.STATE_USER_IGNORED]:
            return MacroReturnedCorruptConfigError(
                ERROR_RETURN_VALUE_STATE.format(node.state))
        if not isinstance(node.comments, list):
            return MacroReturnedCorruptConfigError(ERROR_RETURN_TYPE.format(
                node.comments, "node.comments", type(node.comments),
                "list"
            ))
        for comment in node.comments:
            if not isinstance(comment, basestring):
                return MacroReturnedCorruptConfigError(ERROR_RETURN_TYPE.format(
                    comment, "comment", type(comment), "basestring"))
        for key in keys:
            if not isinstance(key, basestring):
                return MacroReturnedCorruptConfigError(ERROR_RETURN_TYPE.format(
                    key, "key", type(key), "basestring"))


def validate_config(app_config, meta_config, run_macro_list, modules,
                    macro_info_tuples, opt_non_interactive=False):
    """Run validator custom macros on the config and return problems."""
    macro_problem_dict = {}
    for module_name, class_name, method, help in macro_info_tuples:
        macro_name = ".".join([module_name, class_name])
        if macro_name in run_macro_list and method == VALIDATE_METHOD:
            for module in modules:
                if module.__name__ == module_name:
                    macro_inst = getattr(module, class_name)()
                    macro_meth = getattr(macro_inst, method)
                    break
            res = {}
            if not opt_non_interactive:
                arglist = inspect.getargspec(macro_meth).args
                defaultlist = inspect.getargspec(macro_meth).defaults
                optionals = {}
                while defaultlist is not None and len(defaultlist) > 0:
                    if arglist[-1] not in ["self", "config", "meta_config"]:
                        optionals[arglist[-1]] = defaultlist[-1]
                        arglist = arglist[0:-1]
                        defaultlist = defaultlist[0:-1]
                    else:
                        break
                if optionals:
                    res = get_user_values(optionals)
            problem_list = macro_meth(app_config, meta_config, **res)
            if not isinstance(problem_list, list):
                raise ValueError(ERROR_RETURN_VALUE.format(macro_name))
            if problem_list:
                macro_problem_dict.update({macro_name: problem_list})
    return macro_problem_dict


def transform_config(config, meta_config, transformer_macro, modules,
                     macro_info_tuples, opt_non_interactive=False):
    """Run transformer custom macros on the config and return problems."""
    macro_change_dict = {}
    for module_name, class_name, method, help in macro_info_tuples:
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
            arglist = inspect.getargspec(macro_method).args
            defaultlist = inspect.getargspec(macro_method).defaults
            optionals = {}
            while defaultlist is not None and len(defaultlist) > 0:
                if arglist[-1] not in ["self", "config", "meta_config"]:
                    optionals[arglist[-1]] = defaultlist[-1]
                    arglist = arglist[0:-1]
                    defaultlist = defaultlist[0:-1]
                else:
                    break
            if optionals:
                res = get_user_values(optionals)
        return macro_method(config, meta_config, **res)
    return config, []


def pretty_format_config(config):
    """Improve configuration prettiness."""
    for section in config.value.keys():
        keylist = [section]
        scheme = keylist[0]
        if ":" in scheme:
            scheme = scheme.split(":", 1)[0]
        try:
            scheme_module = getattr(rose.formats, scheme)
            pretty_format_keys = getattr(scheme_module, "pretty_format_keys")
            pretty_format_value = getattr(scheme_module, "pretty_format_value")
        except AttributeError:
            continue
        new_keylist = pretty_format_keys(keylist)
        if new_keylist != keylist:
            node = config.get(keylist)
            config.unset(keylist)
            config.set(new_keylist, node.value, node.state, node.comments)
            section = new_keylist[0]
        for keylist, node in list(config.walk([section])):
            values = rose.variable.array_split(node.value, ",")
            node.value = pretty_format_value(values)   
            new_keylist = pretty_format_keys(keylist)
            if new_keylist != keylist:
                config.unset(keylist)
                config.set(new_keylist, node.value, node.state, node.comments)
                

def standard_format_config(config):
    """Standardise any degenerate representations e.g. namelist repeats."""
    for keylist, node in config.walk():
        if len(keylist) == 2:
            scheme, option = keylist
            if ":" in scheme:
                scheme = scheme.split(":", 1)[0]
            try:
                scheme_module = getattr(rose.formats, scheme)
                standard_format = getattr(scheme_module, "standard_format")
            except AttributeError:
                continue
            values = rose.variable.array_split(node.value, ",")
            node.value = standard_format(values)


def get_metadata_for_config_id(setting_id, meta_config):
    """Return a dict of metadata properties and values for a setting id."""
    metadata = {}
    if rose.CONFIG_DELIMITER in setting_id:
        section, option = setting_id.split(rose.CONFIG_DELIMITER, 1)
        search_option = REC_ID_STRIP_DUPL.sub("", option)
    else:
        section = setting_id
        option = None
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
            if option is None and rose.META_PROP_TITLE in metadata:
                # Handle section modifier titles
                modifier = search_id.replace(no_modifier_id, "")
                metadata[rose.META_PROP_TITLE] += " " + modifier
            if (setting_id != search_id and
                rose.META_PROP_DUPLICATE in metadata):
                # foo{bar}(1) cannot inherit duplicate from foo.
                metadata.pop(rose.META_PROP_DUPLICATE)
    node = meta_config.get([search_id], no_ignore=True)
    # If modifier, get metadata for namelist:foo{bar}
    if node is not None:
        for opt, opt_node in node.value.items():
            if not opt_node.is_ignored():
                metadata.update({opt: opt_node.value})
    if rose.META_PROP_TITLE in metadata:
        # Handle duplicate (indexed) settings sharing a title
        if option is None:
            if search_id != setting_id:
                # Handle duplicate sections titles
                metadata.pop(rose.META_PROP_TITLE)
        elif search_option != option:
            # Handle duplicate options titles
            index = option.replace(search_option, "")
            metadata[rose.META_PROP_TITLE] += " " + index
    if (rose.META_PROP_LENGTH in metadata and
        option is not None and search_option != option and
        REC_ID_SINGLE_ELEMENT.search(option)):
        # Option is a single element in an array, not a slice.
        metadata.pop(rose.META_PROP_LENGTH)
    metadata.update({'id': setting_id})
    return metadata


def run_macros(app_config, meta_config, config_name, macro_names,
               opt_conf_dir=None, opt_fix=False,
               opt_non_interactive=False, opt_output_dir=None,
               opt_validate_all=False,
               verbosity=None):
    """Run standard or custom macros for a configuration."""

    reporter = rose.reporter.Reporter(verbosity)

    macro_tuples, modules = get_macros_for_config(
                  app_config, opt_conf_dir,
                  return_modules=True,
                  include_system=True)

    # Add all validator macros to the run list if specified.
    if opt_validate_all:
        for module_name, class_name, method, help in macro_tuples:
            if method == VALIDATE_METHOD:
                macro_name = ".".join([module_name, class_name])
                macro_names.insert(0, macro_name)
        if not macro_names:
            sys.exit(0)
    elif opt_fix:
        for module_name, class_name, method, help in macro_tuples:
            if module_name != rose.macros.__name__:
                continue
            if method == TRANSFORM_METHOD:
                macro_name = ".".join([module_name, class_name])
                macro_names.insert(0, macro_name)
        if not macro_names:
            sys.exit(0)
    # List all macros if none are given.
    if not macro_names:
        for module_name, class_name, method, help in macro_tuples:
            macro_name = ".".join([module_name, class_name])
            macro_id = MACRO_OUTPUT_ID.format(method.upper()[0], macro_name)
            reporter(macro_id + "\n", prefix="")
            for help_line in help.split("\n"):
                reporter(MACRO_OUTPUT_HELP.format(help_line),
                         level=reporter.V, prefix="")
        sys.exit(0)

    # Categorise macros given as arguments.
    macros_by_type = {}
    macros_not_found = [m for m in macro_names]
    for module_name, class_name, method, help in macro_tuples:
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
        sys.exit(1)

    rc = 0

    # Run any validator macros.
    if VALIDATE_METHOD in macros_by_type:
        config_problem_dict = validate_config(app_config, meta_config,
                                              macros_by_type[VALIDATE_METHOD],
                                              modules,
                                              macro_tuples,
                                              opt_non_interactive)
        if config_problem_dict:
            rc = 1
            problem_macros = config_problem_dict.keys()
            problem_macros.sort()
            for macro_name in problem_macros:
                problem_list = config_problem_dict[macro_name]
                sort = rose.config.sort_settings

                problem_list.sort(report_sort)
                method_id = VALIDATE_METHOD.upper()[0]
                macro_id = MACRO_OUTPUT_ID.format(method_id, macro_name)
                reporter(
                    get_reports_as_text(
                        problem_list, macro_id, is_from_transform=False),
                    level=reporter.V, kind=reporter.KIND_ERR, prefix=""
                )

    no_changes = True

    # Run any transform macros.
    if TRANSFORM_METHOD in macros_by_type:
        no_changes = _run_transform_macros(
            macros_by_type[TRANSFORM_METHOD],
            config_name, app_config, meta_config, modules,
            macro_tuples,
            opt_non_interactive=opt_non_interactive,
            opt_conf_dir=opt_conf_dir,
            opt_output_dir=opt_output_dir,
            reporter=reporter)
    if not rc and no_changes:
        reporter(MacroFinishNothingEvent())
    sys.exit(rc)


def report_sort(report1, report2):
    """Sort MacroReport objects by section and option."""
    sect1 = report1.section
    sect2 = report2.section
    if sect1 == sect2:
        opt1 = report1.option
        opt2 = report2.option
        if opt1 is None or opt2 is None:
            return cmp(opt1, opt2)
        return rose.config.sort_settings(opt1, opt2)
    return rose.config.sort_settings(sect1, sect2)


def get_reports_as_text(reports, macro_id, is_from_transform=False):
    """Translate reports into nicely formatted text."""
    warnings = []
    issues = []
    text = ""
    for rep in reports:  # MacroReport instance
        if rep.is_warning:
            warnings.append(rep)
            continue
        issues.append(rep)
    if is_from_transform:
        header = MACRO_OUTPUT_TRANSFORM_CHANGES
    else:
        header = MACRO_OUTPUT_VALIDATE_ISSUES
    header = header.format(macro_id, len(issues))
    text += header
    for rep in issues:
        out = PROBLEM_ENTRY.format(rep.section, rep.option,
                                    rep.value, rep.info)
        text += out
    if warnings:
        header = MACRO_OUTPUT_WARNING_ISSUES
        header = header.format(macro_id, len(warnings))
        text += header
    for rep in warnings:
        out = PROBLEM_ENTRY.format(rep.section, rep.option,
                                    rep.value, rep.info)
        text += out
    return text


def handle_transform(app_config, new_config, change_list, macro_id,
                     opt_conf_dir, opt_output_dir, opt_non_interactive,
                     reporter):
    """Prompt the user to go ahead with macro changes and dump the output."""
    user_allowed_changes = False
    has_changes = any([not i.is_warning for i in change_list])
    reporter(get_reports_as_text(change_list, macro_id,
                                 is_from_transform=True),
             level=reporter.V, prefix="")
    if has_changes and (opt_non_interactive or _get_user_accept()):
        app_config = new_config
        dump_config(app_config, opt_conf_dir, opt_output_dir)
        if reporter is not None:
            reporter(MacroTransformDumpEvent(opt_conf_dir,
                                             opt_output_dir),
                     level=reporter.VV)
        return True
    return False


def _run_transform_macros(macros, config_name, app_config, meta_config,
                          modules, macro_tuples, opt_non_interactive=False,
                          opt_conf_dir=None, opt_output_dir=None,
                          reporter=None):
    no_changes = True
    for transformer_macro in macros:
        macro_config = copy.deepcopy(app_config)
        return_value = transform_config(macro_config,
                                        meta_config,
                                        transformer_macro,
                                        modules, macro_tuples,
                                        opt_non_interactive)
        err_bad_return_value = ERROR_RETURN_VALUE.format(
                                     transformer_macro)
        if (not isinstance(return_value, tuple) or
            len(return_value) != 2):
            raise ValueError(err_bad_return_value)
        new_config, change_list = return_value
        if (not isinstance(new_config, rose.config.ConfigNode) or
            not isinstance(change_list, list)):
            raise ValueError(err_bad_return_value)
        exception = check_config_integrity(new_config)
        if exception is not None:
            raise exception
        if change_list:
            no_changes = False
        method_id = TRANSFORM_METHOD.upper()[0]
        macro_id = MACRO_OUTPUT_ID.format(method_id, transformer_macro)
        handle_transform(app_config, new_config, change_list, macro_id,
                          opt_conf_dir, opt_output_dir, opt_non_interactive,
                          reporter)
    return no_changes

def _get_user_accept():
    try:
        user_input = raw_input(PROMPT_ACCEPT_CHANGES)
    except EOFError:
        user_allowed_changes = False
    else:
        user_allowed_changes = (user_input == PROMPT_OK)
    return user_allowed_changes


def get_user_values(options):
    for k,v in options.items():
        entered = False
        while entered == False:
            try:
                user_input = raw_input("Value for " + str(k) + " (default " +
                                       str(v) + "): ")
            except EOFError:
                user_input = ""
                entered = True
            if len(user_input) > 0:
                try:
                    options[k] = ast.literal_eval(user_input)
                    entered = True
                except ValueError:
                    rose.reporter.Reporter()(
                        "Invalid entry, please try again\n",
                        kind=rose.reporter.Reporter.KIND_ERR,
                        level=rose.reporter.Reporter.FAIL
                    )
            else:
                entered = True
    return options

def dump_config(app_config, opt_conf_dir, opt_output_dir=None):
    """Dump the config in a standard form."""
    pretty_format_config(app_config)
    if opt_output_dir is None:
        directory = opt_conf_dir
    else:
        directory = opt_output_dir
    file_path = os.path.join(directory, rose.SUB_CONFIG_NAME)
    rose.config.dump(app_config, file_path)


def parse_macro_mode_args(mode="macro", argv=None):
    """Parse options/arguments for rose macro and upgrade."""
    opt_parser = RoseOptionParser()
    options = ["conf_dir", "meta_path", "non_interactive", "output_dir"]
    if mode == "macro":
        options.extend(["fix", "validate_all"])
    elif mode == "upgrade":
        options.extend(["downgrade", "all_versions"])
    else:
        raise KeyError("Wrong mode: {0}".format(mode))
    opt_parser.add_my_options(*options)
    if argv is None:
        opts, args = opt_parser.parse_args()
    else:
        opts, args = opt_parser.parse_args(argv)
    opts, args = opt_parser.parse_args(argv)
    if mode == "upgrade" and len(args) > 1:
        sys.stderr.write(opt_parser.get_usage())
        return None
    if opts.conf_dir is None:
        opts.conf_dir = os.getcwd()
    sys.path.append(os.getenv("ROSE_HOME"))
    add_opt_meta_paths(opts.meta_path)
    config_name = os.path.basename((os.path.abspath(opts.conf_dir)))
    config_file_path = os.path.join(opts.conf_dir,
                                    rose.SUB_CONFIG_NAME)
    if (not os.path.exists(config_file_path) or
        not os.path.isfile(config_file_path)):
        rose.reporter.Reporter()(ERROR_LOAD_CONFIG_DIR.format(opts.conf_dir),
                                 kind=rose.reporter.Reporter.KIND_ERR,
                                 level=rose.reporter.Reporter.FAIL)
        return None
    # Load the configuration and the metadata macros.
    config_loader = rose.config.ConfigLoader()
    app_config = config_loader(config_file_path)
    standard_format_config(app_config)

    # Load meta config if it exists.
    meta_config = rose.config.ConfigNode()
    meta_path, warning = load_meta_path(app_config, opts.conf_dir)
    if meta_path is None:
        if mode == "macro":
            text = ERROR_LOAD_METADATA.format("")
            if warning:
                text = warning
            rose.reporter.Reporter()(text,
                                     kind=rose.reporter.Reporter.KIND_ERR,
                                     level=rose.reporter.Reporter.FAIL)
            return None
    else:
        meta_config = load_meta_config(app_config,
                                       directory=opts.conf_dir,
                                       config_type=rose.SUB_CONFIG_NAME,
                                       ignore_meta_error=True)
    return app_config, meta_config, config_name, args, opts


def _report_error(exception=None, text=""):
    """Report an error via rose.reporter utilities."""
    if text:
        text += "\n"
    if exception is not None:
        text += type(exception).__name__ + ": " + str(exception) + "\n"
    rose.reporter.Reporter()(
        text + "\n",
        kind=rose.reporter.Reporter.KIND_ERR,
        level=rose.reporter.Reporter.FAIL
    )


def main():
    """Run rose macro."""
    add_site_meta_paths()
    add_env_meta_paths()
    return_objects = parse_macro_mode_args()
    if return_objects is None:
        sys.exit(1)
    app_config, meta_config, config_name, args, opts = return_objects
    if opts.conf_dir is not None:
        os.chdir(opts.conf_dir)
    verbosity = 1 + opts.verbosity - opts.quietness
    run_macros(app_config, meta_config, config_name, args,
               opts.conf_dir, opts.fix,
               opts.non_interactive, opts.output_dir,
               opts.validate_all, verbosity)


if __name__ == "__main__":
    main()
