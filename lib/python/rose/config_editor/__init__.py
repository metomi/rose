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
"""This package contains the code for the Rose config editor.

This module contains constants that are only used in the config editor.

To override constants at runtime, place a section:

[rose-config-edit]

in your site or user configuration file for Rose, convert the name
of the constants to lowercase, and place constant=value lines in the
section. For example, to override the "ACCEL_HELP_GUI" constant, you
could put the following in your site or user configuration:

[rose-config-edit]
accel_help_gui="<Ctrl>H"

The values you enter will be cast by Python's ast.literal_eval, so:
foo=100
will be cast to an integer, but:
bar="100"
will be cast to a string.

"""

import ast
import os

from rose.resource import ResourceLocator

# Accelerators
# Keyboard shortcut mappings.
ACCEL_NEW = "<Ctrl>N"
ACCEL_OPEN = "<Ctrl>O"
ACCEL_SAVE = "<Ctrl>S"
ACCEL_QUIT = "<Ctrl>Q"
ACCEL_UNDO = "<Ctrl>Z"
ACCEL_REDO = "<Ctrl><Shift>Z"
ACCEL_FIND = "<Ctrl>F"
ACCEL_FIND_NEXT = "<Ctrl>G"
ACCEL_METADATA_REFRESH = "F5"
ACCEL_BROWSER = "<Ctrl>B"
ACCEL_SUITE_RUN = "<Ctrl>R"
ACCEL_TERMINAL = "<Ctrl>T"
ACCEL_HELP_GUI = "F1"

