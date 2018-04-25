.. include:: ../../hyperlinks.rst
   :start-line: 1

.. _Rose Configuration Format:

Rose Configuration Format
=========================

A configuration in Rose is normally represented by a directory with the
following:

* a configuration file in a modified `INI`_ format.
* (optionally) files containing data that cannot easily be represented by the
  INI format.

We have added the following conventions into the Rose configuration format:

#. The file name is normally called ``rose*.conf``, e.g. :rose:file:`rose.conf`,
   :rose:file:`rose-app.conf`, :rose:file:`rose-meta.conf`, etc.
#. Only a hash ``#`` in the beginning of a line starts a comment. Empty lines
   and lines with only white spaces are ignored. There is no support for
   trailing comments. Comments are normally ignored when a configuration file
   is loaded. However, some comments are loaded if the following conditions
   are met:

   * Comment lines at the beginning of a configuration file up to but not
     including the 1st blank line or the 1st setting are comment lines
     associated with the file. They will re-appear at the top of the file
     when it is re-dumped.
   * Comment lines between a blank line and the next setting, and the
     comment lines between the previous setting and the next setting are
     comments associated with the next setting. The comment lines associated
     with a setting will re-appear before the setting when the file is
     re-dumped.

#. Only the equal sign ``=`` is used to delimit a key-value pair - because the 
   colon ``:`` may be used in keys of namelist declarations.
#. A key-value pair declaration does not have to live under a section 
   declaration. Such a declaration lives directly under the *root* level.
#. Key-value pair declarations following a line with only ``[]`` are placed 
   directly under the root level.
#. Declarations are case sensitive. When dealing with case-insensitive
   inputs such as Fortran logicals or numbers in scientific notation,
   lowercase values should be used.
#. When writing namelist inputs, keys should be lowercase.
#. Declarations start at column 1. Continuations start at column >1.

   * Each line is stripped of leading and trailing spaces.
   * A newline ``\n`` character is prefixed to each continuation line.
   * If a continuation line has a leading equal sign ``=`` character, it is
     stripped from the line. This is useful for retaining leading white 
     spaces in a continuation line.

#. A single exclamation ``!`` or a double exclamation ``!!`` in front of a
   section (i.e. ``[!SECTION]``) or key=value pair (i.e. ``!key=value``)
   denotes an ignored setting.

   * E.g. It will be ignored in run time but may be used by other Rose
     utilities.
   * A single exclamation denotes a user-ignored setting.
   * A double exclamation denotes a program-ignored setting. E.g.
     :ref:`command-rose-config-edit` may use a double exclamation to switch
     off a setting according to the setting metadata.

#. The open square bracket (``[``) and close square bracket (``]``) characters
   cannot be used within a section declaration. E.g.
   ``[[hello]``, ``[hello]]``, ``[hello [world] and beyond]`` should all be
   errors on parsing.
#. If a section is declared twice in a file, the later section will append
   settings to the earlier one. If the same key in the same section is
   declared twice, the later value will override the earlier one. This logic
   applies to the state of a setting as well.
#. Once the file is parsed, declaration ordering is insignificant.

   .. note::
      Do not assume order of environment variables.

#. Values of settings accept syntax such as ``$NAME`` or ``${NAME}`` for
   environment variable substitution.

E.g.

.. code-block:: rose

   # This is line 1 of the comment for this file.
   # This is line 2 of the comment for this file.

   # This comment will be ignored.

   # This is a comment for section-1.
   [section-1]
   # This is a comment for key-1.
   key-1=value 1
   # This comment will be ignored.

   # This is line 1 of the comment for key-2.
   # This is line 2 of the comment for key-2.
   key-2=value 2 line 1
         value 2 line 2
   # This is a comment for key-3.
   key-3=value 3 line 1
        =    value 3 line 2 has leading identation.
        =
        =    value 3 line 3 is blank. This is line 4.

   # section-2 is user-ignored.
   [!section-2]
   key-4=value 4
   # ...

   [section-3]
   # key-5 is program ignored.
   !!key-5=value 5

.. note::
   In this document, the shorthand ``SECTION=KEY=VALUE`` is used to represent a
   ``KEY=VALUE`` pair in a ``[SECTION]`` of an INI format file.


Goals
-----

Suite configurations should be portable between users (at least at the same
site). E.g.: another user should be able to run the same suite:

* without making ANY changes to it.
* without having to add/modify things in their ``$HOME/.profile``.

