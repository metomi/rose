.. include:: ../hyperlinks.rst
   :start-line: 1

.. _calendar: https://developer.gnome.org/pygtk/stable/class-gtkcalendar.html
.. _slider: http://www.pygtk.org/pygtk2tutorial/sec-RangeWidgetEample.html
.. _xdot-based: https://github.com/jrfonseca/xdot.py
.. _PEP8: https://www.python.org/dev/peps/pep-0008/
.. _PEP257: https://www.python.org/dev/peps/pep-0257/
.. _RESTful: https://en.wikipedia.org/wiki/Representational_state_transfer
.. _RDBMS: https://en.wikipedia.org/wiki/Relational_database_management_system
.. _JSON: http://www.json.org/


API
===


Introduction
------------

Rose is mainly implemented in `Python`_ and `bash`_.

The sub-sections below explain how to make use of various application
programming interfaces within Rose which are designed for extension. These
are useful for extending Rose components or creating standalone programs that
seek to manipulate Rose information.

Most of these interfaces require a good knowledge of Python.


Rose GTK library
----------------

The Rose/Rosie GUIs (such as the config editor) are written using the Python
bindings for the GTK GUI toolkit (`PyGTK`_). You can write your own custom GTK
widgets and use them within Rose. They should live with the metadata under 
the ``lib/python/widget/`` directory.

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
something based on a `calendar`_ widget) or use a `slider`_ widget for
numbers. You may even want something that uses an image-based interface
such as a latitude-longitude chooser based on a map.

Normally, widgets will be placed within the metadata directory for the suite
or application. Widgets going into the Rose core should be added to the
``lib/python/rose/config_editor/valuewidget/`` directory in a Rose
distribution.

Example
"""""""

See the :ref:`Advanced Tutorial <widget-dev>`.

API Reference
"""""""""""""

All value widgets, custom or core, use the same API. This means that a good
ractical reference is the set of existing value widgets in the package
``rose.config_editor.valuewidget``.

The procedure for implementing a custom value widget is as follows:

Assign a ``widget[rose-config-edit]`` attribute to the relevant variable in the
metadata configuration, e.g.

   .. code-block:: rose

      [namelist:VerifConNL/ScalarAreaCodes]
      widget[rose-config-edit]=module_name.AreaCodeChooser

where the widget class lives in the module ``module_name`` under
``lib/python/widget/`` in the metadata directory for the application or suite.
Modules are imported by the config editor on demand.

This class should have a constructor of the form

   .. code-block:: python

      class AreaCodeChooser(gtk.HBox):

          def __init__(self, value, metadata, set_value, hook, arg_str=None)

with the following arguments:

``value``
  a string that represents the value that the widget should display.

``metadata``
  a map or dictionary of configuration metadata properties for this value,
  such as

  .. code-block:: python

     {'type': 'integer', 'help': 'This is used to count something'}

  You may not need to use this information.

``set_value``
  a function that should be called with a new string value of this widget,
  e.g.

  .. code-block:: python

     set_value("20")

``hook``
  An instance of a class ``rose.config_editor.valuewidget.ValueWidgetHook``
  containing callback functions that you should connect some of your widgets
  to.

``arg_str``
  a keyword argument that stores extra text given to the ``widget`` option
  in the metadata, if any:

  .. code-block:: rose

     widget[rose-config-edit]=modulename.ClassName arg1 arg2 arg3 ...

  would give a ``arg_str`` of ``"arg1 arg2 arg3 ..."``. This could help
  configure your widget - for example, for a table based widget, you might
  give the column names:

  .. code-block:: rose

     widget[rose-config-edit]=table.TableValueWidget NAME ID WEIGHTING

  This means that you can write a generic widget and then configure it for
  different cases. 

``hook`` contains some callback functions that you should implement:

``hook.get_focus(widget) -> None``
  which you should connect your top-level widget (``self``) to as follows:

  .. code-block:: python

     self.grab_focus = lambda: hook.get_focus(my_favourite_focus_widget)

  or define a method in your class

  .. code-block:: python

     def grab_focus(self):
         """Override the focus method, so we can scroll to a particular widget."""
         return hook.get_focus(my_favourite_focus_widget)

  which allows the correct widget (``my_favourite_focus_widget``) in your
  container to receive the focus such as a gtk.Entry
  (``my_favourite_focus_widget``) and will also trigger a scroll action on
  a config editor page. This is important to implement to get the proper
  global find functionality.