# Menu or panel strings
ADD_MENU_BLANK = "Add blank variable"
ADD_MENU_BLANK_MULTIPLE = "Add blank variable..."
ADD_MENU_META = "Add latent variable"
ICON_PATH_SCHEDULER = None
TAB_MENU_CLOSE = "Close"
TAB_MENU_HELP = "Help"
TAB_MENU_EDIT = "Edit comments"
TAB_MENU_INFO = "Info"
TAB_MENU_OPEN_NEW = "Open in a new window"
TAB_MENU_WEB_HELP = "Web Help"
TOP_MENU_FILE = "_File"
TOP_MENU_FILE_CHECK_AND_SAVE = "_Check And Save"
TOP_MENU_FILE_LOAD_APPS = "_Load All Apps"
TOP_MENU_FILE_NEW = "_New"
TOP_MENU_FILE_OPEN = "_Open..."
TOP_MENU_FILE_SAVE = "_Save"
TOP_MENU_FILE_CLOSE = "_Close"
TOP_MENU_FILE_QUIT = "_Quit"
TOP_MENU_EDIT = "_Edit"
TOP_MENU_EDIT_UNDO = "_Undo"
TOP_MENU_EDIT_REDO = "_Redo"
TOP_MENU_EDIT_STACK = "Undo/Redo _Viewer"
TOP_MENU_EDIT_FIND = "_Find..."
TOP_MENU_EDIT_FIND_NEXT = "_Find Next"
TOP_MENU_EDIT_PREFERENCES = "_Preferences"
TOP_MENU_VIEW = "_View"
TOP_MENU_VIEW_LATENT_VARS = "View _Latent Variables"
TOP_MENU_VIEW_FIXED_VARS = "View _Fixed Variables"
TOP_MENU_VIEW_IGNORED_VARS = "View All _Ignored Variables"
TOP_MENU_VIEW_USER_IGNORED_VARS = "View _User Ignored Variables"
TOP_MENU_VIEW_LATENT_PAGES = "View Latent _Pages"
TOP_MENU_VIEW_IGNORED_PAGES = "View All _Ignored Pages"
TOP_MENU_VIEW_USER_IGNORED_PAGES = "View _User Ignored Pages"
TOP_MENU_VIEW_WITHOUT_DESCRIPTIONS = "Hide Variable Descriptions"
TOP_MENU_VIEW_WITHOUT_HELP = "Hide Variable Help"
TOP_MENU_VIEW_WITHOUT_TITLES = "Hide Variable _Titles"
TOP_MENU_VIEW_CUSTOM_DESCRIPTIONS = "Use Custom _Description Format"
TOP_MENU_VIEW_CUSTOM_HELP = "Use Custom _Help Format"
TOP_MENU_VIEW_CUSTOM_TITLES = "Use Custom _Title Format"
TOP_MENU_VIEW_FLAG_OPT_CONF_VARS = "Flag Opt _Config Variables"
TOP_MENU_VIEW_FLAG_OPTIONAL_VARS = "Flag _Optional Variables"
TOP_MENU_VIEW_FLAG_NO_METADATA_VARS = "Flag _No-metadata Variables"
TOP_MENU_VIEW_STATUS_BAR = "View _Status Bar"
TOP_MENU_PAGE = "_Page"
TOP_MENU_PAGE_ADD = "_Add"
TOP_MENU_PAGE_REVERT = "_Revert to Saved"
TOP_MENU_PAGE_INFO = "_Info"
TOP_MENU_PAGE_HELP = "_Help"
TOP_MENU_PAGE_WEB_HELP = "_Web Help"
TOP_MENU_METADATA = "_Metadata"
TOP_MENU_METADATA_CHECK = "_Check fail-if, warn-if"
TOP_MENU_METADATA_GRAPH = "_Graph Metadata"
TOP_MENU_METADATA_MACRO_ALL_V = "Check All _Validator Macros"
TOP_MENU_METADATA_MACRO_AUTOFIX = "_Auto-fix all configurations"
TOP_MENU_METADATA_MACRO_CONFIG = "{0}"
TOP_MENU_METADATA_PREFERENCES = "Layout _Preferences"
TOP_MENU_METADATA_REFRESH = "_Refresh Metadata"
TOP_MENU_METADATA_SWITCH_OFF = "_Switch off Metadata"
TOP_MENU_METADATA_UPGRADE = "_Upgrade..."
TOP_MENU_TOOLS = "_Tools"
TOP_MENU_TOOLS_BROWSER = "Launch _File Browser"
TOP_MENU_TOOLS_SUITE_RUN = "_Run Suite"
TOP_MENU_TOOLS_SUITE_RUN_CUSTOM = "_Custom ..."
TOP_MENU_TOOLS_SUITE_RUN_DEFAULT = "_Default"
TOP_MENU_TOOLS_TERMINAL = "Launch _Terminal"
TOP_MENU_TOOLS_VIEW_OUTPUT = "View _Output"
TOP_MENU_HELP = "_Help"
TOP_MENU_HELP_GUI = "_GUI Help"
TOP_MENU_HELP_ABOUT = "_About"
TOOLBAR_CHECK_AND_SAVE = "Check and save"
TOOLBAR_LOAD_APPS = "Load All Apps"
TOOLBAR_NEW = "New"
TOOLBAR_OPEN = "Open..."
TOOLBAR_SAVE = "Save"
TOOLBAR_BROWSE = "Browse files"
TOOLBAR_UNDO = "Undo"
TOOLBAR_REDO = "Redo"
TOOLBAR_ADD = "Add to page..."
TOOLBAR_REVERT = "Revert page to saved"
TOOLBAR_FIND = "Find expression (regex)"
TOOLBAR_FIND_NEXT = "Find next"
TOP_MENU_TOOLS_OPEN_SUITE_GCONTROL = "Launch Suite Control _GUI"
TOOLBAR_TRANSFORM = "Auto-fix configurations (run built-in transform macros)"
TOOLBAR_VALIDATE = "Check fail-if, warn-if, and run all validator macros"
TOOLBAR_SUITE_GCONTROL = "Launch Suite Control GUI"
TOOLBAR_SUITE_RUN = "Run suite"
TOOLBAR_SUITE_RUN_MENU = "Run suite ..."
TOOLBAR_VIEW_OUTPUT = "View Output"
TREE_PANEL_TITLE = "Index"
TREE_PANEL_ADD_GENERIC = "_Add a new section..."
TREE_PANEL_ADD_SECTION = "_Add {0}"
TREE_PANEL_AUTOFIX_CONFIG = "_Auto-fix configuration"
TREE_PANEL_CLONE_SECTION = "_Clone this section"
TREE_PANEL_EDIT_SECTION = "Edit section comments..."
TREE_PANEL_ENABLE_GENERIC = "_Enable a section..."
TREE_PANEL_ENABLE_SECTION = "_Enable"
TREE_PANEL_GRAPH_SECTION = "_Graph Metadata"
TREE_PANEL_IGNORE_GENERIC = "_Ignore a section..."
TREE_PANEL_IGNORE_SECTION = "_Ignore"
TREE_PANEL_INFO_SECTION = "I_nfo"
TREE_PANEL_HELP_SECTION = "_Help"
TREE_PANEL_NEW_CONFIG = "_Create new configuration..."
TREE_PANEL_REMOVE_GENERIC = "Remove a section..."
TREE_PANEL_REMOVE_SECTION = "_Remove"
TREE_PANEL_URL_SECTION = "_Web Help"
TREE_PANEL_KBD_TIMEOUT = 600
MACRO_MENU_ALL_VALIDATORS = "All Validators"
MACRO_MENU_ALL_VALIDATORS_TIP = "Run all available validator macros."
VAR_MENU_ADD = "_Add to configuration"
VAR_MENU_EDIT_COMMENTS = "Edit _comments"
VAR_MENU_FIX_IGNORE = "Auto-Fix Error"
VAR_MENU_ENABLE = "_Enable"
VAR_MENU_HELP = "_Help"
VAR_MENU_IGNORE = "_User-Ignore"
VAR_MENU_INFO = "I_nfo"
VAR_MENU_REMOVE = "_Remove"
VAR_MENU_URL = "_Web Help"
# Button strings
LABEL_EDIT = "edit"
LABEL_PAGE_HELP = "Page help"
LABEL_PAGE_MACRO_BUTTON = "Macros"

