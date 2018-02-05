API
===


Introduction
------------

Rose is mainly implemented in Python and bash.

The sub-sections below explain how to make use of various application
programming interfaces within Rose which are designed for extension. These
are useful for extending Rose components or creating standalone programs that
seek to manipulate Rose information.

Most of these interfaces require a good knowledge of Python.


Rose GTK library
----------------

The Rose/Rosie GUIs (such as the config editor) are written using the Python
bindings for the GTK GUI toolkit (PyGTK). You can write your own custom GTK
widgets and use them within Rose. They should live with the metadata under 
the lib/python/widget/ directory.

Value Widgets
^^^^^^^^^^^^^

Value widgets are used for operating on the values of settings. In the config
editor, they appear next to the menu button and name label. There are builtin
value widgets in Rose such as text entry boxes, radio buttons, and drop-down
menus. These are chosen by the config editor based on metadata - for example,
if a setting has an integer type, the value widget will be a spin button.

The config editor supports adding user-defined custom widgets which replace
the default widgets. These have the same API, but live in the metadata
directories rather than the Rose source code.

For example, you may wish to add widgets that deal with dates (e.g. using
something based on a calendar widget) or use a slider widget for numbers.
You may even want something that uses an image-based interface such as a
latitude-longitude chooser based on a map.

Normally, widgets will be placed within the metadata directory for the suite
or application. Widgets going into the Rose core should be added to the
lib/python/rose/config_editor/valuewidget/ directory in a Rose distribution.
Example

See the Advanced Tutorial.
API Reference

All value widgets, custom or core, use the same API. This means that a good
ractical reference is the set of existing value widgets in the package
rose.config_editor.valuewidget.

The procedure for implementing a custom value widget is as follows:

Assign a widget[rose-config-edit] attribute to the relevant variable in the
metadata configuration, e.g.

[namelist:VerifConNL/ScalarAreaCodes]
widget[rose-config-edit]=module_name.AreaCodeChooser

where the widget class lives in the module module_name under
lib/python/widget/ in the metadata directory for the application or suite.
Modules are imported by the config editor on demand.

This class should have a constructor of the form

class AreaCodeChooser(gtk.HBox):

    def __init__(self, value, metadata, set_value, hook, arg_str=None)

with the following arguments

value
    a string that represents the value that the widget should display.
metadata

    a map or dictionary of configuration metadata properties for this value,
such as

    {'type': 'integer', 'help': 'This is used to count something'}

    You may not need to use this information.
set_value

    a function that should be called with a new string value of this widget,
e.g.

    set_value("20")

hook

    An instance of a class rose.config_editor.valuewidget.ValueWidgetHook
containing callback functions that you should connect some of your widgets to.
arg_str

    a keyword argument that stores extra text given to the widget option in
the metadata, if any:

    widget[rose-config-edit]=modulename.ClassName arg1 arg2 arg3 ...

    would give a arg_str of "arg1 arg2 arg3 ...". This could help configure
your widget - for example, for a table based widget, you might give the 
column names
    :

    widget[rose-config-edit]=table.TableValueWidget NAME ID WEIGHTING

    This means that you can write a generic widget and then configure it for
different cases. 

hook contains some callback functions that you should implement:

hook.get_focus(widget) -> None

    which you should connect your top-level widget (self) to as follows:

        self.grab_focus = lambda: hook.get_focus(my_favourite_focus_widget)

    or define a method in your class

    def grab_focus(self):
        """Override the focus method, so we can scroll to a particular
widget."""
        return hook.get_focus(my_favourite_focus_widget)

    which allows the correct widget (my_favourite_focus_widget) in your
container to receive the focus such as a gtk.Entry
(my_favourite_focus_widget) and will also trigger a scroll action on a config
editor page. This is important to implement to get the proper global find 
functionality.
hook.trigger_scroll(widget) -> None

    accessed by

        hook.trigger_scroll(my_favourite_focus_widget)

    This should be connected to the focus-in-event GTK signal of your
top-level widget (self):

            self.entry.connect('focus-in-event',
                               hook.trigger_scroll)

    This also is used to trigger a config editor page scroll to your widget.

You may implement the following optional methods for your widget, which help
to preserve cursor position when a widget is refreshed:

set_focus_index(focus_index) -> None

    A method that takes a number as an argument, which is the current cursor
position relative to the characters in the variable value:

    def set_focus_index(self, focus_index):
        """Set the cursor position to focus_index."""
        self.entry.set_position(focus_index)

    For example, a focus_index of 0 means that your widget should set the
cursor position to the beginning of the value. A focus_index of 4 for a
variable value of Operational means that the cursor should be placed between
the r and the a.

    This has no real meaning or importance for widgets that don't display
editable text. If you do not supply this method, the config editor will
attempt to do the right thing anyway.
get_focus_index() -> focus_index

    A method that takes no arguments and returns a number which is the
current cursor position relative to the characters in the variable value:

    def get_focus_index(self):
        """Return the cursor position."""
        return self.entry.get_position()

    This has no real meaning or importance for widgets that don't display
editable text. If you do not supply this method, the config editor will guess
the cursor position anyway, based on the last change to the variable value.
handle_type_error(is_in_error) -> None

    The default behaviour when a variable error is added or removed is to
re-instantiate the widget (refresh and redraw it). This can be overridden
by defining this method in your value widget class. It takes a boolean
is_in_error which is True if there is a value (type) error and False otherwise:

    def handle_type_error(self, is_in_error):
        """Change behaviour based on whether the variable is_in_error."""
        icon_id = gtk.STOCK_DIALOG_ERROR if is_in_error else None
        self.entry.set_icon_from_stock(0, gtk.STOCK_DIALOG_ERROR)

    For example, this is used in a built-in widget for the quoted string
