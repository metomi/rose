Configuration Metadata
======================


Format and Location
-------------------

See Configuration Format.

A configuration metadata is itself a configuration. Each configuration
metadata is represented in a directory with the following:

* ``rose-meta.conf``, the main configuration file. See for detail.
* ``opt/`` directory. For detail, see Optional Configuration.
* other files, e.g.:

  * ``lib/python/widget/my_widget.py`` would be the location of a custom
    widget.
  * ``lib/python/macros/my_macro_validator.py`` would be the location of a
    custom macro.
  * ``etc/`` would contain any resources for the logics in ``lib/python/``,
    such as an icon for the custom widget.

Rose utilities will do a path search for metadata using the following in order
of precedence:

* Configuration metadata embedded in the ``meta/`` directory of a suite or an
  application.
* The ``--meta-path=PATH`` option of relevant commands.
* The value of the ``ROSE_META_PATH`` environment variable.
* The ``meta-path`` setting in site/user configurations.

See Metadata Location for more details.

The configuration metadata that controls default behaviour will be located in
``$ROSE_HOME/etc/rose-meta/``.


Configuration Metadata File
---------------------------

The ``rose-meta.conf`` contains a serialised data structure that is an
unordered map (``sections=``) of unordered maps (``keys=values``).

The section name in a configuration metadata file should be a unique ID to
the relevant configuration setting. The syntax of the ID is
``SECTION-NAME=OPTION-NAME`` or just ``SECTION-NAME``. For example,
``env=MY_ENV_NAME`` is the ID of an environment variable called
``MY_ENV_NAME`` in an application configuration file;
``namelist:something_nl=variable_name1`` is the ID of a
namelist variable called ``variable_name1`` in a namelist group called
``something_nl`` in an application configuration file. If the configuration
metadata applies to a section in a configuration file, the ID is just the
section name.

Where multiple instances of a section are used in a configuration file,
ending in brackets with numbers, the metadata id should just be based on the
original section name (for example ``namelist:extract_control(2)`` should be
found in the metadata under ``namelist:extract_control``).

Finally, the configuration metadata may group settings in namespaces, which
may in turn have common configuration metadata settings. The ID for a
namespace set in the metadata is ``ns=NAME``, e.g.
``ns=env/MyFavouriteEnvironmentVars``.

Metadata Inheritance (Import)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A root level ``import=MY_COMMAND1/VERSION1 MY_COMMAND2/VERSION2 ...`` setting
in the ``rose-meta.conf`` file will tell Rose metadata utilities to locate
the meta keys ``MY_COMMAND1/VERSION1``, ``MY_COMMAND2/VERSION2`` (and so on)
and inherit their configuration and files if found.

For example, you might have a ``rose-meta`` directory that contains the
following files and directories:

   .. code-block:: none

      cheese_sandwich/
          vn1.5/
              rose-meta.conf
          vn2.0/
              rose-meta.conf
      cheese/
          vn1.0/
              rose-meta.conf

and write an app referencing this ``rose-meta`` directory that looks like
this:

   .. code-block:: rose

     meta=cheese_sandwich/vn2.0

     [env]
     CHEESE=camembert
     SANDWICH_BREAD=brown

This will reference the metadata at ``rose-meta/cheese_sandwich/vn2.0``.

Now, we can write the ``rose-meta.conf`` file using an import:

   .. code-block:: rose

      import=cheese/vn1.0

      [env=SANDWICH_BREAD]
      values=white,brown,seeded

which will inherit metadata from metadata from
``rose-meta/cheese/vn1.0/rose-meta.conf``.

Metadata Options
^^^^^^^^^^^^^^^^

The metadata options for a configuration fall into 4 categories: sorting,
values, behaviour and help. They are be described separated below:

Metadata for Sorting
^^^^^^^^^^^^^^^^^^^^

These configuration metadata are used for grouping and sorting the IDs of
the configurations.

ns
  A forward slash ``/`` delimited hierarchical namespace for the container of
  the setting, which overrides the default. The default namespace for the
  setting is derived from the first part of the ID - by splitting up the
  section name by colons ``:`` or forward slashes ``/``. For example, a
  configuration with an ID ``namelist:var_minimise=niter_set`` would have
  the namespace ``namelist/var_minimise``. If a namespace is defined for a
  section, it will become the default for all the settings in that section.

  The namespace is used by the config editor to group settings, so that
  they can be placed in different pages. A namespace for a section will
  become the default for all the settings in that section.

  Note that you should not assign namespaces to variables in duplicate
  sections.