# Loading strings
EVENT_LOAD_CONFIG = "{0} - reading    "
EVENT_LOAD_DONE = "{0} - loading GUI"
EVENT_LOAD_ERRORS = "{0} - errors: {1}"
EVENT_LOAD_METADATA = "{0} - configuring"
EVENT_LOAD_STATUSES = "{0} - checking   "
LOAD_NUMBER_OF_EVENTS = 2

# Other event strings
EVENT_ERR_MARKUP = "<span color='red'>{0}</span>"
EVENT_FOUND_ID = "Found {0}"
EVENT_INVALID_TRIGGERS = "{0}: triggers disabled"
EVENT_LOAD_ATTEMPT = "Attempting to load {0}"
EVENT_LOADED = "Loaded {0}"
EVENT_MACRO_CONFIGS = "{0} configurations"
EVENT_MACRO_TRANSFORM = "{1}: {0}: {2} changes"
EVENT_MACRO_TRANSFORM_ALL = "Transforms: {0}: {1} changes"
EVENT_MACRO_TRANSFORM_ALL_OK = "Transforms: {0}: no changes"
EVENT_MACRO_TRANSFORM_OK = "{1}: {0}: no changes"
EVENT_MACRO_VALIDATE = "{1}: {0}: {2} errors"
EVENT_MACRO_VALIDATE_ALL = "Custom Validators: {0}: {1} errors"
EVENT_MACRO_VALIDATE_ALL_OK = "Custom Validators: {0}: all OK"
EVENT_MACRO_VALIDATE_CHECK_ALL = (
           "Custom Validators, FailureRuleChecker: {0} total problems found")
EVENT_MACRO_VALIDATE_CHECK_ALL_OK = (
           "Custom Validators, FailureRuleChecker: No problems found")
EVENT_MACRO_VALIDATE_OK = "{1}: {0} is OK"
EVENT_MACRO_VALIDATE_NO_PROBLEMS = "Custom Validators: No problems found"
EVENT_MACRO_VALIDATE_PROBLEMS_FOUND = "Custom Validators: {0} problems found"
EVENT_MACRO_VALIDATE_RULE_NO_PROBLEMS = (
                     "FailureRuleChecker: No problems found")
EVENT_MACRO_VALIDATE_RULE_PROBLEMS_FOUND = (
                     "FailureRuleChecker: {0} problems found")
EVENT_REDO = "{0}"
EVENT_REVERT = "Reverted {0}"
EVENT_TIME = "%H:%M:%S"
EVENT_TIME_LONG = "%a %H:%M:%S"
EVENT_UNDO = "{0}"
EVENT_UNDO_ACTION_ID = "{0} {1}"

# Widget strings

CHOICE_LABEL_EMPTY = "(empty)"
CHOICE_MENU_REMOVE = "Remove from list"
CHOICE_TIP_ENTER_CUSTOM = "Enter a custom choice"
CHOICE_TITLE_AVAILABLE = "Available"
CHOICE_TITLE_INCLUDED = "Included"

# Error and warning strings
ERROR_ADD_FILE = "Could not add file {0}: {1}"
ERROR_BAD_FIND = "Bad search expression"
ERROR_BAD_NAME = "{0}: invalid name"
ERROR_BAD_MACRO_EXCEPTION = "Could not apply macro: error: {0}: {1}"
ERROR_BAD_MACRO_RETURN = "Bad return value for macro: {0}"
ERROR_BAD_TRIGGER = ("{0}\nfor <b>{1}</b>\n"
                     "from the configuration <b>{2}</b>. "
                     "\nDisabling triggers for this configuration.")
ERROR_CONFIG_CREATE = ("Error creating application config at {0}:" +
                       "\n  {1}, {2}")
ERROR_CONFIG_CREATE_TITLE = "Error in creating configuration"
ERROR_CONFIG_DELETE = ("Error deleting application config at {0}:" +
                       "\n  {1}, {2}")
ERROR_CONFIG_DELETE_TITLE = "Error in deleting configuration"
ERROR_ID_NOT_FOUND = "Could not find resource: {0}"
ERROR_FILE_DELETE_FAILED = "Delete failed. {0}"
ERROR_IMPORT_CLASS = "Could not retrieve class {0}"
ERROR_IMPORT_WIDGET = "Could not import widget: {0}"
ERROR_IMPORT_WIDGET_TITLE = "Error importing widget."
ERROR_LOAD_OPT_CONFS = "Could not load optional configurations:\n{0}"
ERROR_LOAD_OPT_CONFS_FORMAT = "{0}\n    {1}: {2}\n"
ERROR_LOAD_OPT_CONFS_TITLE = "Error loading opt configs"
ERROR_LOAD_SYNTAX = "Could not load path: {0}\n\nSyntax error:\n{0}\n{1}"
ERROR_METADATA_CHECKER_TITLE = "Flawed metadata warning"
ERROR_METADATA_CHECKER_TEXT = (
                       "{0} problem(s) found in metadata at {1}.\n" +
                       "Some functionality has been switched off.\n\n" +
                       "Run rose metadata-check for more info.")
