.. include:: ../../hyperlinks.rst
   :start-line: 1

.. _Rose Suites:

Suite Configuration
-------------------

The configuration and functionality of a suite will usually be covered by
the use of `Cylc`_. In which case, most of the suite configuration will live
in the Cylc ``flow.cylc`` file. Otherwise, a suite is just a directory of
files.

A suite directory may contain the following:

* A file called :rose:file:`rose-suite.conf`, a configuration file in the
  modified INI format described above. It stores the information on how to
  install the suite. See :rose:file:`rose-suite.conf` for detail.
* A file called :rose:file:`rose-suite.info`, a configuration file in the
  modified INI format described above. It describes the suite's purpose and
  identity, e.g. the title, the description, the owner, the access control
  list, and other information. Apart from a few standard fields, a suite is
  free to store any information in this file. See :rose:file:`rose-suite.info`
  for detail.
* An ``app/`` directory of application configurations used by the suite.
* A ``bin/`` directory of scripts and utilities used by the suite.
* An ``etc/`` directory of other configurations and resources used the suite.
  E.g. :rose:app:`fcm_make` configurations.
* A ``meta/`` directory containing the suite's configuration metadata.
* ``opt/`` directory. For detail, see :ref:`Optional Configuration`.
* Other items, as long as they do not clash with the scheduler's working
  directories. E.g. for a Cylc suite, ``log*/``, ``share/``, ``state/`` and
  ``work/`` should be avoided.

.. rose:file:: rose-suite.conf

   The suite install configuration file :rose:file:`rose-suite.conf` should
   contain the information on how to install the suite.

   .. rose:conf:: opts

      Hardcode an optional configuration to be used by the suite. It is
      generally better to specify optional configurations using the
      :envvar:`ROSE_SUITE_OPT_CONF_KEYS` environment variable or
      ``--opt-conf-key`` argument both of which work with
      :ref:`command-rose-suite-run`.

   .. rose:conf:: env

      Specify the environment variables to export to the suite daemon. The
      usual ``$NAME`` or ``${NAME}`` syntax can be used in values to reference
      environment variables that are already defined before the suite runner is
      invoked. However, it is unsafe to reference other environment variables
      defined in this section. If the value of an environment variable setting
      begins with a  tilde ``~``, all of the characters preceding the first
      slash ``/`` are considered a *tilde-prefix*. Where possible, a
      tilde-prefix is replaced with the home  directory associated with the
      specified login name at run time.

      .. rose:conf:: KEY=VALUE

         Define an environment variable ``KEY`` with the value ``VALUE``.

      .. rose:conf:: ROSE_VERSION=ROSE_VERSION_NUMBER

         If specified, the version of Rose that starts the suite
         run must match the specified version.

      .. rose:conf:: CYLC_VERSION=CYLC_VERSION_NUMBER

         If specified for a Cylc suite, the Rose suite runner
         will attempt to use this version of cylc.

   .. rose:conf:: template variables

      .. rose:conf:: KEY=VALUE

         Define a variable ``KEY`` with the value ``VALUE`` for use
         in the ``flow.cylc`` file.

         The assignment will be inserted after the hashbang line of the
         installed ``flow.cylc`` file.

         .. versionadded:: 2.0.0

   .. rose:conf:: jinja2:suite.rc

      .. rose:conf:: KEY=VALUE

         Define a `Jinja2`_ variable ``KEY`` with the value ``VALUE`` for use
         in the ``flow.cylc`` file.

         The assignment will be inserted after the ``#!jinja2`` line of the
         installed ``flow.cylc`` file.

         .. versionchanged:: 2.0.0

            :rose:conf:`rose-suite.conf[template variables]`
            are preferred at Rose 2.

   .. rose:conf:: empy:suite.rc

      .. rose:conf:: KEY=VALUE

         Define a `EmPy`_ variable ``KEY`` with the value ``VALUE`` for use
         in the ``flow.cylc`` file.

         The assignment will be inserted after the ``#!empy`` line of the
         installed ``flow.cylc`` file.

         .. versionchanged:: 2.0.0

            :rose:conf:`rose-suite.conf[template variables]`

   .. rose:conf:: [file:NAME]

      Specify a file/directory to be installed. ``NAME`` should be a path
      relative to the run time ``$PWD``.

      E.g. ``file:app/APP=source=LOCATION``.

      For a list of configuration options and details on each see
      :rose:conf:`*[file:TARGET]`.

   .. rose:conf:: meta

      Specify the configuration metadata for the suite. The section may be
      used by various Rose utilities, such as the config editor GUI. It can be
      used to specify the suite type.

.. rose:file:: rose-suite.info

   The suite information file :rose:file:`rose-suite.info` should contain the
   information on identify and the purpose of the suite. It has no sections,
   only ``KEY=VALUE`` pairs. The ``owner``, ``project`` and ``title`` settings
   are compulsory. Otherwise, any ``KEY=VALUE`` pairs can appear in this
   file. If the name of a ``KEY`` ends with ``-list``, the value is expected
   to be a space-delimited list. The following keys are known to have special
   meanings:

   .. rose:conf:: owner

      Specify the user ID of the owner of the suite. The owner has full commit
      access to the suite. Only the owner can delete the suite, pass the suite's
      ownership to someone else or change the :rose:conf:`access-list`.

   .. rose:conf:: project

      Specify the name of the project associated with the suite.

   .. rose:conf:: title

      Specify a short title of the suite.

   .. rose:conf:: access-list

      Specify a list of users with commit access to trunk of the suite. A
      ``*`` in the list means that anyone can commit to the trunk of the
      suite. Setting this blank or omitting the setting means that nobody
      apart from the owner can commit to the trunk. Only the suite owner can
      change the access list.

   .. rose:conf:: description

      Specify a long description of the suite.

   .. rose:conf:: sub-project

      Specify a sub-division of :rose:conf:`project`, if applicable.
