# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
"""Module that contains upgrade macro functionality."""

import copy
import inspect
import os
import sys

import rose.config
import rose.macro
import rose.macros.trigger
import rose.reporter


BEST_VERSION_MARKER = "* "
CURRENT_VERSION_MARKER = "= "
ERROR_NO_VALID_VERSIONS = "No versions available."
ERROR_UPGRADE_VERSION = "{0}: invalid version."
INFO_DOWNGRADED = "Downgraded from {0} to {1}"
INFO_UPGRADED = "Upgraded from {0} to {1}"
MACRO_UPGRADE_MODULE = "versions"
MACRO_UPGRADE_MODULE_PATH = MACRO_UPGRADE_MODULE + ".py"
MACRO_UPGRADE_RESOURCE_DIR = "etc"
MACRO_UPGRADE_RESOURCE_FILE_ADD = "rose-macro-add.conf"
MACRO_UPGRADE_RESOURCE_FILE_REMOVE = "rose-macro-remove.conf"
MACRO_UPGRADE_TRIGGER_NAME = "UpgradeTriggerFixing"
NAME_DOWNGRADE = "Downgrade_{0}-{1}"
NAME_UPGRADE = "Upgrade_{0}-{1}"
SAME_UPGRADE_VERSION = "{0}: already at this version."

DOWNGRADE_METHOD = "downgrade"
UPGRADE_METHOD = "upgrade"

IGNORE_MAP = {rose.config.ConfigNode.STATE_NORMAL: "enabled",
              rose.config.ConfigNode.STATE_USER_IGNORED: "user-ignored",
              rose.config.ConfigNode.STATE_SYST_IGNORED: "trig-ignored"}


class UpgradeVersionError(NameError):

    """Raise this error when an incorrect upgrade version is selected."""

    def __str__(self):
        return ERROR_UPGRADE_VERSION.format(self.args[0])


class UpgradeVersionSame(NameError):

    """Raise this error when an incorrect upgrade version is selected."""

    def __str__(self):
        return SAME_UPGRADE_VERSION.format(self.args[0])