ERROR_MIN_PYGTK_VERSION = "Requires PyGTK version {0}, found {1}."
ERROR_MIN_PYGTK_VERSION_TITLE = "Need later PyGTK version to run"
ERROR_NO_OUTPUT = "No output found for {0}"
ERROR_NOT_FOUND = "Could not find path: {0}"
ERROR_NOT_REGEX = "Could not compile expression: {0}\nError info: {1}"
ERROR_ORPHAN_SECTION = "Orphaned section: {0} will not be output at runtime."
ERROR_ORPHAN_SECTION_TIP = "Error: orphaned section!"
ERROR_REMOVE_FILE = "Could not remove file {0}: {1}"
ERROR_RUN_MACRO_TITLE = "Error in running {0}"
ERROR_SECTION_ADD = "Could not add section, already exists: {0}"
ERROR_SECTION_ADD_TITLE = "Error in adding section"
ERROR_SAVE_PATH_FAIL = "Could not save to path!\n {0}"
ERROR_SAVE_BLANK = "Cannot save configuration {0}.\nUnnamed variable in {1}"
ERROR_SAVE_TITLE = "Error saving {0}"
ERROR_UPGRADE = "Error: cannot upgrade {0}"
IGNORED_STATUS_CONFIG = "from configuration."
IGNORED_STATUS_DEFAULT = "from default."
IGNORED_STATUS_MANUAL = "from manual intervention."
IGNORED_STATUS_MACRO = "from macro."
PAGE_WARNING = "Error ({0}): {1}"
PAGE_WARNING_IGNORED_SECTION = "Ignored section: {0}"
PAGE_WARNING_IGNORED_SECTION_TIP = "Ignored section"
PAGE_WARNING_LATENT = "Latent page - no data"
PAGE_WARNING_NO_CONTENT = "No data associated with this page."
PAGE_WARNING_NO_CONTENT_TIP = ("No associated configuration or summary data " +
                               "for this page.")
WARNING_APP_CONFIG_CREATE = "Cannot create another configuration here."
WARNING_APP_CONFIG_CREATE_TITLE = "Warning - application configuration."
WARNING_CONFIG_DELETE = ("Cannot remove a whole configuration:\n{0}\n" +
                         "This must be done externally.")
WARNING_CONFIG_DELETE_TITLE = "Can't remove configuration"
WARNING_ERRORS_FOUND_ON_SAVE = "Errors found in {0}. Save anyway?"
WARNING_FILE_DELETE = ("Not a configuration file entry!\n" +
                       "This file must be manually removed" +
                       " in the filesystem:\n {0}.")
WARNING_FILE_DELETE_TITLE = "Can't remove filesystem file"
WARNING_CANNOT_ENABLE = "Warning - cannot override a trigger setting: {0}"
WARNING_CANNOT_ENABLE_TITLE = "Warning - can't enable"
WARNING_CANNOT_IGNORE = "Warning - cannot override a trigger setting: {0}"
WARNING_CANNOT_IGNORE_TITLE = "Warning - can't ignore"
WARNING_CANNOT_GRAPH = "Warning - graphing not possible"
WARNING_CANNOT_USER_IGNORE = "Warning - cannot override this setting: {0}"
WARNING_NOT_ENABLED = "Should be enabled from "
WARNING_NOT_FOUND = "No results"
WARNING_NOT_FOUND_TITLE = "Couldn't find it"
WARNING_NOT_IGNORED = "Should be ignored "
WARNING_NOT_TRIGGER = "Not part of the trigger mechanism"
WARNING_USER_NOT_TRIGGER_IGNORED = "User-ignored, but should be trigger-ignored"
WARNING_NOT_USER_IGNORABLE = "User-ignored, but is compulsory"
WARNING_TYPE_ENABLED = "enabled"
WARNING_TYPE_TRIGGER_IGNORED = "trigger-ignored"
WARNING_TYPE_USER_IGNORED = "user-ignored"
WARNING_TYPE_NOT_TRIGGER = "trigger"
WARNING_TYPES_IGNORE = [WARNING_TYPE_ENABLED, WARNING_TYPE_TRIGGER_IGNORED,
                        WARNING_TYPE_USER_IGNORED, WARNING_TYPE_NOT_TRIGGER]
WARNING_INTEGER_OUT_OF_BOUNDS = "Warning: integer out of bounds"

# Special metadata "type" values
FILE_TYPE_FORMATS = "formats"
FILE_TYPE_INTERNAL = "file_int"
FILE_TYPE_NORMAL = "file"
FILE_TYPE_TOP = "suite"