``hook.trigger_scroll(widget) -> None``
  accessed by

  .. code-block:: python

     hook.trigger_scroll(my_favourite_focus_widget)

  This should be connected to the ``focus-in-event`` GTK signal of your
  top-level widget (``self``):

  .. code-block:: python

     self.entry.connect('focus-in-event',
                         hook.trigger_scroll)

  This also is used to trigger a config editor page scroll to your widget.

You may implement the following optional methods for your widget, which help
to preserve cursor position when a widget is refreshed:

``set_focus_index(focus_index) -> None``
  A method that takes a number as an argument, which is the current cursor
  position relative to the characters in the variable value:

  .. code-block:: python

     def set_focus_index(self, focus_index):
         """Set the cursor position to focus_index."""
         self.entry.set_position(focus_index)

  For example, a ``focus_index`` of ``0`` means that your widget should set
  the cursor position to the beginning of the value. A ``focus_index`` of
  ``4`` for a variable value of ``Operational`` means that the cursor should
  be placed between the ``r`` and the ``a``.

  This has no real meaning or importance for widgets that don't display
  editable text. If you do not supply this method, the config editor will
  attempt to do the right thing anyway.

``get_focus_index() -> focus_index``
  A method that takes no arguments and returns a number which is the
  current cursor position relative to the characters in the variable value:

  .. code-block:: python

     def get_focus_index(self):
         """Return the cursor position."""
         return self.entry.get_position()

  This has no real meaning or importance for widgets that don't display
  editable text. If you do not supply this method, the config editor will guess
  the cursor position anyway, based on the last change to the variable value.

``handle_type_error(is_in_error) -> None``
  The default behaviour when a variable error is added or removed is to
  re-instantiate the widget (refresh and redraw it). This can be overridden
  by defining this method in your value widget class. It takes a boolean
  ``is_in_error`` which is ``True`` if there is a value (type) error and
  ``False`` otherwise:

  .. code-block:: python

     def handle_type_error(self, is_in_error):
         """Change behaviour based on whether the variable is_in_error."""
         icon_id = gtk.STOCK_DIALOG_ERROR if is_in_error else None
         self.entry.set_icon_from_stock(0, gtk.STOCK_DIALOG_ERROR)

  For example, this is used in a built-in widget for the quoted string
  types ``string`` and ``character``. The quotes around the text are
  normally hidden, but the ``handle_type_error`` shows them if there is an
  error. The method also keeps the keyboard focus, which is the main purpose.

  You may not have much need for this method, as the default error flagging
  and cursor focus handling is normally sufficient.

All the existing variable value widgets are implemented using this API, so
a good resource is the modules within the
``lib/python/rose/config_editor/valuewidget package``.

.. _conf-ed-cust-pages:

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

You may even wish to do something off-the-wall such as an `xdot-based`_
widget set!

API Reference
"""""""""""""

The procedure for generating a custom page widget is as follows:

Assign a ``widget`` option to the relevant namespace in the metadata
configuration, e.g.

   .. code-block:: rose

      [ns:namelist/STASHNUM]
      widget[rose-config-edit]=module_name.MyGreatBigTable

The widget class should have a constructor of the form

   .. code-block:: python

      class MyGreatBigTable(gtk.Table):

          def __init__(self, real_variable_list, missing_variable_list,
                       variable_functions_inst, show_modes_dict,
                       arg_str=None):

The class can inherit from any ``gtk.Container``\-derived class.

The constructor arguments are

``real_variable_list``
  a list of the Variable objects (``x.name``, ``x.value``, ``x.metadata``,
  etc from the ``rose.variable`` module). These are the objects you will
  need to generate your widgets around.

``missing_variable_list``
  a list of 'missing' Variable objects that could be added to the container.
  You will only need to worry about these if you plan to show them by
  implementing the ``'View Latent'`` menu functionality that we'll discuss
  further on.

