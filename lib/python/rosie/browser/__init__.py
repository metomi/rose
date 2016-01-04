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
"""This package contains the specific Python code driving rosie go.

This module contains constants that are only used in rosie go.

To override constants at runtime, place a section:

[rosie-go]

in your site or user configuration file for Rose, convert the name
of the constants to lowercase, and place constant=value lines in the
section. For example, to override the "ACCEL_REFRESH" constant, you
could put the following in your site or user configuration:

[rosie-go]
accel_refresh="<Ctrl>R"

The values you enter will be cast by Python's ast.literal_eval, so:
foo=100
will be cast to an integer, but:
bar="100"
will be cast to a string.

Generate the user config example help by extracting the 'User-relevant'
flagged blocks of text, e.g. via:

sed -n '/User-relevant:/,/^$/p' __init__.py | \
    sed "s/#/##/g; s/## User-relevant:/#/g; s/^\([A-Z_]\+\) = /\L\1=/g;"

Use this text to update the doc/etc/rose-rug-rosie-go/rose.conf.html
text, remembering to add the [rosie-go] section.

"""

import ast
import os

from rose.resource import ResourceLocator

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
RESULT_MENU_SUITE_GCONTROL = "Launch Suite Control GUI"
RESULT_MENU_UNGROUP = "Ungroup"
RESULT_MENU_VIEW_OUTPUT_SUITE = "View Output"
RESULT_MENU_VIEW_SOURCE_SUITE = "View Web"

TOGGLE_ACTION_VIEW_ALL_REVISIONS = "Toggle search all revisions"
TOGGLE_ACTION_VIEW_SEARCH_HISTORY = "Show search history"

TOP_MENU_ABOUT = "_About"
TOP_MENU_CLEAR_HISTORY = "Clear history"
TOP_MENU_EDIT = "_Edit"
TOP_MENU_FILE = "_File"
TOP_MENU_GUI_HELP = "_GUI Help"
TOP_MENU_HELP = "_Help"
TOP_MENU_HISTORY = "Hi_story"
TOP_MENU_NEW_SUITE = "_New Suite..."
TOP_MENU_PREFERENCES = "_Preferences"
TOP_MENU_QUIT = "_Quit"
TOP_MENU_SOURCE = "_Data source"
TOP_MENU_VIEW = "_View"

# Button strings

LABEL_ADD_FILTER = "Add filter"
LABEL_CLEAR_ADVANCED = "Clear filters"
LABEL_HISTORY_BUTTON = "Search all revisions"
LABEL_SEARCH_ADVANCED = "Query"
LABEL_SEARCH_BUTTON = "Search"
LABEL_SEARCH_SIMPLE = "Search"

# Error and warning strings

ERROR_CORRUPTED_HISTORY_ITEM = "Corrupted history item"
ERROR_ENTER_SEARCH = "Please enter something to search for."
ERROR_HISTORY_LOAD = (
    "An error occurred when trying to load your search history.")
ERROR_HISTORY_WRITE = "Unable to save your search history."
ERROR_INVALID_QUERY = "Invalid query syntax: {0}"
ERROR_MODIFIED_LOCAL_COPY_DELETE = "Error: Local copy has uncommitted changes"
ERROR_NO_NEXT_SEARCH = "No next search"
ERROR_NO_PREVIOUS_SEARCH = "No previous search"
ERROR_PERMISSIONS = ("Error: You do not have the required permissions to " +
                     "delete this suite")
ERROR_PREFIX_UNREACHABLE = "Cannot connect to prefix(es) {0}"
ERROR_UNRECOGNISED_LAST_SEARCH = "Unrecognised last search type"
ERROR_UNRECOGNISED_NEXT_SEARCH = "Unrecognised next search type"
ERROR_UNRECOGNISED_SEARCH = "Unrecognised search type"

# Status bar strings

STATUS_FETCHING = "Fetching records..."
STATUS_GOT = "{0} records found at {1}"
STATUS_LOCAL_GOT = "{0} local suites found at {1}"
STATUS_NO_LOCAL_SUITES = "No local suites could be found in {0} {1}"
STATUS_OPENING_HELP = "Opened help in browser"
STATUS_OPENING_LOG = "Opened web browser on {0}"
STATUS_OPENING_WEB = "Opened suite web view"
STATUS_SOURCE_CHANGED = "Data source changed to {0}"
STATUS_UPDATE = "updating view..."

# Suite status tips

LOCAL_STATUS_CORRUPT = "Local copy (corrupted)"
LOCAL_STATUS_DOWNDATE = "Local copy at newer revision"
LOCAL_STATUS_MODIFIED = "Local copy (modified)"
LOCAL_STATUS_NO = "No local copy"
LOCAL_STATUS_OK = "Local copy"
LOCAL_STATUS_SWITCH = "Local copy on different branch"
LOCAL_STATUS_UPDATE = "Local copy at older revision"

# Dialog text

DIALOG_MESSAGE_CHECKOUT = "checkout {0}"
DIALOG_MESSAGE_CREATE_PREFIX = "Choose a repository to create the new suite:"
DIALOG_MESSAGE_CLEAR_HISTORY_CONFIRMATION = ("Delete search history?")
DIALOG_MESSAGE_DELETE_LOCAL_CONFIRM = ("You are about to delete your local" +
                                       " copy of {0}")