META_PROP_INTERNAL = "_internal"

# Setting visibility modes
SHOW_MODE_CUSTOM_DESCRIPTION = "custom-description"
SHOW_MODE_CUSTOM_HELP = "custom-help"
SHOW_MODE_CUSTOM_TITLE = "custom-title"
SHOW_MODE_FIXED = "fixed"
SHOW_MODE_FLAG_NO_META = "flag:no-meta"
SHOW_MODE_FLAG_OPT_CONF = "flag:optional-conf"
SHOW_MODE_FLAG_OPTIONAL = "flag:optional"
SHOW_MODE_IGNORED = "ignored"
SHOW_MODE_USER_IGNORED = "user-ignored"
SHOW_MODE_LATENT = "latent"
SHOW_MODE_NO_DESCRIPTION = "description"
SHOW_MODE_NO_HELP = "help"
SHOW_MODE_NO_TITLE = "title"

# Defaults for the view and layout modes.
SHOULD_SHOW_CUSTOM_DESCRIPTION = False
SHOULD_SHOW_CUSTOM_HELP = False
SHOULD_SHOW_CUSTOM_TITLE = False
SHOULD_SHOW_FLAG_NO_META_VARS = False
SHOULD_SHOW_FLAG_OPT_CONF_VARS = True
SHOULD_SHOW_FLAG_OPTIONAL_VARS = False
SHOULD_SHOW_ALL_COMMENTS = False
SHOULD_SHOW_FIXED_VARS = False
SHOULD_SHOW_IGNORED_PAGES = False
SHOULD_SHOW_IGNORED_VARS = False
SHOULD_SHOW_USER_IGNORED_PAGES = True
SHOULD_SHOW_USER_IGNORED_VARS = True
SHOULD_SHOW_LATENT_PAGES = False
SHOULD_SHOW_LATENT_VARS = False
SHOULD_SHOW_NO_DESCRIPTION = False
SHOULD_SHOW_NO_HELP = True
SHOULD_SHOW_NO_TITLE = False
SHOULD_SHOW_STATUS_BAR = True

# Metadata representation strings:
#     {name} gets replaced with the data/metadata property name.
# For example, you may want to have the description format as:
#     "{name} - {description}"

CUSTOM_FORMAT_DESCRIPTION = "{name}: {description}"
CUSTOM_FORMAT_HELP = "{title}\n\n{help}"
CUSTOM_FORMAT_TITLE = "{title} ({name})"

# Window sizes
WIDTH_TREE_PANEL = 256
SIZE_MACRO_DIALOG_MAX = (800, 600)
SIZE_STACK = (800, 600)
SIZE_PAGE_DETACH = (650, 600)
SIZE_WINDOW = (900, 600)
SPACING_PAGE = 10
SPACING_SUB_PAGE = 5

# Status bar configuration
STATUS_BAR_CONSOLE_TIP = "View more messages (Console)"
STATUS_BAR_CONSOLE_CATEGORY_ERROR = "Error"
STATUS_BAR_CONSOLE_CATEGORY_INFO = "Info"
STATUS_BAR_MESSAGE_LIMIT = 1000
STATUS_BAR_VERBOSITY = 0  # Compare with rose.reporter.Reporter.

# Stack action names and presentation
STACK_GROUP_ADD = "Add"
STACK_GROUP_COPY = "Copy"
STACK_GROUP_IGNORE = "Ignore"
STACK_GROUP_DELETE = "Delete"
STACK_GROUP_RENAME = "Rename"
STACK_GROUP_REORDER = "Reorder"

STACK_ACTION_ADDED = "Added"
STACK_ACTION_CHANGED = "Changed"
STACK_ACTION_CHANGED_COMMENTS = "Changed #"
STACK_ACTION_ENABLED = "Enabled"
STACK_ACTION_IGNORED = "Ignored"
STACK_ACTION_REMOVED = "Removed"

COLOUR_STACK_ADDED = "green"
COLOUR_STACK_CHANGED = "blue"
COLOUR_STACK_CHANGED_COMMENTS = "dark blue"
COLOUR_STACK_ENABLED = "light green"
COLOUR_STACK_IGNORED = "grey"
COLOUR_STACK_REMOVED = "red"

COLOUR_MACRO_CHANGED = "blue"
COLOUR_MACRO_ERROR = "red"
COLOUR_MACRO_WARNING = "orange"

STACK_COL_NS = "Namespace"
STACK_COL_ACT = "Action"
STACK_COL_NAME = "Name"
STACK_COL_VALUE = "Value"
STACK_COL_OLD_VALUE = "Old Value"

COLOUR_VALUEWIDGET_BASE_SELECTED = "GhostWhite"
COLOUR_VARIABLE_CHANGED = "blue"
COLOUR_VARIABLE_TEXT_ERROR = "dark red"
COLOUR_VARIABLE_TEXT_IRRELEVANT = "light grey"
COLOUR_VARIABLE_TEXT_VAL_ENV = "purple4"

