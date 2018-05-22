.. _Rose Applications:

Application Configuration
-------------------------

The configuration of an application is represented by a directory. It may
contain the following:

* :rose:file:`rose-app.conf` - a compulsory configuration file in the
  modified INI format. It contains the following information:

  * the command(s) to run.
  * the metadata type for the application.
  * the list of environment variables.
  * other configurations that can be represented in un-ordered ``key=value``
    pairs, e.g. Fortran namelists.

* ``file/`` directory: other input files, e.g.:

  * FCM configuration files (requires ordering of ``key=value`` pairs).
  * STASH files.
  * other configuration files that require more than ``section=key=value``.

  Files in this directory are copied to the working directory in run time.

  .. note::
     If there is a clash between a ``[file:*]`` section and a file under
     ``file/``, the setting in the ``[file:*]`` section takes precedence.
     E.g. Suppose we have a file ``file/hello.txt``. In the absence of
     ``[file:hello.txt]``, it will copy ``file/hello.txt`` to
     ``$PWD/hello.txt`` in run time. However, if we have a
     ``[file:hello.txt]`` section and a ``source=SOURCE`` setting, then it
     will install the file from ``SOURCE`` instead. If we have
     ``[!file:hello.txt]``, then the file will not be installed at all.

* ``bin/`` directory for e.g. scripts and executables used by the application
  at run time. If a ``bin/`` exists in the application configuration, it will 
  prepended to the ``PATH`` environment variable at run time.
* ``meta/`` directory for the metadata of the application.
* ``opt/`` directory (see :ref:`Optional Configuration`).

E.g. The application configuration directory may look like:

   .. code-block:: bash

      ./bin/
      ./rose-app.conf
      ./file/file1
      ./file/file2
      ./meta/rose-meta.conf
      ./opt/rose-app-extra1.conf
      ./opt/rose-app-extra2.conf
      ...

.. rose:file:: rose-app.conf

   .. rose:conf:: file-install-root

      Root level setting. Specify the root directory to install file targets
      that are specified with a relative path.

   .. rose:conf:: meta

      Root level setting. Specify the configuration metadata for the
      application. This is ignored by the application runner, but may be used
      by other Rose utilities, such as :ref:`command-rose-config-edit`.
      It can be used to specify the application type.

   .. rose:conf:: mode

      Root level setting. Specify the name of a built-in application,
      instead of running a command specified in the :rose:conf:`[command]`
      section.

      See also :ref:`Rose Built-In Applications`.

   .. rose:conf:: command

      Specify the command(s) to run.

      .. rose:conf:: default=COMMAND

         :compulsory: True

         Specify the default command to run.

      .. rose:conf:: ALTERNATE=COMMAND

         Specify an alternate command refered to by the name ``ALTERNATE``
         which can be selected at runtime.

         See the :ref:`rose-tutorial-command-keys` tutorial.
  
   .. rose:conf:: env

      Specify environment variables to be provided to the
      :rose:conf:`[command]` at runtime.

      The usual ``$NAME`` or ``${NAME}`` syntax can be used in values to
      reference environment variables that are already defined when the
      application runner is invoked. However, it is unsafe to reference other
      environment variables defined in this section.

      If the value of an environment variable setting begins with a tilde
      ``~``, all of the characters preceding the first slash ``/`` are
      considered a *tilde-prefix*. Where possible, a tilde-prefix is replaced
      with the home directory associated with the specified login name at run
      time.

      .. rose:conf:: KEY=VALUE

         Define an environment variable ``KEY`` with the value ``VALUE``.

      .. rose:conf:: UNDEF
      
         A special variable that is always undefined at run time.

         Reference to it will cause a failure at run time. It can be used to
         indicate that a value must be overridden at run time.
  
   .. rose:conf:: [etc]

      Specify misc. settings.

      .. tip::

         Currently, only UM defs for science sections are
         thought to require this section.

   .. rose:conf:: [file:TARGET]

      Specify a file/directory to be installed. ``TARGET`` should be a path
      relative to the run time ``$PWD`` or ``STDIN``.

      E.g. ``file:app/APP=source=LOCATION``.

      For a list of configuration options see :rose:conf:`*[file:TARGET]` for
      details.

   .. rose:conf:: namelist:NAME

      Specify a Fortran namelist with the group name called ``NAME``, which
      can be referred to by a :rose:conf:`*[file:TARGET]source` setting of
      a file.

      .. rose:conf:: KEY=VALUE

         Define a new namelist setting ``KEY`` set to ``VALUE`` exactly like a
         Fortran namelist, but without the trailing comma.

      Namelists can be grouped in two ways:

      1. ``[namelist:NAME(SORT-INDEX)]``

         * This allows different namelist files to have namelists with the same
           group name. These will all inherit the same group configuration
           metadata (from ``[namelist:NAME]``).
         * This allows the ``source`` setting of a file to refer to all
           ``[namelist:NAME(SORT-INDEX)]`` as ``namelist:NAME(:)``, and the
           namelist groups will be sorted alphanumerically by the
           ``SORT-INDEX``.

      2. ``[namelist:NAME{CATEGORY}]``

         * This allows the same namelist
           to have different usage and configuration metadata according to its
           category. Namelists will inherit configuration metadata from their
           basic group ``[namelist:NAME]`` as well as from their specific
           category ``[namelist:NAME{CATEGORY}]``.

      These groupings can be combined: ``[namelist:NAME{CATEGORY}(SORT-INDEX)]``

   .. rose:conf:: poll

      Specify prerequisites to poll for before running the actual application.
      Three types of tests can be performed:

      .. rose:conf:: all-files

         A list of space delimited list of file paths. This test
         passes only if all file paths in the list exist.

      .. rose:conf:: any-files

         A list of space delimited list of file paths. This test
         passes if any file path in the list exists.

      .. rose:conf:: test

         A shell command. This test passes if the command returns a 0
         (zero) return code.

         Normally, the :rose:conf:`all-files` and :rose:conf:`any-files`
         tests both test for the existence of file paths.

      .. rose:conf:: file-test
     
         If :rose:conf:`test` is not enough, e.g. you want to test for the
         existence of a string in each file, you can specify a
         :rose:conf:`file-test` to do a ``grep``. E.g.:

         .. code-block:: rose

            all-files=file1 file2
            file-test=test -e {} && grep -q 'hello' {}

         At runtime, any ``{}`` pattern in the above would be replaced
         with the name of the file. The above make sure that both
         ``file1`` and ``file2`` exist and that they both contain the
         string ``hello``.

      .. rose:conf:: delays

         The above tests will only be performed once when the application
         runner starts. If a list of :rose:conf:`delays` are added, the tests
         will be performed a number of times with delays between them. If the
         prerequisites are still not met  after the number of delays, the
         application runner will fail with a time out. The list is a
         comma-separated list. The syntax looks like ``[n*][DURATION]``,
         where ``DURATION`` is an
         :ref:`ISO8601 duration <tutorial-iso8601-durations>` such as
         ``PT5S`` (5 seconds) or ``PT10M`` (10 minutes), and ``n`` is
         an optional number of times to repeat it. E.g.:

         .. code-block:: rose

            # Default
            delays=0

            # Poll 1 minute after the runner begins, repeat every minute 10 times
            delays=10*PT1M

            # Poll when runner begins,
            # repeat every 10 seconds 6 times,
            # repeat every minute 60 times,
            # repeat once after 1 hour
            delays=0,6*PT10S,60*PT1M,PT1H
