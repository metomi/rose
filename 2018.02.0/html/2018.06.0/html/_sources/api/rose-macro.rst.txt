.. _PEP8: https://www.python.org/dev/peps/pep-0008/
.. _PEP257: https://www.python.org/dev/peps/pep-0257/

.. _api-rose-macro:

Rose Macro API
==============

Rose macros manipulate or check configurations, often based on their
metadata. There are four types of macros:

Checkers (validators)
   Check a configuration, perhaps using metadata.
Changers (transformers)
   Change a configuration e.g. adding/removing options.
Upgraders
   Special transformer macros for upgrading and downgrading configurations
   (covered in the :ref:`Upgrade Macro API <rose-upgr-macros>`).
Reporters
   output information about a configuration.

They can be run within :ref:`command-rose-config-edit` or via
:ref:`command-rose-macro`.

.. note::
   This section covers validator, transformer and reporter macros. For upgrader
   macros see :ref:`Upgrade Macro API <rose-upgr-macros>`.

There are built-in Rose macros that handle standard behaviour such as trigger
changing and type checking.

Macros use a Python API, and should be written in Python, unless you are
doing something very fancy. In the absence of a Python house style, it's
usual to follow the standard Python style guidance (`PEP8`_, `PEP257`_).

.. tip::
   You should avoid writing validator macros if the checking can be expressed
   via :ref:`metadata <metadata values>`.


Location
--------

A module containing macros should be stored under a directory
``lib/python/macros/`` in the metadata for a configuration. This directory
should be a Python package.

When developing macros for Rose internals, macros should be placed in the
:py:mod:`rose.macros` package in the Rose Python library. They should be
referenced by the ``lib/python/rose/macros/__init__.py`` classes and a call to
them can be added in the ``lib/python/rose/config_editor/main.py`` module if
they need to be run implicitly by the config editor.


Writing Macros
--------------

.. note::

   For basic usage see the :ref:`macro tutorial <macro-dev>`.

Validator, transformer and reporter macros are Python classes which subclass
from :py:class:`rose.macro.MacroBase` (:ref:`API <api-rose-macro-base>`).

These macros implement their behaviours by providing a ``validate``,
``transform`` or ``report`` method. A macro can contain any combination of
these methods so, for example, a macro might be both a validator and a
transformer.

These methods should accept two :py:class:`rose.config.ConfigNode`
instances as arguments - one is the configuration, and one is the metadata
configuration that provides information about the configuration items.

.. tip::

   See also :ref:`config-api`.

A validator macro should look like:

.. code-block:: python

   import rose.macro

   class SomeValidator(rose.macro.MacroBase):

   """This does some kind of check."""

   def validate(self, config, meta_config=None):
       # Some check on config appends to self.reports using self.add_report
       return self.reports

The returned list should be a list of :py:class:`rose.macro.MacroReport` objects
containing the section, option, value, and warning strings (info) for each
setting that is in error. These are initialised behind the scenes by calling the
inherited method :py:meth:`rose.macro.MacroBase.add_report` via
:py:meth:`self.add_report`. This has the form:

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
to :py:meth:`self.add_report`, ``is_warning``, like so:

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

.. note::
   The extra arguments require default values (``=None`` in this
   example) and that you should add error handling for the input
   accordingly.

On running your macro the user will be prompted to supply values for these
arguments or accept the default values.


.. _api-rose-macro-base:

Python API
----------

.. automodule:: rose.macro
   :members: MacroBase, MacroReport