class MacroUpgrade(rose.macro.MacroBase):

    """Class derived from MacroBase to aid upgrade functionality."""

    ERROR_RENAME_OPT_TO_SECT = "Error: cannot rename {0}={1} to {2}"
    ERROR_RENAME_SECT_TO_OPT = "Error: cannot rename {0} to {1}={2}"
    INFO_ADDED_SECT = "Added"
    INFO_ADDED_VAR = "Added with value {0}"
    INFO_CHANGED_VAR = "Value: {0} -> {1}"
    INFO_STATE = "{0} -> {1}"
    INFO_REMOVED = "Removed"
    INFO_RENAMED_SECT = "Renamed {0} -> {1}"
    INFO_RENAMED_VAR = "Renamed {0}={1} -> {2}={3}"
    UPGRADE_RESOURCE_DIR = MACRO_UPGRADE_RESOURCE_DIR

    def act_from_files(self, config, downgrade=False):
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
            section = keys[0]
            option = None
            value = None
            if len(keys) > 1:
                option = keys[1]
                value = node.value
            self.add_setting(config, [section, option], value=value,
                             state=node.state, comments=node.comments)
        for keys, node in rem_config.walk():
            section = keys[0]
            option = None
            if len(keys) > 1:
                option = keys[1]
            elif node.value:
                continue
            self.remove_setting(config, [section, option])

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

    def add_setting(self, config, keys, value=None, forced=False,
                    state=None, comments=None, info=None):
        """Add a setting to the configuration."""
        section, option = self._get_section_option_from_keys(keys)
        id_ = self._get_id_from_section_option(section, option)
        if option is not None and value is None:
            value = ""
        if info is None:
            if option is None:
                info = self.INFO_ADDED_SECT
            else:
                info = self.INFO_ADDED_VAR.format(repr(value))

        # Search for existing conflicting settings.
        found_setting = False
        if config.get([section, option]) is None:
            strip_dupl = rose.macro.REC_ID_STRIP
            for keys, node in config.walk():
                existing_section = keys[0]
                existing_base_section = (
                    rose.macro.REC_ID_STRIP.sub("", existing_section))
                if len(keys) == 1:
                    existing_option = None
                    existing_base_option = None
                else:
                    existing_option = keys[1]
                    existing_base_option = (
                        rose.macro.REC_ID_STRIP_DUPL.sub("", existing_option))
                if option is None:
                    # For section 'foo', look for 'foo', 'foo{bar}', 'foo(1)'.
                    if (existing_section == section or
                            existing_base_section == section):
                        found_setting = True
                        break
                # For option 'foo', look for 'foo', 'foo(1)'.
                elif (existing_section == section and
                        (existing_option == option or
                         existing_base_option == option)):
                    found_setting = True
                    break
        else:
            found_setting = True

        # If already added, quit, unless "forced".
        if found_setting:
            if forced:
                # If forced, override the existing properties.
                return self.change_setting_value(
                    config, keys, value, state, comments, info)
            return False

        # Add parent section if missing.
        if option is not None and config.get([section]) is None:
            self.add_setting(config, [section])
        if value is not None and not isinstance(value, basestring):
            text = "New value {0} for {1} is not a string"
            raise ValueError(text.format(repr(value), id_))

        # Set (add) the section/option.
        config.set([section, option], value=value, state=state,
                   comments=comments)
        self.add_report(section, option, value, info)

    def change_setting_value(self, config, keys, value, forced=False,
                             comments=None, info=None):
        """Change a setting (option) value in the configuration."""
        section, option = self._get_section_option_from_keys(keys)
        id_ = self._get_id_from_section_option(section, option)
        node = config.get([section, option])
        if node is None:
            if forced:
                return self.add_setting(config, keys, value, node.state,
                                        comments, info)
            return False
        if node.value == value:
            return False
        if option is None:
            text = "Not valid for value change: {0}".format(id_)
            raise TypeError(text)
        if info is None:
            info = self.INFO_CHANGED_VAR.format(repr(node.value), repr(value))
        if value is not None and not isinstance(value, basestring):
            text = "New value {0} for {1} is not a string"
            raise ValueError(text.format(repr(value), id_))
        node.value = value
        if comments is not None:
            node.comments = comments
        self.add_report(section, option, value, info)

    def get_setting_value(self, config, keys, no_ignore=False):
        """Return the value of a setting."""
        section, option = self._get_section_option_from_keys(keys)
        if config.get([section, option], no_ignore=no_ignore) is None:
            return None
        return config.get([section, option]).value

    def remove_setting(self, config, keys, info=None):
        """Remove a setting from the configuration."""
        section, option = self._get_section_option_from_keys(keys)
        if option is None:
            if config.get([section]) is None:
                return False
            option_node_pairs = config.walk([section])
            for opt_keys, option_node in option_node_pairs:
                opt = opt_keys[1]
                self._remove_setting(config, [section, opt], info)
        return self._remove_setting(config, [section, option], info)

    def rename_setting(self, config, keys, new_keys, info=None):
        """Rename a setting in the configuration."""
        section, option = self._get_section_option_from_keys(keys)
        new_section, new_option = self._get_section_option_from_keys(new_keys)
        if option is None:
            if new_option is not None:
                raise TypeError(self.ERROR_RENAME_SECT_TO_OPT.format(
                    section, new_section, new_option))
        elif new_option is None:
            raise TypeError(self.ERROR_RENAME_OPT_TO_SECT.format(
                section, option, new_section))
        node = config.get(keys)
        if node is None:
            return
        if info is None:
            if option is None:
                info = self.INFO_RENAMED_SECT.format(section, new_section)
            else:
                info = self.INFO_RENAMED_VAR.format(section, option,
                                                    new_section, new_option)
        if option is None:
            if config.get([new_section]) is not None:
                self.remove_setting(config, [new_section])
            self.add_setting(config, [new_section], value=None, forced=True,
                             state=node.state, comments=node.comments,
                             info=info)
            for option_keys, opt_node in config.walk([section]):
                renamed_option = option_keys[1]
                self.add_setting(config, [new_section, renamed_option],
                                 value=opt_node.value, forced=True,
                                 state=opt_node.state,
                                 comments=opt_node.comments, info=info)
        else:
            self.add_setting(config, new_keys, value=node.value, forced=True,
                             state=node.state, comments=node.comments,
                             info=info)
        self.remove_setting(config, keys)

    def enable_setting(self, config, keys, info=None):
        """Enable a setting in the configuration."""
        return self._ignore_setting(config, list(keys),
                                    info=info,
                                    state=rose.config.ConfigNode.STATE_NORMAL)

    def ignore_setting(self, config, keys, info=None,
                       state=rose.config.ConfigNode.STATE_USER_IGNORED):
        """User-ignore a setting in the configuration."""
        return self._ignore_setting(config, list(keys),
                                    info=info, state=state)

    def _ignore_setting(self, config, keys, info=None, state=None):
        """Set the ignored state of a setting, if it exists."""
        section, option = self._get_section_option_from_keys(keys)
        id_ = self._get_id_from_section_option(section, option)
        node = config.get([section, option])
        if node is None or state is None:
            return False
        if option is None:
            value = None
        else:
            value = node.value
        info_text = self.INFO_STATE.format(IGNORE_MAP[node.state],
                                           IGNORE_MAP[state])
        if node.state == state:
            return False
        if info is None:
            info = info_text
        node.state = state
        self.add_report(section, option, value, info)

    def _remove_setting(self, config, keys, info=None):
        """Remove a setting from the configuration, if it exists."""
        section, option = self._get_section_option_from_keys(keys)
        id_ = self._get_id_from_section_option(section, option)
        if config.get([section, option]) is None:
            return False
        if info is None:
            info = self.INFO_REMOVED
        config.unset([section, option])
        self.add_report(section, option, None, info)

    def _get_section_option_from_keys(self, keys):
        return (keys + [None])[:2]


