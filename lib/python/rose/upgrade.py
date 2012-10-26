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
"""Module that contains upgrade macro functionality."""


import rose.macro


class MacroUpgrade(rose.macro.MacroBase):

    """Class derived from MacroBase to aid upgrade functionality."""

    INFO_ADDED_SECT = "Added"
    INFO_ADDED_VAR = "Added with value '{0}'"
    INFO_ENABLE = "User-Ignored -> Enabled"
    INFO_IGNORE = "Enabled -> User-ignored"
    INFO_REMOVED = "Removed"
    UPGRADE_RESOURCE_DIR = rose.macro.MACRO_UPGRADE_RESOURCE_DIR

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
        if self.downgrade:
            grade_method = DOWNGRADE_METHOD
        else:
            grade_method = UPGRADE_METHOD
        for module_name, class_name, method, help in macro_info_tuples:
            macro_name = ".".join([module_name, class_name])
            if method == grade_method:
                for module in [self.version_module]:
                    if module.__name__ == module_name:
                        macro_inst = getattr(module, class_name)()
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
            if self.downgrade:
                func = macro.downgrade
            else:
                func = macro.upgrade
            config, i_changes = func(config, meta_config)
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
        return hasattr(macro_instance, DOWNGRADE_METHOD)

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
    rose.macro._handle_transform(app_config, new_config, change_list, macro_id,
                       opt_conf_dir, opt_output_dir, opt_non_interactive)
