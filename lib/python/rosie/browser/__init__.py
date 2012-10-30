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

ACCEL_HISTORY_SHOW = "<Ctrl>H"
ACCEL_REFRESH = "F5"
ACCEL_PREVIOUS_SEARCH = "<Alt>Left"
ACCEL_NEXT_SEARCH = "<Alt>Right"

# Menu, panel and treeview strings

HISTORY_TREEVIEW_ALL_REVISIONS = "View revisions?"
HISTORY_TREEVIEW_PARAMETERS = "Parameters"
HISTORY_TREEVIEW_TYPE = "Type"

RESULT_MENU_CHECKOUT_SUITE = "Checkout Suite"
RESULT_MENU_COPY_SUITE = "Copy Suite"
RESULT_MENU_DELETE_SUITE = "Delete Suite"
RESULT_MENU_DELETE_LOCAL_SUITE = "Delete Working Copy"
RESULT_MENU_EDIT_SUITE = "Edit Suite"
RESULT_MENU_GROUP_COL = "Group Column"
RESULT_MENU_INFO_SUITE = "Info"
RESULT_MENU_LAUNCH_TERMINAL = "Launch Terminal"
RESULT_MENU_RUN_SUITE = "Run Suite"
RESULT_MENU_RUN_SUITE_CUSTOM = "Run Suite ..."
RESULT_MENU_SCHEDULER = "Launch Scheduler"
RESULT_MENU_UNGROUP = "Ungroup"
RESULT_MENU_VIEW_OUTPUT_SUITE = "View Output"
RESULT_MENU_VIEW_SOURCE_SUITE = "View Web"

TOGGLE_ACTION_VIEW_ALL_REVISIONS = 'Toggle view all revisions'
TOGGLE_ACTION_VIEW_AUTHOR = 'View _author'
TOGGLE_ACTION_VIEW_BRANCH = 'View _branch'
TOGGLE_ACTION_VIEW_DATE = 'View _date'
TOGGLE_ACTION_VIEW_FROM_IDX = 'View _from idx'
TOGGLE_ACTION_VIEW_LOCAL = 'View _local'
TOGGLE_ACTION_VIEW_OWNER = 'View _owner'
TOGGLE_ACTION_VIEW_PROJECT = 'View _project'
TOGGLE_ACTION_VIEW_REVISION = 'View _revision'
TOGGLE_ACTION_VIEW_SEARCH_HISTORY = 'Show search history'
TOGGLE_ACTION_VIEW_STATUS = 'View _status'
TOGGLE_ACTION_VIEW_TITLE = 'View _title'

TOP_MENU_ABOUT = '_About'
TOP_MENU_CLEAR_HISTORY = 'Clear history'
TOP_MENU_EDIT = '_Edit'
TOP_MENU_FILE = "_File"
TOP_MENU_GUI_HELP = '_GUI Help'
TOP_MENU_HELP = '_Help'
TOP_MENU_HISTORY = 'Hi_story'
TOP_MENU_NEW_SUITE = '_New Suite...'
TOP_MENU_PREFERENCES = '_Preferences'
TOP_MENU_QUIT = '_Quit'
TOP_MENU_SOURCE = '_Data source'
TOP_MENU_VIEW = '_View'

# Button strings

LABEL_ADD_FILTER = "Add filter"
LABEL_CLEAR_ADVANCED = "Clear filters"
LABEL_HISTORY_BUTTON = "View all revisions"
LABEL_SEARCH_ADVANCED = "Query"
LABEL_SEARCH_BUTTON = "Search"
LABEL_SEARCH_SIMPLE = "Search"

# Error and warning strings

ERROR_CORRUPTED_HISTORY_ITEM = "Corrupted history item"
ERROR_ENTER_SEARCH = "Please enter something to search for."
ERROR_HISTORY_LOAD = "An error occurred when trying to load your search history."
ERROR_HISTORY_WRITE = "Unable to save your search history."
ERROR_INVALID_QUERY = "Invalid query syntax: {0}"
ERROR_MODIFIED_LOCAL_COPY_DELETE = "Error: Local copy has uncommitted changes"
EROOR_NO_NEXT_SEARCH = "No next search"
ERROR_NO_PREVIOUS_SEARCH = "No previous search"
ERROR_PERMISSIONS = ("Error: You do not have the required permissions to " + 
                     "delete this suite")
ERROR_UNRECOGNISED_LAST_SEARCH = "Unrecognised last search type"
ERROR_UNRECOGNISED_NEXT_SEARCH = "Unrecognised next search type"
ERROR_UNRECOGNISED_SEARCH = "Unrecognised search type"

# Status bar strings

STATUS_FETCHING = "Fetching records..."
STATUS_GOT = "{0} records found at {1}"
STATUS_LOCAL_GOT = "{0} local suites found at {1}" 
STATUS_NO_LOCAL_SUITES = "No local suites could be found {0}"
STATUS_SOURCE_CHANGED = "Data source changed to {0}"
STATUS_UPDATE = "updating view..."

# Suite status tips

LOCAL_STATUS_DOWNDATE = "Local copy at newer revision"
LOCAL_STATUS_MODIFIED = "Local copy (modified)"
LOCAL_STATUS_NO = "No local copy"
LOCAL_STATUS_OK = "Local copy"
LOCAL_STATUS_SWITCH = "Local copy on different branch"
LOCAL_STATUS_UPDATE = "Local copy at older revision"