class MacroUpgradeManager(object):

    """Manage the upgrades."""

    def __init__(self, app_config, downgrade=False):
        self.app_config = app_config
        self.downgrade = downgrade
        self.new_version = None
        self.named_tags = []
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
        meta_path, warning = rose.macro.load_meta_path(self.app_config,
                                                       is_upgrade=True)
        if meta_path is None:
            raise OSError(rose.macro.ERROR_LOAD_CONF_META_NODE)
        meta_path = os.path.abspath(meta_path)
        self.named_tags = []
        for node in os.listdir(meta_path):
            node_meta = os.path.join(meta_path, node, rose.META_CONFIG_NAME)
            if os.path.exists(node_meta):
                self.named_tags.append(node)
        self.version_module = get_meta_upgrade_module(meta_path)
        if self.version_module is None:
            # No versions.py.
            self._load_version_macros([])
            return
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

    def get_tags(self, only_named=False):
        """Return relevant tags, reversed order for downgrades."""
        tags = [m.AFTER_TAG for m in self.version_macros]
        if self.downgrade:
            tags = [m.BEFORE_TAG for m in self.version_macros]
        if only_named:
            return [t for t in tags if t in self.named_tags]
        return tags

    def get_new_tag(self, only_named=False):
        """Obtain the default upgrade version."""
        tags = self.get_tags(only_named=only_named)
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

    def transform(self, config, meta_config=None, opt_non_interactive=False,
                  custom_inspector=False):
        """Transform a configuration by looping over upgrade macros."""
        self.reports = []
        for macro in self.get_macros():
            if self.downgrade:
                func = macro.downgrade
            else:
                func = macro.upgrade
            res = {}
            if not opt_non_interactive:
                arglist = inspect.getargspec(func).args
                defaultlist = inspect.getargspec(func).defaults
                optionals = {}
                while defaultlist is not None and len(defaultlist) > 0:
                    if arglist[-1] not in ["self", "config", "meta_config"]:
                        optionals[arglist[-1]] = defaultlist[-1]
                        arglist = arglist[0:-1]
                        defaultlist = defaultlist[0:-1]
                    else:
                        break

                if optionals:
                    if custom_inspector:
                        res = custom_inspector(optionals, "upgrade_macro")
                    else:
                        res = rose.macro.get_user_values(optionals)
            upgrade_macro_result = func(config, meta_config, **res)
            config, i_changes = upgrade_macro_result
            self.reports += i_changes
        opt_node = config.get([rose.CONFIG_SECT_TOP,
                               rose.CONFIG_OPT_META_TYPE], no_ignore=True)
        new_value = self.meta_flag_no_tag + "/" + self.new_tag
        opt_node.value = new_value
        if self.downgrade:
            info = INFO_DOWNGRADED.format(self.tag, self.new_tag)
        else:
            info = INFO_UPGRADED.format(self.tag, self.new_tag)
        report = rose.macro.MacroReport(rose.CONFIG_SECT_TOP,
                                        rose.CONFIG_OPT_META_TYPE,
                                        new_value, info)
        self.reports += [report]
        return config, self.reports

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
                    temp_list.remove(macro)
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


def get_meta_upgrade_module(meta_path):
    """Import and return the versions.py module for a given meta_path.

    The meta_path should not contain a version, just the category.
    For example, it should be '/some/path/to/rose-meta/my-command'
    rather than '/some/path/to/my-command/vn9.1'.

    Let ImportErrors bubble up so they can be reported.

    """
    meta_path = os.path.abspath(meta_path)
    if not os.path.isfile(os.path.join(meta_path, MACRO_UPGRADE_MODULE_PATH)):
        return None
    category = os.path.basename(meta_path)
    version_module = None
    if os.path.exists(os.path.join(meta_path, "__init__.py")):
        # The category directory is a package.
        sys.path.insert(0, os.path.dirname(meta_path))
        category_package = __import__(category)
        version_module = getattr(category_package, MACRO_UPGRADE_MODULE, None)
        sys.path.pop(0)
    else:
        sys.path.insert(0, meta_path)
        version_module = __import__(MACRO_UPGRADE_MODULE)
        sys.path.pop(0)
    return version_module