types string and character. The quotes around the text are normally hidden,
but the handle_type_error shows them if there is an error. The method also
keeps the keyboard focus, which is the main purpose.

    You may not have much need for this method, as the default error flagging
and cursor focus handling is normally sufficient.

All the existing variable value widgets are implemented using this API, so
a good resource is the modules within the
lib/python/rose/config_editor/valuewidget package.

Config Editor Custom Pages
^^^^^^^^^^^^^^^^^^^^^^^^^^

A 'page' in the config editor is the container inside a tab or detached tab
that (by default) contains a table of variable widgets. The config editor
allows custom 'pages' to be defined that may or may not use the standard
set of variable widgets (menu button, name, value widget). This allows any
presentation of the underlying variable information.

For example, you may wish to present the variables in a more structured,
two-dimensional form rather than as a simple list. You may want to strip
down or add to the information presented by default - e.g. hiding names or
embedding widgets within a block of help text.

You may even wish to do something off-the-wall such as an xdot-based widget
set!
API Reference

The procedure for generating a custom page widget is as follows:

Assign a widget option to the relevant namespace in the metadata
configuration, e.g.

    [ns:namelist/STASHNUM]
    widget[rose-config-edit]=module_name.MyGreatBigTable

The widget class should have a constructor of the form

    class MyGreatBigTable(gtk.Table):

        def __init__(self, real_variable_list, missing_variable_list,
                     variable_functions_inst, show_modes_dict,
                     arg_str=None):

The class can inherit from any gtk.Container-derived class.

The constructor arguments are

real_variable_list
    a list of the Variable objects (x.name, x.value, x.metadata, etc from
the rose.variable module). These are the objects you will need to generate
your widgets around.
missing_variable_list
    a list of 'missing' Variable objects that could be added to the container.
You will only need to worry about these if you plan to show them by
implementing the 'View Latent' menu functionality that we'll discuss
further on.
variable_functions_inst
    an instance of the class
rose.config_editor.ops.variable.VariableOperations.
This contains methods to operate on the variables.
These will update the undo stack and take care of any errors.
These methods are the only ways that you should write to the variable states
or values. For documentation, see the module
lib/python/rose/config_editor/ops/variable.py.
show_modes_dict
    a dictionary that looks like this:

        show_modes_dict = {'latent': False, 'fixed': False, 'ignored': True,
                           'user-ignored': False, 'title': False,
                           'flag:optional': False, 'flag:no-meta': False}

    which could be ignored for most custom pages, as you need. The meaning of
the different keys in a non-custom page is:

    'latent'
        False means don't display widgets for variables in the metadata or
that have been deleted (the variable_list.ghosts variables)
    'fixed'
        False means don't display widgets for variables if they only have
one value set in the metadata values option.
    'ignored'
        False means don't display widgets for variables if they're
ignored (in the configuration, but commented out).
    'user-ignored'
        (If ignored is False) False means don't display widgets for
user-ignored variables. True means always show user-ignored variables.
    'title'
        Short for 'View with no title', False means show the title of a
variable, True means show the variable name instead.
    'flag:optional'
        True means indicate if a variable is optional, and False means do
not show an indicator.
    'flag:no-meta'
        True means indicate if a variable has any metadata content, and
False means do not show an indicator.

    If you wish to implement actions based on changes in these properties
(e.g. displaying and hiding fixed variables depending on the 'fixed'
setting), the custom page widget should expose a method named
'show_mode_change' followed by the key. However, 'ignored' is handled
separately (more below). These methods should take a single boolean that
indicates the display status. For example:

    def show_fixed(self, should_show)

    The argument should_show is a boolean. If True, fixed variables should
be shown. If False, they should be hidden by your custom container.
arg_str

    a keyword argument that stores extra text given to the widget option
in the metadata, if any:

    widget[rose-config-edit] = modulename.ClassName arg1 arg2 arg3 ...

    would give a arg_str of "arg1 arg2 arg3 ...". This could help configure
your widget - for example, for a table based widget, you might give the
column names
    :

    widget[rose-config-edit] = table.TableValueWidget NAME ID WEIGHTING

    This means that you can write a generic widget and then configure it
for different cases. 

Refreshing the whole page in order to display a small change to a variable
(the default) can be undesirable. To deal with this, custom page widgets can
optionally expose some variable-change specific methods that do this
themselves. These take a single rose.variable.Variable instance as an argument.

def add_variable_widget(self, variable) -> None
    will be called when a variable is created.
def reload_variable_widget(self, variable) -> None
    will be called when a variable's status is changed, e.g. it goes into
an error state.
def remove_variable_widget(self, variable) -> None
    will be called when a variable is removed.
def update_ignored(self) -> None
    will be called to allow you to update ignored widget display, if (for
example) you show/hide ignored variables. If you don't have any custom
behaviour for ignored variables, it's worth writing a method that does
nothing - e.g. one that contains just pass).

If you take the step of using your own variable widgets, rather than the
VariableWidget class in lib/python/rose/config_editor/variable.py (the default
for normal config-edit pages), each variable-specific widget should have an
attribute variable set to their rose.variable.Variable instance. You can
implement 'ignored' status display by giving the widget a method set_ignored
which takes no arguments. This should examine the ignored_reason dictionary
attribute of the widget's variable instance - the variable is ignored if
this is not empty. If the variable is ignored, the widget should indicate
this e.g. by greying out part of it.

All existing page widgets use this API, so a good resource is the modules in
lib/python/rose/config_editor/pagewidget/.

