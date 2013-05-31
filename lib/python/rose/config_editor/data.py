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
"""This module contains:

VarData -- class to store rose.variable.Variable instances
SectData -- class to store rose.section.Section instances
ConfigData -- class to store and process a directory into internal
data structures
ConfigDataManager -- class to load and process objects in ConfigData

"""

import atexit
import copy
import itertools
import glob
import os
import re
import shutil
import sys
import tempfile

import rose.config
import rose.config_editor.data_helper
import rose.gtk.util
import rose.macro
import rose.metadata_check
import rose.resource
import rose.section
import rose.macros.trigger
import rose.variable


REC_NS_SECTION = re.compile(r"^(" + rose.META_PROP_NS + rose.CONFIG_DELIMITER +
                            r")(.*)$")


class VarData(object):

    """Stores past, present, and missing variables."""

    def __init__(self, v_map, latent_v_map, save_v_map, latent_save_v_map):
        self.now = v_map
        self.latent = latent_v_map
        self.save = save_v_map
        self.latent_save = latent_save_v_map

    def foreach(self, save=False, no_latent=False):
        """Yield all (section, variables) tuples for real and latent."""
        if save:
            real = self.save
            latent = self.latent_save
        else:
            real = self.now
            latent = self.latent
        for section, variables in real.items():
            yield section, variables
        if not no_latent:
            for section, variables in latent.items():
                yield section, variables

    def get_all(self, save=False, no_latent=False):
        """Return all real and latent variables."""
        if save:
            real = self.save
            latent = self.latent_save
        else:
            real = self.now
            latent = self.latent
        all_vars = list(itertools.chain(*real.values()))
        if not no_latent:
            all_vars += list(itertools.chain(*latent.values()))
        return all_vars

    def get_var(self, section, option, save=False, no_latent=False):
        """Return the variable specified by section, option."""
        var_id = section + rose.CONFIG_DELIMITER + option
        if save:
            nodes = [self.save, self.latent_save]
        else:
            nodes = [self.now, self.latent]
        if no_latent:
            nodes.pop()
        for node in nodes:
            for var in node.get(section, []):
                if var.metadata['id'] == var_id:
                    return var
        return None
                

class SectData(object):

    """Stores past, present, and missing sections."""

    def __init__(self, sections, latent_sections, save_sections,
                 latent_save_sections):
        self.now = sections
        self.latent = latent_sections
        self.save = save_sections
        self.latent_save = latent_save_sections

    def get_all(self, save=False, no_latent=False):
        """Return all sections that match the save/latent criteria."""
        if save:
            real = self.save
            latent = self.latent_save
        else:
            real = self.now
            latent = self.latent
        all_sections = real.values()
        if not no_latent:
            all_sections += latent.values()
        return all_sections

    def get_sect(self, section, save=False, no_latent=False):
        """Return the section data specified by section."""
        if save:
            nodes = [self.save, self.latent_save]
        else:
            nodes = [self.now, self.latent]
        if no_latent:
            nodes.pop()
        for node in nodes:
            if section in node:
                return node[section]
        return None


class ConfigData(object):

    """Stores information about a configuration."""

    def __init__(self, config, s_config, directory, opt_conf_lookup, meta,
                 meta_id, meta_files, macros, is_top, is_disc,
                 var_data=None, sect_data=None):
        self.config = config
        self.save_config = s_config
        self.directory = directory
        self.opt_configs = opt_conf_lookup
        self.meta = meta
        self.meta_id = meta_id
        self.meta_files = meta_files
        self.macros = macros
        self.is_top_level = is_top
        self.is_discovery = is_disc
        self.vars = var_data
        self.sections = sect_data