def main():
    """Run rose upgrade."""
    return_objects = rose.macro.parse_macro_mode_args("upgrade")
    if return_objects is None:
        sys.exit(1)
    app_config, config_map, meta_config, config_name, args, opts = (
        return_objects)
    if opts.conf_dir is not None:
        os.chdir(opts.conf_dir)
    verbosity = 1 + opts.verbosity - opts.quietness
    reporter = rose.reporter.Reporter(verbosity)
    meta_opt_node = app_config.get([rose.CONFIG_SECT_TOP,
                                    rose.CONFIG_OPT_META_TYPE],
                                   no_ignore=True)
    if meta_opt_node is None or len(meta_opt_node.value.split("/")) < 2:
        reporter(rose.macro.MetaConfigFlagMissingError())
        sys.exit(1)
    try:
        upgrade_manager = MacroUpgradeManager(app_config, opts.downgrade)
    except OSError as e:
        reporter(e)
        sys.exit(1)

    need_all_versions = opts.all_versions or args
    ok_versions = upgrade_manager.get_tags(only_named=not need_all_versions)
    if args:
        user_choice = args[0]
    else:
        best_mark = BEST_VERSION_MARKER
        curr_mark = CURRENT_VERSION_MARKER
        all_versions = [" " * len(curr_mark) + v for v in ok_versions]
        if opts.downgrade:
            all_versions.reverse()
            if all_versions:
                all_versions[0] = best_mark + all_versions[0].lstrip()
            all_versions.append(curr_mark + upgrade_manager.tag)
        else:
            if all_versions:
                all_versions[-1] = best_mark + all_versions[-1].lstrip()
            all_versions.insert(0, curr_mark + upgrade_manager.tag)
        reporter("\n".join(all_versions) + "\n", prefix="")
        sys.exit()
    if user_choice == upgrade_manager.tag:
        reporter(UpgradeVersionSame(user_choice))
        sys.exit(1)
    elif user_choice not in ok_versions:
        reporter(UpgradeVersionError(user_choice))
        sys.exit(1)
    upgrade_manager.set_new_tag(user_choice)
    macro_config = copy.deepcopy(app_config)
    combined_config_map = rose.macro.combine_opt_config_map(config_map)
    macro_function = (
        lambda conf, meta: upgrade_manager.transform(
            conf, meta, opts.non_interactive)
    )
    method_id = UPGRADE_METHOD.upper()[0]
    if opts.downgrade:
        method_id = DOWNGRADE_METHOD.upper()[0]
    macro_id = rose.macro.MACRO_OUTPUT_ID.format(method_id,
                                                 upgrade_manager.get_name())
    new_config_map, changes_map = rose.macro.apply_macro_to_config_map(
        combined_config_map, meta_config, macro_function, macro_name=macro_id)
    has_changes = rose.macro.handle_transform(config_map, new_config_map,
                                              changes_map, macro_id,
                                              opts.conf_dir, opts.output_dir,
                                              opts.non_interactive, reporter)
    if not has_changes:
        return
    new_meta_config = rose.macro.load_meta_config(
        new_config_map[None], directory=opts.conf_dir,
        config_type=rose.SUB_CONFIG_NAME,
        ignore_meta_error=True
    )
    config_map = new_config_map
    combined_config_map = rose.macro.combine_opt_config_map(config_map)
    macro_function = (
        lambda conf, meta:
        rose.macros.trigger.TriggerMacro().transform(conf, meta)
    )
    new_config_map, changes_map = rose.macro.apply_macro_to_config_map(
        combined_config_map, new_meta_config, macro_function,
        macro_name=macro_id)
    trig_macro_id = rose.macro.MACRO_OUTPUT_ID.format(
        rose.macro.TRANSFORM_METHOD.upper()[0],
        MACRO_UPGRADE_TRIGGER_NAME
    )
    if any(changes_map.values()):
        rose.macro.handle_transform(config_map, new_config_map,
                                    changes_map, trig_macro_id,
                                    opts.conf_dir, opts.output_dir,
                                    opts.non_interactive, reporter)

if __name__ == "__main__":
    rose.macro.add_meta_paths()
    main()