Generally speaking, a visible change, click, or key press in the custom page
widget should make instant changes to variable value(s), and the value that
the user sees. Pages are treated as temporary, superficial views of variable
data, and changes are always assumed to be made directly to the main copy
of the configuration in memory (this is automatic when the
rose.config_editor.ops.variable.VariableOperations methods are used, as
they should be). Closing the page shouldn't change, or lose, any data!
The custom class should return a gtk object to be packed into the page
framework, so it's best to subclass from an existing gtk Container type
such as gtk.VBox (or gtk.Table, in the example above).

In line with the general philosophy, metadata should not be critical to
page operations - it should be capable of displaying variables even when
they have no or very little metadata, and still make sense if some
variables are missing or new.

Config Editor Custom Sub Panels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A 'sub panel' or 'summary panel' in the config editor is a panel that
appears at the bottom of a page and is intended to display some summarised
information about sub-pages (sub-namespaces) underneath the page. For
example, the top-level file page, by default, has a sub panel to
summarise the individual file sections.

Any actual data belonging to the page will appear above the sub panel in a
separate representation.

Sub panels are capable of using quite a lot of functionality such as
modifying the sections and options in the sub-pages directly.
API Reference

The procedure for generating a custom sub panel widget is as follows:

Assign a widget[rose-config-edit:sub-ns] option to the relevant namespace
in the metadata configuration, e.g.

    [ns:namelist/all_the_foo_namelists]
    widget[rose-config-edit:sub-ns]=module_name.MySubPanelForFoos

Note that because the actual data on the page has a separate representation,
you need to write [rose-config-edit:sub-ns] rather than just
[rose-config-edit].

The widget class should have a constructor of the form

    class MySubPanelForFoos(gtk.VBox):

        def __init__(self, section_dict, variable_dict,
                     section_functions_inst, variable_functions_inst,
                     search_for_id_function, sub_functions_inst,
                     is_duplicate_boolean, arg_str=None):

The class can inherit from any gtk.Container-derived class.

The constructor arguments are:

section_dict
    a dictionary (map, hash) of section name keys and section data object
values (instances of the rose.section.Section class). These contain some of
the data such as section ignored status and comments that you may want to
present. These objects can usually be used by the section_functions_inst
methods as arguments - for example, passed in in order to ignore or enable
a section.
variable_dict
    a dictionary (map, hash) of section name keys and lists of variable data
objects (instances of the rose.variable.Variable class). These contain useful
information for the variable (option) such as state, value, and comments.
Like section data objects, these can usually be used as arguments to the
variable_functions_inst methods to accomplish things like changing a variable
value or adding or removing a variable.
section_functions_inst
    an instance of the class rose.config_editor.ops.section.SectionOperations.
This contains methods to operate on the variables. These will update the undo
stack and take care of any errors. Together with sub_functions_inst, these
methods are the only ways that you should write to the section states or
other attributes. For documentation, see the module
lib/python/rose/config_editor/ops/section.py.
variable_functions_inst
    an instance of the class
rose.config_editor.ops.variable.VariableOperations.
This contains methods to operate on the variables. These will update the
undo stack and take care of any errors. These methods are the only ways
that you should write to the variable states or values. For documentation,
see the module lib/python/rose/config_editor/ops/variable.py.
search_for_id_function
    a function that accepts a setting id (a section name, or a variable id)
as an argument and asks the config editor to navigate to the page for that
setting. You could use this to allow a click on a section name in your widget
to launch the page for the section.
sub_functions_inst
    an instance of the class rose.config_editor.ops.group.SubDataOperations.
This contains some convenience methods specifically for sub panels, such as
operating on many sections at once in an optimised way. For documentation,
see the module lib/python/rose/config_editor/ops/group.py.
is_duplicate_boolean
    a boolean that denotes whether or not the sub-namespaces in the summary
data consist only of duplicate sections (e.g. only namelist:foo(1),
namelist:foo(2), ...). For example, this could be used by your widget to
decide whether to implement a "Copy section" user option.
arg_str

    a keyword argument that stores extra text given to the widget option
in the metadata, if any - e.g.:

    widget[rose-config-edit:sub-ns] = modulename.ClassName arg1 arg2 arg3 ...

    would give a arg_str of "arg1 arg2 arg3 ...". You can use this to help 
configure your widget.

All existing sub panel widgets use this API, so a good resource is the
modules in lib/python/rose/config_editor/panelwidget/.


Rose Macros
-----------

Rose macros manipulate or check configurations, often based on their
metadata. There are four types of macros:

* Checkers (validators) - check a configuration, perhaps using metadata.
* Changers (transformers) - change a configuration e.g. adding/removing
  options.
* Upgraders - these are special transformer macros for upgrading and
  downgrading configurations. (covered in the Upgrade Macro API)
* Reporters - output information about a configuration.

There are built-in rose macros that handle standard behaviour such as trigger
changing and type checking.

This section explains how to add your own custom macros to transform and
validate configurations. See Upgrade Macro API for upgrade macros.

Macros use a Python API, and should be written in Python, unless you are
doing something very fancy. In the absence of a Python house style, it's
usual to follow the standard Python style guidance (PEP8, PEP257).

They can be run within rose config-edit or via rose macro.

You should avoid writing checker macros if the checking can be expressed via
metadata.

Location
^^^^^^^^

A module containing macros should be stored under a directory
lib/python/macros/ in the metadata for a configuration. This directory should
be a Python package.

When developing macros for Rose internals, macros should be placed in the
rose.macros package in the Rose Python library. They should be referenced by
the lib/python/rose/macros/__init__.py classes and a call to them can be
added in the lib/python/rose/config_editor/main.py module if they need to be
run implicitly by the config editor.