class ConfigDataManager(object):

    """Loads the information from the various configurations."""

    def __init__(self, util, reporter, page_ns_show_modes,
                 reload_ns_tree_func):
        """Load the root configuration and all its sub-configurations."""
        self.util = util
        self.helper = rose.config_editor.data_helper.ConfigDataHelper(
                                  self, util)
        self.reporter = reporter
        self.page_ns_show_modes = page_ns_show_modes
        self.reload_ns_tree_func = reload_ns_tree_func
        self.config = {}  # Stores configuration name: object
        self._builtin_value_macro = rose.macros.value.ValueChecker()  # value
        self.builtin_macros = {}  # Stores other Rose built-in macro instances
        self._bad_meta_dir_paths = []  # Stores flawed metadata directories.
        self.trigger = {}  # Stores trigger macro instances per configuration
        self.trigger_id_trees = {}  # Stores trigger dependencies
        self.trigger_id_value_lookup = {}  # Stores old values of trigger vars
        self.namespace_meta_lookup = {}  # Stores titles etc of namespaces
        self._config_section_namespace_lookup = {}  # Store section namespaces
        self.locator = rose.resource.ResourceLocator(paths=sys.path)

    def load(self, top_level_directory, config_obj_dict):
        if top_level_directory is not None:
            for filename in os.listdir(top_level_directory):
                if filename in [rose.TOP_CONFIG_NAME, rose.SUB_CONFIG_NAME]:
                    self.load_top_config(top_level_directory)
                    break
            else:
                self.load_top_config(None)
        elif not config_obj_dict:
            self.load_top_config(None)
        else:
            self.top_level_name = config_obj_dict.keys()[0]
            self.top_level_directory = None
        for name, obj in config_obj_dict.items():
            is_discovery = self.helper.get_config_is_discovery(obj)
            self.load_config(config_name=name, config=obj,
                             is_discovery=is_discovery)
        self.saved_config_names = set(self.config.keys())

    def load_top_config(self, top_level_directory):
        """Load the config at the top level and any sub configs."""
        self.top_level_directory = top_level_directory
        if top_level_directory is None:
            self.top_level_name = rose.config_editor.UNTITLED_NAME
        else:
            self.top_level_name = os.path.basename(top_level_directory)
            config_container_dir = os.path.join(top_level_directory,
                                                rose.SUB_CONFIGS_DIR)
            if os.path.isdir(config_container_dir):
                sub_contents = os.listdir(config_container_dir)
                sub_contents.sort()
                for config_dir in sub_contents:
                    conf_path = os.path.join(config_container_dir, config_dir)
                    if (os.path.isdir(conf_path) and
                        not config_dir.startswith('.')):
                        self.load_config(conf_path)
            self.load_config(top_level_directory)
            self.reload_ns_tree_func()

    def load_info_config(self, config_directory):
        """Load any information (discovery) config."""
        disc_path = os.path.join(config_directory,
                                 rose.INFO_CONFIG_NAME)
        if os.path.isfile(disc_path):
            config_obj, master_obj = self.load_config_file(disc_path)
            self.load_config(config_name="/" + self.top_level_name + "-info",
                             config=config_obj, is_discovery=True)

    def load_config(self, config_directory=None,
                    config_name=None, config=None,
                    reload_tree_on=False, is_discovery=False,
                    skip_load_event=False):
        """Load the configuration and meta-data. Load namespaces."""
        is_top_level = False
        if config_directory is None:
            name = "/" + config_name.lstrip("/")
            config = config
            s_config = copy.deepcopy(config)
            if not skip_load_event:
                self.reporter.report_load_event(
                              rose.config_editor.EVENT_LOAD_CONFIG.format(
                                                       name.lstrip("/")))
        else:
            config_directory = config_directory.rstrip("/")
            if config_directory != self.top_level_directory:
                # One of the sub configurations
                head, tail = os.path.split(config_directory)
                name = ''
                while tail != rose.SUB_CONFIGS_DIR:
                    name = "/" + os.path.join(tail, name).rstrip('/')
                    head, tail = os.path.split(head)
                name = "/" + name.lstrip("/")
            elif rose.TOP_CONFIG_NAME not in os.listdir(config_directory):
                # Just editing a single sub configuration, not a suite
                name = "/" + self.top_level_name
            else:
                # A suite configuration
                self.load_info_config(config_directory)
                name = "/" + self.top_level_name + "-conf"
            if not skip_load_event:
                self.reporter.report_load_event(
                              rose.config_editor.EVENT_LOAD_CONFIG.format(
                                                       name.lstrip("/")))
            config_path = os.path.join(config_directory, rose.SUB_CONFIG_NAME)
            if not os.path.isfile(config_path):
                if (os.path.abspath(config_directory) ==
                    os.path.abspath(self.top_level_directory)):
                    config_path = os.path.join(config_directory,
                                               rose.TOP_CONFIG_NAME)
                    is_top_level = True
                else:
                    text = rose.config_editor.ERROR_NOT_FOUND.format(
                                                              config_path)
                    title = rose.config_editor.DIALOG_TITLE_CRITICAL_ERROR
                    rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                             text, title)
                    sys.exit(2)
            config, s_config = self.load_config_file(config_path)
        opt_conf_lookup = self.load_optional_configs(config_directory)
        meta_config = self.load_meta_config(config, config_directory)
        meta_files = self.load_meta_files(config, config_directory)
        macro_module_prefix = self.helper.get_macro_module_prefix(name)
        macros = rose.macro.load_meta_macro_modules(
                      meta_files, module_prefix=macro_module_prefix)
        meta_id = self.helper.get_config_meta_flag(config)
        # Initialise configuration data object.
        self.config[name] = ConfigData(config, s_config, config_directory,
                                       opt_conf_lookup, meta_config,
                                       meta_id, meta_files, macros,
                                       is_top_level, is_discovery)
        self.load_builtin_macros(name)
        self.load_file_metadata(name)
        self.filter_meta_config(name)
        
        # Load section and variable data into the object.
        sects, l_sects = self.load_sections_from_config(name)
        s_sects, s_l_sects = self.load_sections_from_config(name)
        self.config[name].sections = SectData(sects, l_sects, s_sects,
                                              s_l_sects)
        var, l_var = self.load_vars_from_config(name)
        s_var, s_l_var = self.load_vars_from_config(name)
        self.config[name].vars = VarData(var, l_var, s_var, s_l_var)
        
        if not skip_load_event:
            self.reporter.report_load_event(
                          rose.config_editor.EVENT_LOAD_METADATA.format(
                                                        name.lstrip("/")))
        # Process namespaces and ignored statuses.
        self.load_node_namespaces(name)
        self.load_node_namespaces(name, from_saved=True)
        self.load_ignored_data(name)
        self.load_metadata_for_namespaces(name)
        if reload_tree_on:
            self.reload_ns_tree_func()

    def load_config_file(self, config_path):
        """Return two copies of the rose.config.ConfigNode at config_path."""
        try:
            config = rose.config.load(config_path)
        except rose.config.ConfigSyntaxError as e:
            text = rose.config_editor.ERROR_LOAD_SYNTAX.format(
                                                    config_path, e)
            title = rose.config_editor.DIALOG_TITLE_CRITICAL_ERROR
            rose.gtk.util.run_dialog(
                            rose.gtk.util.DIALOG_TYPE_ERROR,
                            text, title)
            sys.exit(2)
        else:
            master_config = rose.config.load(config_path)
        rose.macro.standard_format_config(config)
        rose.macro.standard_format_config(master_config)
        return config, master_config

    def load_optional_configs(self, config_directory):
        """Load any optional configurations."""
        opt_conf_lookup = {}
        if config_directory is None:
            return opt_conf_lookup
        opt_dir = os.path.join(config_directory, rose.config.OPT_CONFIG_DIR)
        if not os.path.isdir(opt_dir):
            return opt_conf_lookup
        opt_exceptions = {}
        opt_glob = os.path.join(opt_dir, rose.GLOB_OPT_CONFIG_FILE)
        for path in glob.glob(opt_glob):
            if os.access(path, os.F_OK | os.R_OK):
                name = re.search(rose.RE_OPT_CONFIG_FILE, path).group(1)
                try:
                    opt_config = rose.config.load(path)
                except Exception as e:
                    opt_exceptions.update({path: e})
                    continue
                opt_conf_lookup.update({name: opt_config})
        if opt_exceptions:
            err_text = ""
            err_format = rose.config_editor.ERROR_LOAD_OPT_CONFS_FORMAT
            for path in sorted(opt_exceptions):
                err = opt_exceptions[path]
                err_text += err_format.format(path, type(e).__name__, e)
            err_text = err_text.rstrip()
            text = rose.config_editor.ERROR_LOAD_OPT_CONFS.format(err_text)
            title = rose.config_editor.ERROR_LOAD_OPT_CONFS_TITLE
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     text, title=title, modal=False)
        return opt_conf_lookup

    def load_builtin_macros(self, config_name):
        """Load Rose builtin macros."""
        self.builtin_macros[config_name] = {
                     rose.META_PROP_COMPULSORY:
                     rose.macros.compulsory.CompulsoryChecker(),
                     rose.META_PROP_TYPE:
                     self._builtin_value_macro}

    def load_sections_from_config(self, config_name, save=False):
        """Return maps of section objects from the configuration."""
        sect_map = {}
        latent_sect_map = {}
        real_sect_ids = []
        if save:
            config = self.config[config_name].save_config
        else:
            config = self.config[config_name].config
        meta_config = self.config[config_name].meta
        items = config.value.items()
        for section, node in config.value.items():
            if not isinstance(node.value, dict):
                if "" in sect_map:
                    sect_map[""].options.append(section)
                    continue
                meta_data = self.helper.get_metadata_for_config_id(
                                            "", config_name)
                sect_map.update({"": rose.section.Section("", [section],
                                                          meta_data)})
                real_sect_ids.append("")
                continue
            meta_data = self.helper.get_metadata_for_config_id(section,
                                                               config_name)
            options = node.value.keys()
            sect_map.update({section: rose.section.Section(section, options,
                                                           meta_data)})
            sect_map[section].comments = list(node.comments)
            real_sect_ids.append(section)
            if node.is_ignored():
                reason = {}
                if (node.state ==
                    rose.config.ConfigNode.STATE_SYST_IGNORED):
                    reason = {rose.variable.IGNORED_BY_SYSTEM:
                              rose.config_editor.IGNORED_STATUS_CONFIG}
                elif (node.state ==
                      rose.config.ConfigNode.STATE_USER_IGNORED):
                    reason = {rose.variable.IGNORED_BY_USER:
                              rose.config_editor.IGNORED_STATUS_CONFIG}
                sect_map[section].ignored_reason.update(reason)
        if "" not in sect_map:
            # This always exists for a configuration.
            meta_data = self.helper.get_metadata_for_config_id("",
                                                               config_name)
            sect_map.update({"": rose.section.Section("", [], meta_data)})
            real_sect_ids.append("")
        for setting_id, sect_node in meta_config.value.items():
            if sect_node.is_ignored() or isinstance(sect_node.value, str):
                continue
            section, option = self.util.get_section_option_from_id(setting_id)
            if section in real_sect_ids:
                continue
            ignored_reason = {}
            meta_data = {}
            for prop_opt, opt_node in sect_node.value.items():
                if opt_node.is_ignored():
                    continue
                meta_data.update({prop_opt: opt_node.value})
            meta_data.update({'id': setting_id})
            if section not in ['ns', 'file:*']:
                latent_sect_map.update(
                      {section: rose.section.Section(section, [], meta_data)})
        return sect_map, latent_sect_map

    def load_vars_from_config(self, config_name, only_this_section=None,
                              save=False, update=False):
        """Return maps of variables from the configuration"""
        config_data = self.config[config_name]
        if save:
            config = config_data.save_config
            section_map = config_data.sections.save
            latent_section_map = config_data.sections.latent_save
        else:
            config = config_data.config
            section_map = config_data.sections.now
            latent_section_map = config_data.sections.latent
        meta_config = config_data.meta
        if update:
            if save:
                var_map = config_data.vars.save
                latent_var_map = config_data.vars.latent_save
            else:
                var_map = config_data.vars.now
                latent_var_map = config_data.vars.latent
        else:
            var_map = {}
            latent_var_map = {}
        meta_ns_ids = []
        real_var_ids = []
        basic_dupl_map = {}
        if only_this_section is None:
            key_nodes = config.walk()
        else:
            key_nodes = config.walk(keys=[only_this_section])
            self._load_dupl_sect_map(basic_dupl_map, only_this_section)
        for keylist, node in key_nodes:
            if len(keylist) < 2:
                self._load_dupl_sect_map(basic_dupl_map, keylist[0])
                continue
            section, option = keylist
            flags = self.load_option_flags(config_name, section, option)
            ignored_reason = {}
            if section_map[section].ignored_reason:
                ignored_reason.update({
                        rose.variable.IGNORED_BY_SECTION:
                        rose.config_editor.IGNORED_STATUS_CONFIG})
            if (node.state ==
                rose.config.ConfigNode.STATE_SYST_IGNORED):
                ignored_reason.update({
                        rose.variable.IGNORED_BY_SYSTEM:
                        rose.config_editor.IGNORED_STATUS_CONFIG})
            elif (node.state ==
                  rose.config.ConfigNode.STATE_USER_IGNORED):
                ignored_reason.update({
                        rose.variable.IGNORED_BY_USER:
                        rose.config_editor.IGNORED_STATUS_CONFIG})
            cfg_comments = node.comments
            var_id = self.util.get_id_from_section_option(section, option)
            real_var_ids.append(var_id)
            meta_data = self.helper.get_metadata_for_config_id(var_id,
                                                               config_name)
            var_map.setdefault(section, [])
            if update:
                id_list = [v.metadata['id'] for v in var_map[section]]
                if var_id in id_list:
                    for i, var in enumerate(var_map[section]):
                        if var.metadata['id'] == var_id:
                            var_map[section].pop(i)
                            break
            var_map[section].append(rose.variable.Variable(
                                                  option,
                                                  node.value,
                                                  meta_data,
                                                  ignored_reason,
                                                  error={},
                                                  flags=flags,
                                                  comments=cfg_comments))
        id_node_stack = meta_config.value.items()
        while id_node_stack:
            setting_id, sect_node = id_node_stack.pop(0)
            if sect_node.is_ignored() or isinstance(sect_node.value, str):
                continue
            section, option = self.util.get_section_option_from_id(setting_id)
            if section in basic_dupl_map:
                # There is a matching duplicate e.g. foo(3) or foo{bar}(1)
                for dupl_section in basic_dupl_map[section]:
                    dupl_id = self.util.get_id_from_section_option(
                                               dupl_section, option)
                    id_node_stack.insert(0, (dupl_id, sect_node))
                continue
            if (only_this_section is not None and
                section != only_this_section):
                continue
            flags = self.load_option_flags(config_name, section, option)
            ignored_reason = {}
            sect_data = section_map.get(section)
            if sect_data is None:
                sect_data = latent_section_map.get(section)
            if sect_data is not None and sect_data.ignored_reason:
                ignored_reason = {
                        rose.variable.IGNORED_BY_SECTION:
                        rose.config_editor.IGNORED_STATUS_CONFIG}
            meta_data = {}
            for prop_opt, opt_node in sect_node.value.items():
                if opt_node.is_ignored():
                    continue
                meta_data.update({prop_opt: opt_node.value})
            meta_data.update({'id': setting_id})
            if setting_id in real_var_ids:
                # This variable isn't missing, so skip.
                continue
            if option is not None and section not in ['ns', 'file:*']:
                value = rose.variable.get_value_from_metadata(meta_data)
                latent_var_map.setdefault(section, [])
                if update:
                    id_list = [v.metadata['id'] for v in
                               latent_var_map[section]]
                    if setting_id in id_list:
                        for var in latent_var_map[section]:
                            if var.metadata['id'] == setting_id:
                                latent_var_map[section].remove(var)
                latent_var_map[section].append(
                                rose.variable.Variable(
                                               option,
                                               value,
                                               meta_data,
                                               ignored_reason,
                                               error={},
                                               flags=flags))
        return var_map, latent_var_map

    def _load_dupl_sect_map(self, basic_dupl_map, section):
        basic_section = rose.macro.REC_ID_STRIP.sub("", section)
        if basic_section != section:
            basic_dupl_map.setdefault(basic_section, [])
            basic_dupl_map[basic_section].append(section)
            mod_section = rose.macro.REC_ID_STRIP_DUPL.sub("", section)
            if mod_section != basic_section and mod_section != section:
                basic_dupl_map.setdefault(mod_section, [])
                basic_dupl_map[mod_section].append(section)

    def load_option_flags(self, config_name, section, option):
        """Load flags for an option."""
        config_data = self.config[config_name]
        flags = {}
        opt_conf_flags = self._load_opt_conf_flags(config_name,
                                                   section, option)
        if opt_conf_flags:
            flags.update({rose.config_editor.FLAG_TYPE_OPT_CONF:
                          opt_conf_flags})
        return flags

    def _load_opt_conf_flags(self, config_name, section, option):
        opt_config_map = self.config[config_name].opt_configs
        opt_conf_diff_format = rose.config_editor.VAR_FLAG_TIP_OPT_CONF_STATE
        opt_flags = {}
        for opt_name in sorted(opt_config_map):
            opt_config = opt_config_map[opt_name]
            opt_node = opt_config.get([section, option])
            if opt_node is not None:
                opt_sect_node = opt_config.get([section])
                text = opt_conf_diff_format.format(opt_sect_node.state,
                                                    section,
                                                    opt_node.state,
                                                    option,
                                                    opt_node.value)
                opt_flags[opt_name] = text
        return opt_flags

    def add_section_to_config(self, section, config_name):
        """Add a blank section to the configuration."""
        self.config[config_name].config.set([section])

    def dump_to_internal_config(self, config_name, only_this_ns=None):
        """Return a rose.config.ConfigNode object from variable info."""
        config = rose.config.ConfigNode()
        var_map = self.config[config_name].vars.now
        sect_map = self.config[config_name].sections.now
        user_ignored_state = rose.config.ConfigNode.STATE_USER_IGNORED
        syst_ignored_state = rose.config.ConfigNode.STATE_SYST_IGNORED
        enabled_state = rose.config.ConfigNode.STATE_NORMAL
        sections_to_be_dumped = []
        if only_this_ns is None:
            allowed_sections = set(sect_map.keys() + var_map.keys())
        else:
            allowed_sections = self.helper.get_sections_from_namespace(
                                                             only_this_ns)
        for section in sect_map:
            if (only_this_ns is not None and
                section not in allowed_sections):
                continue
            sections_to_be_dumped.append(section)
        for section in allowed_sections:
            variables = var_map.get(section, [])
            for variable in variables:
                if only_this_ns is not None:
                    if variable.metadata['full_ns'] != only_this_ns:
                        continue
                option = variable.name
                if not variable.name:
                    var_id = variable.metadata["id"]
                    option = self.util.get_section_option_from_id(var_id)[1]
                value = variable.value
                var_state = enabled_state
                if variable.ignored_reason:
                    if rose.variable.IGNORED_BY_USER in variable.ignored_reason:
                        var_state = user_ignored_state
                    elif (rose.variable.IGNORED_BY_SYSTEM in
                          variable.ignored_reason):
                        var_state = syst_ignored_state
                var_comments = variable.comments
                config.set([section, option], value,
                            state=var_state,
                            comments=var_comments)
        for section_id in sections_to_be_dumped:
            comments = sect_map[section_id].comments
            if not section_id:
                config.comments = list(comments)
                continue
            section_state = enabled_state
            if sect_map[section_id].ignored_reason:
                if (rose.variable.IGNORED_BY_USER in
                    sect_map[section_id].ignored_reason):
                    section_state = user_ignored_state
                elif (rose.variable.IGNORED_BY_SYSTEM in
                      sect_map[section_id].ignored_reason):
                    section_state = syst_ignored_state
            node = config.get([section_id])
            if node is None:
                config.set([section_id], state=section_state)
                node = config.get([section_id])
            else:
                node.state = section_state
            node.comments = list(comments)
        return config

    def load_meta_path(self, config=None, directory=None):
        """Retrieve the path to the metadata."""
        return rose.macro.load_meta_path(config, directory)

    def clear_meta_lookups(self, config_name):
        for ns in self.namespace_meta_lookup.keys():
            if (ns.startswith(config_name) and
                self.util.split_full_ns(self, ns)[0] == config_name):
                self.namespace_meta_lookup.pop(ns)
        if config_name in self._config_section_namespace_lookup:
            self._config_section_namespace_lookup.pop(config_name)

    def load_meta_config(self, config=None, directory=None):
        """Load the main metadata, and any specified in 'config'."""
        if config is None:
            config = rose.config.ConfigNode()
        error_handler = rose.config_editor.util.launch_error_dialog
        return rose.macro.load_meta_config(config, directory,
                                           error_handler)

    def load_meta_files(self, config=None, directory=None):
        """Load the file paths of files within the metadata directory."""
        if config is None:
            config = rose.config.ConfigNode()
        meta_filepaths = []
        meta_path, warning = self.load_meta_path(config, directory)
        if meta_path is None:
            return []
        try:
            file_tuples = os.walk(meta_path)
        except OSError:
            return []
        for dirpath, dirnames, filenames in file_tuples:
            if '/.' in dirpath:
                continue
            for fname in filenames:
                meta_filepaths.append(os.path.join(dirpath, fname))
        return meta_filepaths

    def filter_meta_config(self, config_name):
        """Filter out invalid metadata e.g. app metadata for suite configs."""
        # TODO: Remove after different default metadata for different configs
        config_data = self.config[config_name]
        config = config_data.config
        meta_config = config_data.meta
        directory = config_data.directory
        if config_data.is_top_level:
            good_id_prefixes = rose.TOP_CONFIG_DEFAULT_META_IDS
            bad_id_prefixes = (rose.INFO_CONFIG_DEFAULT_META_IDS +
                               rose.SUB_CONFIG_DEFAULT_META_IDS)
        elif config_data.is_discovery:
            good_id_prefixes = rose.INFO_CONFIG_DEFAULT_META_IDS
            bad_id_prefixes = (rose.SUB_CONFIG_DEFAULT_META_IDS +
                               rose.TOP_CONFIG_DEFAULT_META_IDS)
        else:
            good_id_prefixes = rose.SUB_CONFIG_DEFAULT_META_IDS
            bad_id_prefixes = (rose.INFO_CONFIG_DEFAULT_META_IDS +
                               rose.TOP_CONFIG_DEFAULT_META_IDS)
        for key in good_id_prefixes:
            if key in bad_id_prefixes:
                bad_id_prefixes.remove(key)
            for bad_key in list(bad_id_prefixes):
                if bad_key.startswith(key):
                    bad_id_prefixes.remove(bad_key)
        for key in meta_config.value.keys():
            for bad_key in bad_id_prefixes:
                if key.startswith(bad_key):
                    meta_config.value.pop(key)
                    break
        meta_dir_path = self.load_meta_path(config, directory)[0]
        reports = rose.metadata_check.metadata_check(meta_config,
                                                     directory)
        if reports and meta_dir_path not in self._bad_meta_dir_paths:
            # There are problems with some metadata.
            title = rose.config_editor.ERROR_METADATA_CHECKER_TITLE.format(
                                                      meta_dir_path)
            text = rose.config_editor.ERROR_METADATA_CHECKER_TEXT.format(
                                            len(reports), meta_dir_path)
            self._bad_meta_dir_paths.append(meta_dir_path)
            reports_text = rose.macro.get_reports_as_text(
                                      reports,
                                      "rose.metadata_check.MetadataChecker")
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     text, title, modal=False,
                                     extra_text=reports_text)
        for report in reports:
            meta_config.unset([report.section, report.option])

    def load_ignored_data(self, config_name):
        """Deal with ignored variables and sections.

        In particular, this assigns errors based on incorrect ignore
        state.

        'Doc table' in the comments refers to
        doc/rose-configuration.html#appendix-ignored-config-edit

        """
        self.trigger[config_name] = rose.macros.trigger.TriggerMacro()
        config = self.config[config_name].config
        sect_map = self.config[config_name].sections.now
        latent_sect_map = self.config[config_name].sections.latent
        var_map = self.config[config_name].vars.now
        latent_var_map = self.config[config_name].vars.latent
        config_for_macro = rose.config.ConfigNode()
        enabled_state = rose.config.ConfigNode.STATE_NORMAL
        user_ignored_state = rose.config.ConfigNode.STATE_USER_IGNORED
        syst_ignored_state = rose.config.ConfigNode.STATE_SYST_IGNORED
        # Deliberately reset state information in the macro config.
        for keylist, node in config.walk():
            if len(keylist) == 1 and node.value.keys():
                # Setting non-empty section info would overwrite options.
                continue
            config_for_macro.set(keylist, copy.deepcopy(node.value))
        meta_config = self.config[config_name].meta
        bad_list = self.trigger[config_name].validate(config_for_macro,
                                                      meta_config)
        if bad_list:
            self.trigger[config_name].trigger_family_lookup.clear()
            return
        trig_config, change_list = self.trigger[config_name].transform(
                                        config_for_macro, meta_config)
        self.trigger_id_value_lookup.setdefault(config_name, {})
        var_id_map = {}
        for variables in var_map.values():
            for variable in variables:
                var_id_map.update({variable.metadata['id']: variable})
        latent_var_id_map = {}
        for variables in latent_var_map.values():
             for variable in variables:
                 latent_var_id_map.update({variable.metadata['id']: variable})
        trig_ids = self.trigger[config_name].trigger_family_lookup.keys()
        while trig_ids:
            var_id = trig_ids.pop()
            var = var_id_map.get(var_id)
            if var is None:
                value = None
            else:
                value = var.value
            self.trigger_id_value_lookup[config_name].update(
                                  {var_id: value})
            sect, opt = self.util.get_section_option_from_id(var_id)
            if sect.endswith(")"):
                continue
            node = meta_config.get([sect, rose.META_PROP_DUPLICATE])
            if node is not None and node.value == rose.META_PROP_VALUE_TRUE:
                search_string = sect + "("
                for section in sect_map:
                    if section.startswith(search_string):
                        new_id = self.util.get_id_from_section_option(
                                                               section, opt)
                        trig_ids.append(new_id)
        id_node_map = {}
        id_node_map.update(sect_map)
        id_node_map.update(latent_sect_map)
        id_node_map.update(var_id_map)
        id_node_map.update(latent_var_id_map)
        ignored_dict = self.trigger[config_name].ignored_dict
        enabled_dict = self.trigger[config_name].enabled_dict
        for setting_id, node_inst in id_node_map.items():
            is_latent = False
            section, option = self.util.get_section_option_from_id(setting_id)
            is_section = (option is None)
            if is_section:
                if section not in sect_map:
                    is_latent = True
            else:
                if setting_id not in var_id_map:
                    is_latent = True
            trig_cfg_node = trig_config.get([section, option])
            if trig_cfg_node is None:
                # Latent variable or sections cannot be user-ignored.
                if (setting_id in ignored_dict and
                    setting_id not in enabled_dict):
                    trig_cfg_state = syst_ignored_state
                else:
                    trig_cfg_state = enabled_state
            else:
                trig_cfg_state = trig_cfg_node.state
            if (trig_cfg_state == enabled_state and
                not node_inst.ignored_reason):
                # For speed, skip the rest of the checking.
                # Doc table: E -> E
                continue
            comp_val = node_inst.metadata.get(rose.META_PROP_COMPULSORY)
            node_is_compulsory = comp_val == rose.META_PROP_VALUE_TRUE
            ignored_reasons = node_inst.ignored_reason.keys()
            if trig_cfg_state == syst_ignored_state:
                # It should be trigger-ignored.
                # Doc table: * -> I_t
                info = ignored_dict.get(setting_id)
                if rose.variable.IGNORED_BY_SYSTEM not in ignored_reasons:
                    help_str = ", ".join(info.values())
                    if rose.variable.IGNORED_BY_USER in ignored_reasons:
                        # It is user-ignored but should be trigger-ignored.
                        # Doc table: I_u -> I_t
                        if node_is_compulsory:
                            # Doc table: I_u -> I_t -> compulsory
                            key = rose.config_editor.WARNING_TYPE_USER_IGNORED
                            val = getattr(rose.config_editor,
                                          "WARNING_USER_NOT_TRIGGER_IGNORED")
                            node_inst.warning.update({key: val})
                        else:
                            # Doc table: I_u -> I_t -> optional
                            pass
                    else:
                        # It is not ignored at all.
                        # Doc table: E -> I_t
                        if is_latent:
                            # Fix this for latent settings.
                            node_inst.ignored_reason.update(
                                 {rose.variable.IGNORED_BY_SYSTEM:
                                  rose.config_editor.IGNORED_STATUS_CONFIG})
                        else:
                            # Flag an error for real settings.
                            node_inst.error.update(
                                 {rose.config_editor.WARNING_TYPE_ENABLED:
                                  (rose.config_editor.WARNING_NOT_IGNORED +
                                   help_str)})
                else:
                    # Otherwise, they both agree about trigger-ignored.
                    # Doc table: I_t -> I_t
                    pass
            elif rose.variable.IGNORED_BY_SYSTEM in ignored_reasons:
                # It should be enabled, but is trigger-ignored.
                # Doc table: I_t
                if (setting_id in enabled_dict and
                    setting_id not in ignored_dict):
                    # It is a valid trigger.
                    # Doc table: I_t -> E
                    parents = self.trigger[config_name].enabled_dict.get(
                                                                setting_id)
                    help_str = (rose.config_editor.WARNING_NOT_ENABLED + 
                                ', '.join(parents))
                    err_type = rose.config_editor.WARNING_TYPE_TRIGGER_IGNORED
                    node_inst.error.update({err_type: help_str})
                elif (setting_id not in enabled_dict and
                      setting_id not in ignored_dict):
                    # It is not a valid trigger.
                    # Doc table: I_t -> not trigger
                    if node_is_compulsory:
                        # This is an error for compulsory variables.
                        # Doc table: I_t -> not trigger -> compulsory
                        help_str = rose.config_editor.WARNING_NOT_TRIGGER
                        err_type = rose.config_editor.WARNING_TYPE_NOT_TRIGGER
                        node_inst.error.update({err_type: help_str})
                    else:
                        # Overlook for optional variables.
                        # Doc table: I_t -> not trigger -> optional
                        pass
            elif rose.variable.IGNORED_BY_USER in ignored_reasons:
                # It possibly should be enabled, but is user-ignored.
                # Doc table: I_u
                # We've already covered I_u -> I_t
                if node_is_compulsory:
                    # Compulsory settings should not be user-ignored.
                    # Doc table: I_u -> E -> compulsory
                    # Doc table: I_u -> not trigger -> compulsory
                    help_str = rose.config_editor.WARNING_NOT_USER_IGNORABLE
                    err_type = rose.config_editor.WARNING_TYPE_USER_IGNORED
                    node_inst.error.update({err_type: help_str})
            # Remaining possibilities are not a problem:
            # Doc table: E -> E, E -> not trigger

    def load_file_metadata(self, config_name, section_name=None):
        """Deal with file section variables."""
        if section_name is not None and not section_name.startswith("file:"):
            return False
        config = self.config[config_name].config
        meta_config = self.config[config_name].meta
        file_sections = []
        for section, sect_node in config.value.items():
            if not isinstance(sect_node.value, dict):
                continue
            if not sect_node.is_ignored() and section.startswith("file:"):
                file_sections.append(section)
        file_ids = []
        for setting_id, sect_node in meta_config.value.items():
            # The following 'wildcard-esque' id is an exception.
            # Wildcards are not supported in Rose metadata.
            if (not sect_node.is_ignored() and 
                setting_id.startswith("file:*=")):
                file_ids.append(setting_id)
        for section in file_sections:
            for file_entry in file_ids:
                sect_node = meta_config.get([file_entry])
                for meta_prop, opt_node in sect_node.value.items():
                    if opt_node.is_ignored():
                        continue
                    prop_val = opt_node.value
                    new_id = section + '=' + file_entry.replace(
                                                        'file:*=', '', 1)
                    if meta_config.get([new_id, meta_prop]) is None:
                        meta_config.set([new_id, meta_prop], prop_val)

    def load_node_namespaces(self, config_name, only_this_section=None,
                             from_saved=False):
        """Load namespaces for variables and sections."""
        config_sections = self.config[config_name].sections
        config_vars = self.config[config_name].vars
        for section, variables in config_vars.foreach(from_saved):
            if (only_this_section is not None and
                section != only_this_section):
                continue
            for variable in variables:
                self.load_ns_for_node(variable, config_name)
        section_objects = []
        if only_this_section is not None:
            if only_this_section in config_sections.now:
                section_objects = [config_sections.now[only_this_section]]
            elif only_this_section in config_sections.latent:
                section_objects = [config_sections.latent[only_this_section]]
        else:
            section_objects = config_sections.get_all(save=from_saved)
        for sect_obj in section_objects:
            self.load_ns_for_node(sect_obj, config_name)
        
    def load_ns_for_node(self, node, config_name):
        """Load a namespace for a variable or section."""
        meta_config = self.config[config_name].meta
        node_id = node.metadata.get('id')
        section, option = self.util.get_section_option_from_id(node_id)
        subspace = node.metadata.get(rose.META_PROP_NS)
        if subspace is None or option is None:
            new_namespace = self.helper.get_default_namespace_for_section(
                                             section, config_name)
        else:
            new_namespace = config_name + '/' + subspace
        if new_namespace == config_name + '/':
            new_namespace = config_name
        node.metadata['full_ns'] = new_namespace
        return new_namespace

    def load_metadata_for_namespaces(self, config_name):
        """Load namespace metadata, e.g. namespace titles."""
        config_data = self.config[config_name]
        meta_config = config_data.meta
        for section, sect_node in meta_config.value.items():
            if sect_node.is_ignored():
                continue
            ns_match = REC_NS_SECTION.match(section)
            if ns_match is not None:
                base, subspace = ns_match.groups()
                if subspace:
                    namespace = config_name + "/" + subspace
                else:
                    namespace = config_name
                self.namespace_meta_lookup.setdefault(namespace, {})
                ns_metadata = self.namespace_meta_lookup[namespace]
                for option, opt_node in sect_node.value.items():
                    if opt_node.is_ignored():
                        continue
                    value = meta_config[section][option].value
                    if option == rose.META_PROP_MACRO:
                        if option in ns_metadata:
                            ns_metadata[option] += ", " + value
                        else:
                            ns_metadata[option] = value
                    else:
                        ns_metadata.update({option: value})
        ns_sections = {}  # Namespace-sections key value pairs.
        for variable in config_data.vars.get_all():
            ns = variable.metadata['full_ns']
            var_id = variable.metadata['id']
            sect, opt = self.util.get_section_option_from_id(var_id)
            ns_sections.setdefault(ns, [])
            if sect not in ns_sections[ns]:
                ns_sections[ns].append(sect)
            if rose.META_PROP_MACRO in variable.metadata:
                macro_info = variable.metadata[rose.META_PROP_MACRO]
                self.namespace_meta_lookup.setdefault(ns, {})
                ns_metadata = self.namespace_meta_lookup[ns]
                if rose.META_PROP_MACRO in ns_metadata:
                    ns_metadata[rose.META_PROP_MACRO] += ", " + macro_info
                else:
                    ns_metadata[rose.META_PROP_MACRO] = macro_info
        default_ns_sections = {}
        for section_data in config_data.sections.get_all():
            # Use the default section namespace.
            ns = section_data.metadata["full_ns"]
            ns_sections.setdefault(ns, [])
            if section_data.name not in ns_sections[ns]:
                ns_sections[ns].append(section_data.name)
            default_ns_sections.setdefault(ns, [])
            if section_data.name not in default_ns_sections[ns]:
                default_ns_sections[ns].append(section_data.name)
        for ns in ns_sections:
            self.namespace_meta_lookup.setdefault(ns, {})
            ns_metadata = self.namespace_meta_lookup[ns]
            ns_metadata['sections'] = ns_sections[ns]
            for ns_section in ns_sections[ns]:
                # Loop over metadata from contributing sections.
                # Note: rogue-variable section metadata can be overridden.
                metadata = self.helper.get_metadata_for_config_id(ns_section,
                                                                  config_name)
                for key, value in metadata.items():
                    if (ns_section not in default_ns_sections.get(ns, []) and
                        key in [rose.META_PROP_TITLE,
                                rose.META_PROP_DESCRIPTION]):
                        # ns created from variables, not a section - no title.
                        continue
                    if key == rose.META_PROP_MACRO:
                        if key in ns_metadata:
                            ns_metadata[rose.META_PROP_MACRO] += ", " + macro_info
                        else:
                            ns_metadata[rose.META_PROP_MACRO] = macro_info
                    else:
                        ns_metadata.setdefault(key, value)
        self.load_namespace_has_sub_data(config_name)
        for config_name in self.config.keys():
            icon_path = self.helper.get_icon_path_for_config(config_name)
            self.namespace_meta_lookup.setdefault(config_name, {})
            self.namespace_meta_lookup[config_name].setdefault(
                                                    "icon", icon_path)
            if self.config[config_name].is_top_level:
                self.namespace_meta_lookup[config_name].setdefault(
                                    rose.META_PROP_TITLE,
                                    rose.config_editor.TITLE_PAGE_SUITE)
                self.namespace_meta_lookup[config_name].setdefault(
                                                  rose.META_PROP_SORT_KEY,
                                                  " 1")
            elif self.config[config_name].is_discovery:
                self.namespace_meta_lookup[config_name].setdefault(
                                    rose.META_PROP_TITLE,
                                    rose.config_editor.TITLE_PAGE_INFO)
                self.namespace_meta_lookup[config_name].setdefault(
                                                  rose.META_PROP_SORT_KEY,
                                                  " 0")
    def load_namespace_has_sub_data(self, config_name=None):
        """Load namespace sub-data status."""
        file_ns = "/" + rose.SUB_CONFIG_FILE_DIR
        file_ns_sub = file_ns + "/"
        ns_hierarchy = {}
        for ns in self.namespace_meta_lookup:
            if config_name is None or ns.startswith(config_name):
                parent_ns = ns.rsplit("/", 1)[0]
                ns_hierarchy.setdefault(parent_ns, [])
                ns_hierarchy[parent_ns].append(ns)
        for ns, prop_map in self.namespace_meta_lookup.items():
            if config_name is None or ns.startswith(config_name):
                if file_ns_sub in ns:
                    title = re.sub(".*" + file_ns_sub, "", ns)
                    prop_map.setdefault(rose.META_PROP_TITLE,
                                        title.replace(":", "/"))
                elif ns.endswith(file_ns):
                    prop_map.setdefault("has_sub_data", True)
                elif (rose.META_PROP_DUPLICATE in prop_map and
                    ns_hierarchy.get(ns, [])):
                    prop_map.setdefault("has_sub_data", True)
