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
"""This package contains the specific Python code driving the config editor.

This module contains constants that are only used in the config editor.

"""

import ast
import os

import rose.config

# Accelerators

ACCEL_NEW = "<Ctrl>N"
ACCEL_OPEN = "<Ctrl>O"
ACCEL_SAVE = "<Ctrl>S"
ACCEL_QUIT = "<Ctrl>Q"
ACCEL_UNDO = "<Ctrl>Z"
ACCEL_REDO = "<Ctrl><Shift>Z"
ACCEL_FIND = "<Ctrl>F"
ACCEL_FIND_NEXT = "<Ctrl>G"
ACCEL_BROWSER = "<Ctrl>B"
ACCEL_SUITE_RUN = "<Ctrl>R"
ACCEL_TERMINAL = "<Ctrl>T"
ACCEL_HELP_GUI = "F1"

# Menu or panel strings
ADD_MENU_BLANK = 'Add blank variable'
ADD_MENU_BLANK_MULTIPLE = 'Add blank variable...'
ADD_MENU_META = 'Add latent variable'
TAB_MENU_CLOSE = 'Close'
TAB_MENU_HELP = 'Help'
TAB_MENU_EDIT = 'Edit comments'
TAB_MENU_INFO = "Info"
TAB_MENU_OPEN_NEW = 'Open in a new window'
TAB_MENU_WEB_HELP = 'Web Help'
TOP_MENU_FILE = "_File"
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
TOP_MENU_VIEW_LATENT = "View _Latent Variables"
TOP_MENU_VIEW_FIXED = "View _Fixed Variables"
TOP_MENU_VIEW_IGNORED = "View All _Ignored Variables"
TOP_MENU_VIEW_USER_IGNORED = "View _User Ignored Variables"
TOP_MENU_VIEW_WITHOUT_TITLES = "Hide _Titles"
TOP_MENU_VIEW_FLAG_OPTIONAL = "Flag _Optional Variables"
TOP_MENU_VIEW_FLAG_NO_METADATA = "Flag _No-metadata Variables"
TOP_MENU_PAGE = "_Page"
TOP_MENU_PAGE_ADD = "_Add"
TOP_MENU_PAGE_REVERT = "_Revert to Saved"
TOP_MENU_PAGE_INFO = "_Info"
TOP_MENU_PAGE_HELP = "_Help"
TOP_MENU_PAGE_WEB_HELP = "_Web Help"
TOP_MENU_METADATA = "_Metadata"
TOP_MENU_METADATA_CHECK = "_Check fail-if, warn-if"
TOP_MENU_METADATA_SWITCH_OFF = "_Switch off Metadata"
TOP_MENU_METADATA_MACRO_ALL_V = "Check All _Validator Macros"
TOP_MENU_METADATA_MACRO_CONFIG = "{0}"
TOP_MENU_TOOLS = "_Tools"
TOP_MENU_TOOLS_BROWSER = "Launch _File Browser"
TOP_MENU_TOOLS_SUITE_RUN = "_Run Suite"
TOP_MENU_TOOLS_SUITE_RUN_CUSTOM = "_Custom ..."
TOP_MENU_TOOLS_SUITE_RUN_DEFAULT = "_Default"
TOP_MENU_TOOLS_TERMINAL = "Launch _Terminal"
TOP_MENU_HELP = "_Help"
TOP_MENU_HELP_GUI = "_GUI Help"
TOP_MENU_HELP_ABOUT = "_About"
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
TOOLBAR_VALIDATE = "Check fail-if, warn-if, and run all validator macros"
TOOLBAR_SUITE_RUN = "Run suite"
TOOLBAR_SUITE_RUN_MENU = "Run suite ..."
TREE_PANEL_TITLE = 'Index'
TREE_PANEL_ADD_SECTION = '_Add new section...'
TREE_PANEL_CLONE_SECTION = '_Clone this section'
TREE_PANEL_EDIT_SECTION = 'Edit section comments...'
TREE_PANEL_ENABLE_SECTION = '_Enable a section...'
TREE_PANEL_IGNORE_SECTION = '_Ignore a section...'
TREE_PANEL_INFO_SECTION = 'I_nfo'
TREE_PANEL_HELP_SECTION = '_Help'
TREE_PANEL_NEW_CONFIG = "_Create new configuration..."
TREE_PANEL_REMOVE = '_Remove'
TREE_PANEL_URL_SECTION = '_Web Help'
TREE_PANEL_KBD_TIMEOUT = 600
MACRO_MENU_ALL_VALIDATORS = "All Validators"
MACRO_MENU_ALL_VALIDATORS_TIP = "Run all available validator macros."
VAR_MENU_ADD = '_Add to configuration'
VAR_MENU_EDIT_COMMENTS = "Edit _comments"
VAR_MENU_ENABLE = '_Enable'
VAR_MENU_HELP = '_Help'
VAR_MENU_IGNORE = '_Ignore'
VAR_MENU_INFO = 'I_nfo'
VAR_MENU_REMOVE = '_Remove'
VAR_MENU_URL = '_Web Help'

