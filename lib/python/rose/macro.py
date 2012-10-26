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
"""
Module to list or run available custom macros for a configuration.

It also stores macro base classes and macro library functions.

"""
import copy
import inspect
import os
import re
import sys

import rose.config
import rose.config_editor.variable
import rose.formats.namelist
from rose.opt_parse import RoseOptionParser
import rose.resource
import rose.variable


ALLOWED_MACRO_CLASS_METHODS = ["transform", "validate"]
ARG_DOWNGRADE = "downgrade"
ERROR_LOAD_CONFIG_DIR = "{0}: not an application directory.\n"
ERROR_LOAD_MACRO = "Could not load macro {0}: {1}"
ERROR_LOAD_METADATA_DIR = "Could not find metadata directory.\n"
ERROR_LOAD_METADATA = "Could not load metadata {0}: {1}"
ERROR_LOAD_META_PATH = "Could not find {0}\n"
ERROR_LOAD_CONF_META_NODE = "Could not find meta flag"
ERROR_MACRO_NOT_FOUND = "Error: could not find macro {0}\n"
ERROR_NO_MACROS = "Please specify a macro name.\n"
ERROR_NO_VALID_VERSIONS = "No versions available."
ERROR_UPGRADE_VERSION = "Invalid version: {0} should be one of {1}"
INFO_DOWNGRADED = "Downgraded from {0} to {1}"
INFO_UPGRADED = "Upgraded from {0} to {1}"
MACRO_DIRNAME = os.path.join(os.path.join("lib", "python"), "macros")
MACRO_EXT = ".py"
MACRO_OUTPUT_HELP = "    # {0}"
MACRO_OUTPUT_ID = "[{0}] {2}"
MACRO_OUTPUT_TRANSFORM_CHANGES = "{0}: changes: {1}\n"
MACRO_OUTPUT_VALIDATE_ISSUES = "{0}: issues: {1}\n"
MACRO_OUTPUT_WARNING_ISSUES = "{0}: warnings: {1}\n"
MACRO_UPGRADE_MODULE = "versions"
MACRO_UPGRADE_RESOURCE_DIR = "etc"
MACRO_UPGRADE_RESOURCE_FILE_ADD = "rose-macro-add.conf"
MACRO_UPGRADE_RESOURCE_FILE_REMOVE = "rose-macro-remove.conf"
NAME_DOWNGRADE = "Downgrade{0}-{1}"
NAME_UPGRADE = "Upgrade{0}-{1}"
REC_MODIFIER = re.compile(r"\{.+\}")
REC_ID_STRIP_DUPL = re.compile(r"\([\d:, ]+\)")
REC_ID_STRIP = re.compile('(?:\{.+\})?(?:\([\d:, ]+\))?$')
PROBLEM_ENTRY = "    {0}={1}={2}\n        {3}\n"
PROMPT_ACCEPT_CHANGES = "Accept y/n (default n)? "
PROMPT_CHOOSE_VERSION = ("Eligible versions: {0}\n" +
                         "Enter a version (or press <return> " +
                         "for the last one): ")
PROMPT_OK = "y"
TRANSFORM_CHANGE = "    {0}={1}={2}\n        {3}"
TRANSFORM_METHOD = "transform"
VALIDATE_METHOD = "validate"
VERBOSE_LIST = "{0} - ({1}) - {2}"


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


class MacroBase(object):

    """Base class for macros for validating or transforming configurations."""
    
    def _get_section_option_from_id(self, var_id):
        """Return a configuration section and option from an id."""
        section_option = var_id.split(rose.CONFIG_DELIMITER, 1)
        if len(section_option) == 1:
            return var_id, None
        return section_option

    def _get_id_from_section_option(self, section, option):
        """Return a variable id from a section and option."""
        if option is None:
            return section
        return section + rose.CONFIG_DELIMITER + option

    def _sorter(self, rep1, rep2):
        # Sort [section], [section, option], [section, None]
        id1 = self._get_id_from_section_option(rep1.section, rep1.option)
        id2 = self._get_id_from_section_option(rep2.section, rep2.option)
        if id1 == id2:
            return cmp(rep1.value, rep2.value)
        return rose.config.sort_settings(id1, id2)

    def _load_meta_config(self, config, meta=None, directory=None):
        """Return a metadata configuration object."""
        if isinstance(meta, rose.config.ConfigNode):
            return meta
        return load_meta_config(config, directory)

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

    def add_report(self, report_list, *args, **kwargs):
        report_list.append(MacroReport(*args, **kwargs))