# Dialog text
DIALOG_BODY_ADD_CONFIG = "Choose configuration to add to"
DIALOG_BODY_ADD_SECTION = "Specify new configuration section name"
DIALOG_BODY_IGNORE_ENABLE_CONFIG = "Choose configuration"
DIALOG_BODY_IGNORE_SECTION = "Choose the section to ignore"
DIALOG_BODY_ENABLE_SECTION = "Choose the section to enable"
DIALOG_BODY_FILE_ADD = "The file {0} will be added at your next save."
DIALOG_BODY_FILE_REMOVE = "The file {0} will be deleted at your next save."
DIALOG_BODY_GRAPH_CONFIG = "Choose the configuration to graph"
DIALOG_BODY_GRAPH_SECTION = "Choose a particular section to graph"
DIALOG_BODY_MACRO_CHANGES = "<b>{0} {1}</b>\n    {2}\n"
DIALOG_BODY_MACRO_CHANGES_MAX_LENGTH = 150  # Must > raw CHANGES text above
DIALOG_BODY_MACRO_CHANGES_NUM_HEIGHT = 3  # > Number, needs more height.
DIALOG_BODY_NL_CASE_CHANGE = ("Mixed-case names cause trouble in namelists." +
                              "\nSuggested: {0}")
DIALOG_BODY_REMOVE_CONFIG = "Choose configuration"
DIALOG_BODY_REMOVE_SECTION = "Choose the section to remove"
DIALOG_COLUMNS_UPGRADE = ["Name", "Version", "Upgrade Version", "Upgrade?"]
DIALOG_HELP_TITLE = "Help for {0}"
DIALOG_LABEL_AUTOFIX = "Run built-in transform (fixer) macros?"
DIALOG_LABEL_AUTOFIX_ALL = "Run built-in transform (fixer) macros for all configurations?"
DIALOG_LABEL_CHOOSE_SECTION_ADD_VAR = "Choose a section for the new variable:"
DIALOG_LABEL_CHOOSE_SECTION_EDIT = "Choose a section to edit:"
DIALOG_LABEL_CONFIG_CHOOSE_META = "Metadata id:"
DIALOG_LABEL_CONFIG_CHOOSE_NAME = "New config name:"
DIALOG_LABEL_MACRO_TRANSFORM_CHANGES = ("<b>{0}:</b> <i>{1}</i>\n" +
                                        "changes: {2}")
DIALOG_LABEL_MACRO_TRANSFORM_NONE = (
    "No configuration changes from this macro.")
DIALOG_LABEL_MACRO_VALIDATE_ISSUES = ("<b>{0}</b> <i>{1}</i>\n" +
                                      "errors: {2}")
DIALOG_LABEL_MACRO_VALIDATE_NONE = "Configuration OK for this macro."
DIALOG_LABEL_MACRO_WARN_ISSUES = ("warnings: {0}")
DIALOG_LABEL_NULL_SECTION = "None"
DIALOG_LABEL_PREFERENCES = ("Please edit your site and user " +
                            "configurations to make changes.")
DIALOG_LABEL_UPGRADE_ALL = "Show all possible versions"
DIALOG_TIP_SUITE_RUN_HELP = "Read the help for rose suite-run"
DIALOG_TEXT_MACRO_CHANGED = "changed"
DIALOG_TEXT_MACRO_ERROR = "error"
DIALOG_TEXT_MACRO_WARNING = "warning"
DIALOG_TEXT_UNREGISTERED_SUITE = ("Cannot launch gcontrol: " +
                                  "suite {0} is not registered.")
DIALOG_TITLE_MACRO_TRANSFORM = "{0} - Changes for {1}"
DIALOG_TITLE_MACRO_TRANSFORM_NONE = "{0}"
DIALOG_TITLE_MACRO_VALIDATE = "{0} - Issues for {1}"
DIALOG_TITLE_MACRO_VALIDATE_NONE = "{0}"
DIALOG_TITLE_ADD = "Add section"
DIALOG_TITLE_AUTOFIX = "Automatic fixing"
DIALOG_TITLE_CHOOSE_SECTION = "Choose section"
DIALOG_TITLE_CONFIG_CREATE = "Create configuration"
DIALOG_TITLE_CRITICAL_ERROR = "Error"
DIALOG_TITLE_EDIT_COMMENTS = "Edit comments for {0}"
DIALOG_TITLE_ENABLE = "Enable section"
DIALOG_TITLE_ERROR = "Error"
DIALOG_TITLE_GRAPH = "rose metadata-graph"
DIALOG_TITLE_IGNORE = "Ignore section"
DIALOG_TITLE_INFO = "Information"
DIALOG_TITLE_OPEN = "Open configuration"
DIALOG_TITLE_MACRO_CHANGES = "Accept changes made by {0}?"
DIALOG_TITLE_META_LOAD_ERROR = "Error loading metadata."
DIALOG_TITLE_NL_CASE_WARNING = "Mixed-case warning"
DIALOG_TITLE_PREFERENCES = "Configure preferences"
DIALOG_TITLE_REMOVE = "Remove section"
DIALOG_TITLE_SAVE_CHANGES = "Save changes?"
DIALOG_TITLE_UNREGISTERED_SUITE = "Suite not registered"
DIALOG_TITLE_UPGRADE = "Upgrade configurations"
DIALOG_TITLE_WARNING = "Warning"
DIALOG_VARIABLE_ERROR_TITLE = "{0} error for {1}"
DIALOG_VARIABLE_WARNING_TITLE = "{0} warning for {1}"
DIALOG_NODE_INFO_ATTRIBUTE = "<b>{0}</b>"
DIALOG_NODE_INFO_CHANGES = "<span foreground='blue'>{0}</span>\n"
DIALOG_NODE_INFO_DATA = "<span foreground='blue'>Data</span>\n"
DIALOG_NODE_INFO_DELIMITER = "  "
DIALOG_NODE_INFO_METADATA = ("<span foreground='blue'>" +
                                 "Metadata</span>\n")