# Button strings
LABEL_EDIT = "edit"

# Loading strings
LOAD_CONFIG = "reading    "
LOAD_DONE = "loading GUI"
LOAD_METADATA = "configuring"
LOAD_NUMBER_OF_EVENTS = 2
LOAD_STATUSES = "checking   "

# Widget strings

CHOICE_LABEL_EMPTY = "(empty)"
CHOICE_MENU_REMOVE = "Remove from list"
CHOICE_TIP_ENTER_CUSTOM = "Enter a custom choice"
CHOICE_TITLE_AVAILABLE = "Available"
CHOICE_TITLE_INCLUDED = "Included"

# Error and warning strings
ERROR_ADD_FILE = "Could not add file {0}: {1}"
ERROR_BAD_NAME = "{0}: invalid name"
ERROR_BAD_TRIGGER = ('{0}\nfor <b>{1}</b>\n'
                     'from the configuration <b>{2}</b>. '
                     '\nDisabling triggers for this configuration.')
ERROR_BAD_MACRO_RETURN = 'Bad return value {0}'
ERROR_CONFIG_CREATE = ("Error creating application config at {0}:" +
                       "\n  {1}, {2}")
ERROR_CONFIG_CREATE_TITLE = "Error in creating configuration"
ERROR_CONFIG_DELETE = ("Error deleting application config at {0}:" +
                       "\n  {1}, {2}")
ERROR_CONFIG_DELETE_TITLE = "Error in deleting configuration"
ERROR_ID_NOT_FOUND = 'Could not find resource: {0}'
ERROR_FILE_DELETE_FAILED = 'Delete failed. {0}'
ERROR_IMPORT_CLASS = 'Could not retrieve class {0}'
ERROR_IMPORT_WIDGET = 'Could not import widget: {0}'
ERROR_IMPORT_WIDGET_TITLE = 'Error importing widget.'
ERROR_LOAD_SYNTAX = 'Could not load path: {0}\n\nSyntax error:\n{0}\n{1}'
ERROR_MIN_PYGTK_VERSION = 'Requires PyGTK version {0}, found {1}.'
ERROR_MIN_PYGTK_VERSION_TITLE = 'Need later PyGTK version to run'
ERROR_NOT_FOUND = 'Could not find path: {0}'
ERROR_NOT_REGEX = 'Could not compile expression: {0}\nError info: {1}'
ERROR_ORPHAN_SECTION = 'Orphaned section: will not be output in a file.'
ERROR_ORPHAN_SECTION_TIP = 'Error: orphaned section!'
ERROR_REMOVE_FILE = "Could not remove file {0}: {1}"
ERROR_RUN_MACRO_TITLE = 'Error in running {0}'
ERROR_SUITE_RUN_INVALID = "Could not run suite - no suite config loaded."
ERROR_SAVE_PATH_FAIL = 'Could not save to path!\n {0}'
IGNORED_STATUS_CONFIG = 'from configuration.'
IGNORED_STATUS_DEFAULT = 'from default.'
IGNORED_STATUS_MANUAL = 'from manual intervention.'
IGNORED_STATUS_MACRO = 'from macro.'
PAGE_WARNING = 'Error ({0}): {1}'
PAGE_WARNING_IGNORED_SECTION = 'Section {0} is ignored.'
PAGE_WARNING_IGNORED_SECTION_TIP = 'Ignored section'
PAGE_WARNING_NO_CONTENT = "This page has no associated data."
PAGE_WARNING_NO_CONTENT_TIP = ("No associated configuration or summary data " +
                               "for this page.")
WARNING_APP_CONFIG_CREATE = "Cannot create another configuration here."
WARNING_APP_CONFIG_CREATE_TITLE = "Warning - application configuration."
WARNING_CONFIG_DELETE = ("Cannot remove a whole configuration:\n{0}\n" +
                         "This must be done externally.")