``variable_functions_inst``
  an instance of the class
  ``rose.config_editor.ops.variable.VariableOperations``. This contains
  methods to operate on the variables. These will update the
  undo stack and take care of any errors. These methods are the only ways that
  you should write to the variable states or values. For documentation, see 
  the module ``lib/python/rose/config_editor/ops/variable.py``.

``show_modes_dict``
  a dictionary that looks like this:

  .. code-block:: python

     show_modes_dict = {'latent': False, 'fixed': False, 'ignored': True,
                        'user-ignored': False, 'title': False,
                        'flag:optional': False, 'flag:no-meta': False}

  which could be ignored for most custom pages, as you need. The meaning of
  the different keys in a non-custom page is:

  ``'latent'``
    False means don't display widgets for variables in the metadata or
    that have been deleted (the ``variable_list.ghosts`` variables)

  ``'fixed'``
    False means don't display widgets for variables if they only have
    one value set in the metadata ``values`` option.

  ``'ignored'``
    False means don't display widgets for variables if they're
    ignored (in the configuration, but commented out).

  ``'user-ignored'``
    (If ``ignored`` is False) False means don't display widgets for
    user-ignored variables. True means always show user-ignored variables.

  ``'title'``
    Short for 'View with no title', False means show the title of a
    variable, True means show the variable name instead.

  ``'flag:optional'``
    True means indicate if a variable is ``optional``, and False means do
    not show an indicator.

  ``'flag:no-meta'``
    True means indicate if a variable has any metadata content, and
    False means do not show an indicator.

  If you wish to implement actions based on changes in these properties
  (e.g. displaying and hiding fixed variables depending on the 'fixed'
  setting), the custom page widget should expose a method named
  ``'show_mode_change'`` followed by the key. However, ``'ignored'`` is
  handled separately (more below). These methods should take a single
  boolean that indicates the display status. For example:

  .. code-block:: python

     def show_fixed(self, should_show)

  The argument ``should_show`` is a boolean. If True, fixed variables should
  be shown. If False, they should be hidden by your custom container.

``arg_str``
  a keyword argument that stores extra text given to the ``widget`` option
  in the metadata, if any:

  .. code-block:: rose

     widget[rose-config-edit] = modulename.ClassName arg1 arg2 arg3 ...

  would give a ``arg_str`` of ``"arg1 arg2 arg3 ..."``. This could help
  configure your widget - for example, for a table based widget, you might
  give the column names:

  .. code-block:: rose

     widget[rose-config-edit] = table.TableValueWidget NAME ID WEIGHTING

  This means that you can write a generic widget and then configure it
  for different cases. 

Refreshing the whole page in order to display a small change to a variable
(the default) can be undesirable. To deal with this, custom page widgets can
optionally expose some variable-change specific methods that do this
themselves. These take a single ``rose.variable.Variable`` instance as an
argument.

``def add_variable_widget(self, variable) -> None``
  will be called when a variable is created.
``def reload_variable_widget(self, variable) -> None``
  will be called when a variable's status is changed, e.g. it goes into
  an error state.
``def remove_variable_widget(self, variable) -> None``
  will be called when a variable is removed.
``def update_ignored(self) -> None``
  will be called to allow you to update ignored widget display, if (for
  example) you show/hide ignored variables. If you don't have any custom
  behaviour for ignored variables, it's worth writing a method that does
  nothing - e.g. one that contains just ``pass``).

If you take the step of using your own variable widgets, rather than the
``VariableWidget`` class in ``lib/python/rose/config_editor/variable.py``
(the default for normal config-edit pages), each variable-specific widget
should have an attribute ``variable`` set to their ``rose.variable.Variable``
instance. You can implement 'ignored' status display by giving the widget a
method ``set_ignored`` which takes no arguments. This should examine the
``ignored_reason`` dictionary attribute of the widget's ``variable``
instance - the variable is ignored if this is not empty. If the variable is
ignored, the widget should indicate this e.g. by greying out part of it.

All existing page widgets use this API, so a good resource is the modules in
``lib/python/rose/config_editor/pagewidget/``.