class MacroUpgrade(MacroBase):

    """Class derived from MacroBase to aid upgrade functionality."""

    INFO_ADDED_SECT = "Added"
    INFO_ADDED_VAR = "Added with value '{0}'"
    INFO_ENABLE = "User-Ignored -> Enabled"
    INFO_IGNORE = "Enabled -> User-ignored"
    INFO_REMOVED = "Removed"
    UPGRADE_RESOURCE_DIR = MACRO_UPGRADE_RESOURCE_DIR

    def act_from_files(self, changes, config, downgrade=False):
        """Parse a change configuration into actions."""
        res_map = self._get_config_resources()
        add_config = res_map.get(MACRO_UPGRADE_RESOURCE_FILE_ADD)
        rem_config = res_map.get(MACRO_UPGRADE_RESOURCE_FILE_REMOVE)
        if add_config is None:
            add_config = rose.config.ConfigNode()
        if rem_config is None:
            rem_config = rose.config.ConfigNode()
        if downgrade:
            add_config, rem_config = rem_config, add_config
        for keys, node in add_config.walk():
            if len(keys) == 2:
                self.add_option(changes, config, keys[0], keys[1],
                                state=node.state,
                                comments=node.comments)
            else:
                self.add_section(changes, config, keys[0],
                                 state=node.state,
                                 comments=node.comments)
        for keys, node in rem_config.walk():
            if len(keys) == 2:
                self.remove_option(changes, config, keys[0], keys[1])
            elif (not node.value.keys() or config.get(keys) is None or
                  not config.get(keys).value.keys()):
                self.remove_section(changes, config, keys[0])

    def _get_config_resources(self):
        # Get macro configuration resources.
        macro_file = inspect.getfile(self.__class__)
        this_dir = os.path.dirname(os.path.abspath(macro_file))
        res_dir = os.path.join(this_dir, self.UPGRADE_RESOURCE_DIR,
                               self.BEFORE_TAG)
        add_path = os.path.join(res_dir, MACRO_UPGRADE_RESOURCE_FILE_ADD)
        rem_path = os.path.join(res_dir, MACRO_UPGRADE_RESOURCE_FILE_REMOVE)
        file_map = {}
        file_map[MACRO_UPGRADE_RESOURCE_FILE_ADD] = add_path
        file_map[MACRO_UPGRADE_RESOURCE_FILE_REMOVE] = rem_path
        for key, path in file_map.items():
            if os.path.isfile(path):
                file_map[key] = rose.config.load(path)
            else:
                file_map.pop(key)
        return file_map

    def add_section(self, changes, config, section, state=None, comments=None,
                    info=None):
        """Add a section to the configuration."""
        return self._add_setting(changes, config, section, state=state,
                                 comments=comments, info=info)

    def add_option(self, changes, config, section, name, value=None,
                   state=None, comments=None, info=None):
        """Add a variable to the configuration."""
        return self._add_setting(changes, config, section, name, value,
                                 state=state, comments=comments, info=info)

    def enable_section(self, changes, config, section, info=None):
        """Set or unset the user-ignored flag for a section."""
        return self._ignore_setting(changes, config, section,
                                    should_be_user_ignored=False, info=info)

    def enable_variable(self, changes, config, section, name, info=None):
        """Set or unset the user-ignored flag for a variable."""
        return self._ignore_setting(changes, config, section, name,
                                    should_be_user_ignored=False, info=info)


    def get_value(self, config, section, name=None, no_ignore=False):
        """Return the value of a setting."""
        if config.get([section, name], no_ignore=no_ignore) is None:
            return None
        return config.get([section, name]).value

    def ignore_section(self, changes, config, section, info=None):
        """Set or unset the user-ignored flag for a section."""
        return self._ignore_setting(changes, config, section,
                                    should_be_user_ignored=True, info=info)

    def ignore_option(self, changes, config, section, name, info=None):
        """Set or unset the user-ignored flag for a variable."""
        return self._ignore_setting(changes, config, section, name,
                                    should_be_user_ignored=True, info=info)

    def remove_section(self, changes, config, section, info=None):
        """Remove a section from the configuration, if it exists."""
        if config.get([section]) is None:
            return False
        option_node_pairs = config.walk([section])
        for option, option_node in option_node_pairs:
            self.remove_option(changes, config, section, option)
        return self._remove_setting(changes, config, section, info)

    def remove_option(self, changes, config, section, name, info=None):
        """Remove a variable from the configuration, if it exists."""
        return self._remove_setting(changes, config, section, name, info)

    def _add_setting(self, changes, config, section, name=None, value=None,
                     state=None, comments=None, info=None):
        """Add a setting to the configuration."""
        id_ = self._get_id_from_section_option(section, name)
        if name is not None and value is None:
            value = ""
        if info is None:
            if name is None:
                info = self.INFO_ADDED_SECT
            else:
                info = self.INFO_ADDED_VAR.format(value)
        if name is not None and config.get([section]) is None:
            self.add_section(changes, config, section)
        if config.get([section, name]) is not None:
            return False
        if value is not None and not isinstance(value, basestring):
            text = "New value {0} for {1} is not a string"
            raise ValueError(text.format(id_, value))
        config.set([section, name], value=value, state=state,
                   comments=comments)
        self.add_report(changes, section, name, value, info)

    def _ignore_setting(self, changes, config, section, name=None,
                        should_be_user_ignored=False, info=None):
        """Set the ignored state of a setting, if it exists."""
        id_ = self._get_id_from_section_option(section, name)
        if name is None:
            value = None
        else:
            value = config.get([section, name]).value
        if config.get([section, name]) is None:
            return False
        state = config.get([section, name]).state
        if should_be_user_ignored:
            info_text = self.IGNORE
            new_state = rose.config.ConfigNode.STATE_USER_IGNORED
        else:
            info_text = self.ENABLE
            new_state = rose.config.ConfigNode.STATE_NORMAL
        if state == new_state:
            return False
        if info is None:
            info = info_text
        config.set([section, name], state=new_state)
        self.add_report(changes, section, name, value, info)

    def _remove_setting(self, changes, config, section, name=None, info=None):
        """Remove a setting from the configuration, if it exists."""
        id_ = self._get_id_from_section_option(section, name)
        if config.get([section, name]) is None:
            return False
        state = config.get([section, name]).state
        if info is None:
            info = self.INFO_REMOVED
        config.unset([section, name])
        self.add_report(changes, section, name, None, info)