# Dialog text

DIALOG_MESSAGE_CHECKOUT = "checkout {0}"
DIALOG_MESSAGE_CLEAR_HISTORY_CONFIRMATION = ("Delete search history?")
DIALOG_MESSAGE_DELETE_LOCAL_CONFIRM = ("You are about to delete your local" +
                                       " copy of {0}")
DIALOG_MESSAGE_DELETE_CONFIRMATION = ("Warning: you are about to delete " + 
                       "\"{0}\". This will permanently delete all branches, "+ 
                       "trunk and any local copy." + 
                       "\n\nAre you sure you wish to proceed?")
DIALOG_MESSAGE_UNCOMPLETED_FILTER = "Uncompleted filter"                       
DIALOG_TITLE_CHECKOUT = "Checkout"
DIALOG_TITLE_DELETE = "Confirm Delete"
DIALOG_TITLE_HISTORY_ERROR = "History Error"
DIALOG_TITLE_INFO = "Suite Info"
DIALOG_TITLE_UNCOMPLETED_FILTER = "Filter error"

# Tool-tip text

TIP_ADD_FILTER_BUTTON = "Add query filter"
TIP_ADD_FILTER_GROUP = "Add bracket"
TIP_ADDRESS_BAR = "Enter a search url"
TIP_CLEAR_BUTTON = "Clear query filters"
TIP_CLOSE_HISTORY_BUTTON = "Close search history"
TIP_FILTER = "Filter"
TIP_FILTER_ACTION = "Operator"
TIP_FILTER_COLUMN = "Property"
TIP_FILTER_OPERATOR = "Filters operator"
TIP_FILTER_TEXT = "Value"
TIP_HISTORY_BUTTON = "Toggle view all revisions"
TIP_LOCAL_SUITES = "Show local suites"
TIP_NEXT_SEARCH = "Go forward one search"
TIP_PREV_SEARCH = "Go back one search"
TIP_REFRESH = "Refresh"
TIP_REMOVE_FILTER_BUTTON = "Remove query filter"
TIP_REMOVE_FILTER_GROUP = "Remove bracket"
TIP_SEARCH_ADVANCED = "Query by logical expressions"
TIP_SEARCH_BUTTON = "Search database"
TIP_SEARCH_SIMPLE = "Search for text"
TIP_SEARCH_SIMPLE_ENTRY = "Enter text to search for"
TIP_SHOW_HIDE_BUTTON = "Show/hide the advanced search pane"
TIP_STATUSBAR_SOURCE = "Data source"
TIP_TOOLBAR_CHECKOUT = "Checkout"
TIP_TOOLBAR_COPY = "Copy"
TIP_TOOLBAR_EDIT = "Edit"
TIP_TOOLBAR_NEW = "New"
TIP_TOOLBAR_LAUNCH_SCHEDULER = "Launch Scheduler"
TIP_TOOLBAR_LAUNCH_TERMINAL = "Launch Terminal"
TIP_TOOLBAR_VIEW_OUTPUT = "View Output"
TIP_TOOLBAR_VIEW_WEB = "View Web"

# Window settings

COLUMNS_HIDDEN = ["branch", "author", "date", "status", "from_idx"]
PREFIX_LEN = 5
SIZE_WINDOW = (900, 600)
SIZE_WINDOW_NEW_SUITE = (500, 400)
SIZE_TOP_TREES = 100
SIZE_LEFT_TREE = 600
TITLEBAR = "{0} - rosie go"

# Window titles and text

LABEL_ADVANCED_SEARCH = "Advanced Search"
LABEL_EDIT_PROJECT = "New suite project:"
LABEL_ERROR_DISCOVERY = "Ignore errors in suite info?"
LABEL_HISTORY_TREEVIEW = "Search History"
TITLE_NEW_SUITE_WIZARD = "Edit new suite information"
TITLE_ERROR_DISCOVERY = "Errors found"
TITLE_HISTORY_IO_ERROR = "History read/write error"
TITLE_HISTORY_NAVIGATION_ERROR = "History navigation error"
TITLE_INVALID_QUERY = "Error"

# Miscellaneous
COPYRIGHT = '(C) British Crown Copyright 2012 Met Office.'
DEFAULT_QUERY = "list_my_suites"
DELIM_KEYVAL = ": "
HELP_URL = None
HISTORY_LOCATION = "~/.metomi/rosie-browse.history"
ICON_PATH_WINDOW = 'etc/images/rosie-icon-trim.png'
ICON_PATH_SCHEDULER = None
LOGO_PATH = 'etc/images/rose-logo.png'
PROGRAM_NAME = "rosie go"
PROJECT_URL = None
SCHEDULER_COMMAND = "cylc gcontrol {0}"
SHOULD_SHOW_ADVANCED_CONTROLS = False
SIZE_ADDRESS = 10
SIZE_HISTORY = 100


def load_override_config():
    """Load any overrides of the above settings."""
    config = rose.config.default_node()
    node = config.get(["rosie-browse"], no_ignore=True)
    if node is None:
        return
    for option, opt_node in node.value.items():
        if opt_node.is_ignored():
            continue
        try:
            cast_value = ast.literal_eval(opt_node.value)
        except Exception:
            cast_value = opt_node.value
        globals()[option.replace("-", "_").upper()] = cast_value


load_override_config()