Generally speaking, a visible change, click, or key press in the custom page
widget should make instant changes to variable value(s), and the value that
the user sees. Pages are treated as temporary, superficial views of variable
data, and changes are always assumed to be made directly to the main copy
of the configuration in memory (this is automatic when the
``rose.config_editor.ops.variable.VariableOperations`` methods are used, as
they should be). Closing the page shouldn't change, or lose, any data!
The custom class should return a gtk object to be packed into the page
framework, so it's best to subclass from an existing gtk Container type
such as ``gtk.VBox`` (or ``gtk.Table``, in the example above).

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
"""""""""""""

The procedure for generating a custom sub panel widget is as follows:

Assign a ``widget[rose-config-edit:sub-ns]`` option to the relevant
namespace in the metadata configuration, e.g.

   .. code-block:: rose

      [ns:namelist/all_the_foo_namelists]
      widget[rose-config-edit:sub-ns]=module_name.MySubPanelForFoos

Note that because the actual data on the page has a separate representation,
you need to write ``[rose-config-edit:sub-ns]`` rather than just
``[rose-config-edit]``.

The widget class should have a constructor of the form

   .. code-block:: python

      class MySubPanelForFoos(gtk.VBox):

          def __init__(self, section_dict, variable_dict,
                       section_functions_inst, variable_functions_inst,
                       search_for_id_function, sub_functions_inst,
                       is_duplicate_boolean, arg_str=None):

The class can inherit from any ``gtk.Container``\-derived class.

The constructor arguments are:

``section_dict``
  a dictionary (map, hash) of section name keys and section data object
  values (instances of the ``rose.section.Section`` class). These contain
  some of the data such as section ignored status and comments that you may
  want to present. These objects can usually be used by the
  ``section_functions_inst`` methods as arguments - for example, passed in
  in order to ignore or enable a section.

``variable_dict``
  a dictionary (map, hash) of section name keys and lists of variable data
  objects (instances of the ``rose.variable.Variable`` class). These contain
  useful information for the variable (option) such as state, value, and
  comments. Like section data objects, these can usually be used as arguments
  to the ``variable_functions_inst`` methods to accomplish things like
  changing a variable value or adding or removing a variable.

``section_functions_inst``
  an instance of the class rose.config_editor.ops.section.SectionOperations.
  This contains methods to operate on the variables. These will update the
  undo stack and take care of any errors. Together with
  ``sub_functions_inst``, these methods are the only ways that you should
  write to the section states or other attributes. For documentation, see the
  module ``lib/python/rose/config_editor/ops/section.py``.

``variable_functions_inst``
  an instance of the class
  ``rose.config_editor.ops.variable.VariableOperations``.
  This contains methods to operate on the variables. These will update the
  undo stack and take care of any errors. These methods are the only ways
  that you should write to the variable states or values. For documentation,
  see the module ``lib/python/rose/config_editor/ops/variable.py``.

``search_for_id_function``
  a function that accepts a setting id (a section name, or a variable id)
  as an argument and asks the config editor to navigate to the page for that
  setting. You could use this to allow a click on a section name in your widget
  to launch the page for the section.

``sub_functions_inst``
  an instance of the class
  ``rose.config_editor.ops.group.SubDataOperations``. This contains some
  convenience methods specifically for sub panels, such as operating on many
  sections at once in an optimised way. For documentation, see the module
  ``lib/python/rose/config_editor/ops/group.py``.

``is_duplicate_boolean``
  a boolean that denotes whether or not the sub-namespaces in the summary
  data consist only of duplicate sections (e.g. only ``namelist:foo(1)``,
  ``namelist:foo(2)``, ...). For example, this could be used by your widget to
  decide whether to implement a "Copy section" user option.

``arg_str``
  a keyword argument that stores extra text given to the ``widget`` option
  in the metadata, if any - e.g.:

  .. code-block:: rose

     widget[rose-config-edit:sub-ns] = modulename.ClassName arg1 arg2 arg3 ...

  would give a ``arg_str`` of ``"arg1 arg2 arg3 ..."``. You can use this to
  help configure your widget.

All existing sub panel widgets use this API, so a good resource is the
modules in ``lib/python/rose/config_editor/panelwidget/``.


Rose Macros
-----------

Rose macros manipulate or check configurations, often based on their
metadata. There are four types of macros:

* Checkers (validators) - check a configuration, perhaps using metadata.
* Changers (transformers) - change a configuration e.g. adding/removing
  options.