class MacroValidatorCollection(MacroBase):

    """Collate several macros into one."""

    def __init__(self, *macros):
        self.macros = macros
        super(MacroCollection, self).__init__()

    def validate(self, config, meta_config):
        problem_list = []
        for macro_inst in self.macros:
            if not hasattr(macro_inst, VALIDATE_METHOD):
                continue
            macro_method = getattr(macro_inst, VALIDATE_METHOD)
            p_list = macro_meth(config, meta_config)
            p_list.sort(self._sorter)
            problem_list += p_list
        return problem_list 


class MacroTransformerCollection(MacroBase):

    """Collate several macros into one."""

    def __init__(self, *macros):
        self.macros = macros
        super(MacroCollection, self).__init__()

    def transform(self, config, meta_config=None):
        change_list = []
        for macro_inst in self.macros:
            if not hasattr(macro_inst, TRANSFORM_METHOD):
                continue
            macro_method = getattr(macro_inst, TRANSFORM_METHOD)
            config, c_list = macro_method(config, meta_config)
            c_list.sort(self._sorter)
            change_list += c_list
        return config, change_list


class MacroUpgradeManager(object):

    """Manage the upgrades."""

    def __init__(self, app_config, downgrade=False):
        self.app_config = app_config
        self.downgrade = downgrade
        self.new_version = None
        opt_node = app_config.get([rose.CONFIG_SECT_TOP,
                                  rose.CONFIG_OPT_META_TYPE], no_ignore=True)
        tag_items = opt_node.value.split("/")
        if len(tag_items) > 1:
            self.tag = tag_items.pop(-1)
        else:
            self.tag = "HEAD"
        self.meta_flag_no_tag = "/".join(tag_items)
        self.load_all_tags()

    def load_all_tags(self):
        """Load an ordered list of the available upgrade macros."""
        meta_path = load_meta_path(self.app_config, is_upgrade=True)
        if meta_path is None:
            raise OSError(ERROR_LOAD_CONF_META_NODE)
        sys.path.append(os.path.abspath(meta_path))
        try:
            self.version_module = __import__(MACRO_UPGRADE_MODULE)
        except ImportError:
            # No versions.py.
            sys.path.pop()
            self._load_version_macros([])
            return
        sys.path.pop()
        macro_info_tuples = rose.macro.get_macro_class_methods(
                                           [self.version_module])
        version_macros = []
        for module_name, class_name, method, help in macro_info_tuples:
            macro_name = ".".join([module_name, class_name])
            if method == rose.macro.TRANSFORM_METHOD:
                for module in [self.version_module]:
                    if module.__name__ == module_name:
                        macro_inst = getattr(module, class_name)()
                        if (self.downgrade and
                            not self._check_can_downgrade(macro_inst)):
                            continue
                        version_macros.append(macro_inst)
        self._load_version_macros(version_macros)

    def get_tags(self):
        """Return relevant tags, reversed order for downgrades."""
        if self.downgrade:
            return [m.BEFORE_TAG for m in self.version_macros]
        return [m.AFTER_TAG for m in self.version_macros]
        
    def get_new_tag(self):
        """Obtain the default upgrade version."""
        tags = self.get_tags()
        if not tags:
            return None
        return tags[-1]

    def set_new_tag(self, tag):
        """Set the new tag for upgrading/downgrading to."""
        self.new_tag = tag

    def get_name(self):
        """Retrieve the display name for this."""
        if self.downgrade:
            return NAME_DOWNGRADE.format(self.tag, self.new_tag)
        else:
            return NAME_UPGRADE.format(self.tag, self.new_tag)

    def get_macros(self):
        """Return the list of upgrade macros to be applied."""
        if self.downgrade:
            prev_tags = [m.AFTER_TAG for m in self.version_macros]
            next_tags = [m.BEFORE_TAG for m in self.version_macros]
        else:
            prev_tags = [m.BEFORE_TAG for m in self.version_macros]
            next_tags = [m.AFTER_TAG for m in self.version_macros]
        try:
            start_index = prev_tags.index(self.tag)
            end_index = next_tags.index(self.new_tag)
        except ValueError:
            return []
        return self.version_macros[start_index: end_index + 1]

    def transform(self, config, meta_config=None):
        """Transform a configuration by looping over upgrade macros."""
        change_list = []
        for macro in self.get_macros():
            config, i_changes = macro.transform(config, meta_config,
                                                downgrade=self.downgrade)
            change_list += i_changes
        opt_node = config.get([rose.CONFIG_SECT_TOP,
                               rose.CONFIG_OPT_META_TYPE], no_ignore=True)
        new_value = self.meta_flag_no_tag + "/" + self.new_tag
        opt_node.value = new_value
        if self.downgrade:
            info = INFO_DOWNGRADED.format(self.tag, self.new_tag)
        else:
            info = INFO_UPGRADED.format(self.tag, self.new_tag)
        report = MacroReport(rose.CONFIG_SECT_TOP, rose.CONFIG_OPT_META_TYPE,
                             new_value, info)
        change_list += [report]  
        return config, change_list

    def _check_can_downgrade(self, macro_instance):
        # Check whether a macro instance supports a downgrade transform.
        if not hasattr(macro_instance, TRANSFORM_METHOD):
            return False
        func = getattr(macro_instance, TRANSFORM_METHOD)
        if (callable(func) and
            ARG_DOWNGRADE in inspect.getargspec(func).args):
            return True
        return False

    def _upgrade_sort(self, mac1, mac2):
        return ((mac1.BEFORE_TAG == mac2.AFTER_TAG) -
                (mac2.BEFORE_TAG == mac1.AFTER_TAG))

    def _load_version_macros(self, macro_insts):
        self.version_macros = []
        for macro in macro_insts:
            if self.downgrade and macro.AFTER_TAG == self.tag:
                self.version_macros = [macro]
                break
            if not self.downgrade and macro.BEFORE_TAG == self.tag:
                self.version_macros = [macro]
                break
        if self.tag == "HEAD":
            # Try to figure out the latest upgrade version.
            macro_insts.sort(self._upgrade_sort)
            prev_taglist = [m.BEFORE_TAG for m in macro_insts]
            next_taglist = [m.AFTER_TAG for m in macro_insts]
            temp_list = list(macro_insts)
            for macro in list(temp_list[1:]):
                if macro.BEFORE_TAG not in next_taglist:
                    # Disconnected macro.
                    temp_list.pop(macro)
            if temp_list:
                self.version_macros = [temp_list[-1]]            
        if not self.version_macros:
            return
        while macro_insts:
            for macro in list(macro_insts):
                if (self.downgrade and
                    macro.AFTER_TAG == self.version_macros[-1].BEFORE_TAG):
                    macro_insts.remove(macro)
                    self.version_macros.append(macro)
                    break
                if (not self.downgrade and
                    macro.BEFORE_TAG == self.version_macros[-1].AFTER_TAG):
                    macro_insts.remove(macro)
                    self.version_macros.append(macro)
                    break
            else:
                # No more macros found.
                break