Code
^^^^

Examples

See the macro Advanced Tutorial.
API Documentation

The rose.macro.MacroBase class (subclassed by all rose macros) is documented
here.
API Reference

Validator, transformer and reporter macros are python classes which subclass
from rose.macro.MacroBase (api docs).

These macros implement their behaviours by providing a validate, transform or
report method. A macro can contain any combination of these methods so, for
example, a macro might be both a validator and a transformer.

These methods should accept two rose.config.ConfigNode (api docs) instances
as arguments - one is the configuration, and one is the metadata
configuration that provides information about the configuration items.

A validator macro should look like:

import rose.macro

class SomeValidator(rose.macro.MacroBase):

    """This does some kind of check."""

    def validate(self, config, meta_config=None):
        # Some check on config appends to self.reports using self.add_report
        return self.reports

The returned list should be a list of rose.macro.MacroReport objects
containing the section, option, value, and warning strings for each setting
that is in error. These are initialised behind the scenes by calling the
inherited method rose.macro.MacroBase.add_report via self.add_report. This
has the form:

    def add_report(self, section=None, option=None, value=None, info=None,
                   is_warning=False):

This means that you should call it with the relevant section first, then the
relevant option, then the relevant value, then the relevant error message,
and optionally a warning flag that we'll discuss later. If the setting is a
section, the option should be None and the value None. For example,

    def validate(self, config, meta_config=None):
        editor_value = config.get(["env", "MY_FAVOURITE_STREAM_EDITOR"]).value
        if editor_value != "sed":
            self.add_report("env",                         # Section
                            "MY_FAVOURITE_STREAM_EDITOR",  # Option
                            editor_value,                  # Value
                            "Should be 'sed'!")            # Message
        return self.reports

Validator macros have the option to give warnings, which do not count as
formal errors in the Rose config editor GUI. These should be used when
something may be wrong, such as warning when using an advanced-developer-only
option. They are invoked by passing a 5th argument to self.add_report,
is_warning, like so:

            self.add_report("env",
                            "MY_FAVOURITE_STREAM_EDITOR",
                            editor_value,
                            "Could be 'sed'",
                            is_warning=True)

A transformer macro should look like:

import rose.macro

class SomeTransformer(rose.macro.MacroBase):

    """This does some kind of change to the config."""

    def transform(self, config, meta_config=None):
        # Some operation on config which calls self.add_report for each change.
        return config, self.reports

The returned list should be a list of 4-tuples containing the section,
option, value, and information strings for each setting that was changed
(e.g. added, removed, value changed). If the setting is a section, the
option should be None and the value None. If an option was removed, the
value should be the old value - otherwise it should be the new one
(added/changed). For example,

    def transform(self, config, meta_config=None):
        """Add some more snow control."""
        if config.get(["namelist:snowflakes"]) is None:
            config.set(["namelist:snowflakes"])
            self.add_report(list_of_changes,
                            "namelist:snowflakes", None, None,
                            "Updated snow handling in time for Christmas")
            config.set(["namelist:snowflakes", "l_unique"], ".true.")
            self.add_report("namelist:snowflakes", "l_unique", ".true.",
                            "So far, anyway.")
        return config, self.reports

The current working directory within a macro is always the configuration's
directory. This makes it easy to access non-rose-app.conf files (e.g. in the
file/ subdirectory).

There are also reporter macros which can be used where you need to output
some information about a configuration. A reporter macro takes the same form
as validator and transform macros but does not require a return value.

    def report(self, config, meta_config=None):
        """ Write some information about the configuration to a report file.

        Note: report methods do not have a return value.

        """
        with open('report/file', 'r') as report_file:
            report_file.write(str(config.get(["namelist:snowflakes"])))

Macros also support the use of keyword arguments, giving you the ability to
have the user specify some input or override to your macro. For example a
transformer macro could be written as follows to allow the user to input
some_value:

    def transform(self, config, meta_config=None, some_value=None):
        """Some transformer macro"""
        return

Note that the extra arguments require default values (=None in this example)
and that you should add error handling for the input accordingly.

On running your macro the user will be prompted to supply values for these
arguments or accept the default values.


Rose Upgrade Macros
-------------------

Rose upgrade macros are used to upgrade application configurations between
metadata versions. They are classes, very similar to the Transform macros
above, but with a few differences:

* an upgrade method instead of a transform method
* an optional downgrade method, identical in API to the upgrade method, but
  intended for performing the reverse operation
* a more helpful API via rose.upgrade.MacroUpgrade methods
* BEFORE_TAG and AFTER_TAG attributes - the version of metadata they apply
  to (BEFORE_TAG) and the version they upgrade to (AFTER_TAG)

An example upgrade macro might look like this:

class Upgrade272to273(rose.upgrade.MacroUpgrade):

    """Upgrade from 27.2 to 27.3."""

    BEFORE_TAG = "27.2"
    AFTER_TAG = "27.3"

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["env", "NEW_VARIABLE"], "0")
        self.remove_setting(config, ["namelist:old_things", "OLD_VARIABLE"])
        return config, self.reports

The class name is unimportant - the BEFORE_TAG and AFTER_TAG identify the
macro.

Metadata versions are usually structured in a rose-meta/CATEGORY/VERSION/
hierarchy - where CATEGORY denotes the type or family of application
(sometimes it is the command used), and VERSION is the particular version 
e.g. 27.2 or HEAD.

Upgrade macros live under the CATEGORY directory in a versions.py
file - rose-meta/CATEGORY/versions.py.