Input configurations should be programming language neutral.

* Any processing logic should be application/version independent, generic and
  future-proof.
* Data structure should be represented in formats easily understood and
  manipulatable by a human and a computer.

The life cycles of application configurations in a suite may differ from that
of the suite.

* The configuration of an application may be independent of the suite.
* The configuration of an application should be portable between suitable
  suites.

The configurations are independent of the utilities. For example, the
configuration metadata for the suite and application configurations will
drive the Rose config editor GUI, but will not be bound or restricted by it.


.. _Optional Configuration:

Optional Configuration
----------------------

In a Rose configuration directory, we can add an ``opt/`` sub-directory for
optional configuration files. Optional configuration files contain additional
configuration, which can be selected at run time to override the configuration
in the main ``rose-${TYPE}.conf`` file. The name of each optional configuration
should follow the syntax ``rose-${TYPE}-${KEY}.conf``, where ``${KEY}`` is a
short name to describe the override functionality of the optional
configuration file.

A root level ``opts=KEY ...`` setting in the main configuration will tell the
run time program to load the relevant optional configurations in the ``opt/``
sub-directory at run time. Individual Rose utilities may also read optional
configuration keys from environment variables and/or command line options.

Where multiple ``$KEY`` settings are given, the optional configurations are 
applied in that order - for example, a setting:

.. code-block:: rose

   opts=ketchup mayonnaise

implies loading the optional configuration ``rose-app-ketchup.conf`` and then
the optional configuration ``rose-app-mayonnaise.conf``, which may override
the previous one.

By default, a Rose command will fail if an optional configuration file is
missing. However, if you put the optional configuration key in brackets,
then the optional configuration file is allowed to be missing. E.g.:

.. code-block:: rose

   opts=ketchup (mayonnaise)

In the above example, ``rose-app-mayonnaise.conf`` can be missing.

Some Rose utilities (e.g. :ref:`command-rose-suite-run`,
:ref:`command-rose-task-run`, :ref:`command-rose-app-run`, etc) allow
optional configurations to be selected at run time using:

#. The ``ROSE_APP_OPT_CONF_KEYS`` Environment variables.
#. The command line options ``--opt-conf-key=KEY`` or ``-O KEY``.

.. tip::
   See reference of individual commands for detail.

.. note::
   By default optional configurations must exist else an error will
   be raised. To specify an optional configuration which may be missing write
   the name of the configuration inside parenthesis (e.g. ``(foo)``).

Optional Configurations and Metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Metadata utilities such as :ref:`command-rose-app-upgrade` and
:ref:`command-rose-macro` treat each
main + optional configuration as a separate entity to be transformed,
upgraded, or validated. Use cases with more than one optional configuration
are not handled.

When transforming or upgrading, each optional configuration is treated
separately and re-created after the transform as a functional difference
from the main upgraded configuration.

The logic for transforming or upgrading a main configuration ``C`` with
optional configurations ``O1`` and ``O2`` into a new main configuration ``Ct``
and new optional configurations ``O1t`` and ``O2t`` can be represented like
this:

.. code-block:: none

   C => Ct
   C + O1 => C1t
   C + O2 => C2t
   O1t = C1t - Ct
   O2t = C2t - Ct


Import Configuration
--------------------

A root level ``import=PATH1 PATH2...`` setting in the main configuration will
tell Rose utilities to search for configurations at ``PATH1``, ``PATH2`` (and
so on) and inherit configuration and files from them if found.

.. tip::
   At the moment, use of this is only encouraged for configuration metadata.


Re-define Configuration at Run Time
-----------------------------------

Some Rose utilities (e.g. :ref:`command-rose-suite-run`,
:ref:`command-rose-task-run`, :ref:`command-rose-app-run`, etc) allow you
to re-define configuration settings at run time using the
``--define=[SECTION]NAME=VALUE`` or ``-D [SECTION]NAME=VALUE`` options on
the command line. This would add new settings or override any settings
defined in the main and optional configurations. E.g.:

.. code-block:: bash

   # Set [env]FOO=foo, and [env]BAR=bar
   # (Overriding any original settings of [env]FOO or [env]BAR)
   rose task-run -D '[env]FOO=foo' -D '[env]BAR=bar'

   # Switch off [env]BAZ
   rose task-run -D '[env]!BAZ='


.. toctree::
   :name: configuration-toctree
   :caption: More Information
   :maxdepth: 1
   :glob:

   *