class MacroReport(object):

    """Class to hold information about a macro issue."""

    def __init__(self, section=None, option=None, value=None,
                 info=None, is_warning=False):
        self.section = section
        self.option = option
        self.value = value
        self.info = info
        self.is_warning = is_warning


def load_meta_path(config=None, directory=None, is_upgrade=False):
    """Retrieve the path to the metadata."""
    if config is None:
        config = rose.config.ConfigNode()
    if directory is not None and not is_upgrade:
        config_meta_dir = os.path.join(directory, rose.CONFIG_META_DIR)
        if os.path.isdir(config_meta_dir):
            return config_meta_dir
    locator = rose.resource.ResourceLocator(paths=sys.path)
    opt_node = config.get([rose.CONFIG_SECT_TOP,
                           rose.CONFIG_OPT_META_TYPE], no_ignore=True)
    ignore_meta_error = opt_node is None
    if opt_node is None:
        opt_node = config.get([rose.CONFIG_SECT_TOP,
                               rose.CONFIG_OPT_PROJECT], no_ignore=True)
    if opt_node is None:
        meta_path = "etc/metadata/all"
    else:
        meta_path = opt_node.value
        if is_upgrade:
            meta_path = meta_path.split("/")[0]
        if not meta_path:
            return None
    try:
        meta_path = locator.locate(meta_path)
    except rose.resource.ResourceError:
        if not ignore_meta_error:
            sys.stderr.write(ERROR_LOAD_META_PATH.format(meta_path))
        return None
    return meta_path