WARNING_CONFIG_DELETE_TITLE = "Can't remove configuration"
WARNING_FILE_DELETE = ("Not a configuration file entry!\n" +
                       "This file must be manually removed" +
                       " in the filesystem:\n {0}.")
WARNING_FILE_DELETE_TITLE = "Can't remove filesystem file"
WARNING_CANNOT_ENABLE = 'Warning - cannot override a trigger setting: {0}'
WARNING_CANNOT_ENABLE_TITLE = "Warning - can't enable"
WARNING_CANNOT_IGNORE = 'Warning - cannot override a trigger setting: {0}'
WARNING_CANNOT_IGNORE_TITLE = "Warning - can't ignore"
WARNING_CANNOT_USER_IGNORE = 'Warning - cannot override this setting: {0}'
WARNING_NOT_ENABLED = 'Should be enabled from '
WARNING_NOT_FOUND = 'No results'
WARNING_NOT_FOUND_TITLE = "Couldn't find it"
WARNING_NOT_IGNORED = 'Should be ignored '
WARNING_NOT_TRIGGER = 'Not part of the trigger mechanism'
WARNING_NOT_USER_IGNORABLE = 'User-ignored, but is compulsory'
WARNING_TYPE_ENABLED = 'enabled'
WARNING_TYPE_IGNORED = 'ignored'
WARNING_TYPE_NOT_TRIGGER = 'trigger'

# Special metadata 'type' values
FILE_TYPE_FORMATS = 'formats'
FILE_TYPE_INTERNAL = 'file_int'
FILE_TYPE_NORMAL = 'file'
FILE_TYPE_TOP = 'suite'

META_PROP_INTERNAL = '_internal'

# Setting visibility modes
SHOW_MODE_FIXED = 'fixed'
SHOW_MODE_IGNORED = 'ignored'
SHOW_MODE_USER_IGNORED = 'user-ignored'
SHOW_MODE_LATENT = 'latent'
SHOW_MODE_NO_TITLE = 'title'

SHOULD_SHOW_ALL_COMMENTS = False
SHOULD_SHOW_FIXED = False
SHOULD_SHOW_IGNORED = False
SHOULD_SHOW_USER_IGNORED = True
SHOULD_SHOW_LATENT = False
SHOULD_SHOW_NO_TITLE = False

# Window sizes
WIDTH_TREE_PANEL = 256
SIZE_MACRO_DIALOG_MAX = (800, 600)
SIZE_STACK = (800, 600)
SIZE_PAGE_DETACH = (650, 600)
SIZE_WINDOW = (900, 600)
SPACING_PAGE = 10
SPACING_SUB_PAGE = 5

# Stack action names and presentation
STACK_ACTION_ADDED = 'Added'
STACK_ACTION_CHANGED = 'Changed'
STACK_ACTION_CHANGED_COMMENTS = 'Changed #'
STACK_ACTION_ENABLED = 'Enabled'
STACK_ACTION_IGNORED = 'Ignored'
STACK_ACTION_REMOVED = 'Removed'

COLOUR_STACK_ADDED = 'green'
COLOUR_STACK_CHANGED = 'blue'
COLOUR_STACK_CHANGED_COMMENTS = 'dark blue'
COLOUR_STACK_ENABLED = 'light green'
COLOUR_STACK_IGNORED = 'grey'
COLOUR_STACK_REMOVED = 'red'

COLOUR_MACRO_CHANGED = 'blue'
COLOUR_MACRO_ERROR = 'red'
COLOUR_MACRO_WARNING = 'orange'

STACK_COL_NS = 'Namespace'
STACK_COL_ACT = 'Action'
STACK_COL_NAME = 'Name'
STACK_COL_VALUE = 'Value'
STACK_COL_OLD_VALUE = 'Old Value'

COLOUR_VALUEWIDGET_BASE_SELECTED = "GhostWhite"
COLOUR_VARIABLE_CHANGED = 'blue'
COLOUR_VARIABLE_TEXT_ERROR = 'dark red'
COLOUR_VARIABLE_TEXT_IRRELEVANT = 'light grey'
COLOUR_VARIABLE_TEXT_VAL_ENV = 'purple4'

