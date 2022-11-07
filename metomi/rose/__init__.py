# Copyright (C) British Crown (Met Office) & Contributors.
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
"""This package contains the Python code for Rose utilities.

This module contains the constants that are used globally within these.

"""

# File format syntax
CONFIG_DELIMITER = "="

# Filenames and directory names
CONFIG_NAMES = [
    "rose-app.conf",
    "rose-meta.conf",
    "rose-suite.conf",
    "rose-suite.info",
]
GLOB_CONFIG_FILE = "rose*.conf"
META_CONFIG_NAME = "rose-meta.conf"
CONFIG_META_DIR = "meta"
SUB_CONFIG_NAME = "rose-app.conf"
SUB_CONFIGS_DIR = "app"
SUB_CONFIG_FILE_DIR = "file"
INFO_CONFIG_NAME = "rose-suite.info"
TOP_CONFIG_NAME = "rose-suite.conf"
META_DEFAULT_VN_DIR = "HEAD"

# Optional configurations - not applicable to rose.conf optional configs.
GLOB_OPT_CONFIG_FILE = "rose-*-*.conf"
RE_OPT_CONFIG_FILE = "rose-.*?-(.+).conf$"


# Configuration specification names
CONFIG_SECT_CMD = "command"
CONFIG_SECT_TOP = ""
CONFIG_OPT_META_PATH = "meta-path"
CONFIG_OPT_META_TYPE = "meta"
CONFIG_OPT_OWNER = "owner"
CONFIG_OPT_PROJECT = "project"
INFO_CONFIG_DEFAULT_META_IDS = [
    "=access-list",
    "=description",
    "=owner",
    "=project",
    "=sub-project",
    "=title",
    "=type",
]
SUB_CONFIG_DEFAULT_META_IDS = [
    "=file-install-root",
    "=meta",
    "=mode",
    "=opts",
    "command",
    "file:",
    "poll",
]
CONFIG_SETTING_INDEX_DEFAULT = "1"


# Metadata specification names
META_DIR_MACRO = "macros"
META_DIR_WIDGET = "widget"
META_PROP_COMPULSORY = "compulsory"
META_PROP_COPY_MODE = "copy-mode"
META_PROP_DESCRIPTION = "description"
META_PROP_DUPLICATE = "duplicate"
META_PROP_ELEMENT_TITLES = "element-titles"
META_PROP_FAIL_IF = "fail-if"
META_PROP_HELP = "help"
META_PROP_LENGTH = "length"
META_PROP_MACRO = 'macro'
META_PROP_NS = "ns"
META_PROP_PATTERN = "pattern"
META_PROP_RANGE = "range"
META_PROP_SORT_KEY = "sort-key"
META_PROP_TITLE = "title"
META_PROP_TRIGGER = "trigger"
META_PROP_TYPE = "type"
META_PROP_URL = "url"
META_PROP_VALUES = "values"
META_PROP_VALUE_TITLES = "value-titles"
META_PROP_VALUE_HINTS = "value-hints"
META_PROP_WARN_IF = "warn-if"
META_PROP_WIDGET = "widget"

# Value used to denote copy mode never or clear for a metadata setting.
COPY_MODE_NEVER = "never"
COPY_MODE_CLEAR = "clear"

# Value used to denote "on" for a metadata setting.
META_PROP_VALUE_TRUE = "true"
META_PROP_VALUE_FALSE = "false"  # Not actually used.

# Allowed type settings (that actually do something)
# "meta" and "file" are for internal use.
TYPE_VALUES = [
    "boolean",
    "character",
    "integer",
    "logical",
    "quoted",
    "raw",
    "real",
    "meta",
    "file",
    "python_list",
    "python_boolean",
    "spaced_list",
]

# Preferred Fortran logical and environment boolean syntax
TYPE_BOOLEAN_VALUE_FALSE = "false"
TYPE_BOOLEAN_VALUE_TRUE = "true"
TYPE_LOGICAL_VALUE_FALSE = ".false."
TYPE_LOGICAL_VALUE_TRUE = ".true."
TYPE_LOGICAL_FALSE_TITLE = "false"
TYPE_LOGICAL_TRUE_TITLE = "true"

# Preferred Python boolean syntax
TYPE_PYTHON_BOOLEAN_VALUE_FALSE = "False"
TYPE_PYTHON_BOOLEAN_VALUE_TRUE = "True"

# File variable names in the specification.
FILE_VAR_CHECKSUM = "checksum"
FILE_VAR_MODE = "mode"
FILE_VAR_SOURCE = "source"

# Paths in the Rose distribution.
FILEPATH_README = "README.md"

__version__ = "2.0.2"