def load_meta_config(config, directory=None):
    """Return the metadata config for a configuration."""
    meta_config = rose.config.ConfigNode()
    meta_list = ['etc/metadata/all/' + rose.META_CONFIG_NAME]
    config_meta_path = load_meta_path(config, directory)
    if config_meta_path is not None:
        path = os.path.join(config_meta_path, rose.META_CONFIG_NAME)
        if path not in meta_list:
            meta_list.append(path)
    locator = rose.resource.ResourceLocator(paths=sys.path)
    opt_node = config.get([rose.CONFIG_SECT_TOP,
                           rose.CONFIG_OPT_META_TYPE], no_ignore=True)
    ignore_meta_error = opt_node is None
    for meta_key in meta_list:
        try:
            meta_path = locator.locate(meta_key)
        except rose.resource.ResourceError:
            if not ignore_meta_error:
                sys.stderr.write(ERROR_LOAD_META_PATH.format(meta_path))
        else:
            try:
                meta_config = rose.config.load(meta_path, meta_config)
            except rose.config.SyntaxError as e:
                sys.stderr.write(ERROR_LOAD_METADATA.format(meta_path, e))
    return meta_config


def load_meta_macro_modules(meta_files):
    """Import metadata macros and return them in an array."""
    modules = []
    for meta_file in meta_files:
        meta_dir = os.path.dirname(meta_file)
        if (not meta_dir.endswith(MACRO_DIRNAME) or
            not meta_file.endswith(MACRO_EXT)):
            continue
        macro_name = os.path.basename(meta_file).rpartition(MACRO_EXT)[0]
        sys.path.append(os.path.abspath(meta_dir))
        try:
            modules.append(__import__(macro_name))
        except Exception as e:
            info = ERROR_LOAD_MACRO.format(meta_file, e)
            sys.stderr.write(info + "\n")
        sys.path.pop()
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
    meta_path = load_meta_path(app_config, config_directory)
    if meta_path is None:
        sys.stderr.write(ERROR_LOAD_METADATA)
        sys.exit(2)
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