# Dialog text
DIALOG_BODY_ADD_CONFIG = 'Choose configuration to add to'
DIALOG_BODY_ADD_SECTION = 'Specify new configuration section name'
DIALOG_BODY_IGNORE_ENABLE_CONFIG = 'Choose configuration'
DIALOG_BODY_IGNORE_SECTION = 'Choose the section to ignore'
DIALOG_BODY_ENABLE_SECTION = 'Choose the section to enable'
DIALOG_BODY_FILE_ADD = 'The file {0} will be added at your next save.'
DIALOG_BODY_FILE_REMOVE = 'The file {0} will be deleted at your next save.'
DIALOG_BODY_MACRO_CHANGES = "<b>{0} {1}</b>\n    {2}\n"
DIALOG_BODY_MACRO_CHANGES_MAX_LENGTH = 150  # Must > raw CHANGES text above
DIALOG_BODY_MACRO_CHANGES_NUM_HEIGHT = 3  # > Number, needs more height.
DIALOG_BODY_NL_CASE_CHANGE = ("Mixed-case names cause trouble in namelists." +
                              "\nSuggested: {0}")
DIALOG_HELP_TITLE = "Help for {0}"
DIALOG_LABEL_CHOOSE_SECTION_ADD_VAR = "Choose a section for the new variable:"
DIALOG_LABEL_CHOOSE_SECTION_EDIT = "Choose a section to edit:"
DIALOG_LABEL_CONFIG_CHOOSE_META = "Metadata id:"
DIALOG_LABEL_CONFIG_CHOOSE_NAME = "New config name:"
DIALOG_LABEL_MACRO_TRANSFORM_CHANGES = ("<b>{0}:</b> <i>{1}</i>\n" +
                                        "changes: {2}")
DIALOG_LABEL_MACRO_TRANSFORM_NONE = "The configuration needs no changes."
DIALOG_LABEL_MACRO_VALIDATE_ISSUES = ("<b>{0}</b> <i>{1}</i>\n" +
                                      "errors: {2}")
DIALOG_LABEL_MACRO_VALIDATE_NONE = "The configuration looks OK."
DIALOG_LABEL_MACRO_WARN_ISSUES = ("warnings: {0}")
DIALOG_LABEL_PREFERENCES = ("Please edit your site and user " +
                            "configurations to make changes.")
DIALOG_TIP_SUITE_RUN_HELP = "Read the help for rose suite-run"
DIALOG_TEXT_MACRO_CHANGED = "changed"
DIALOG_TEXT_MACRO_ERROR = "error"
DIALOG_TEXT_MACRO_WARNING = "warning"
DIALOG_TITLE_MACRO_TRANSFORM = "{0} - Changes for {1}"
DIALOG_TITLE_MACRO_TRANSFORM_NONE = "{0}"
DIALOG_TITLE_MACRO_VALIDATE = "{0} - Issues for {1}"
DIALOG_TITLE_MACRO_VALIDATE_NONE = "{0}"
DIALOG_TITLE_ADD = "Add section"
DIALOG_TITLE_CHOOSE_SECTION = "Choose section"
DIALOG_TITLE_CONFIG_CREATE = "Create configuration"
DIALOG_TITLE_CRITICAL_ERROR = "Error"
DIALOG_TITLE_EDIT_COMMENTS = "Edit comments for {0}"
DIALOG_TITLE_ENABLE = "Enable section"
DIALOG_TITLE_ERROR = "Error"
DIALOG_TITLE_IGNORE = "Ignore section"
DIALOG_TITLE_INFO = "Information"
DIALOG_TITLE_OPEN = "Open configuration"
DIALOG_TITLE_MACRO_CHANGES = 'Accept changes made by {0}?'
DIALOG_TITLE_META_LOAD_ERROR = "Error loading metadata."
DIALOG_TITLE_NL_CASE_WARNING = "Mixed-case warning"
DIALOG_TITLE_PREFERENCES = "Configure preferences"
DIALOG_TITLE_SAVE_CHANGES = "Save changes?"
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
STACK_VIEW_TITLE = 'Undo and Redo Stack Viewer'

# Page names

TITLE_PAGE_INFO = "suite info"
TITLE_PAGE_MARKUP = "<b>{0}</b>"
TITLE_PAGE_SUITE = "suite conf"
TREE_PANEL_MAX_EXPANDED = 5

# File panel names

FILE_PANEL_EXPAND = 2
FILE_PANEL_MENU_OPEN = "Open"
TITLE_FILE_PANEL = "Other files"

# Summary (sub) data panel names

