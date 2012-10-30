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
"""This module contains:

ConfigData -- class to store and process a directory into internal
data structures

"""

import atexit
import copy
import itertools
import os
import re
import shutil
import sys
import tempfile

import rose.config
import rose.gtk.util
import rose.macro
import rose.resource
import rose.section
import rose.macros.trigger
import rose.variable


REC_NS_SECTION = re.compile(r"^(" + rose.META_PROP_NS + rose.CONFIG_DELIMITER +
                            r")(.*)$")
REC_ELEMENT_SECTION = re.compile(r"^(.*)\((\d*)\)$")


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


class ConfigData(object):

    """Stores information about a configuration."""

    def __init__(self, config, s_config, directory, meta, meta_id, meta_files,
                 macros, is_top, is_disc, var_data=None, sect_data=None):
        self.config = config
        self.save_config = s_config
        self.directory = directory
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

    def __init__(self, util, top_level_directory, config_obj_dict,
                 tree_trig_update, signal_load_event):
        """Load the root configuration and all its sub-configurations."""
        self.util = util
        self.tree_update = tree_trig_update
        self.signal_load_event = signal_load_event
        self.config = {}  # Stores configuration name: object
        self.trigger = {}  # Stores trigger macro instances per configuration
        self.trigger_id_trees = {}  # Stores trigger dependencies
        self.trigger_id_value_lookup = {}  # Stores old values of trigger vars
        self.namespace_tree = {}  # Stores the namespace hierarchy
        self.namespace_meta_lookup = {}  # Stores titles etc of namespaces
        self.locator = rose.resource.ResourceLocator(paths=sys.path)
        if top_level_directory is not None:
            for filename in os.listdir(top_level_directory):
                if filename in [rose.TOP_CONFIG_NAME, rose.SUB_CONFIG_NAME]:
                    self.load_top_config(top_level_directory)
                    break
            else:
                path = os.path.join(top_level_directory, rose.TOP_CONFIG_NAME)
                text = rose.config_editor.ERROR_NOT_FOUND.format(path)
                title = rose.config_editor.DIALOG_TITLE_CRITICAL_ERROR
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                         text, title)
                sys.exit(2)
        elif not config_obj_dict:
            self.load_top_config(None)
        else:
            self.top_level_name = config_obj_dict.keys()[0]
            self.top_level_directory = None
        for name, obj in config_obj_dict.items():
            is_discovery = self.get_config_is_discovery(obj)
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
            self.reload_namespace_tree()

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
                    reload_tree_on=False, is_discovery=False):
        """Load the configuration and meta-data. Load namespaces."""
        is_top_level = False
        if config_directory is None:
            name = "/" + config_name.lstrip("/")
            config = config
            s_config = copy.deepcopy(config)
            self.signal_load_event(rose.config_editor.LOAD_CONFIG,
                                   name.lstrip("/"))
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
            self.signal_load_event(rose.config_editor.LOAD_CONFIG,
                                   name.lstrip("/"))
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
        meta_config = self.load_meta_config(config, config_directory)
        meta_files = self.load_meta_files(config, config_directory)
        macros = rose.macro.load_meta_macro_modules(meta_files)
        meta_id = self.get_config_meta_flag(config)
        
        # Initialise configuration data object.
        self.config[name] = ConfigData(config, s_config, config_directory,
                                       meta_config, meta_id, meta_files,
                                       macros, is_top_level, is_discovery)
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
        
        # Process namespaces and ignored statuses.
        self.load_variable_namespaces(name)
        self.load_variable_namespaces(name, from_saved=True)
        self.load_ignored_data(name)
        self.load_metadata_for_namespaces(name)
        self.signal_load_event(rose.config_editor.LOAD_METADATA,
                               name.lstrip("/"))
        if reload_tree_on:
            self.reload_namespace_tree()

    def load_config_file(self, config_path):
        """Return two copies of the rose.config.ConfigNode at config_path."""
        try:
            config = rose.config.load(config_path)
        except rose.config.SyntaxError as e:
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
                meta_data = self.get_metadata_for_config_id("", config_name)
                sect_map.update({"": rose.section.Section("", [section],
                                                          meta_data)})
                real_sect_ids.append("")
                continue
            meta_data = self.get_metadata_for_config_id(section, config_name)
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
            meta_data = self.get_metadata_for_config_id("", config_name)
            sect_map.update({"": rose.section.Section("", [], meta_data)})
            real_sect_ids.append("")
        for setting_id, sect_node in meta_config.value.items():
            if sect_node.is_ignored():
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

    def load_vars_from_config(self, config_name, save=False):
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
        var_map = {}
        latent_var_map = {}
        meta_ns_ids = []
        real_var_ids = []
        for keylist, node in config.walk():
            if len(keylist) < 2:
                continue
            section, option = keylist
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
            meta_data = self.get_metadata_for_config_id(var_id, config_name)
            var_map.setdefault(section, [])
            var_map[section].append(rose.variable.Variable(
                                                  option,
                                                  node.value,
                                                  meta_data,
                                                  ignored_reason,
                                                  error={},
                                                  comments=cfg_comments))
        for setting_id, sect_node in meta_config.value.items():
            if sect_node.is_ignored():
                continue
            section, option = self.util.get_section_option_from_id(setting_id)
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
                latent_var_map[section].append(
                                rose.variable.Variable(
                                               option,
                                               value,
                                               meta_data,
                                               ignored_reason,
                                               error={}))
        return var_map, latent_var_map

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
            allowed_sections = sect_map.keys()
        else:
            allowed_sections = self.get_sections_from_namespace(only_this_ns)
        for section, sect_data in sect_map.items():
            if (only_this_ns is not None and
                section not in allowed_sections):
                continue
            sections_to_be_dumped.append(section)
        for section in allowed_sections:
            variables = var_map.get(section, [])
            for variable in variables:
                var_id = variable.metadata.get('id')
                if only_this_ns is not None:
                    if variable.metadata['full_ns'] != only_this_ns:
                        continue
                section, option = self.util.get_section_option_from_id(var_id)
                if section not in sections_to_be_dumped:
                    sections_to_be_dumped.append(section)
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
        if config is None:
            config = rose.config.ConfigNode()
        if directory is not None:
            config_meta_dir = os.path.join(directory, rose.CONFIG_META_DIR)
            if os.path.isdir(config_meta_dir):
                return config_meta_dir
        value = self.get_config_meta_flag(config)
        if value is None:
            meta_path = 'all'
        else:
            meta_path = value
        meta_path = 'etc/metadata/' + meta_path
        try:
            meta_path = self.locator.locate(meta_path)
        except rose.resource.ResourceError:
            if not self.get_config_is_discovery(config):
                text = rose.config_editor.ERROR_NOT_FOUND.format(meta_path)
                title = rose.config_editor.DIALOG_TITLE_META_LOAD_ERROR
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                         text, title)
            return None
        else:
            return meta_path

    def get_config_meta_flag(self, config):
        """Return the metadata id flag."""
        for keylist in [[rose.CONFIG_SECT_TOP, rose.CONFIG_OPT_META_TYPE],
                        [rose.CONFIG_SECT_TOP, rose.CONFIG_OPT_PROJECT]]:
            type_node = config.get(keylist, no_ignore=True)
            if type_node is not None and type_node.value:
                return type_node.value
        return None

    def get_config_is_discovery(self, config):
        """Return whether a configuration is a discovery configuration."""
        # The logic here will be improved once suite integration is worked on.
        node = config.get([rose.CONFIG_SECT_TOP, rose.CONFIG_OPT_PROJECT])
        return node is not None

    def load_meta_config(self, config=None, directory=None):
        """Load the main metadata, and any specified in 'config'."""
        should_warn = True
        if config is None:
            config = rose.config.ConfigNode()
        else:
            should_warn = not self.get_config_is_discovery(config)
        meta_config = rose.config.ConfigNode()
        meta_list = ['etc/metadata/all/' + rose.META_CONFIG_NAME]
        config_meta_path = self.load_meta_path(config, directory)
        if config_meta_path is not None:
            meta_list.append(os.path.join(config_meta_path,
                                          rose.META_CONFIG_NAME))
        for meta_key in meta_list:
            try:
                meta_path = self.locator.locate(meta_key)
            except rose.resource.ResourceError:
                if should_warn:
                    rose.gtk.util.run_dialog(
                             rose.gtk.util.DIALOG_TYPE_ERROR,
                             rose.config_editor.ERROR_ID_NOT_FOUND.format(
                                                                   meta_key))
            else:
                try:
                    meta_config = rose.config.load(meta_path, meta_config)
                except rose.config.SyntaxError as e:
                    rose.gtk.util.run_dialog(
                                  rose.gtk.util.DIALOG_TYPE_ERROR,
                                  rose.config_editor.ERROR_LOAD_SYNTAX +
                                  meta_path + "\n" + str(e))
        return meta_config

    def load_meta_files(self, config=None, directory=None):
        """Load the file paths of files within the metadata directory."""
        if config is None:
            config = rose.config.ConfigNode()
        meta_filepaths = []
        meta_path = self.load_meta_path(config, directory)
        if meta_path is None:
            return []
        try:
            file_tuples = os.walk(meta_path)
        except OSError:
            return []
        for dirpath, dirnames, filenames in file_tuples:
            if '/.svn' in dirpath:
                continue
            for fname in filenames:
                meta_filepaths.append(os.path.join(dirpath, fname))
        return meta_filepaths

    def filter_meta_config(self, config_name):
        # TODO: Remove after different default metadata for different configs
        config_data = self.config[config_name]
        meta_config = config_data.meta
        filter_list = []
        no_filter_list = []
        delim = rose.CONFIG_DELIMITER
        if config_data.is_top_level or config_data.is_discovery:
            filter_list.append(rose.CONFIG_SECT_CMD)
        if config_data.is_discovery:
            filter_list.append(delim + rose.CONFIG_OPT_META_TYPE)
        else:
            filter_list.append("")
            no_filter_list.append(delim + rose.CONFIG_OPT_META_TYPE)
        for key in meta_config.value.keys():
            if (key in filter_list or
                any([key.startswith(a + delim) for a in filter_list]) and
                key not in no_filter_list and
                not any([key.startswith(a + delim) for a in no_filter_list])):
                meta_config.value.pop(key)

    def load_ignored_data(self, config_name):
        """Deal with ignored variables and sections."""
        self.trigger[config_name] = rose.macros.trigger.TriggerMacro()
        config = self.config[config_name].config
        sect_map = self.config[config_name].sections.now
        var_map = self.config[config_name].vars.now
        latent_var_map = self.config[config_name].vars.latent
        config_for_macro = rose.config.ConfigNode()
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
            self.handle_bad_trigger_dependency(config_name,
                                               bad_list[0])
            return
        trig_config, change_list = self.trigger[config_name].transform(
                                        config_for_macro, meta_config)
        self.trigger_id_value_lookup.setdefault(config_name, {})
        var_id_map = {}
        for variables in var_map.values():
            for variable in variables:
                var_id_map.update({variable.metadata['id']: variable})
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

        for section, sect_node in trig_config.value.items():
            meta_node = meta_config.get([section], no_ignore=True)
            if not isinstance(sect_node.value, dict):
                option_items = [(section, sect_node)]
                section = ""
            else:
                option_items = sect_node.value.items()
            if sect_node.state == syst_ignored_state:
                # Trigger-ignored section
                if not sect_map[section].ignored_reason:
                    parents = self.trigger[config_name].ignored_dict.get(
                                                        section, {})
                    help_str = ", ".join(parents.values())
                    sect_map[section].error.update(
                         {rose.config_editor.WARNING_TYPE_ENABLED:
                          (rose.config_editor.WARNING_NOT_IGNORED +
                           help_str)})
            elif sect_map[section].ignored_reason:
                # User-ignored or enabled trigger state, ignored in config.
                if (section in self.trigger[config_name].enabled_dict and
                    section not in self.trigger[config_name].ignored_dict):
                    # Enabled trigger state
                    parents = self.trigger[config_name].enabled_dict[section]
                    help_str = (rose.config_editor.WARNING_NOT_ENABLED + 
                                ',  '.join(parents.values()))
                    err_type = rose.config_editor.WARNING_TYPE_IGNORED
                    sect_map[section].error.update({err_type: help_str})
                elif (rose.variable.IGNORED_BY_SYSTEM in
                      sect_map[section].ignored_reason and
                      meta_node is not None and
                      meta_node.get(
                      [rose.META_PROP_COMPULSORY],
                      no_ignore=True).value == rose.META_PROP_VALUE_TRUE):
                    # Section is trigger-ignored without a trigger.
                    help_str = rose.config_editor.WARNING_NOT_TRIGGER
                    err_type = rose.config_editor.WARNING_TYPE_NOT_TRIGGER
                    sect_map[section].error.update({err_type: help_str})
            for option, opt_node in option_items:
                value = opt_node.value
                state = opt_node.state
                var_id = self.util.get_id_from_section_option(section, option)
                var = var_id_map[var_id]
                ignored_reasons = var.ignored_reason.keys()
                if (state == syst_ignored_state and
                    rose.variable.IGNORED_BY_SYSTEM not in ignored_reasons and
                    rose.variable.IGNORED_BY_USER not in ignored_reasons):
                    parents = self.trigger[config_name].ignored_dict[var_id]
                    help_str = ", ".join(parents.values())
                    help_str = rose.config_editor.WARNING_NOT_IGNORED + help_str
                    err_type = rose.config_editor.WARNING_TYPE_ENABLED
                    var.error.update({err_type: help_str})
                elif (state != syst_ignored_state and
                      rose.variable.IGNORED_BY_SYSTEM in ignored_reasons):
                    if var_id in self.trigger[config_name].enabled_dict:
                        parents = self.trigger[config_name].enabled_dict[
                                                                    var_id]
                        help_str = (rose.config_editor.WARNING_NOT_ENABLED + 
                                    ', '.join(parents))
                        err_type = rose.config_editor.WARNING_TYPE_IGNORED
                        var.error.update({err_type: help_str})
                    elif (var_id not in
                          self.trigger[config_name].ignored_dict and
                          var.metadata.get(rose.META_PROP_COMPULSORY) ==
                          rose.META_PROP_VALUE_TRUE):
                        # Variable is trigger-ignored without a trigger.
                        help_str = rose.config_editor.WARNING_NOT_TRIGGER
                        err_type = rose.config_editor.WARNING_TYPE_NOT_TRIGGER
                        var.error.update({err_type: help_str})

    def load_file_metadata(self, config_name):
        """Deal with file section variables."""
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

    def load_variable_namespaces(self, config_name, from_saved=False):
        """Load namespaces for variables, using defaults if not specified."""
        config_vars = self.config[config_name].vars
        for section, variables in config_vars.foreach(from_saved):
            for variable in variables:
                self.load_ns_for_variable(variable, config_name)
        
    def load_ns_for_variable(self, var, config_name):
        """Load a namespace for a variable."""
        meta_config = self.config[config_name].meta
        var_id = var.metadata.get('id')
        section, option = self.util.get_section_option_from_id(var_id)
        subspace = var.metadata.get(rose.META_PROP_NS)
        if subspace is None:
            new_namespace = self.get_default_namespace_for_section(
                                             section, config_name)
        else:
            new_namespace = config_name + '/' + subspace
        if new_namespace == config_name + '/':
            new_namespace = config_name
        var.metadata['full_ns'] = new_namespace
        return new_namespace

    def reload_metadata_for_vars(self, variables, config_name):
        for variable in variables:
            var_id = variable.metadata['id']
            new_meta = self.get_metadata_for_config_id(var_id, config_name)
            variable.process_metadata(new_meta)
            self.load_ns_for_variable(variable, config_name)

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
                for option, opt_node in sect_node.value.items():
                    if opt_node.is_ignored():
                        continue
                    value = meta_config[section][option].value
                    self.namespace_meta_lookup[namespace].update(
                                                            {option: value})
        ns_sections = {}  # Namespace-sections key value pairs.
        for variable in config_data.vars.get_all():
            ns = variable.metadata['full_ns']
            var_id = variable.metadata['id']
            sect, opt = self.util.get_section_option_from_id(var_id)
            ns_sections.setdefault(ns, [])
            if sect not in ns_sections[ns]:
                ns_sections[ns].append(sect)
        default_ns_sections = {}
        for section in config_data.sections.get_all():
            ns = self.get_default_namespace_for_section(
                                  section.name, config_name)
            ns_sections.setdefault(ns, [])
            if section.name not in ns_sections[ns]:
                ns_sections[ns].append(section.name)
            default_ns_sections.setdefault(ns, [])
            if section.name not in default_ns_sections[ns]:
                default_ns_sections[ns].append(section.name)
        for ns in ns_sections:
            self.namespace_meta_lookup.setdefault(ns, {})
            self.namespace_meta_lookup[ns]['sections'] = ns_sections[ns]
            if len(ns_sections[ns]) == 1:
                ns_section = ns_sections[ns][0]
                metadata = self.get_metadata_for_config_id(ns_section,
                                                           config_name)
                for key, value in metadata.items():
                    if (ns_section not in default_ns_sections.get(ns, []) and
                        key == rose.META_PROP_TITLE):
                        # ns created from variables, not a section - no title.
                        continue
                    self.namespace_meta_lookup[ns].setdefault(key, value)
        file_ns_bit = "/" + rose.SUB_CONFIG_FILE_DIR + "/"
        for ns, prop_map in self.namespace_meta_lookup.items():
            if file_ns_bit in ns:
                title = re.sub(".*" + file_ns_bit, "", ns)
                prop_map.setdefault(rose.META_PROP_TITLE,
                                    title.replace(":", "/"))
        for config_name in self.config.keys():
            icon_path = self.get_icon_path_for_config(config_name)
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
    
    def handle_bad_trigger_dependency(self, config_name, err_report):
        """Handle a bad 'trigger' dependency event."""
        section = err_report.section
        option = err_report.option
        err_string = err_report.info
        setting_id = self.util.get_id_from_section_option(section, option)
        rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                 rose.config_editor.ERROR_BAD_TRIGGER.format(
                                      err_string, setting_id, config_name))
        self.trigger[config_name].trigger_family_lookup.clear()

    def reload_namespace_tree(self, view_missing=False):
        """Make the tree of namespaces and load to the tree panel."""
        self.namespace_tree = {}
        configs = self.config.keys()
        configs.sort(rose.config.sort_settings)
        configs.sort(lambda x, y: cmp(self.config[y].is_top_level,
                                      self.config[x].is_top_level))
        for config_name in configs:
            config_data = self.config[config_name]
            top_spaces = config_name.lstrip('/').split('/')
            self.update_namespace_tree(top_spaces, self.namespace_tree,
                                       prev_spaces=[])
            self.load_metadata_for_namespaces(config_name)
            meta_config = config_data.meta
            # Load tree from sections (usually vast majority of tree nodes)
            for section_id, section_data in config_data.sections.now.items():
                ns = self.get_default_namespace_for_section(
                                      section_id, config_name)
                self.namespace_meta_lookup.setdefault(ns, {})
                self.namespace_meta_lookup[ns].setdefault(
                                    'title', ns.split('/')[-1])
                spaces = ns.lstrip('/').split('/')
                self.update_namespace_tree(spaces,
                                           self.namespace_tree,
                                           prev_spaces=[])
            # Now load tree from variables
            self.load_variable_namespaces(config_name)
            for var in config_data.vars.get_all(no_latent=not view_missing):
                ns = var.metadata['full_ns']
                self.namespace_meta_lookup.setdefault(ns, {})
                self.namespace_meta_lookup[ns].setdefault(
                                    'title', ns.split('/')[-1])
                spaces = ns.lstrip('/').split('/')
                self.update_namespace_tree(spaces,
                                           self.namespace_tree,
                                           prev_spaces=[])
        self.tree_update()

    def update_namespace_tree(self, spaces, subtree, prev_spaces):
        """Recursively load the namespace tree for a single path (spaces).

        The tree is specified with subtree, and it requires an array of names
        to load (spaces).

        """
        if spaces:
            this_ns = "/" + "/".join(prev_spaces + [spaces[0]])
            comment = self.get_ns_comment_string(this_ns)
            change = ""
            meta = self.namespace_meta_lookup.get(this_ns, {})
            meta.setdefault('title', spaces[0])
            subtree.setdefault(spaces[0], [{}, meta, comment, change])
            prev_spaces += [spaces[0]]
            self.update_namespace_tree(spaces[1:], subtree[spaces[0]][0],
                                       prev_spaces)

    def is_ns_in_tree(self, ns):
        spaces = ns.lstrip('/').split('/')
        subtree = self.namespace_tree
        while spaces:
            if spaces[0] not in subtree:
                return False
            subtree = subtree[spaces[0]][0]
            spaces.pop(0)
        return True

    def is_ns_sub_data(self, ns):
        """Return whether a namespace is mentioned in summary data."""
        ns_meta = self.namespace_meta_lookup.get(ns, {})
        if (ns_meta.get(rose.META_PROP_DUPLICATE) == rose.META_PROP_VALUE_TRUE
            and not ns.split("/")[-1].isdigit()):
            return True
        if ns.split("/")[-1] == rose.SUB_CONFIG_FILE_DIR:
            return True
        return False

    def is_ns_content(self, ns):
        """Return whether a namespace has any existing content."""
        config_name = self.util.split_full_ns(self, ns)[0]
        for section in self.get_sections_from_namespace(ns):
            if section in self.config[config_name].sections.now:
                return True
        return self.is_ns_sub_data(ns)

    def get_metadata_for_config_id(self, node_id, config_name):
        """Retrieve the corresponding metadata for a variable."""
        config_data = self.config[config_name]
        meta_config = config_data.meta
        meta_data = {}
        if not node_id:
            return {'id': node_id}
        return rose.macro.get_metadata_for_config_id(node_id, meta_config)

    def get_variable_by_id(self, var_id, config_name, save=False,
                           latent=False):
        """Return the matching variable or None."""
        sect, opt = self.util.get_section_option_from_id(var_id)
        return self.config[config_name].vars.get_var(sect, opt, save,
                                                     no_latent=not latent)

    def clear_flag(self, flag_type, config_name=None):
        """Remove a flag from configuration variables."""
        if config_name is None:
            configs = self.config.keys()
        else:
            configs = [config_name]
        for name in configs:
            for var in self.config[name].vars.get_all():
                if flag_type in var.flags:
                    var.flags.pop(flag_type)