If you have many upgrade macros, you may want to separate them into different
modules in the same directory. You can then import from those in versions.py,
so that they are still exposed in that module. You'll need to make your
directory a package by creating an __init__.py file, which should contain
the line import versions. To avoid conflict with other CATEGORY upgrade
modules (or other Python modules), please name these very modules carefully
or use absolute or package level imports like this: from .versionXX_YY import
FooBar.

Upgrade macros are subclasses of rose.upgrade.MacroUpgrade. They have all
the functionality of the transform macros documented above.
rose.upgrade.MacroUpgrade also has some additional convenience methods
defined for you to call. All methods return None unless otherwise specified.

def act_from_files(self, config, downgrade=False)

    A method that takes the app configuration (config, a
rose.config.ConfigNode instance) and an optional boolean downgrade keyword
argument. This initiates a search for etc/VERSION/rose-macro-add.conf and
etc/VERSION/rose-macro-remove.conf, where VERSION is equal to the BEFORE_TAG
of the macro. These files should be Rose app config-like patch files,
containing settings to be added (rose-macro-add.conf) and settings to be
removed (rose-macro-remove.conf). If downgrading (downgrade set to True),
the settings in rose-macro-remove.conf will be added, and the ones in
rose-macro-add.conf removed.

        def upgrade(self, config, meta_config=None):
            self.act_from_files(config)
            return config, self.reports

    Note that you can use other methods (below) as well as this in the
same upgrade.

    If settings are defined in either file, and changes can be made,
the self.reports will be updated automatically.
def add_setting(self, config, keys, value=None, forced=False, state=None,
comments=None, info=None):

    A method that attempts to add the setting defined by the list keys
([section] or [section, option] strings) with the value value to the app
config config. The arguments mostly follow rose.config.ConfigNode 
attributes, and are as follows:

    config
        The application configuration object (rose.config.ConfigNode instance)
    keys
        A list of strings denoting config settings - [section_name] for a
section, [section_name, option_name] for an option. For example, it might
be ["namelist:foo", "bar"].
    value (optional)
        A string or None denoting the new setting value. None should be
used for sections only. Options must have a string value defined.
    forced (optional)
        If the setting already exists, override the value to the new value.
    state (optional)
        Set the state of the new setting (rose.config.ConfigNode
states) - None implies the default, which is
rose.config.ConfigNode.STATE_NORMAL. You may also use
rose.config.ConfigNode.STATE_USER_IGNORED.
    comments (optional)
        A list of comment strings (lines) for the new setting or None.
    info (optional)
        A short string containing no new lines, describing the addition of