SUMMARY_DATA_PANEL_IGNORED_MARKUP = "<b>{0}</b>"
SUMMARY_DATA_PANEL_MAX_LEN = 15
SUMMARY_DATA_PANEL_SECTION_TITLE = "Section"
FILE_CONTENT_PANEL_OPT_TIP = "Content available for file."
FILE_CONTENT_PANEL_TIP = "Content included in file"

# Tooltip (hover-over) text

TREE_PANEL_TIP_ADDED_CONFIG = 'Added configuration since the last save'
TREE_PANEL_TIP_ADDED_VARS = 'Added variable(s) since the last save'
TREE_PANEL_TIP_CHANGED_CONFIG = 'Modified since the last save'
TREE_PANEL_TIP_CHANGED_SECTIONS = 'Modified section data since the last save'
TREE_PANEL_TIP_CHANGED_VARS = 'Modified variable data since the last save'
TREE_PANEL_TIP_DIFF_SECTIONS = 'Added/removed sections since the last save'
TREE_PANEL_TIP_REMOVED_VARS = 'Removed variable(s) since the last save'

KEY_TIP_ADDED = 'Added since the last save.'
KEY_TIP_CHANGED = 'Modified since the last save, old value {0}'
KEY_TIP_CHANGED_COMMENTS = 'Modified comments since the last save.'
KEY_TIP_ENABLED = 'Enabled since the last save.'
KEY_TIP_SECTION_IGNORED = "Section ignored since the last save."
KEY_TIP_TRIGGER_IGNORED = 'Trigger ignored since the last save.'
KEY_TIP_MISSING = 'Removed since the last save.'
KEY_TIP_USER_IGNORED = 'User ignored since the last save.'
TIP_CONFIG_CHOOSE_META = "Enter a metadata identifier for the new config"
TIP_CONFIG_CHOOSE_NAME = "Enter a directory name for the new config."
TIP_CONFIG_CHOOSE_NAME_ERROR = "Invalid directory name for the new config."
TIP_ADD_TO_PAGE = 'Add to page...'
TIP_REVERT_PAGE = 'Revert page to last save'
TIP_SUITE_RUN_ARG = 'Enter extra suite run arguments'
TREE_PANEL_ERROR = ' (1 error)'
TREE_PANEL_ERRORS = ' ({0} errors)'
TREE_PANEL_MODIFIED = ' (modified)'
TERMINAL_TIP_CLOSE = 'Close terminal'
VAR_COMMENT_TIP = "# {0}"
VAR_FLAG_TIP_OPTIONAL = "Flag: optional"
VAR_FLAG_TIP_NO_META = "Flag: no metadata"
VAR_MENU_TIP_ERROR = 'Error '
VAR_MENU_TIP_FIXED = 'Fixed variable (only one allowed value)'
VAR_MENU_TIP_IGNORED = 'Ignored because {0}'
VAR_MENU_TIP_LATENT = 'This variable could be added to the configuration.'
VAR_MENU_TIP_WARNING = 'Warning '
VAR_WIDGET_ENV_INFO = 'Set to environment variable'

# Flags for variable widgets

FLAG_TYPE_DEFAULT = "Default flag"
FLAG_TYPE_ERROR = "Error flag"
FLAG_TYPE_OPTIONAL = "Optional flag"
FLAG_TYPE_NO_META = "No metadata flag"

# Relevant metadata properties

META_PROP_WIDGET = "widget[rose-config-edit]"

# Miscellaneous
COPYRIGHT = '(C) British Crown Copyright 2012 Met Office.'
LAUNCH_COMMAND = 'rose config-edit'
LAUNCH_COMMAND_CONFIG = 'rose config-edit -C'
LAUNCH_SUITE_RUN = 'rose suite-run'
LAUNCH_SUITE_RUN_HELP = 'rose help suite-run'
MIN_PYGTK_VERSION = (2, 12, 0)
PROGRAM_NAME = 'rose edit'
PROJECT_URL = None
UNTITLED_NAME = 'Untitled'
VAR_ID_IN_CONFIG = 'Variable id {0} from the configuration {1}'

override_config = rose.config.ConfigNode()


def false_function(*args):
    """Return False, no matter what the arguments are."""
    return False


def load_override_config():
    override_config = rose.config.default_node()
    if override_config.get(["rose-config-edit"], no_ignore=True) is None:
        return
    for option in override_config.get(["rose-config-edit"]).value.keys():
        value = override_config.get(["rose-config-edit", option]).value
        try:
            cast_value = ast.literal_eval(value)
        except Exception:
            cast_value = value
        globals()[option.replace("-", "_").upper()] = cast_value


load_override_config()