sort-key
  A character string that can be used as a sort key for ordering an option
  within its namespace.

  It can also be used to order sections and namespaces.

  The sort-key is used by the config editor to group settings on a page.
  Items with a sort-key will be sorted to the top of a name-space. Items
  without a sort-key will be sorted after, in ascending order of their IDs.

  The sorting procedure in pseudo code is a normal ASCII-like sorting of a
  list of ``setting_sort_key + "~" + setting_id`` strings. If there is no
  ``setting_sort_key``, null string will be used.

  For example, the following metadata:

  .. code-block:: rose

     [env=apple]

     [env=banana]

     [env=cherry]
     sort-key=favourites-01

     [env=melon]
     sort-key=do-not-like-01

     [env=prune]
     sort-key=do-not-like-00

  would produce a sorting order of ``env=prune``, ``env=melon``,
  ``env=cherry``, ``env=apple``, ``env=banana``.

Metadata for Values
^^^^^^^^^^^^^^^^^^^

These configuration metadata are used to define the valid values of a setting. 
A Rose utility such as the config editor can use these metadata to display the
correct widget for a setting and to check its input. However, if the value of
a setting contains a string that looks like an environment variable, these
metadata will normally be ignored.

type
  The type/class of the setting. The type names are based on the intrinsic
  Fortran types, such as ``integer`` and ``real``. Currently supported types
  are:

  ``boolean``
    *example option*: ``PRODUCE_THINGS=true``

    *description*: either ``true`` or ``false``

    *usage*: environment variables, javascript/JSON inputs

  ``character``
    *example option*: ``sea_colour='blue'``

    *description*: Fortran character type - a single quoted string, single
    quotes escaped in pairs

    *usage*: Fortran character types

  ``integer``
    *example option*: ``num_lucky=5``

    *description*: generic integer type

    *usage*: any integer-type input

  ``logical``
    *example option*: ``l_spock=.true.``

    *description*: Fortran logical type - either ``.true.`` or ``.false.``

    *usage*: Fortran logical types

  ``python_boolean``
    *example option*: ``ENABLE_THINGS=True``

    *description*: Python boolean type - either ``True`` or ``False``

    *usage*: Python boolean types

  ``python_list``
    *description*: used to signify a Python-compatible formatted list such
    as ``["Foo", 50, False]``. This encapsulates ``length``, so do not use a
    separate ``length`` declaration for this setting.

    *usage*: use for inputs that expect a string that looks like a Python
    list - e.g. Jinja2 list input variables.

  ``quoted``
    *example option*: ``js_measure_cloud_mode="laser"``

    *description*: a double quoted string, double quotes escaped with
    backslash

    *usage*: Inputs that require double quotes and allow backslash escaping
    e.g. javascript/JSON inputs.

  ``real``
     *example option*: ``n_avogadro=6.02e23``
     
     *description*: Fortran real number type, generic floating point numbers

     *usage*: Fortran real types, generic floating point numbers. Scientific
     notation must use the "e" or "E" format.

     *comment*: Internally implemented within Rose using Python's floating
     point specification.

  ``raw``
    *description*: placeholder used in derived type specifications where
    none of the above types apply

    *usage*: only in derived types

  ``spaced_list``
    *description*: used to signify a space separated list such as
    ``"Foo" 50 False``.

    *usage*: use for inputs that expect a string that contains a number of
    space separated items - e.g. in fcm_make app configs.

  Note that not all inputs need to have ``type`` defined. In some cases
  using ``values`` or ``pattern`` is better.

  A derived type may be defined by a comma ``,`` separated list of intrinsic
  types, e.g. ``integer, character, real, integer``. The default is a raw
  string.

length
  Define the length of an array. If not present, the setting is assumed to
  be a scalar. A positive integer defines a fixed length array. A colon ``:``
  defines a dynamic length array.

  N.B. You do not need to use ``length`` if you already have
  ``type=python_list`` for a setting.

element-titles
  Define a list of comma separated "titles" to appear above array entries.
  If not present then no titles are displayed.

  N.B. where the number of element-titles is greater than the length of the
  array, it will only display titles up to the length of the array.
  Additionally, where the associated array is longer than the number of
  element-titles, blank headings will be placed above them.

values
  Define a comma ``,`` separated list of permitted values of a setting (or an
  element in the setting if it is an array). This metadata overrides the
  ``type``, ``range`` and ``pattern`` metadata.

  For example, the config editor may use this list to determine the widget
  to display the setting. It may display the choices using a set of radio
  buttons if the list of values is small, or a drop down combo box if the list
  of values is large. If the list only contains one value, the config editor
  will expect the setting to always have this value, and may display it as a
  special setting.

value-titles
  Define a comma ``,`` separated list of titles to associate with each of the
  elements of ``values`` which will be displayed instead of the value. This
  list should contain the same number of elements as the ``values`` entry.

  For example, given the following metadata:

  .. code-block:: rose

     [env=HEAT]
     values=0, 1, 2
     value-titles=low, medium, high

  the config editor will display ``low`` for option value ``0``, ``medium``
  for ``1`` and ``high`` for ``2``.