def validate_config(app_config, meta_config, run_macro_list, modules,
                    macro_info_tuples):
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
            problem_list = macro_meth(app_config, meta_config)
            if problem_list:
                macro_problem_dict.update({macro_name: problem_list})
    return macro_problem_dict


def transform_config(config, meta_config, transformer_macro, modules,
                     macro_info_tuples):
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
        return macro_method(config, meta_config)
    return config, []


def pretty_format_config(config):
    """Improve configuration prettiness."""
    for keylist, node in config.walk():
        if len(keylist) == 2:
            scheme, option = keylist
            if ":" in scheme:
                scheme = scheme.split(":", 1)[0]
            try:
                scheme_module = getattr(rose.formats, scheme)
                pretty_format = getattr(scheme_module, "pretty_format")
            except AttributeError:
                continue
            values = rose.variable.array_split(node.value, ",")
            node.value = pretty_format(values)


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
    search_id = REC_ID_STRIP_DUPL.sub("", setting_id)
    no_modifier_id = REC_MODIFIER.sub("", search_id)
    if no_modifier_id != search_id:
        node = meta_config.get([no_modifier_id], no_ignore=True)
        if node is not None:
            metadata.update(dict([(o, n.value) for o, n
                                    in node.value.items()]))
            if rose.META_PROP_TITLE in metadata:
                metadata.pop(rose.META_PROP_TITLE)
    node = meta_config.get([search_id], no_ignore=True)
    if node is not None:
        metadata.update(dict([(o, n.value) for o, n
                                in node.value.items()]))
    if search_id != setting_id and rose.META_PROP_TITLE in metadata:
        # Individual items of an array should not steal its title
        metadata.pop(rose.META_PROP_TITLE)
    metadata.update({'id': setting_id})
    return metadata


