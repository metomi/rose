 .. include:: ../../hyperlinks.rst
    :start-line: 1

.. _tutorial-rose-configurations:

Rose Configurations
===================

:term:`Rose configurations <Rose configuration>` are directories containing a
Rose configuration file along with other optional assets which define behaviour
such as:

* Execution.
* File installation.
* Environment variables.

Rose configurations may be used standalone or alternatively in combination with
the `Cylc`_ workflow engine. There are two types of Rose configuration for use
with `Cylc`_:

:term:`Rose application configuration`
   A runnable Rose configuration which executes a defined command.
:term:`Rose suite configuration`
   A Rose configuration designed to run :term:`Cylc suites <Cylc suite>`.
   For instance it may be used to define Jinja2 variables for use in the
   ``suite.rc`` file.


Rose Configuration Format
-------------------------

Rose configurations are directories containing a Rose configuration file along
with other optional files and directories.

All Rose configuration files use the same format which is based on the `INI`_
file format.

* Comments start with a ``#`` character.
* Settings are written as ``key=value`` pairs.
* Sections are written inside square brackets i.e. ``[section-name]``

Unlike the :ref:`Cylc file format`:

* Sections cannot be nested.
* Settings should not be indented.
* Comments must start on a new line (i.e. you cannot have inline comments).
* There should not be spaces around the ``=`` operator in a ``key=value`` pair.

.. code-block:: rose

   # Comment.
   setting=value

   [section]
   key=value
   multi-line-setting=multi
                     =line
                     =value

Throughout this tutorial we will refer to settings in the following format:

* ``file`` - would refer to a Rose configuration file.
* ``file|setting`` - would refer to a setting in a Rose configuration file.
* ``file[section]`` - would refer to a section in a Rose configuration file.
* ``file[section]setting`` - would refer to a setting in a section in a Rose
  configuration file.


Why Use Rose Configurations?
----------------------------

With Rose configurations the inputs and environment required for a particular
purpose can be encapsulated in a simple human-readable configuration.

Configuration settings can have metadata associated with them which may be used
for multiple purposes including automatic checking and transforming.

Rose configurations can be edited either using a text editor or with
the :ref:`command-rose-config-edit` GUI which makes use of metadata for display
and on-the-fly validation purposes.

.. TODO - add rose edit screenshot.

.. TODO - rename rose config-edit to rose edit.