DIALOG_NODE_INFO_MAX_LEN = 80
DIALOG_NODE_INFO_SUB_ATTRIBUTE = "<i>{0}:</i>"
STACK_VIEW_TITLE = "Undo and Redo Stack Viewer"

# Page names

TITLE_PAGE_IGNORED_MARKUP = "<b>{0}</b> {1}"
TITLE_PAGE_INFO = "suite info"
TITLE_PAGE_LATENT_COLOUR = "grey"
TITLE_PAGE_LATENT_MARKUP = ("<span foreground='" +
                            TITLE_PAGE_LATENT_COLOUR +
                            "'><i>{0}</i>" + "</span>")
TITLE_PAGE_PREVIEW_MARKUP = ("<span foreground='" +
                            TITLE_PAGE_LATENT_COLOUR +
                            "'><u>{0}</u>" + "</span>")
TITLE_PAGE_ROOT_MARKUP = "<b>{0}</b>"
TITLE_PAGE_SUITE = "suite conf"
TREE_PANEL_MAX_EXPANDED = 5

# File panel names

FILE_PANEL_EXPAND = 2
FILE_PANEL_MENU_OPEN = "Open"
TITLE_FILE_PANEL = "Other files"

# Summary (sub) data panel names

SUMMARY_DATA_PANEL_ERROR_TIP = "Error ({0}): {1}\n"
SUMMARY_DATA_PANEL_ERROR_MARKUP = "<span color='red'>X</span>"
SUMMARY_DATA_PANEL_FILTER_LABEL = "Filter:"
SUMMARY_DATA_PANEL_FILTER_MAX_CHAR = 8
SUMMARY_DATA_PANEL_GROUP_LABEL = "Group:"
SUMMARY_DATA_PANEL_IGNORED_SECT_MARKUP = "<b>^</b>"
SUMMARY_DATA_PANEL_IGNORED_SYST_MARKUP = "<b>!!</b>"
SUMMARY_DATA_PANEL_IGNORED_USER_MARKUP = "<b>!</b>"
SUMMARY_DATA_PANEL_MODIFIED_MARKUP = "<span color='blue'>*</span>"
SUMMARY_DATA_PANEL_MAX_LEN = 15
SUMMARY_DATA_PANEL_MENU_ADD = "Add new section"
SUMMARY_DATA_PANEL_MENU_COPY = "Clone this section"
SUMMARY_DATA_PANEL_MENU_ENABLE = "Enable this section"
SUMMARY_DATA_PANEL_MENU_GO_TO = "View {0}"
SUMMARY_DATA_PANEL_MENU_IGNORE = "Ignore this section"
SUMMARY_DATA_PANEL_MENU_REMOVE = "Remove this section"
SUMMARY_DATA_PANEL_SECTION_TITLE = "Section"
SUMMARY_DATA_PANEL_INDEX_TITLE = "Index"
FILE_CONTENT_PANEL_FORMAT_LABEL = "Hide available sections"
FILE_CONTENT_PANEL_MENU_OPTIONAL = "Toggle optional status"
FILE_CONTENT_PANEL_OPT_TIP = "Items available for file source"
FILE_CONTENT_PANEL_TIP = "Items included in file source"
FILE_CONTENT_PANEL_TITLE = "Available sections"

# Tooltip (hover-over) text

TREE_PANEL_TIP_ADDED_CONFIG = "Added configuration since the last save"
TREE_PANEL_TIP_ADDED_VARS = "Added variable(s) since the last save"
TREE_PANEL_TIP_CHANGED_CONFIG = "Modified since the last save"
TREE_PANEL_TIP_CHANGED_SECTIONS = "Modified section data since the last save"
TREE_PANEL_TIP_CHANGED_VARS = "Modified variable data since the last save"
TREE_PANEL_TIP_DIFF_SECTIONS = "Added/removed sections since the last save"
TREE_PANEL_TIP_REMOVED_VARS = "Removed variable(s) since the last save"