def run_macros(app_config, meta_config, config_name, macro_names,
               opt_conf_dir, opt_all=False, opt_non_interactive=False,
               opt_output_dir=None, opt_validate_all=False,
               opt_quietness=False):
    """Run standard or custom macros for a configuration."""

    macro_tuples, modules = get_macros_for_config(
                  app_config, opt_conf_dir,
                  return_modules=True,
                  include_system=should_include_system)

    should_include_system = opt_all
    if macro_names:
        should_include_system = True

    # Add all validator macros to the run list if specified.
    if opt_validate_all:
        for module_name, class_name, method, help in macro_tuples:
            if method == VALIDATE_METHOD:
                macro_name = ".".join([module_name, class_name])
                macro_names.insert(0, macro_name)
        if not macro_names:
            sys.exit(0)
    
    # List all macros if none are given.
    if not macro_names:
        for module_name, class_name, method, help in macro_tuples:
            macro_name = ".".join([module_name, class_name])
            macro_id = MACRO_OUTPUT_ID.format(method.upper()[0], config_name,
                                              macro_name)
            if opt_quietness:
                print macro_id
            else:
                print macro_id
                for help_line in help.split("\n"):
                    print MACRO_OUTPUT_HELP.format(help_line)
        sys.exit(0)
    
    # Categorise macros given as arguments.
    macros_by_type = {}
    macros_not_found = [m for m in macro_names]
    for module_name, class_name, method, help in macro_tuples:
        this_macro_name = ".".join([module_name, class_name])
        if this_macro_name in macro_names:
            macros_by_type.setdefault(method, [])
            macros_by_type[method].append(this_macro_name)
            macros_not_found.remove(this_macro_name)
    for macro_name in macros_not_found:
        sys.stderr.write(ERROR_MACRO_NOT_FOUND.format(macro_name))
        RC = 1
    RC = 0
    
    # Run any validator macros.
    if VALIDATE_METHOD in macros_by_type:
        config_problem_dict = validate_config(app_config, meta_config,
                                              macros_by_type[VALIDATE_METHOD],
                                              modules,
                                              macro_tuples)
        if config_problem_dict:
            RC = 1
            if not opt_quietness:
                problem_macros = config_problem_dict.keys()
                problem_macros.sort()
                for macro_name in problem_macros:
                    problem_list = config_problem_dict[macro_name]
                    sort = rose.config.sort_settings
                    
                    problem_list.sort(lambda x, y: cmp(x.option, y.option))
                    problem_list.sort(lambda x, y: sort(x.section, y.section))
                    method_id = VALIDATE_METHOD.upper()[0]
                    macro_id = MACRO_OUTPUT_ID.format(method_id, config_name,
                                                      macro_name)
                    warnings = []
                    problems = []
                    for rep in problem_list:  # MacroReport instance
                        if rep.is_warning:
                            warnings.append(rep)
                            continue
                        problems.append(rep)
                    header = MACRO_OUTPUT_VALIDATE_ISSUES
                    header = header.format(macro_id, len(problems))
                    sys.stderr.write(header)
                    for rep in problems:
                        out = PROBLEM_ENTRY.format(rep.section, rep.option,
                                                   rep.value, rep.info)
                        sys.stderr.write(out)
                    if warnings:
                        header = MACRO_OUTPUT_WARNING_ISSUES
                        header = header.format(macro_id, len(warnings))
                        sys.stderr.write(header)
                    for rep in warnings:
                        out = PROBLEM_ENTRY.format(rep.section, rep.option,
                                                   rep.value, rep.info)
                        sys.stderr.write(out)

    # Run any transform macros.
    if TRANSFORM_METHOD in macros_by_type:
        _run_transform_macros(macros_by_type[TRANSFORM_METHOD],
                              config_name, app_config, meta_config, modules,
                              macro_tuples, summarise_all=False,
                              opt_non_interactive=False, opt_output_dir=None)


def _run_transform_macros(macros, config_name, app_config, meta_config,
                          modules, macro_tuples, opt_non_interactive=False,
                          opt_conf_dir=None, opt_output_dir=None):
    for transformer_macro in macros:
        user_allowed_changes = False
        macro_config = copy.deepcopy(app_config)
        new_config, change_list = transform_config(macro_config,
                                                   meta_config,
                                                   transformer_macro,
                                                   modules, macro_tuples)
        method_id = TRANSFORM_METHOD.upper()[0]
        macro_id = MACRO_OUTPUT_ID.format(method_id, config_name,
                                          transformer_macro)
        _handle_transform(app_config, new_config, change_list, macro_id,
                          opt_conf_dir, opt_output_dir, opt_non_interactive)


def run_upgrade_macros(app_config, meta_config, config_name, args,
                       opt_conf_dir, opt_downgrade, opt_non_interactive, 
                       opt_output_dir, opt_quietness):
    """CLI function to run upgrade/downgrade macros."""
    meta_opt_node = app_config.get([rose.CONFIG_SECT_TOP,
                                    rose.CONFIG_OPT_META_TYPE],
                                   no_ignore=True)
    if meta_opt_node is None or len(meta_opt_node.value.split("/")) < 2:
        sys.exit(ERROR_LOAD_CONF_META_NODE)
    upgrade_manager = MacroUpgradeManager(app_config, opt_downgrade)
    ok_versions = upgrade_manager.get_tags()
    ok_vn_text = " ".join(ok_versions)
    if not ok_versions:
        sys.exit(ERROR_NO_VALID_VERSIONS)
    if args:
        user_choice = args[0]
    elif opt_non_interactive:
        user_choice = upgrade_manager.get_new_tag()
    else:
        try:
            user_choice = raw_input(PROMPT_CHOOSE_VERSION.format(ok_vn_text))
        except EOFError:
            sys.exit(1)
        else:
            if not user_choice.strip():
                user_choice = upgrade_manager.get_new_tag()
    if user_choice not in ok_versions:
        sys.exit(ERROR_UPGRADE_VERSION.format(user_choice, ok_vn_text))
    upgrade_manager.set_new_tag(user_choice)
    macro_config = copy.deepcopy(app_config)
    new_config, change_list = upgrade_manager.transform(
                                      macro_config, meta_config)
    method_id = TRANSFORM_METHOD.upper()[0]
    macro_id = MACRO_OUTPUT_ID.format(method_id, config_name,
                                      upgrade_manager.get_name())
    _handle_transform(app_config, new_config, change_list, macro_id,
                      opt_conf_dir, opt_output_dir, opt_non_interactive)