* Upgraders - these are special transformer macros for upgrading and
  downgrading configurations. (covered in the
  :ref:`Upgrade Macro API <rose-upgr-macros>`)
* Reporters - output information about a configuration.

There are built-in rose macros that handle standard behaviour such as trigger
changing and type checking.

This section explains how to add your own custom macros to transform and
validate configurations. See :ref:`Upgrade Macro API <rose-upgr-macros>` for
upgrade macros.

Macros use a Python API, and should be written in Python, unless you are
doing something very fancy. In the absence of a Python house style, it's
usual to follow the standard Python style guidance (`PEP8`_, `PEP257`_).

They can be run within ``rose config-edit`` or via ``rose macro``.

You should avoid writing checker macros if the checking can be expressed via
metadata.

Location
^^^^^^^^

A module containing macros should be stored under a directory
``lib/python/macros/`` in the metadata for a configuration. This directory
should be a Python package.

When developing macros for Rose internals, macros should be placed in the
``rose.macros`` package in the Rose Python library. They should be referenced
by the ``lib/python/rose/macros/__init__.py`` classes and a call to them can
be added in the ``lib/python/rose/config_editor/main.py module`` if they need
to be run implicitly by the config editor.

Code
^^^^

Examples
""""""""

See the macro :ref:`Advanced Tutorial <macro-dev>`.