#------------------ Data model helper functions ------------------------------

    def get_data_for_namespace(self, ns, from_saved=False):
        """Return a list of vars and a list of latent vars for this ns."""
        config_name = self.util.split_full_ns(self, ns)[0]
        config_data = self.config[config_name]
        allowed_sections = self.get_sections_from_namespace(ns)
        variables = []
        latents = []
        if from_saved:
            var_map = config_data.vars.save
            latent_var_map = config_data.vars.latent_save
        else:
            var_map = config_data.vars.now
            latent_var_map = config_data.vars.latent
        for section in allowed_sections:
            variables.extend(var_map.get(section, []))
            latents.extend(latent_var_map.get(section, []))
        ns_vars = [v for v in variables if v.metadata.get('full_ns') == ns]
        ns_latents = [v for v in latents if v.metadata.get('full_ns') == ns]
        return ns_vars, ns_latents

    def get_sub_data_for_namespace(self, ns, from_saved=False):
        """Return any sections/variables below this namespace."""
        sub_data = {"sections": [], "variables": []}
        config_name = self.util.split_full_ns(self, ns)[0]
        config_data = self.config[config_name]
        for sect, sect_data in config_data.sections.now.items():
            sect_ns = self.get_default_namespace_for_section(sect, config_name)
            if sect_ns.startswith(ns):
                sub_data['sections'].append(sect_data)
        for sect, variables in config_data.vars.now.items():
            for variable in variables:
                if variable.metadata['full_ns'].startswith(ns):
                    sub_data['variables'].append(variable)
        return sub_data

    def get_ns_comments(self, ns):
        """Return any section comments for this namespace."""
        comments = []
        config_name = self.util.split_full_ns(self, ns)[0]
        config_data = self.config[config_name]
        sections = self.get_sections_from_namespace(ns)
        sections.sort(rose.config.sort_settings)
        for section in sections:
            s_ns = self.get_default_namespace_for_section(section,
                                                          config_name)
            if s_ns == ns:
                sect_data = config_data.sections.now.get(section)
                if sect_data is not None:
                    comments.extend(sect_data.comments)
        return comments

    def get_ns_comment_string(self, ns):
        """Return a comment string for this namespace."""
        comment = ""
        comments = self.get_ns_comments(ns)
        if comments:
            comment = "#" + "\n#".join(comments)
        return comment

    def get_ns_variable(self, var_id, ns):
        """Return a variable with this id in the config specified by ns."""
        config_name = self.util.split_full_ns(self, ns)[0]
        config_data = self.config[config_name]
        sect, opt = self.util.get_section_option_from_id(var_id)
        var = config_data.vars.get_var(sect, opt)
        if var is None:
            var = config_data.vars.get_var(sect, opt, save=True)
        return var  # May be None.
            
    def get_sections_from_namespace(self, namespace):
        """Return all sections contributing to a namespace."""
        # FIXME: What about files?
        ns_metadata = self.namespace_meta_lookup.get(namespace, {})
        sections = ns_metadata.get('sections', [])
        if sections:
            return [s for s in sections]
        base, subsp = self.util.split_full_ns(self, namespace)
        ns_section = subsp.replace('/', ':')
        if (ns_section in self.config[base].sections.now or
            ns_section in self.config[base].sections.latent):
            return [ns_section]
        return []

    def get_all_namespaces(self, just_this_config=None):
        """Return all unique namespaces."""
        all_namespaces = []
        if just_this_config is None:
            configs = self.config.keys()
        else:
            configs = [just_this_config]
        for config_name in configs:
            all_namespaces += [config_name]
            self.load_variable_namespaces(config_name)
            for var in self.config[config_name].vars.get_all(no_latent=True):
                all_namespaces.append(var.metadata['full_ns'])
            for section in self.config[config_name].sections.now:
                ns = self.get_default_namespace_for_section(section,
                                                            config_name)
                all_namespaces.append(ns)
        unique_namespaces = []
        for ns in all_namespaces:
            if ns not in unique_namespaces:
                unique_namespaces.append(ns)
        unique_namespaces.sort(lambda x, y: y.count('/') - x.count('/'))
        return unique_namespaces

    def get_missing_sections(self, config_name=None):
        """Return full section ids that are missing."""
        full_sections = []
        if config_name is not None:
            config_names = [config_name]
        else:
            config_names = self.config.keys()
        for config_name in config_names:
            section_store = self.config[config_name].sections
            miss_sections = []
            real_sections = section_store.now.keys()
            for section in section_store.latent.keys():
                if section not in real_sections:
                    miss_sections.append(section)
            for section in self.config[config_name].vars.latent:
                if (section not in real_sections and
                    section not in miss_sections):
                    miss_sections.append(section)
            full_sections += [config_name + ':' + s for s in miss_sections]
        sorter = rose.config.sort_settings
        full_sections.sort(sorter)
        return full_sections

    def get_default_namespace_for_section(self, section, config_name):
        """Return the default namespace for the section."""
        config_data = self.config[config_name]
        meta_config = config_data.meta
        node = meta_config.get([section, rose.META_PROP_NS], no_ignore=True)
        if node is not None:
            subspace = node.value
        else:
            match = REC_ELEMENT_SECTION.match(section)
            if match:
                node = meta_config.get([match.groups()[0], rose.META_PROP_NS])
                if node is None or node.is_ignored():
                    subspace = section.replace('(', '/')
                    subspace = subspace.replace(')', '').replace(':', '/')
                else:
                    subspace = node.value + '/' + str(match.groups()[1])
            elif section.startswith(rose.SUB_CONFIG_FILE_DIR + ":"):
                subspace = section.replace('/', ':')
                subspace = subspace.replace(':', '/', 1)
            else:
                subspace = section.replace(':', '/')
        section_ns = config_name + '/' + subspace
        if not subspace:
            section_ns = config_name
        return section_ns

    def get_format_sections(self, config_name):
        """Return all format-like sections in the current data."""
        format_keys = []
        for section in self.config[config_name].sections.now:
            if (section not in format_keys and 
                ':' in section and not section.startswith('file:')):
                format_keys.append(section)
        format_keys.sort(rose.config.sort_settings)
        return format_keys

    def get_icon_path_for_config(self, config_name):
        """Return the path to the config identifier icon or None."""
        icon_path = None
        for filename in self.config[config_name].meta_files:
            if filename.endswith('/images/icon.png'):
                icon_path = filename
                break
        return icon_path