def _handle_transform(app_config, new_config, change_list, macro_id,
                      opt_conf_dir, opt_output_dir, opt_non_interactive):
    user_allowed_changes = False
    if change_list:
        header = MACRO_OUTPUT_TRANSFORM_CHANGES
        sys.stdout.write(header.format(macro_id, len(change_list)))
        for rep in change_list:  # MacroReport instances
            out = TRANSFORM_CHANGE.format(
                        rep.section, rep.option, rep.value, rep.info)
            sys.stdout.write(out + "\n")
        if not opt_non_interactive:
            user_allowed_changes = _get_user_accept()
    else:
        user_allowed_changes = False
    if user_allowed_changes or opt_non_interactive:
        app_config = new_config
        dump_config(app_config, opt_conf_dir, opt_output_dir)
            

def _get_user_accept():
    try:
        user_input = raw_input(PROMPT_ACCEPT_CHANGES)
    except EOFError:
        user_allowed_changes = False
    else:
        user_allowed_changes = (user_input == PROMPT_OK)
    return user_allowed_changes


def dump_config(app_config, opt_conf_dir, opt_output_dir=None):
    pretty_format_config(app_config)
    if opt_output_dir is None:
        directory = opt_conf_dir
    else:
        directory = opt_output_dir
    file_path = os.path.join(directory, rose.SUB_CONFIG_NAME)
    rose.config.dump(app_config, file_path)


def main(mode):
    opt_parser = RoseOptionParser()
    options = ["conf_dir", "meta_path", "non_interactive", "output_dir"]
    if mode == "macro":
        options.extend(["all", "validate_all"])
    elif mode == "upgrade":
        options.extend(["downgrade"])
    else:
        raise KeyError("Wrong mode: {0}".format(mode))
    opt_parser.add_my_options(*options)
    opts, args = opt_parser.parse_args()
    if opts.conf_dir is None:
        opts.conf_dir = os.getcwd()
    sys.path.append(os.getenv("ROSE_HOME"))
    if opts.meta_path is not None:
        sys.path = opts.meta_path + sys.path
    config_name = os.path.basename((os.path.abspath(opts.conf_dir)))
    config_file_path = os.path.join(opts.conf_dir,
                                    rose.SUB_CONFIG_NAME)
    if (not os.path.exists(config_file_path) or
        not os.path.isfile(config_file_path)):
        sys.stderr.write(ERROR_LOAD_CONFIG_DIR.format(opts.conf_dir))
        sys.exit(2)
    # Load the configuration and the metadata macros.
    app_config = rose.config.load(config_file_path)
    standard_format_config(app_config)

    # Load meta config if it exists.
    meta_config = None
    meta_path = load_meta_path(app_config, opts.conf_dir)
    if meta_path is None:
        if mode == "macro":
            sys.stderr.write(ERROR_LOAD_METADATA)
            sys.exit(2)
    else:
        meta_config_path = os.path.join(meta_path, rose.META_CONFIG_NAME)
        if os.path.isfile(meta_config_path):
            meta_config = rose.config.load(meta_config_path)

    if mode == "macro":
        run_macros(app_config, meta_config, config_name, args,
                   opts.all, opts.conf_dir,
                   opts.non_interactive, opts.output_dir,
                   opts.validate_all, opts.quietness)
    else:
        if len(args) > 1:
            sys.exit(opt_parser.get_usage())
        run_upgrade_macros(app_config, meta_config, config_name, args,
                           opts.conf_dir, opts.downgrade,
                           opts.non_interactive,
                           opts.output_dir, opts.quietness)
    sys.exit(0)

if __name__ == "__main__":
    mode = None
    if len(sys.argv) > 1:
        mode = sys.argv.pop(1)
    main(mode)