KEY_TIP_ADDED = "Added since the last save."
KEY_TIP_CHANGED = "Modified since the last save, old value {0}"
KEY_TIP_CHANGED_COMMENTS = "Modified comments since the last save."
KEY_TIP_ENABLED = "Enabled since the last save."
KEY_TIP_SECTION_IGNORED = "Section ignored since the last save."
KEY_TIP_TRIGGER_IGNORED = "Trigger ignored since the last save."
KEY_TIP_MISSING = "Removed since the last save."
KEY_TIP_USER_IGNORED = "User ignored since the last save."
TIP_CONFIG_CHOOSE_META = "Enter a metadata identifier for the new config"
TIP_CONFIG_CHOOSE_NAME = "Enter a directory name for the new config."
TIP_CONFIG_CHOOSE_NAME_ERROR = "Invalid directory name for the new config."
TIP_ADD_TO_PAGE = "Add to page..."
TIP_LATENT_PAGE = "Latent page"
TIP_MACRO_RUN_PAGE = "Choose a macro to run for this page"
TIP_REVERT_PAGE = "Revert page to last save"
TIP_SUITE_RUN_ARG = "Enter extra suite run arguments"
TIP_VALUE_ADD_URI = "Add a URI - for example a file path, or a web url"
TREE_PANEL_ERROR = " (1 error)"
TREE_PANEL_ERRORS = " ({0} errors)"
TREE_PANEL_MODIFIED = " (modified)"
TERMINAL_TIP_CLOSE = "Close terminal"
VAR_COMMENT_TIP = "# {0}"
VAR_FLAG_MARKUP = "<span size='small'>{0}</span>"
VAR_FLAG_TIP_FIXED = "Fixed variable (only one allowed value)"
VAR_FLAG_TIP_NO_META = "Flag: no metadata"
VAR_FLAG_TIP_OPT_CONF = "Optional conf overrides:\n{0}"
# Numbers below mean: 0-opt config name, 1-id state/value.
VAR_FLAG_TIP_OPT_CONF_INFO = "    {0}: {1}\n"
# Numbers below mean: 0-sect state, 1-sect, 2-opt state, 3-opt, 4-opt value.
VAR_FLAG_TIP_OPT_CONF_STATE = "{0}{1}={2}{3}={4}"
VAR_FLAG_TIP_OPTIONAL = "Flag: optional"
VAR_MENU_TIP_ERROR = "Error "
VAR_MENU_TIP_LATENT = "This variable could be added to the configuration."
VAR_MENU_TIP_WARNING = "Warning "
VAR_MENU_TIP_FIX_IGNORE = "Auto-fix the variable's ignored state error"
VAR_WIDGET_ENV_INFO = "Set to environment variable"

# Flags for variable widgets

FLAG_TYPE_DEFAULT = "Default flag"
FLAG_TYPE_ERROR = "Error flag"
FLAG_TYPE_FIXED = "Fixed flag"
FLAG_TYPE_NO_META = "No metadata flag"
FLAG_TYPE_OPT_CONF = "Opt conf override flag"
FLAG_TYPE_OPTIONAL = "Optional flag"

# Relevant metadata properties

META_PROP_WIDGET = "widget[rose-config-edit]"
META_PROP_WIDGET_SUB_NS = "widget[rose-config-edit:sub-ns]"

# Miscellaneous
COPYRIGHT = "(C) British Crown Copyright 2012-4 Met Office."
HELP_FILE = "rose-rug-config-edit.html"
LAUNCH_COMMAND = "rose config-edit"
LAUNCH_COMMAND_CONFIG = "rose config-edit -C"
LAUNCH_COMMAND_GRAPH = "rose metadata-graph -C"
LAUNCH_SUITE_RUN = "rose suite-run"
LAUNCH_SUITE_RUN_HELP = "rose help suite-run"
MAX_APPS_THRESHOLD = 10
MIN_PYGTK_VERSION = (2, 12, 0)
PROGRAM_NAME = "rose edit"
PROJECT_URL = "http://github.com/metomi/rose/"
UNTITLED_NAME = "Untitled"
VAR_ID_IN_CONFIG = "Variable id {0} from the configuration {1}"


def false_function(*args, **kwargs):
    """Return False, no matter what the arguments are."""
    return False


def load_override_config():
    conf = ResourceLocator.default().get_conf().get(["rose-config-edit"])
    if conf is None:
        return
    for key, node in conf.value.items():
        if node.is_ignored():
            continue
        try:
            cast_value = ast.literal_eval(node.value)
        except Exception:
            cast_value = node.value
        globals()[key.replace("-", "_").upper()] = cast_value


load_override_config()
