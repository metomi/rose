Rose Environment Variables
==========================


.. envvar:: NPROC

   Description
      Specifies the number of processors to run on. Default is 1.
   Used By
      * :ref:`command-rose-mpi-launch`

.. envvar:: ROSE_APP_COMMAND_KEY

   Description
      Can be set to define which command in an app config to use.
   Used By
      * :ref:`command-rose-app-run`
      * :ref:`command-rose-task-run`

.. envvar:: ROSE_APP_OPT_CONF_KEYS

   Description
      Each ``KEY`` in this space delimited list switches on an optional
      configuration in an application. The ``(KEY)`` syntax can be used to
      denote an optional configuration that can be missing. The configurations
      are applied in first-to-last order.
   Used By
      * :ref:`command-rose-app-run`
      * :ref:`command-rose-task-run`

.. envvar:: ROSE_BUNCH_LOG_PREFIX

   Description
      Environment variable provided to Rose Bunch instances at runtime to
      identify the log prefix that will be used for output e.g. for a bunch
      instance named  ``foo`` then ``ROSE_BUNCH_LOG_PREFIX=foo``.
   Provided At Runtime By
      * Rose Bunch

.. envvar:: ROSE_CONF_PATH

   Description
      Specify a colon (``:``) separated list of paths for searching and loading
      site/user configuration. If this environment variable is not defined, the
      normal behaviour is to search for and load :rose:file:`rose.conf` from
      ``$ROSE_HOME/etc`` and then ``$HOME/.metomi``.
   Used By
      * :ref:`command-rose-test-battery`

.. envvar:: ROSE_CYCLING_MODE

   Description
      The cycling mode to use when manipulating dates. Can be either ``360day``
      or ``gregorian``.
   Used By
      * :ref:`command-rose-date`
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_DATA

   Description
      The path to the data directory of the running suite.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_DATAC

   Description
      The path to the data directory of this cycle time in the running suite.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_DATAC????

   Description
      The path to the data directory of the cycle time with an offset relative
      to the current cycle time. ``????`` is a duration:

      * A ``__`` (double underscore) prefix denotes a cycle time in the
        future. Otherwise, it is a cycle time in the past.
      * ``PnM`` denotes *n* months.
      * ``PnW`` denotes *n* weeks.
      * ``PnD`` or ``nD`` denotes *n* days.
      * ``PTnH`` or ``TnH`` denotes *n* hours.
      * ``PTnM`` denotes *n* minutes.

      E.g. ``ROSE_DATACPT6H`` is the data directory of 6 hours before the
      current cycle time.

      E.g. ``ROSE_DATACP1D`` and ``ROSE_DATACPT24H`` are both the data directory
      of 1 day before the current cycle time.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_ETC

   Description
      The path to the ``etc`` directory of the running suite.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_FILE_INSTALL_ROOT

   Description
      If specified, change to the specified directory to install files.
   Used By
      * :ref:`command-rose-app-run`
      * :ref:`command-rose-task-run`

.. envvar:: ROSE_HOME

   Description
      Specifies the path to the Rose home directory.
   Used and Provided By
      * ``rose``

.. envvar:: ROSE_HOME_BIN

   Description
      Specifies the path to the ``bin/`` or ``sbin/`` directory of the current
      Rose utility.
   Used and Provided By
      * ``rose``

.. envvar:: ROSE_LAUNCHER

   Description
      Specifies the launcher program to run the prog.
   Used By
      * :ref:`command-rose-mpi-launch`

.. envvar:: ROSE_LAUNCHER_FILEOPTS

   Description
      Override ``[rose-mpi-launch]launcher-fileopts.LAUNCHER`` setting for the
      selected :envvar:`ROSE_LAUNCHER`.
   Used By
      * :ref:`command-rose-mpi-launch`

.. envvar:: ROSE_LAUNCHER_LIST

   Description
      Specifies an alternative list of launchers.
   Used By
      * :ref:`command-rose-mpi-launch`

.. envvar:: ROSE_LAUNCHER_PREOPTS

   Description
      Override ``[rose-mpi-launch]launcher-preopts.LAUNCHER`` setting for the
      selected :envvar:`ROSE_LAUNCHER`.
   Used By
      * :ref:`command-rose-mpi-launch`