value-hints
  Define a comma ``,`` separated list of suggested values for a variable as
  ``value-hints``, but still allows the user to provide their own override.
  This is like an auto-complete widget.

  For example, given the following metadata:

  .. code-block:: rose

     [env=suggested_fruit]
     value-hints=pineapple,cherry,banana,apple,pear,mango,kiwi,grapes,peach,fig,
                =orange,strawberry,blackberry,blackcurrent,raspberry,melon,plum

  the config editor will display possible option values when the user
  starts typing if they match a suggested value.

range
  Specify a range of values. It can either be a simple comma ``,`` separated
  list of allowed values, or a logical expression in the Rose metadata
  mini-language. This metadata is only valid if ``type`` is either ``integer``
  or ``real``.

  A simple list may contain a mixture of allowed numbers and number ranges
  such as ``1, 2, 4:8, 10:`` (which means the value can be 1, 2, between 4
  and 8 inclusive, or any values greater than or equal to 10.)

  A logical expression uses the Rose metadata mini-language, using the
  variable ``this`` to denote the value of the current setting, e.g.
  ``this <-1 and this >1``. Inter-variable comparisons are not permitted
  (but see the ``fail-if`` property below for a way to implement this).

pattern
  Specify a regular expression (Python's extended regular expression
  syntax) to compare against the whole value of the setting.

  For example, if we write the following metadata:

  .. code-block:: rose

     [namelist:cheese=country_of_origin]
     pattern=^"[A-Z].+"$

  then we expect all valid values for ``country_of_origin`` to start with a
  double quote (``^"``), begin with an uppercase letter (``[A-Z]``), contain
  some other characters or spaces (``.+``), and end with a quote (``"$``).

  If you have an array variable (for example,
  ``TARTAN_PAINT_COLOURS='blue','red','blue'``) and you want to specify a
  pattern that each element of the array must match, you can construct a
  regular expression that repeats and includes commas. For example, if each
  element in our ``TARTAN_PAINT_COLOURS`` array must obey the regular
  expression ``'red'|'blue'``, then we can write:

  .. code-block:: rose

     [env=TARTAN_PAINT_COLOURS]
     length=:
     pattern=^('red'|'blue')(?:,('red'|'blue'))*$

fail-if, warn-if
  Specify a logical expression using the Rose mini-language to validate the
  value of the current setting with respect to other settings. If the logical
  expression evaluates to true in a ``fail-if`` metadata, the system will
  consider the setting in error. On the other hand, in a ``warn-if`` metadata,
  the system will only issue a warning. The logical expression uses a
  Python-like syntax (documented fully in the appendix). It can reference the
  value of the current setting with the ``this`` variable and the value of
  other settings with their IDs. E.g.:

  .. code-block:: rose

     [namelist:test=my_test_var]
     fail-if=this < namelist:test=control_lt_var;

  means that an error will be flagged if the numeric value of ``my_test_var``
  is less than the numeric value of ``control_lt_var``.

  .. code-block:: rose

     fail-if=this != 1 + namelist:test=ctrl_var_1 *
     (namelist:test=ctrl_var_2 - this);

  shows a more complex operation, again with numeric values.

  To check array elements, the ID should be expressed with a bracketed
  index, as in the configuration:

  .. code-block:: rose

     fail-if=this(2) != "'0A'" and this(4) == "'0A'";

  Array elements can also be checked using ``any`` and ``all``. E.g.:

  .. code-block:: rose

     fail-if=any(namelist:test=ctrl_array < this);
     fail-if=all(this == 0);

  Similarly, the number of array elements can be checked using ``len``. E.g.:

  .. code-block:: rose

     fail-if=len(namelist:test=ctrl_array) < this;
     fail-if=len(this) == 0;

  Expressions can be chained together and brackets used:

  .. code-block:: rose

     fail-if=this(4) == "'0A'" and (namelist:test=ctrl_var_1 != "'N'" or
     namelist:test=ctrl_var_2 != "'Y'" or all(namelist:test=ctrl_arr_3 == 'N'));

  Multiple failure conditions can be added, by using a semicolon as the
  separator - the semicolon is optional for a single statement or the last in
  a block, but is recommended. Multiple failure conditions are essentially
  similar to chaining them together with ``or``, but the system can process
  each expression one by one to target the error message.

  .. code-block:: rose

     fail-if=this > 0; this % 2 == 1; this * 3 > 100;

  You can add a message to the error or warning message to make it clearer
  by adding a hash followed by the comment at the end of a configuration
  metadata line:

  .. code-block:: rose

     fail-if=any(namelist:test=ctrl_array % this == 0); # Needs to be common divisor for ctrl_array

  When using multiple failure conditions, different messages can be added
  if they are placed on individual lines:

  .. code-block:: rose

     fail-if=this > 0; # Needs to be less than or equal to 0
             this % 2 == 1; # Needs to be odd
             this * 3 > 100; # Needs to be more than 100/3.

  A slightly different usage of this functionality can do things like
  warn of deprecated content:

  .. code-block:: rose

     warn-if=True;  # This option is deprecated

  This would always evaluate True and give a warning if the setting is
  present.

  Please note: when dividing a real-numbered setting by something, make
  sure that the expression does not actually divide an integer by an
  integer - for example, ``this / 2`` will evaluate as ``0`` if ``this`` has
  a value of ``1``, but ``0.5`` if it has a value of ``1.0``. This is a
  result of Python's implicit typing.

  You can get around this by making sure either the numerator or denominator 
  is a real number - e.g. by rewriting it as ``this / 2.0`` or
  ``1.0 * this / 2``.

Metadata for Behaviour
^^^^^^^^^^^^^^^^^^^^^^

These metadata are used to define how the setting should behave in different
states.

compulsory
  A ``true`` value indicates that the setting should be compulsory. If this
  flag is not set, the setting is optional.

  Compulsory sections should be physically present in the configuration at
  all times. Compulsory options should be physically present in the
  configuration if their parent section is physically present.

  Optional settings can be removed as the user wishes. Compulsory settings
  may however be triggered ignored (see below). For example, the config editor
  may issue a warning if a compulsory setting is not defined. It may also hide
  a compulsory variable that only has a single permitted value.

trigger
  A setting has the following states:

  * normal
  * user ignored (stored in the configuration file with a ``!`` flag, ignored
    at run time)
  * logically ignored (stored in the configuration file with a ``!!`` flag,
    ignored at runtime)

  If a setting is user ignored, the trigger will do nothing. Otherwise:

  * If the logic for a setting in the trigger is fulfilled, it will cause
    the setting to be enabled.
  * If it is not, it will cause the setting to be logically ignored.

  The trigger expression is a list of settings triggered by (different
  values of) this setting. If the values are not given, the setting will be
  triggered only if the current setting is enabled.

  The syntax contains id-values pairs, where the values part is optional.
  Each pair must be separated by a semi-colon. Within each pair, any values
  must be separated from the id by a colon and a space (``:``). Values must
  be formatted in the same way as the setting "values" defined above (i.e.
  comma separated).

  The trigger syntax looks like:

  .. code-block:: rose

     [namelist:trig_nl=trigger_variable]
     trigger=namelist:dep_nl=A;
             namelist:dep_nl=B;
             namelist:value_nl=X: 10;
             env=Y: 20, 30, 40;
             namelist:value_nl=Z: 20;

  In this example:

  * When ``namelist:trig_nl=trigger_variable`` is ignored, all the variables
    in the trigger expression will be ignored, irrespective of its value.
  * When ``namelist:trig_nl=trigger_variable`` is enabled,
    ``namelist:dep_nl=A`` and ``namelist:dep_nl=B`` will both be enabled,
    and the other variables may be enabled according to its value:

    * When the value of the setting is not ``10``, ``20``, ``30``, or ``40``,
      ``namelist:value_nl=X``, ``env=Y`` and ``namelist:value_nl=Z`` will be
      ignored.
    * When the value of the setting is ``10``, ``namelist:value_nl=X`` will be
      enabled, but ``env=Y`` and ``namelist:value_nl=Z`` will be ignored.
    * When the value of the setting is ``20``, ``env=Y`` and
      ``namelist:value_nl=Z`` will be enabled, but ``namelist:value_nl=X``
      will be ignored.
    * When the value of the setting is ``30``, ``env=Y`` will be enabled,
      but ``namelist:value_nl=X`` and ``namelist:value_nl=Z`` will be
      ignored.
    * If the value of the setting contains an environment
      variable-like string, e.g. ``${TEN_MULTIPLE}``, all three will be
      enabled.

  Settings mentioned in trigger expressions will have their default
  state set to ignored unless explicitly triggered. The config editor will
  issue warnings if variables or sections are in the incorrect state when it
  loads a configuration. Triggering thereafter will work as normal.

  Where multiple triggers act on a setting, the setting is triggered only
  if all triggers are active (i.e. an *AND* relationship). For example, for
  the two triggers here:

  .. code-block:: rose

     [env=IS_WATER]
     trigger=env=IS_ICE: true;

     [env=IS_COLD]
     trigger=env=IS_ICE: true;

  the setting ``env=IS_ICE`` is only enabled if both ``env=IS_WATER`` and
  ``env=IS_COLD`` are ``true`` and enabled. Otherwise, it is ignored.

  The trigger syntax also supports a logical expression using the Rose 
  metadata mini-language, in the same way as the ``range`` or ``fail-if``
  metadata. As with ``range``, inter-variable comparisons are disallowed.

  .. code-block:: rose

     [env=SNOWFLAKE_SIDES]
     trigger=env=CUSTOM_SNOWFLAKE_GEOMETRY: this != 6;
             env=SILLY_SNOWFLAKE_GEOMETRY: this < 2;

  In this example, the setting ``env=CUSTOM_SNOWFLAKE_GEOMETRY`` is enabled
  if ``env=SNOWFLAKE_SIDES`` is enabled and not ``6``.
  ``env=SILLY_SNOWFLAKE_GEOMETRY`` is only enabled when
  ``env=SNOWFLAKE_SIDES`` is enabled and less than ``2``. The logical
  expression syntax can be used with non-numeric variables in the same way
  as the fail-if metadata.

duplicate
  Allow duplicated copies of the setting. This is used for sections where
  there may be more than one with the same metadata - for example multiple
  namelist groups of the same name. If this setting is true for a given name,
  the application configuration will accept multiple namelist groups of this
  name. The config editor may then provide the option to clone or copy a
  namelist to generate an additional namelist. Otherwise, the config editor
  may issue warning for configuration sections that are found with multiple
  copies or an index.

macro
  Associate a setting with a comma-delimited set of custom macros (but not
  upgrade macros).

  E.g. for a macro class called ``FibonacciChecker`` in the metadata under
  ``lib/python/macros/fib.py``, we may have:

  .. code-block:: rose

     macro=fib.FibonacciChecker

  This may be used in the config editor to visually associate the setting
  with these macros. If a macro class has both a ``transform`` and a
  ``validate`` method, you can specify which you need by appending the
  method to the name e.g.:

  .. code-block:: rose

     macro=fib.Fibonacci.validate

widget[gui-application]
  Indicate that the gui-application (e.g. config-edit) should use a
  special widget to display this setting.

  E.g. If we want to use a slider instead of an entry box for a floating
  point real number.

  The widget may take space-delimited arguments which would be specified
  after the widget name. E.g. to set up a hypothetical table with named
  columns X, Y, VCT, and Level, we may do:

  .. code-block:: rose

     widget[rose-config-edit]=table.TableWidget X Y VCT Level

  You may override to a Rose built-in widget by specifying a full ``rose``
  class path in Python - for example, to always show radiobuttons for an
  option with ``values`` set:

  .. code-block:: rose

     widget[rose-config-edit]=rose.config_editor.valuewidget.radiobuttons.RadioButtonsValueWidget

  Another useful Rose built-in widget to use is the array element aligning
  page widget, ``rose.config_editor.pagewidget.table.PageArrayTable``. You
  can set this for a section or namespace to make sure each nth variable
  value element lines up horizontally. For example:

  .. code-block:: rose

     [namelist:meal_choices]
     customers='Athos','Porthos','Aramis','d''Artagnan'
     entrees='soup','pate','soup','asparagus'
     main='beef','spaghetti','coq au vin','lamb'
     petits_fours=.false.,.true.,.false.,.true.

  could use the following metadata:

  .. code-block:: rose

     [namelist:meal_choices]
     widget[rose-config-edit]=rose.config_editor.pagewidget.table.PageArrayTable

  to align the elements on the page like this:

  .. code-block:: none

     customers        Athos      Porthos      Aramis      d'Artagnan
     entrees          soup        pate         soup       asparagus
     main             beef      spaghetti   coq au vin       lamb
     petits_fours    .false.     .true.       .false.       .true.

copy-mode (metadata usage with the rose-suite.info file)
  Setting copy-mode in the metadata allows for the field to be either
  ``never`` copied or copied with any value associated to be ``clear``.

  For example: in a rose-suite.info file

  .. code-block:: rose

     [ensemble members]
     copy-mode=never

  Setting the ``ensemble members`` field to include ``copy-mode=never``
  means that the ensemble members field would never be copied.

   .. code-block:: rose

      [additional info]
      copy-mode=clear

  Setting the ``additional info`` field to include ``copy-mode=never`` means
  that the additional info field would be copied, but any value associated
  with it would be cleared.

Metadata for Help
^^^^^^^^^^^^^^^^^

These metadata provide help for a configuration.

url
  A web URL containing help for the setting. For example:

  .. code-block:: rose

     url=http://www.something.com/FOO/view/dev/doc/FOO.html

  For example, the config editor will trigger a web browser to display this
  when a variable name is clicked. A partial URL can be used for variables if
  the variable's section or namespace has a relevant parent url property to
  use as a prefix. For example:

  .. code-block:: rose

     [namelist:foo]
     url=https://www.google.com/search

     [namelist:foo=bar]
     url=?q=nearest+bar

help
  (Long) help for the setting. For example, the config editor will use
  this in a popup dialog for a variable. Embedding variable ids in the help
  string will allow links to the variables to be created within the popup
  dialog box, e.g.

  .. code-block:: rose

     help=Used in conjunction with namelist:Var_DiagnosticsNL=n_linear_adj_test to do something linear.

  Web URLs beginning with ``http://`` will also be presented as links in the
  config editor.

description
  (Medium) description for the setting. For example, the configuration
  editor will use this as part of the hover over text.

  The config editor will also use descriptions set for sections or
  namespaces as page header text (appears at the top of a panel or page),
  with clickable id and URL links as in help. Descriptions set for variables
  may be automatically shown underneath the variable name in the config editor,
  depending on view options.

title
  (Short) title for the setting. For example, the config editor can use
  this specification as the label of a setting, instead of the variable name.


Appendix: Metadata Location
---------------------------

Centralised Rose metadata is referred to with either the ``meta`` or
``project`` top level flag in a configuration. It needs to live in a
system-global-readable location.

Rose utilities will do a path search for metadata using the following in
order of precedence:

* The ``--meta-path=PATH`` option of relevant commands.
* The content of the ``ROSE_META_PATH`` environment variable.
* The ``meta-path`` setting in site/user configurations.

Each of the above settings can be a colon-separated list of paths.

Underneath each directory in the search path should be a hierarchy like the
following:

   .. code-block:: bash

      ${APP}/HEAD/
      ${APP}/${VERSION}/
      ${APP}/versions.py # i.e. the upgrade macros

N.B. A Rose suite info is likely to have no versions.

Note that, in some cases, a number of different executables may share the
same application configuration metadata in which case APP is given a name
which covers all the uses.

The Rose team recommend placing metadata in a ``rose-meta`` directory at the
top of a project's source tree. Central metadata, if any, at the
``meta-path`` location in the site configuration, should be a collection of
regularly-updated subdirectories from all of the relevant projects'
``rose-meta`` directories.

For example, a system ``CHOCOLATE`` may have a flat metadata structure
within the repository:

   .. code-block:: bash

      CHOCOLATE/doc/
      ...
      CHOCOLATE/rose-meta/
      CHOCOLATE/rose-meta/choc-dark/
      CHOCOLATE/rose-meta/choc-milk/
    

and the system ``CAFFEINE`` may have a hybrid structure, with both flat and
hierarchical components:

   .. code-block:: rose

      CAFFEINE/doc/
      ...
      CAFFEINE/rose-meta/caffeine-guarana/
      CAFFEINE/rose-meta/caffeine-coffee/cappuccino/
      CAFFEINE/rose-meta/caffeine-coffee/latte/
      CAFFEINE/rose-meta/caffeine-tea/yorkshire/
      CAFFEINE/rose-meta/caffeine-tea/lapsang/

and a site configuration with:

   .. code-block:: rose

      meta-path=/path/to/rose-meta

We would expect the following directories in ``/path/to/rose-meta``:

   .. code-block:: bash

      /path/to/rose-meta/caffeine-guarana/
      /path/to/rose-meta/caffeine-coffee/
      /path/to/rose-meta/caffeine-tea/
      /path/to/rose-meta/choc-dark/
      /path/to/rose-meta/choc-milk/

with ``caffeine-coffee`` containing subdirectories ``cappuccino`` and
``latte``, and ``caffeine-tea`` containing ``yorkshire`` and ``lapsang``.


Appendix: Upgrade and Versions
------------------------------

Terminology:

The HEAD (i.e. development) version
  The configuration metadata most relevant to the latest revision of the
  source tree.

A named version
  The configuration metadata most relevant to a release, or a particular
  revision, of the software. This will normally be a copy of the HEAD version
  at a given revision, although it may be updated with some backward
  compatible fixes.

Each change in the HEAD version that requires an upgrade procedure should
introduce an upgrade macro. Each upgrade macro will provide the following
information:

* A tag of the configuration which can be applied by this macro (i.e. the
  previous tag).
* A tag of the configuration after the transformation.

This allows our system to build up a chain if multiple upgrades need to be
applied. The tag can be any name, but will normally refer to the ticket
number that introduces the change.

Every new upgrade macro creates a new tagged version. A named version is
simply a tagged version for which a copy of the relevant configuration
metadata is made available.

Named versions for system releases are typically created at the end of the
release process. The associated upgrade macro is typically only required in
order to create the new name tag and, therefore, does not normally alter the
application configuration.

Application configurations can reference the configuration metadata as
follows:

   .. code-block:: rose

      #!cfg
      # Refer to the HEAD version
      # (typically you wouldn't do this since no upgrade process is possible)
      # For flat metadata
      meta=my-command
      # For hierarchical metadata
      meta=/path/to/metadata/my-command/HEAD

      # Refer to a named or tagged version in the flat metadata
      meta=my-command/8.3
      meta=my-command/t123
      # Refer to a named or tagged version in the hierarchical metadata
      meta=/path/to/metadata/my-command/8.3

If a version is defined then the Rose utilities will first look for the
corresponding named version. If this cannot be found then the HEAD version
is used and, if an upgrade is available, a warning will be given to indicate
that the configuration metadata being used requires upgrade macros to be run.
If the version defined does not correspond to a tagged version then a warning
will be given.

Please note that if a hierarchical structure for the metadata is being used,
the ``HEAD`` tag must be specified explictly.

When to create named versions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One option is to create a new named version for each release of your system.
This makes it easy for users to understand. However, if there is a new
release which does not require a change to the metadata then you will still
have to create a new copy and force the user to go through a null upgrade
which may not be desirable. An alternative is to only create a new named
version at releases which require changes. The name then indicates the
metadata is relevant for a particular release and all subsequent releases
(unless an upgrade macro is available to a later release).

It is also possible to make any tagged version between releases a named
version, but it will usually be better not to. In which case, the user will
be using HEAD and will be prompted to upgrade (which is probably what you
want if you're not using a release).

Sharing metadata between different executables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If 2 different commands share the majority of their inputs then you may
choose to use the same configuration metadata for both commands. Any
differences (in terms of available inputs) can then be triggered by the
command in use. Whether this is desirable will partly depend on how many of
the inputs are shared.

One downside of sharing metadata is that your application configuration may
contain (ignored) settings which have no relevance to the command you are
using.

Note that we intend to introduce support for configuration metadata to
include / inherit from other metadata. This may mean that it makes sense to
have separate metadata for different commands even when the majority of
inputs are shared.

Another reason you may want to share metadata is if you have 2 related
commands which you want to configure using the same set of inputs (i.e. a
single application configuration).

This works by setting an alternate command in the application configuration
and then using the ``--command-key`` option to ``rose app-run``.

Using development versions of upgrade macros
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Users will be able to test out development versions of the upgrade macros by
adding a working copy of the relevant branch into their metadata search path.
However, care must be taken when doing this. Running the upgrade macro will
change the ``meta`` setting to refer to the new tag. If the upgrade macro is
subsequently changed or other upgrade macros are added to the chain prior to
this tag (because they get committed to the trunk first) then this will
result in application configurations which have not gone through the correct
upgrade process. Therefore, when using development versions of the upgrade
macros it is safest to not commit any resulting changes (or to use a branch
of the suite which you are happy to discard).


Appendix: Metadata Mini-Language
--------------------------------

The Rose metadata mini-language supports writing a logical expression in
Python-like syntax, using variable ids to reference their associated values.

Expressions are set as the value of metadata properties such as ``fail-if``
and ``range``.

The language is a small sub-set of Python - a limited set of operators is
supported. No built-in object methods, functions, or modules are
supported - neither are control blocks such as ``if``\/``for``, statements
such as ``del`` or ``with``, or defining your own functions or classes.
Anything that requires that kind of power should be in proper Python code
as a macro.

Nevertheless, the language allows considerable power in terms of defining
simple rules for variable values.

Operators
^^^^^^^^^

The following *numeric* operators are supported:

   .. code-block:: rose

      +     # add
      -     # subtract
      *     # multiply
      **    # power or exponent - e.g. 2 ** 3 implies 8
      /     # divide
      //    # integer divide (floor) - e.g. 3 // 2 implies 1
      %     # remainder e.g. 5 % 3 implies 2

The following *string* operators are supported:

   .. code-block:: rose

      +      # concatenate - e.g. "foo" + "bar" implies "foobar"
      *      # self-concatenate some number of times - e.g. "foo" * 2 implies "foofoo"
      %      # formatting - e.g. "foo %s baz" % "bar" implies "foo bar baz"
      in     # contained in (True/False) - e.g. "oo" in "foobar" implies True
      not in # opposite sense of in

      # Where m, n are integers or expressions that evaluate to integers
      # (negative numbers count from the end of the string):
      [n]   # get nth character from string - e.g. "foo"[1] implies "o"
      [m:n] # get slice of string from m to n - e.g. "foobar"[1:5] implies "ooba"
      [m:]  # get slice of string from m onwards - e.g. "foobar"[1:] implies
        "oobar"
      [:n]  # get slice of string up to n - e.g. "foobar"[:5] implies "fooba"

The following *logical* operators are supported:

   .. code-block:: rose

      and   # Logical AND
      or    # Logical OR
      not   # Logical NOT

The following *comparison* operators are supported:

   .. code-block:: rose

      is    # Is the same object as (usually used for 'is none')
      <     # Less than
      >     # Greater than
      ==    # Equal to
      >=    # Greater than or equal to
      <=    # Less than or equal to
      !=    # Not equal to

Operator precedence is intended to be the same as Python. However, with the
current choice of language engine, the ``%`` and ``//`` operators may not
obey this - make sure you force the correct behaviour using brackets.

Constants
^^^^^^^^^

The following are special constants:

   .. code-block:: rose

      None  # Python None
      False # Python False
      True  # Python True

Using Variable Ids
^^^^^^^^^^^^^^^^^^

Putting a variable id in the expression means that when the expression
is evaluated, the string value of the variable is cast and substituted into
the expression.

For example, if we have a configuration that looks like this:

   .. code-block:: rose

      [namelist:zoo]
      num_elephants=2
      elephant_mood='peaceful'

and an expression in the configuration metadata:

   .. code-block:: rose

      namelist:zoo=elephant_mood != 'annoyed' and num_elephants >= 2

then the expression would become:

   .. code-block:: rose

      'peaceful' != 'annoyed' and 2 >= 2

If the variable is not currently available (ignored or missing) then the
expression cannot be evaluated. If inter-variable comparisons are not allowed
for the expression's parent option (such as with ``trigger`` and ``range``)
then referencing other variable ids is not allowed.

In this case the expression would be false.

You may use ``this`` as a placeholder for the current variable id - for
example, the fail-if expression:

   .. code-block:: rose

      [namelist:foo=bar]
      fail-if=namelist:foo=bar > 100 and namelist:foo=bar % 2 == 1

is the same as:

   .. code-block:: rose

      [namelist:foo=bar]
      fail-if=this > 100 and this % 2 == 1

Arrays
^^^^^^

The syntax has some special ways of dealing with variable values that are
arrays - i.e. comma-separated lists.

You can refer to a single element of the value for a given variable id
(or ``this``) by suffixing a number in round brackets - e.g.:

   .. code-block:: none

      namelist:foo=bar(2)

references the second element in the value for ``bar`` in the section
``namelist:foo``. This follows Fortran index numbering and syntax, which
starts at 1 rather than 0 - i.e. referencing the 1st element in the array
``foo`` is written as ``foo(1)``.

If we had a configuration:

   .. code-block:: rose

      [namelist:foo]
      bar='a', 'b', 'c', 'd'

``namelist:foo=bar(2)`` would get substituted in an expression with ``'b'``
when the expression was evaluated. For example, an expression that contained:

   .. code-block:: none

      namelist:foo=bar(2) == 'c'

would be evaluated as:

   .. code-block:: none

      'b' == 'c'

Should you wish to make use of the array length in an expression you can
make use of the ``len`` function, which behaves in the same manner as its
Python and Fortran equivalents to return the array length. For example:

   .. code-block:: none

      len(namelist:foo=bar) > 3

would be expanded to:

   .. code-block:: none

      4 > 3

and evaluate as true.

There are two other special array functions, ``any`` and ``all``, which
behave in a similar fashion to their Python and Fortran equivalents, but
have a different syntax.

They allow you to write a shorthand expression within an ``any()`` or
``all()`` bracket which implies a loop over each array element. For example:

   .. code-block:: none

      any(namelist:foo=bar == 'e')

evaluates true if *any* elements in the value of ``bar`` in the section
``namelist:foo`` are ``'e'``. For the above configuration snippet, this
would be expanded before evaluation to be:

   .. code-block:: none

      'a' == 'e' or 'b' == 'e' or 'c' == 'e' or 'd' == 'e'

Similarly,

   .. code-block:: none

      all(namelist:foo=bar == 'e')

evaluates true if *all* elements are ``'e'``. Again, with the above
configuration, this would be expanded before proper evaluation:

   .. code-block:: none

      'a' == 'e' and 'b' == 'e' and 'c' == 'e' and 'd' == 'e'

Internals
^^^^^^^^^

Rose uses an external engine to evaluate the raw language string after
variable ids and any ``any()`` and ``all()`` functions have been substituted
and expanded.

The current choice of engine is Jinja2, which is responsible for the
details of the supported Pythonic syntax. This may change.

**Do not use any Jinja2-specific syntax.**


Appendix: Config Editor Ignored Mechanics
-----------------------------------------

This describes the intended behaviour of the config editor when there is
an ignored state mismatch for a setting - e.g. a setting might be enabled
when it should be trigger-ignored.

The config editor differs from the strict command line macro equivalent
because the *Switch Off Metadata* mode and accidentally metadata-less
configurations need to be presented in a nice way without lots of
not-necessarily-errors. The config editor should only report the errors
where the state is definitely wrong or makes a material difference to the user.

The table contains error and fixing information for some varieties of
ignored state mismatches. The actual situations are considerably more
varied, given section-ignoring and latent variables - the table holds
the most important varieties.

The ``State`` contains the actual states. The ``Trigger State`` column
contains the trigger-mechanism's expected states. The states can be:

``IT`` - ``!!``
  trigger ignored
``IU`` - ``!``
  user ignored
``E`` - **(normal)**
  enabled

  .. TODO - large table to go here