API Documentation
"""""""""""""""""

The ``rose.macro.MacroBase`` class (subclassed by all rose macros) is
documented here.

.. TODO - add reference link to Rose Config API page (once added) on 'here'.

API Reference
"""""""""""""

Validator, transformer and reporter macros are python classes which subclass
from ``rose.macro.MacroBase`` (api docs).

.. TODO - add ref link to Rose Config API page (once added) on 'api docs'.

These macros implement their behaviours by providing a ``validate``,
``transform`` or ``report`` method. A macro can contain any combination of
these methods so, for example, a macro might be both a validator and a
transformer.

These methods should accept two ``rose.config.ConfigNode`` (api docs)
instances as arguments - one is the configuration, and one is the metadata
configuration that provides information about the configuration items.

.. TODO - add ref link to Rose Config API page (once added) on 'api docs'.

A validator macro should look like:

   .. code-block:: python

      import rose.macro

      class SomeValidator(rose.macro.MacroBase):

      """This does some kind of check."""

      def validate(self, config, meta_config=None):
          # Some check on config appends to self.reports using self.add_report
          return self.reports

The returned list should be a list of ``rose.macro.MacroReport`` objects
containing the section, option, value, and warning strings for each setting
that is in error. These are initialised behind the scenes by calling the
inherited method ``rose.macro.MacroBase.add_report`` via
``self.add_report``. This has the form:

   .. code-block:: python

      def add_report(self, section=None, option=None, value=None, info=None,
                   is_warning=False):

This means that you should call it with the relevant section first, then the
relevant option, then the relevant value, then the relevant error message,
and optionally a warning flag that we'll discuss later. If the setting is a
section, the option should be ``None`` and the value None. For example,

   .. code-block:: python

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
something *may* be wrong, such as warning when using an
advanced-developer-only option. They are invoked by passing a 5th argument
to ``self.add_report``, ``is_warning``, like so:

   .. code-block:: python

      self.add_report("env",
                      "MY_FAVOURITE_STREAM_EDITOR",
                      editor_value,
                      "Could be 'sed'",
                      is_warning=True)

A transformer macro should look like:

   .. code-block:: python

      import rose.macro

      class SomeTransformer(rose.macro.MacroBase):

      """This does some kind of change to the config."""

      def transform(self, config, meta_config=None):
          # Some operation on config which calls self.add_report for each change.
          return config, self.reports

The returned list should be a list of 4-tuples containing the section,
option, value, and information strings for each setting that was changed
(e.g. added, removed, value changed). If the setting is a section, the
option should be ``None`` and the value None. If an option was removed,
the value should be the old value - otherwise it should be the new one
(added/changed). For example,

   .. code-block:: python

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
directory. This makes it easy to access non-``rose-app.conf`` files (e.g.
in the ``file/`` subdirectory).

There are also reporter macros which can be used where you need to output
some information about a configuration. A reporter macro takes the same form
as validator and transform macros but does not require a return value.

   .. code-block:: python

       def report(self, config, meta_config=None):
           """ Write some information about the configuration to a report file.

           Note: report methods do not have a return value.

           """
           with open('report/file', 'r') as report_file:
               report_file.write(str(config.get(["namelist:snowflakes"])))

Macros also support the use of keyword arguments, giving you the ability to
have the user specify some input or override to your macro. For example a
transformer macro could be written as follows to allow the user to input
``some_value``:

   .. code-block:: python

      def transform(self, config, meta_config=None, some_value=None):
          """Some transformer macro"""
          return

Note that the extra arguments require default values (``=None`` in this
example) and that you should add error handling for the input accordingly.

On running your macro the user will be prompted to supply values for these
arguments or accept the default values.


.. _rose-upgr-macros:

Rose Upgrade Macros
-------------------

Rose upgrade macros are used to upgrade application configurations between
metadata versions. They are classes, very similar to the Transform macros
above, but with a few differences:

* an ``upgrade`` method instead of a ``transform`` method
* an optional ``downgrade`` method, identical in API to the ``upgrade``
  method, but intended for performing the reverse operation
* a more helpful API via ``rose.upgrade.MacroUpgrade`` methods
* ``BEFORE_TAG`` and ``AFTER_TAG`` attributes - the version of metadata they
  apply to (``BEFORE_TAG``) and the version they upgrade to (``AFTER_TAG``)

An example upgrade macro might look like this:

   .. code-block:: python

      class Upgrade272to273(rose.upgrade.MacroUpgrade):

      """Upgrade from 27.2 to 27.3."""

      BEFORE_TAG = "27.2"
      AFTER_TAG = "27.3"

      def upgrade(self, config, meta_config=None):
          self.add_setting(config, ["env", "NEW_VARIABLE"], "0")
          self.remove_setting(config, ["namelist:old_things", "OLD_VARIABLE"])
          return config, self.reports

The class name is unimportant - the ``BEFORE_TAG`` and ``AFTER_TAG`` identify
the macro.

Metadata versions are usually structured in a ``rose-meta/CATEGORY/VERSION/``
hierarchy - where ``CATEGORY`` denotes the type or family of application
(sometimes it is the command used), and ``VERSION`` is the particular version 
e.g. ``27.2`` or ``HEAD``.

Upgrade macros live under the ``CATEGORY`` directory in a ``versions.py``
file - ``rose-meta/CATEGORY/versions.py``.

If you have many upgrade macros, you may want to separate them into different
modules in the same directory. You can then import from those in
``versions.py``, so that they are still exposed in that module. You'll need
to make your directory a package by creating an ``__init__.py`` file, which
should contain the line ``import versions``. To avoid conflict with other
``CATEGORY`` upgrade modules (or other Python modules), please name these
very modules carefully or use absolute or package level imports like this:
``from .versionXX_YY import FooBar``.

Upgrade macros are subclasses of ``rose.upgrade.MacroUpgrade``. They have all
the functionality of the transform macros documented above.
``rose.upgrade.MacroUpgrade`` also has some additional convenience methods
defined for you to call. All methods return ``None`` unless otherwise
specified.

.. TODO - complete the python API part that goes here


Rosie Web
---------

This section explains how to use the Rosie web service API. All Rosie
discovery services (e.g. ``rosie search``, ``rosie go``, web page) use a
`RESTful`_ API to interrogate a web server, which then interrogates an
`RDBMS`_. Returned data is encoded in the `JSON`_ format.

You may wish to utilise the Python class ``rosie.ws_client.Client`` as an
alternative to this API.

Location
^^^^^^^^

The URLs to access the web API of a Rosie web service (with a given prefix
name) can be found in your rose site configuration file as the value of
``[rosie-id]prefix-ws.PREFIX_NAME``. To access the API for a given repository
with prefix ``PREFIX_NAME``, you must select a format (the only currently
supported format is 'json') and use a url that looks like:

   .. code-block:: none

      http://host/PREFIX_NAME/get_known_keys?format=json

Usage
^^^^^

.. TODO - complete/remove section as desired


Rose Python Modules
-------------------

.. TODO - complete/remove section as desired


Rose Bash Library
-----------------

.. TODO - complete/remove section as desired