.. envvar:: ROSE_LAUNCHER_POSTOPTS

   Description
      Override ``[rose-mpi-launch]launcher-postopts.LAUNCHER`` setting for the
      selected :envvar:`ROSE_LAUNCHER`.
   Used By
      * :ref:`command-rose-mpi-launch`

.. envvar:: ROSE_LAUNCHER_ULIMIT_OPTS

   Description
      Tell launcher to run:

      .. NOTEFORWRITERS - bash syntax highlighting is ugly on below code
         blocks so instead just use 'none'

      .. code-block:: none

         rose mpi-launch --inner $@

      Specify the arguments to ``ulimit``. E.g. Setting this variable to:

      .. code-block:: none

         -a -s unlimited -d unlimited -a

      results in:

      .. code-block:: none

         ulimit -a; ulimit -s unlimited; ulimit -d unlimited; ulimit -a

   Used By
      * :ref:`command-rose-mpi-launch`

.. envvar:: ROSE_META_PATH

   Description
      Defines a metadata search path, colon-separated for multiple paths.
   Used by
      * :ref:`command-rose-config-edit`
      * :ref:`command-rose-macro`

.. envvar:: ROSE_NS

   Description
      Defines the rose namespace. Used to identify if a utility belongs to
      ``rose`` or ``rosie``.
   Used and Provided By
      * ``rose``

.. envvar:: ROSE_ORIG_HOST

   Description
      The name of the host where the :ref:`command-rose-suite-run` command was
      invoked.
   Provided By
      * :ref:`command-rose-suite-run`

.. envvar:: ROSE_SUITE_DIR

   Description
      The path to the root directory of the running suite.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_SUITE_DIR_REL

   Description
      The path to the root directory of the running suite relative to ``$HOME``.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_SUITE_NAME

   Description
      The name of the running suite.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_SUITE_OPT_CONF_KEYS

   Description
      Each ``KEY`` in this space delimited list switches on an optional
      configuration when installing a suite. The ``(KEY)`` syntax can be used to
      denote an optional configuration that can be missing. The configurations
      are applied in first-to-last order.
   Used By
      * :ref:`command-rose-suite-run`

.. envvar:: ROSE_TASK_APP

   Description
      Specify a named application configuration.
   Used By
      * :ref:`command-rose-task-run`

.. envvar:: ROSE_TASK_CYCLE_TIME

   Description
      The cycle time of the suite task, if there is one.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_TASK_LOG_DIR

   Description
      The directory for log files of the suite task.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_TASK_LOG_ROOT

   Description
      The root path for log files of the suite task.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_TASK_N_JOBS

   .. warning::
      (Deprecated) Use the ``opt.jobs`` setting in the application configuration
      instead.

   Description
      The number of jobs to run in parallel in ``fcm make`` (``default=4``).
   Used By
      * ``fcm_make`` built-in application
      * ``fcm_make2`` built-in application

.. envvar:: ROSE_TASK_MIRROR_TARGET

   .. warning::
      (Deprecated)

   Description
      The mirror target for the mirror step in the ``fcm-make.cfg``
      configuration.
   Provided By
      * ``fcm_make`` built-in application

.. envvar:: ROSE_TASK_NAME

   Description
      The name of the suite task.
   Provided By
      * :ref:`command-rose-task-env`
   Used By
      * :ref:`command-rose-app-run`

.. envvar:: ROSE_TASK_OPTIONS

   .. warning::
      (Deprecated) Use the ``args`` setting in the application configuration
      instead.

   Description
      Additional options and arguments for ``fcm make`` or
      :ref:`command-rose-app-run`.
   Used By
      * ``fcm_make`` built-in application
      * ``fcm_make2`` built-in application

.. envvar:: ROSE_TASK_PREFIX

   Description
      The prefix in the task name.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_TASK_SUFFIX

   Description
      The suffix in the task name.
   Provided By
      * :ref:`command-rose-task-env`

.. envvar:: ROSE_UTIL

   Description
      Used to identify which ``rose`` or ``rosie`` utility is being run.
   Used and Provided By
      * ``rose``

.. envvar:: ROSE_VERSION

   Description
      The current version of Rose.
   Used and Provided By
      * ``rose``
      * :ref:`command-rose-suite-run`