the setting.

    Example usage:

        def upgrade(self, config, meta_config=None):
            self.add_setting(config, ["namelist:breakfast_nl", "bacon"], "2",
                             comments=["Mmmm. Bacon."], info="Add for
food:#810")
            return config, self.reports

def change_setting_value(self, config, keys, value, forced=False,
comments=None, info=None):

    A method that attempts to change an existing setting value defined by
keys to a new one (value) in the app config config. The arguments are:

    config, keys, comments, info
        As in add_setting above.
    value
        Required argument, must be a string for option values, and can be
None for section values.
    forced (optional)
        Add the setting if it does not exist.

    Example usage:

        def upgrade(self, config, meta_config=None):
            self.change_setting_value(config, ["namelist:breakfast_nl",
"coffee"], "'more'",
                                      info="Add for food:#820")
            return config, self.reports

def get_setting_value(self, config, keys, no_ignore=False): (-> value)

    A method that returns a setting value or None, functionally similar to
rose.config.ConfigNode.get. The arguments are:

    config, keys

        As in add_setting above.
    no_ignore (optional)
        False means return the setting value if the setting is ignored. True
means return None if the setting is ignored. If the setting is missing, None
is returned.

    Example usage:

        def upgrade(self, config, meta_config=None):
            if self.get_setting_value(
                        config, ["namelist:breakfast_nl", "coffee"]) == "'empty'":
                self.add_setting(config, ["namelist:breakfast_nl", "tea"],
                                 "'extra_strong'")
            return config, self.reports

def remove_setting(self, config, keys, info=None):

    A method that removes a setting defined by keys in config with an
optional info message. The arguments are:

    config, keys, info
        As in add_setting above.

    Example usage:

        def upgrade(self, config, meta_config=None):
            self.remove_setting(config, ["namelist:breakfast_nl", "cheeseburger"],
                                info="Cheeseburgers are for lunch")
            return config, self.reports

    Example of removing an entire namelist:

        def upgrade(self, config, meta_config=None):
            self.remove_setting(config, ["namelist:breakfast_nl"],
                                info="We don't serve breakfast anymore")
            return config, self.reports

def rename_setting(self, config, keys, new_keys, info=None):

    A method that attempts to rename the setting defined by the list keys
([section] or [section, option] strings) to the new name defined by new_keys.
The arguments mostly follow rose.config.ConfigNode attributes, and are as
follows:

    config
        The application configuration object (rose.config.ConfigNode instance)
    keys
        A list of strings denoting config settings - [section_name] for a
section, [section_name, option_name] for an option. For example, it might be
["namelist:foo", "bar_old"].
    new_keys
        A list of strings denoting config settings - [section_name] for a
section, [section_name, option_name] for an option. For example, it might be
["namelist:foo", "bar_new"].
    info (optional)
        A short string containing no new lines, describing the renaming of
the setting.

    Example usage:

        def upgrade(self, config, meta_config=None):
            self.rename_setting(config, ["namelist:breakfast_nl", "bad_coffee"],
                                ["namelist:breakfast_nl", "good_coffee"],
                                info="Mmmm... nicer coffee...")
            return config, self.reports

def enable_setting(self, config, keys, info=None):

    A method to make sure a setting defined by keys in config is not
user-ignored. The arguments are:

    config, keys, info
        As in add_setting above.

    Example usage:

        def upgrade(self, config, meta_config=None):
            self.enable_setting(config, ["namelist:breakfast_nl", "egg_monitoring"])
            return config, self.reports

def ignore_setting(self, config, keys, info=None, state=rose.config.ConfigNode.STATE_USER_IGNORED):

    Inverse of enable_setting, a method to make sure a setting defined by
keys in config is ignored (default state is user-ignored). The arguments are:

    config, keys, info
        As in add_setting above.
    state
        One of rose.config.ConfigNode.STATE_USER_IGNORED (default),
rose.config.ConfigNode.STATE_SYST_IGNORED (trigger-ignored). When using it,
you can just use config.STATE... rather than the full
rose.config.ConfigNode.STATE....

    Example usage:

        def upgrade(self, config, meta_config=None):
            self.ignore_setting(config, ["namelist:breakfast_nl", "milk_bottle_date"])
            return config, self.reports

There is an upgrade macro development tutorial and more examples in the
upgrade file for the upgrade usage tutorial (versions.py), at
$ROSE_HOME/etc/rose-meta/rose-demo-upgrade/versions.py, where $ROSE_HOME
is the path to your local Rose distribution, locatable by invoking rose
--version.


Rosie Web
---------

This section explains how to use the Rosie web service API. All Rosie
discovery services (e.g. rosie search, rosie go, web page) use a RESTful
API to interrogate a web server, which then interrogates an RDBMS.
Returned data is encoded in the JSON format.

You may wish to utilise the Python class rosie.ws_client.Client as an
alternative to this API.

Location
^^^^^^^^

The URLs to access the web API of a Rosie web service (with a given prefix
name) can be found in your rose site configuration file as the value of
[rosie-id]prefix-ws.PREFIX_NAME. To access the API for a given repository
with prefix PREFIX_NAME, you must select a format (the only currently
supported format is 'json') and use a url that looks like:

http://host/PREFIX_NAME/get_known_keys?format=json

Usage
^^^^^

The API contains the following methods:

get_known_keys
    returns the main property names stored for suites (e.g. idx, branch,
owner) plus any additional names specified in the site config and takes
the format argument. For example, entering a URL in a web browser:

    http://host/PREFIX_NAME/get_known_keys?format=json

    may give

    ["access-list", "idx", "branch", "owner", "project", "revision",
"status",  "title"]

get_optional_keys
    returns all unique optional or user-defined property names given in
suite discovery information and takes the format argument. For example,
entering this URL in Firefox:

    http://host/PREFIX_NAME/get_optional_keys?format=json

    may give

    ["access-list", "description", "endgame_status", "operational_flag",
"tag-list"]

get_query_operators
    returns all the SQL-like operators used to compare column values that
you may use in queries (below) (e.g. eq, ne, contains, like) and takes the
format argument. For example, entering this URL in a web browser:

    http://host/PREFIX_NAME/get_query_operators?format=json

    may give

    ["eq", "ge", "gt", "le", "lt", "ne", "contains", "endswith", "ilike",
"like", "match", "startswith"]

query
    takes a list of queries q and the format argument. The syntax of the
query looks like:

    CONJUNCTION+[OPEN_GROUP+]FIELD+OPERATOR+VALUE[+CLOSE_GROUP]

    where

    CONJUNCTION
        and or or
    OPEN_GROUP
        optional, one or more (
    FIELD
        e.g. idx or description
    OPERATOR
        e.g. contains or between, one of the operators returned by
get_query_operators
    VALUE
        e.g. euro4m or 200
    CLOSE_GROUP
        optional, one or more )

    The first CONJUNCTION is technically superfluous. The OPEN_GROUP and
CLOSE_GROUP do not have to be used. Entering this URL in a web browser:

    http://host/PREFIX_NAME/query?q=and+idx+endswith+78&q=or+owner+eq+bob&format=json

    may give

    [{"idx": "mo1-aa078", "branch": "trunk", "revision": 200, "owner": "fred",
      "project": "fred's project.", "title": "fred's awesome suite",
      "status": "M ", "access-list": ["fred", "jack"], "description": "awesome"},
     {"idx": "mo1-aa090", "branch": "trunk", "revision": 350, "owner": "bob",
      "project": "var", "title": "A copy of var.vexcs.", "status": "M ",
      "access-list": ["*"], "operational": "Y"}]

    This returned all current suites that have an idx that ends with 78 and
also all suites that have the owner bob. Each suite is returned as an entry
in a list - each entry is an associative array of property name-value pairs.
These pairs contain all database information about a suite.

    query also takes the optional argument all_revs which switches on
searching older revisions of current suites and deleted suites. For example,
entering this URL in a web browser:

    http://host/mo1/json/query?q=and+idx+endswith+78&all_revs&format=json

    may give

    [{"idx": "mo1-aa078", "branch": "trunk", "revision": 120, "owner": "fred",
      "project": "fred's project.", "title": "fred's new suite",
      "status": "A "}
     {"idx": "mo1-aa078", "branch": "trunk", "revision": 199, "owner": "fred",
      "project": "fred's project.", "title": "fred's awesome suite",
      "status": "M ", "access-list": ["fred", "jack"], "description": "awesome"},
     {"idx": "mo1-aa078", "branch": "trunk", "revision": 200, "owner": "fred",
      "project": "fred's project.", "title": "fred's awesome suite",
      "status": "M ", "access-list": ["fred", "jack"], "description": "awesome"}]

    This returned all past and present suites that have an idx that ends
with 78. You can see that older revisions of the aa078 suite appear.

    You can also use parentheses in your search to group expressions. For
example, entering this URL in a web browser:

    http://host/PREFIX_NAME/query?q=and+(+owner+eq+bob&q=or+owner+eq+fred+)&q=and+project+eq+test&format=json

    would search for all suites that are owned by bob or fred that have the
project test.
search
    takes any number of string arguments and the format argument and returns
a list of matching suites with properties in the same format as query. The
suite database is searched for suites with any property with a value that
contains any of the string arguments. For example, entering this URL in a
web browser:

    http://host/PREFIX_NAME/search?var+bob+nowcast&format=json

    may give

    [{"idx": "mo1-aa090", "branch": "trunk", "revision": 330, "owner": "bob",
      "project": "um", "title": "A copy of um.alpra.", "status": "M ",
      "description": "Bob's UM suite"},
     {"idx": "mo1-aa092", "branch": "trunk", "revision": 340, "owner": "jim",
      "project": "var", "title": "6D Quantum VAR.", "status": "M ",
      "location": "NAE"},
     {"idx": "mo1-aa100", "branch": "trunk", "revision": 352, "owner": "ops_account",
      "project": "nowcast", "title": "The operational Nowcast suite",
      "status": "M ", "ensemble": "yes"}]

    This returned all suites that contain one or more of these search terms.
Each suite is returned as an entry in a list, and each entry is an
associative array of suite property name-value pairs. These pairs contain
all database information about a suite.

    search also takes the optional argument all_revs in the same way as
query, above. This switches on searching older revisions of current suites
and deleted suites. For example, entering this URL in a web browser:

    http://host/PREFIX_NAME/search?var+bob&all_revs&format=json

    may give

    [{"idx": "mo1-aa001", "branch": "trunk", "revision": 120, "owner": "bob",
      "project": "useless", "title": "Bob's useless suite.", "status": "A "},
     {"idx": "mo1-aa001", "branch": "trunk", "revision": 122, "owner": "bob",
      "project": "useless", "title": "Bob's useless suite.", "status": "D "},
     {"idx": "mo1-aa090", "branch": "trunk", "revision": 320, "owner": "bob",
      "project": "um", "title": "A copy of um.alpra.", "status": "A "},
     {"idx": "mo1-aa090", "branch": "trunk", "revision": 321, "owner": "bob",
      "project": "um", "title": "A copy of um.alpra.", "status": "M "},
     {"idx": "mo1-aa090", "branch": "trunk", "revision": 330, "owner": "bob",
      "project": "um", "title": "A copy of um.alpra.", "status": "M "},
     {"idx": "mo1-aa092", "branch": "trunk", "revision": 335, "owner": "jim",
      "project": "var", "title": "6D Quantum VAR.", "status": "A "},
     {"idx": "mo1-aa092", "branch": "trunk", "revision": 338, "owner": "jim",
      "project": "var", "title": "6D Quantum VAR.", "status": "M ",
      "location": "Africa"},
     {"idx": "mo1-aa092", "branch": "trunk", "revision": 340, "owner": "jim",
      "project": "var", "title": "6D Quantum VAR.", "status": "M ",
      "location": "NAE"}]

    This returned all past and present suites that contained a match for at
least one of the search terms. Older versions of suites appear, and you can
also see a deleted suite (aa001).


Rose Python Modules
-------------------

This gives some brief information about Rose python modules. For more
information, see the files themselves.

Rose Main Modules
^^^^^^^^^^^^^^^^^

This section describes the modules under the lib/python/rose package.

rose
    (__init__.py) stores some constants used by Rose programs.
rose.app_run
    callable, Rose application runner.
rose.apps.*
    (package) built-in Rose applications.
rose.bush
    callable, Rose Bush services logic.
rose.c3
    library, implements the C3 algorithm (e.g. to linearise multiple
inheritance).
rose.checksum
    library, determine the MD5 checksum for a file or files in a directory.
rose.config
    library, parses and dumps rose configuration files. Contains the main
configuration object rose.config.ConfigNode which is manipulated in most
rose programs.
rose.config_cli
    callable, implements the rose config command.
rose.config_dump
    callable, implements the rose config-dump command.
rose.config_editor/*
    (package) Rose configuration editor logic. See Rose Config Editor Modules.
rose.config_processor
    library, base class for rose configuration processing.
rose.config_processors
    (package) subclasses for rose configuration processing.
rose.config_tree
    library, representation of a Rose configruation directory.
rose.date
    callable, implements the rose date command. Contains date shift library.
rose.env
    library, handles environment variable substitution.
rose.env_cat
    callable, implements rose env-cat command.
rose.external
    library, contains minimal wrapper functions for calling external programs.
rose.formats
    (package) contains modules that deal with supported format parsing. The
only current supported format is Fortran namelist, through
rose.formats.namelist.
rose.fs_util
    library, file system utilities with event reporting.
rose.gtk
    (package) contains modules that deal with generic GTK operations and
contain shared widgets.
rose.host_select
    callable, ranks and selects host machines.
rose.job_runner
    library, run jobs with multiple processes.
rose.macro
    callable, runs internal and custom macros for an application or suite.
rose.macros
    (package) Built-in macros. See Rose Build-in Macro Modules.
rose.meta_type
    library, classes for the various metadata type groups.
rose.meta_type
    library, data types in a Rose configuration metadata.
rose.metadata_check
    callable, validates configuration metadata.
rose.metadata_gen
    callable, generates template metadata for an application.
rose.metadata_graph
    callable, implement the rose metadata-graph command.
rose.namelist_dump
    callable, dumps namelist files to a Rose configuration object.
rose.opt_parse
    library, contains an optparse.OptionParser subclass. All command-line
option parsing in Rose should use this.
rose.popen
    library, utilities for spawning and monitoring processes.
rose.resource
    library, locates files or directories.
rose.run
    library, base class for application, suite and task runners.
rose.run_source_vc
    library, functions to print out version control information for rose
suite-run.
rose.scheme_handler
    library, logic to load python modules based on named schemes.
rose.section
    library, contains section-specific data utilities. Counterpart of
rose.variable.
rose.stem
    callable, converts user-friendly options for testing code into options
for rose suite-run.
rose.suite_clean
    callable, remove runtime directories of suites.
rose.suite_control
    Invoke control commands (currently gcontrol and shutdown) of a running
suite.
rose.suite_engine_proc
    library, base class and utilities for interacting with a suite engine.
rose.suite_engine_procs
    (package) library for interacting with specific suite engines.
rose.suite_hook
    callable, hooks to suite engine events.
rose.suite_log
    callable, implements the rose suite-log command.
rose.suite_restart
    callable, implements the rose suite-restart command.
rose.suite_run
    callable, suite runner.
rose.suite_scan
    callable, scans for running suites.
rose.task_env
    callable, provides an environment for a suite task.
rose.task_run
    callable, task runner.
rose.upgrade
    library, provides configuration upgrade functionality.
rose.variable
    library, utilities for processing metadata and a basic data structure
used by the config editor to hold values and metadata for options.
rose.ws
    library, logic for web services, e.g. Rose Bush and Rosie Disco.

Rose Config Editor Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^

This section describes the modules under the lib/python/rose/config_editor
package. These are specific to the config editor.

rose.config_editor
    (__init__.py) stores some constants used for display in the config editor.
All of these can be overridden using your user config.
rose.config_editor.keywidget, rose.config_editor.menuwidget,
rose.config_editor.pagewidget (package), rose.config_editor.variable,
rose.config_editor.valuewidget (package)
    These contain GTK code that control the adding/removing/modifying of
options on a config editor tab. These can all be overridden using custom
widgets (especially rose.config_editor.valuewidget modules).
rose.config_editor.loader
    This controls the loading and retrieval of configuration data within the
config editor.
rose.config_editor.main
    This contains the centralised main control code of the config
editor - updates, undo stack, etc.
rose.config_editor.menu
    This module contains the menu for the config editor and various
menu-related functions such as adding and removing sections.
rose.config_editor.page
    This module contains control code for each config editor tab, and
interfaces with rose.config_editor.pagewidget objects (including custom
pages).
rose.config_editor.panel
    This creates and alters the GTK Treeview panel of the config editor.
rose.config_editor.stack
    This holds the Undo and Redo stack templates, and contains various
functions to alter variables. This is the main functional interface for 
custom pages.
rose.config_editor.util
    Various small utilities.
rose.config_editor.window
    Creates the main GTK window of the config editor and provides functions
to launch dialogs.

Rose Built-in Macro Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The lib/python/rose/macros package contains built-in macros that perform
checking against metadata. Most of these are run each time something changes
in the config editor. They can be run on the command line via rose macro.

rose.macros.compulsory
    checks/fixes compulsory sections and options
rose.macros.format
    checks format-specific sections and options, using options in
rose.formats modules
rose.macros.rule
    checks fail-if and warn-if metadata conditions
rose.macros.trigger
    checks trigger validity and transforms configuration ignored states
rose.macros.value
    checks type, range, length, pattern, or values metadata

Rosie Modules
^^^^^^^^^^^^^

This section describes the modules under the lib/python/rosie package.

rosie.browser
    (package) GTK client code for rosie (rosie go).
rosie.browser.history
    Methods and classes for recording suite search history. Used by rosie go.
rosie.browser.main
    Main control code for rosie go.
rosie.browser.result
    Custom widget with methods for displaying suite search results. Used by
rosie go.
rosie.browser.status
    Classes for getting and updating statuses for checked out suites. Used by
rosie go.
rosie.browser.suite
    Contains a wrapper class for handling the creation, copying, checking out
and deleting of suites. Used by rosie go.
rosie.browser.util
    Library of widgets for rosie.browser.
rosie.db
    Interface code to the suite database, called by the web server.
rosie.db_create
    Callable, implements rosa db-create command.
rosie.graph
    Callable, implements rosie graph command.
rosie.suite_id
    Callable, implements the rosie id command to identify suites.
rosie.svn_post_commit
    Callable, implements the rosa svn-post-commit command.
rosie.svn_pre_commit
    Callable, implements the rosa svn-pre-commit command.
rosie.usertools.*
    (package) logic shared by rosa svn-post-commit and rosa svn-pre-commit for
accessing user information, e.g. from Unix password file or LDAP.
rosie.vc
    Callable, implements wrappers to version control system.
rosie.ws
    Callable, Rosie Discovery service (Rosie Disco).
rosie.ws_client
    Library, Rosie Disco clients.
rosie.ws_client_auth
    Library, Rosie Disco client authentication schemes and keyring
management.
rosie.ws_client_cli
    Callable, Rosie Disco CLI clients.


Rose Bash Library
-----------------

They live under lib/bash/. Each module contains a set of functions. To import
a module, load the file into your script. E.g. To load rose_usage, you would
do:

. $ROSE_HOME/lib/bash/rose_usage

The modules are:

rose_init
    Called by rose on initialisation. This is not meant to be a module for
general use.
rose_log
    Provide functions to print log messages.
rose_usage
    If your script has a header similar to the ones used by a Rose command
line utility, you can use this function to print the synopsis section of the
script header.