DIALOG_MESSAGE_DELETE_CONFIRMATION = (
    "Warning: you are about to delete " +
    "\"{0}\". This will permanently delete all branches, " +
    "trunk and any local copy." +
    "\n\nAre you sure you wish to proceed?")
DIALOG_MESSAGE_UNCOMPLETED_FILTER = "Uncompleted filter"
DIALOG_MESSAGE_UNREGISTERED_SUITE = ("Cannot launch gcontrol: " +
                                     "suite {0} is not registered.")
DIALOG_TITLE_CHECKOUT = "Checkout"
DIALOG_TITLE_CREATE_PREFIX = "Create"
DIALOG_TITLE_DELETE = "Confirm Delete"
DIALOG_TITLE_HISTORY_ERROR = "History Error"
DIALOG_TITLE_INFO = "Suite Info"
DIALOG_TITLE_UNCOMPLETED_FILTER = "Filter error"
DIALOG_TITLE_UNREGISTERED_SUITE = "Suite not registered"

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
TIP_HISTORY_BUTTON = "Toggle search all revisions"
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
TIP_TOOLBAR_LAUNCH_SUITE_GCONTROL = RESULT_MENU_SUITE_GCONTROL
TIP_TOOLBAR_LAUNCH_TERMINAL = "Launch Terminal"
TIP_TOOLBAR_VIEW_OUTPUT = "View Output"
TIP_TOOLBAR_VIEW_WEB = "View Web"

# Window settings

TITLEBAR = "{0} - rosie go"

# User-relevant: Generic Settings
# Configure a list of columns that should be shown at startup.
COLUMNS_SHOWN = ["local", "idx", "revision", "owner", "title"]
# Configure the width and height of rosie go in pixels (as a tuple).
SIZE_WINDOW = (900, 600)
# Configure the width and height of the suite wizard in pixels (as a tuple).
SIZE_WINDOW_NEW_SUITE = (400, 180)
# Configure the width and height of the info editor in pixels (as a tuple).
SIZE_WINDOW_NEW_SUITE_EDIT = (800, 500)
# Configure the height in pixels of the advanced search panel.
SIZE_TOP_TREES = 100
# Show or hide the advanced search controls (bracketed queries).
SHOULD_SHOW_ADVANCED_CONTROLS = False
# Configure the maximum number of searches or queries to keep in the history.
SIZE_HISTORY = 100

# Window titles and text

LABEL_ADVANCED_SEARCH = "Advanced Search"
LABEL_EDIT_PROJECT = "New suite project:"
LABEL_ERROR_DISCOVERY = "Error against metadata. Abort creating suite?"
LABEL_ERROR_LOCAL = "Unable to retrieve details for local suites."
LABEL_ERROR_PREFIX = "Unable to retrieve settings for prefix: {0}"
LABEL_HISTORY_TREEVIEW = "Search History"
TITLE_NEW_SUITE_WIZARD_FROMID = "Create suite from {0}: edit suite information"
TITLE_NEW_SUITE_WIZARD_PREFIX = "Create suite at {0}: edit suite information"
TITLE_ERROR_DISCOVERY = "Errors found"
TITLE_HISTORY_IO_ERROR = "History read/write error"
TITLE_HISTORY_NAVIGATION_ERROR = "History navigation error"
TITLE_ERROR = "Error"
TITLE_INVALID_PREFIX = "Error"
TITLE_INVALID_QUERY = "Error"

# Miscellaneous
COPYRIGHT = "(C) British Crown Copyright 2012-6 Met Office."
DEFAULT_FILTER_EXPR = "eq"
DEFAULT_QUERY = "list_my_suites"
DELIM_KEYVAL = ": "
HELP_FILE = "rose-rug-rosie-go.html"
HISTORY_LOCATION = "~/.metomi/rosie-browse.history"
ICON_PATH_WINDOW = "etc/images/rosie-icon-trim.png"
ICON_PATH_SCHEDULER = None
LOGO_PATH = "etc/images/rose-logo.png"
PROGRAM_NAME = "rosie go"
PROJECT_URL = "http://github.com/metomi/rose/"
SIZE_ADDRESS = 10
SPLASH_CONFIG = "configuration"
SPLASH_DIRECTOR = "suite director"
SPLASH_HISTORY = "search history"
SPLASH_INITIAL_QUERY = "{0} - running initial query"
SPLASH_LOADING = "{0} - loading {1}"
SPLASH_READY = "{0} - ready"
SPLASH_SEARCH_MANAGER = "search manager"
SPLASH_SETUP_WINDOW = "main window"


def load_override_config():
    """Load any overrides of the above settings."""
    conf = ResourceLocator.default().get_conf()
    for s in ["rosie-browse", "rosie-go"]:
        node = conf.get([s], no_ignore=True)
        if node is None:
            continue
        for key, node in node.value.items():
            if node.is_ignored():
                continue
            try:
                cast_value = ast.literal_eval(node.value)
            except Exception:
                cast_value = node.value
            globals()[key.replace("-", "_").upper()] = cast_value


load_override_config()
