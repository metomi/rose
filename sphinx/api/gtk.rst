.. include:: ../hyperlinks.rst
   :start-line: 1

.. _calendar: https://developer.gnome.org/pygtk/stable/class-gtkcalendar.html
.. _slider: http://www.pygtk.org/pygtk2tutorial/sec-RangeWidgetEample.html
.. _xdot-based: https://github.com/jrfonseca/xdot.py

.. _api-gtk:

Rose GTK library
================

The Rose/Rosie GUIs (such as the config editor) are written using the Python
bindings for the GTK GUI toolkit (`PyGTK`_). You can write your own custom GTK
widgets and use them within Rose. They should live with the metadata under 
the ``lib/python/widget/`` directory.

Value Widgets
-------------

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
^^^^^^^

See the :ref:`Advanced Tutorial <widget-dev>`.

API Reference
^^^^^^^^^^^^^

All value widgets, custom or core, use the same API. This means that a good
practical reference is the set of existing value widgets in the package
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

  .. note::
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

  .. note::
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

  .. note::
     This has no real meaning or importance for widgets that don't display
     editable text. If you do not supply this method, the config editor will
     guess the cursor position anyway, based on the last change to the
     variable value.

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

  .. tip::
     You may not have much need for this method, as the default error
     flagging and cursor focus handling is normally sufficient.

.. tip::
   All the existing variable value widgets are implemented using this
   API, so a good resource is the modules within the
   ``lib/python/rose/config_editor/valuewidget`` package.

.. _conf-ed-cust-pages:

Config Editor Custom Pages
--------------------------

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
^^^^^^^^^^^^^

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

.. py:method:: add_variable_widget(self, variable) -> None

   Will be called when a variable is created.
.. py:method:: reload_variable_widget(self, variable) -> None

   Will be called when a variable's status is changed, e.g. it goes into
   an error state.
.. py:method:: remove_variable_widget(self, variable) -> None

   Will be called when a variable is removed.
.. py:method:: update_ignored(self) -> None

   Will be called to allow you to update ignored widget display, if (for
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

.. tip::
   All existing page widgets use this API, so a good resource is the
   modules in ``lib/python/rose/config_editor/pagewidget/``.

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

.. note::
   In line with the general philosophy, metadata should not be critical to
   page operations - it should be capable of displaying variables even when
   they have no or very little metadata, and still make sense if some
   variables are missing or new.

Config Editor Custom Sub Panels
-------------------------------

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
^^^^^^^^^^^^^

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

.. tip::
   All existing sub panel widgets use this API, so a good resource is the
   modules in ``lib/python/rose/config_editor/panelwidget/``.
