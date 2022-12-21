.. include:: hyperlinks.rst
   :start-line: 1

Glossary
========

.. glossary::
   :sorted:

   suite
   Cylc suite
      A Cylc suite is a directory containing a ``suite.rc`` file which contains
      :term:`graphing<graph>` representing a workflow.

      See also:

      * :ref:`Relationship between Cylc suites, Rose suite configurations and
        Rosie suites <cylc-rose-rosie-suite-relationship-diagram>`


   suite directory
      The suite directory contains all of the configuration for a suite (e.g.
      the ``suite.rc`` file and for Rose suites the :rose:file:`rose-suite.conf`
      file).

      This is the directory which is registered using ``cylc reg`` or, for Rose
      suites, it is the one in which the :ref:`command-rose-suite-run` command
      is executed.

      .. note::

         If a suite is written in the ``cylc-run`` directory the suite
         directory is also the :term:`run directory`.

      See also:

      * :term:`run directory`
      * :ref:`Rose suite installation diagram
        <rose-suite-installation-diagram>`

   graph
      The graph of a :term:`suite<Cylc suite>` refers to the
      :term:`graph strings<graph string>` contained within the
      ``[scheduling][dependencies]`` section. For example the following is,
      collectively, a graph:

      .. code-block:: cylc

         [P1D]
             graph = foo => bar
         [PT12H]
             graph = baz

      .. digraph:: example
         :align: center

         size = "7,15"

         subgraph cluster_1 {
             label = "2000-01-01T00:00Z"
             style = dashed
             "foo.01T00" [label="foo\n2000-01-01T00:00Z"]
             "bar.01T00" [label="bar\n2000-01-01T00:00Z"]
             "baz.01T00" [label="baz\n2000-01-01T00:00Z"]
         }

         subgraph cluster_2 {
             label = "2000-01-01T12:00Z"
             style = dashed
             "baz.01T12" [label="baz\n2000-01-01T12:00Z"]
         }

         subgraph cluster_3 {
             label = "2000-01-02T00:00Z"
             style = dashed
             "foo.02T00" [label="foo\n2000-01-02T00:00Z"]
             "bar.02T00" [label="bar\n2000-01-02T00:00Z"]
             "baz.02T00" [label="baz\n2000-01-02T00:00Z"]
         }

         "foo.01T00" -> "bar.01T00"
         "foo.02T00" -> "bar.02T00"

   graph string
      A graph string is a collection of dependencies which are placed under a
      ``graph`` section in the ``suite.rc`` file. E.G:

      .. code-block:: cylc-graph

         foo => bar => baz & pub => qux
         pub => bool

   dependency
      A dependency is a relationship between two :term:`tasks<task>` which
      describes a constraint on one.

      For example the dependency
      ``foo => bar`` means that the :term:`task` ``bar`` is *dependent* on the
      task ``foo``. This means that the task ``bar`` will only run once the
      task ``foo`` has successfully completed.

      See also:

      * :term:`task trigger`

   task trigger
      :term:`Dependency <dependency>` relationships can be thought of the other
      way around as "triggers".

      For example the dependency ``foo => bar`` could be described in two ways:

      * "``bar`` is dependent on ``foo``"
      * "``foo`` is triggered by ``bar``"

      In practice a trigger is the left-hand side of a dependency (``foo`` in
      this example).

      See also:

      * :term:`dependency`
      * :term:`qualifier`
      * :term:`family trigger`

   cycle
      In a :term:`cycling suite<cycling>` one cycle is one repetition of the
      workflow.

      For example, in the following workflow each dotted box represents a cycle
      and the :term:`tasks<task>` within it are the :term:`tasks<task>`
      belonging to that cycle. The numbers (i.e. ``1``, ``2``, ``3``) are the
      :term:`cycle points<cycle point>`.

      .. digraph:: example
         :align: center

         size = "3,5"

         subgraph cluster_1 {
             label = "1"
             style = dashed
             "foo.1" [label="foo\n1"]
             "bar.1" [label="bar\n1"]
             "baz.1" [label="baz\n1"]
         }

         subgraph cluster_2 {
             label = "2"
             style = dashed
             "foo.2" [label="foo\n2"]
             "bar.2" [label="bar\n2"]
             "baz.2" [label="baz\n2"]
         }

         subgraph cluster_3 {
             label = "3"
             style = dashed
             "foo.3" [label="foo\n3"]
             "bar.3" [label="bar\n3"]
             "baz.3" [label="baz\n3"]
         }

         "foo.1" -> "bar.1" -> "baz.1"
         "foo.2" -> "bar.2" -> "baz.2"
         "foo.3" -> "bar.3" -> "baz.3"
         "bar.1" -> "bar.2" -> "bar.3"

   cycling
      A cycling :term:`suite<Cylc suite>` is one in which the workflow repeats.

      See also:

      * :term:`cycle`
      * :term:`cycle point`

   cycle point
      A cycle point is the unique label given to a particular :term:`cycle`.
      If the :term:`suite<Cylc suite>` is using :term:`integer cycling` then
      the cycle points will be numbers e.g. ``1``, ``2``, ``3``, etc. If the
      :term:`suite<Cylc suite>` is using :term:`datetime cycling` then the
      labels will be :term:`ISO8601` datetimes e.g. ``2000-01-01T00:00Z``.

      See also:

      * :term:`initial cycle point`
      * :term:`final cycle point`

   initial cycle point
      In a :term:`cycling suite <cycling>` the initial cycle point is the point
      from which cycling begins.

      If the initial cycle point were 2000 then the first cycle would
      be on the 1st of January 2000.

      See also:

      * :term:`cycle point`
      * :term:`final cycle point`

   final cycle point
      In a :term:`cycling suite <cycling>` the final cycle point is the point
      at which cycling ends.

      If the final cycle point were 2001 then the final cycle would be no later
      than the 1st of January 2001.

      See also:

      * :term:`cycle point`
      * :term:`initial cycle point`

   integer cycling
      An integer cycling suite is a :term:`cycling suite<cycling>` which has
      been configured to use integer cycling. When a suite uses integer cycling
      integer :term:`recurrences <recurrence>` may be used in the :term:`graph`,
      e.g. ``P3`` means every third cycle. This is configured by setting
      ``[scheduling]cycling mode = integer`` in the ``suite.rc`` file.

      See also:

      * :ref:`Cylc tutorial <tutorial-integer-cycling>`

   datetime cycling
      A datetime cycling is the default for a :term:`cycling suite<cycling>`.
      When using datetime cycling :term:`cycle points<cycle point>` will be
      :term:`ISO8601 datetimes <ISO8601 datetime>` e.g. ``2000-01-01T00:00Z``
      and ISO8601 :term:`recurrences<recurrence>` can be used e.g. ``P3D``
      means every third day.

      See also:

      * :ref:`Cylc tutorial <tutorial-datetime-cycling>`

   wall-clock time
      In a Cylc suite the wall-clock time refers to the actual time (in the
      real world).

      See also:

      * :term:`datetime cycling`
      * :ref:`Clock Trigger Tutorial <tutorial-cylc-clock-trigger>`

   ISO8601
      ISO8601 is an international standard for writing dates and times which is
      used in Cylc with :term:`datetime cycling`.

      See also:

      * :term:`ISO8601 datetime`
      * :term:`recurrence`
      * `Wikipedia (ISO8601) <https://en.wikipedia.org/wiki/ISO_8601>`_
      * `International Organisation For Standardisation
        <https://www.iso.org/iso-8601-date-and-time-format.html>`_
      * `a summary of the international standard date and time notation
        <http://www.cl.cam.ac.uk/%7Emgk25/iso-time.html>`_

   ISO8601 datetime
      A date-time written in the ISO8601
      format, e.g:

      * ``2000-01-01T00:00Z``: midnight on the 1st of January 2000

      See also:

      * :ref:`Cylc tutorial <tutorial-iso8601-datetimes>`
      * :term:`ISO8601`

   ISO8601 duration
      A duration written in the ISO8601 format e.g:

      * ``PT1H30M``: one hour and thirty minutes.

      See also:

      * :ref:`Cylc tutorial <tutorial-iso8601-durations>`
      * :term:`ISO8601`

   recurrence
      A recurrence is a repeating sequence which may be used to define a
      :term:`cycling suite<cycling>`. Recurrences determine how often something
      repeats and take one of two forms depending on whether the
      :term:`suite<Cylc suite>` is configured to use :term:`integer cycling`
      or :term:`datetime cycling`.

      See also:

      * :term:`integer cycling`
      * :term:`datetime cycling`

   inter-cycle dependency
      In a :term:`cycling suite <cycling>` an inter-cycle dependency
      is a :term:`dependency` between two tasks in different cycles.

      For example in the following suite the task ``bar`` is dependent on
      its previous occurrence:

      .. code-block:: cylc

         [scheduling]
             initial cycle point = 1
             cycling mode = integer
             [[dependencies]]
                 [[[P1]]]
                     graph = """
                         foo => bar => baz
                         bar[-P1] => bar
                     """

      .. digraph:: example
         :align: center

         size = "3,5"

         subgraph cluster_1 {
             label = "1"
             style = dashed
             "foo.1" [label="foo\n1"]
             "bar.1" [label="bar\n1"]
             "baz.1" [label="baz\n1"]
         }

         subgraph cluster_2 {
             label = "2"
             style = dashed
             "foo.2" [label="foo\n2"]
             "bar.2" [label="bar\n2"]
             "baz.2" [label="baz\n2"]
         }

         subgraph cluster_3 {
             label = "3"
             style = dashed
             "foo.3" [label="foo\n3"]
             "bar.3" [label="bar\n3"]
             "baz.3" [label="baz\n3"]
         }

         "foo.1" -> "bar.1" -> "baz.1"
         "foo.2" -> "bar.2" -> "baz.2"
         "foo.3" -> "bar.3" -> "baz.3"
         "bar.1" -> "bar.2" -> "bar.3"

   qualifier
      A qualifier is used to determine the :term:`task state` to which a
      :term:`dependency` relates.

      See also:

      * :ref:`Cylc tutorial <tutorial-qualifiers>`
      * :term:`task state`

   task
      A task represents an activity in a workflow. It is a specification of
      that activity consisting of the script or executable to run and certain
      details of the environment it is run in.

      The task specification is used to create a :term:`job` which is executed
      on behalf of the task.

      Tasks submit :term:`jobs <job>` and therefore each :term:`job` belongs
      to one task. Each task can submit multiple :term:`jobs <job>`.

      See also:

      * :term:`job`
      * :term:`job script`

   task state
      During a :term:`task's <task>` life it will proceed through various
      states. These include:

      * waiting
      * running
      * succeeded

      See also:

      * :ref:`Cylc tutorial <tutorial-tasks-and-jobs>`
      * :term:`task`
      * :term:`job`
      * :term:`qualifier`

   run directory
      When a :term:`suite <Cylc suite>` is run a directory is created for all
      of the files generated whilst the suite is running. This is called the
      run directory and typically resides in the ``cylc-run`` directory:

      ``~/cylc-run/<suite-name>``

      .. note::

         If a suite is written in the ``cylc-run`` directory the run
         directory is also the :term:`suite directory`.

      The run directory can be accessed by a running suite using the
      environment variable ``CYLC_SUITE_RUN_DIR``.

      See also:

      * :term:`suite directory`
      * :ref:`Suite Directory Vs Run Directory`
      * :term:`work directory`
      * :term:`share directory`
      * :term:`job log directory`

   work directory
      When Cylc executes a :term:`job` it does so inside the
      :term:`job's <job>` working directory. This directory is created by Cylc
      and lies within the directory tree inside the relevant suite's
      :term:`run directory`.

      .. code-block:: sub

         <run directory>/work/<cycle>/<task-name>

      The location of the work directory can be accessed by a :term:`job` via
      the environment variable ``CYLC_TASK_WORK_DIR``.

      Any files installed by :term:`Rose apps <Rose app>` will be placed within
      this directory.

      See also:

      * :term:`run directory`
      * :term:`share directory`
      * :ref:`Rose suite installation diagram
        <rose-suite-installation-diagram>`

   share directory
      The share directory resides within a suite's :term:`run directory`. It
      serves the purpose of providing a storage place for any files which need
      to be shared between different tasks.

      .. code-block:: sub

         <run directory>/share

      The location of the share directory can be accessed by a :term:`job` via
      the environment variable ``CYLC_SUITE_SHARE_DIR``.

      In cycling suites files are typically stored in cycle sub-directories.

      See also:

      * :term:`run directory`
      * :term:`work directory`

   suite log
   suite log directory
      A Cylc suite logs events and other information to the suite log files
      when it runs. There are three log files:

      * ``out`` - the stdout of the suite.
      * ``err`` - the stderr of the suite, which may contain useful debugging
        information in the event of any error(s).
      * ``log`` - a log of suite events, consisting of information about
        user interaction.

      The suite log directory lies within the :term:`run directory`:

      .. code-block:: sub

         <run directory>/log/suite

   job log
   job log directory
      When Cylc executes a :term:`job`, stdout and stderr are redirected to the
      ``job.out`` and ``job.err`` files which are stored in the job log
      directory.

      The job log directory lies within the :term:`run directory`:

      .. code-block:: sub

         <run directory>/log/job/<cycle>/<task-name>/<submission-no>

      Other files stored in the job log directory:

      * `job`: the :term:`job script`.
      * `job-activity.log`: a log file containing details of the
        :term:`job's <job>` progress.
      * `job.status`: a file holding Cylc's most up-to-date
        understanding of the :term:`job's <job>` present status.

   job
      A job is the realisation of a :term:`task` consisting of a file called
      the :term:`job script` which is executed when the job "runs".

      See also:

      * :term:`task`
      * :term:`job script`

   job script
      A job script is the file containing a bash script which is executed when
      a :term:`job` runs. A task's job script can be found in the
      :term:`job log directory`.

      See also:

      * :term:`task`
      * :term:`job`
      * :term:`job submission number`

   job host
      The job host is the compute platform that a :term:`job` runs on. For
      example ``some-host`` would be the job host for the task ``some-task`` in
      the following suite:

      .. code-block:: cylc

         [runtime]
             [[some-task]]
                 [[[remote]]]
                     host = some-host

   job submission number
      Cylc may run multiple :term:`jobs <job>` per :term:`task` (e.g. if the
      task failed and was re-tried). Each time Cylc runs a :term:`job` it is
      assigned a submission number. The submission number starts at 1,
      incrementing with each submission.

      See also:

      * :term:`job`
      * :term:`job script`

   batch system
      A batch system or job scheduler is a system for submitting
      :term:`jobs <job>` onto a compute platform.

      See also:

      * `Wikipedia (job scheduler)
        <https://en.wikipedia.org/wiki/Job_scheduler>`_
      * :term:`directive`

   directive
      Directives are used by :term:`batch systems <batch system>` to determine
      what a :term:`job's <job>` requirements are, e.g. how much memory
      it requires.

      Directives are set in the ``suite.rc`` file in the ``[runtime]`` section
      (``[runtime][<task-name>][directives]``).

      See also:

      * :term:`batch system`



   suite server program
      When we say that a :term:`suite` is "running" we mean that the cylc
      suite server program is running.

      The suite server program is responsible for running the suite. It submits
      :term:`jobs <job>`, monitors their status and maintains the suite state.

      .. _daemon: https://en.wikipedia.org/wiki/Daemon_(computing)

      By default a suite server program is a `daemon`_ meaning that it runs in
      the background (potentially on another host).

   start
   startup
      When a :term:`suite` starts the Cylc :term:`suite server program` is
      run. This program controls the suite and is what we refer to as
      "running".

      * A :term:`Cylc suite` is started using ``cylc run``.
      * A :term:`Rose suite configuration` (or :term:`Rosie Suite`) is started
        using :ref:`command-rose-suite-run`.

      A suite start can be either :term:`cold <cold start>` or :term:`warm <warm
      start>` (cold by default).

      See also:

      * :ref:`Starting Suites`
      * :term:`suite server program`
      * :term:`warm start`
      * :term:`cold start`
      * :term:`shutdown`
      * :term:`restart`
      * :term:`reload`

   cold start
      A cold start is one in which the :term:`suite` :term:`starts <start>`
      from the :term:`initial cycle point`. This is the default behaviour of
      ``cylc run``.

      See also:

      * :term:`warm start`

   warm start
      In a :term:`cycling suite <cycling>`
      a warm start is one in which the :term:`suite` :term:`starts <start>`
      from a :term:`cycle point` after the :term:`initial cycle point`.
      Tasks in cycles before this point as assumed to have succeeded.

      See also:

      * :term:`cold start`

   stop
   shutdown
      When a :term:`suite` is shutdown the :term:`suite server program` is
      stopped. This means that no further :term:`jobs <job>` will be submitted.

      By default Cylc waits for any submitted or running :term:`jobs <job>` to
      complete (either succeed or fail) before shutting down.

      See also:

      * :ref:`Stopping Suites`
      * :term:`start`
      * :term:`restart`
      * :term:`reload`

   restart
      When a :term:`stopped <stop>` :term:`suite` is "restarted" Cylc will pick
      up where it left off. Cylc will detect any :term:`jobs <job>` which
      have changed state (e.g. succeeded) during the period in which the
      :term:`suite` was :term:`shutdown`.

      See also:

      * :ref:`Restarting Suites`
      * :term:`start`
      * :term:`Stop`
      * :term:`Reload`

   reload
      Any changes made to the ``suite.rc`` file whilst the suite is running
      will not have any effect until the suite is either:
      
      * :term:`Shutdown` and :term:`rerun <start>`
      * :term:`Shutdown` and :term:`restarted <restart>`
      * "Reloaded"

      Reloading does not require the suite to be :term:`shutdown`. When a suite
      is reloaded any currently "active" :term:`tasks <task>` will continue with
      their "pre-reload" configuration, whilst new tasks will use the new
      configuration.

      Reloading changes is safe providing they don't affect the
      :term:`suite's <suite>` :term:`graph`. Changes to the graph have certain
      caveats attached, see the `Cylc User Guide`_ for details.

      See also:

      * :ref:`Reloading Suites`
      * `Cylc User Guide`_

   parameterisation
      Parameterisation is a way to consolidate configuration in the Cylc
      ``suite.rc`` file by implicitly looping over a set of pre-defined
      variables e.g:

      .. code-block:: cylc

         [cylc]
             [[parameters]]
                 foo = 1..3
         [scheduling]
             [[dependencies]]
                 graph = bar<foo> => baz<foo>

      .. minicylc::
         :theme: none

         bar_foo1 => baz_foo1
         bar_foo2 => baz_foo2
         bar_foo3 => baz_foo3

      See also:

      * :ref:`Cylc tutorial <tutorial-cylc-parameterisation>`

   family
      In Cylc a family is a collection of :term:`tasks <task>` which share a
      common configuration and which can be referred to collectively in the
      :term:`graph`.

      By convention families are named in upper case with the exception of the
      special ``root`` family from which all tasks inherit.

      See also:

      * :ref:`Cylc tutorial <tutorial-cylc-families>`
      * :term:`family inheritance`
      * :term:`family trigger`

   family inheritance
      A :term:`task` can be "added" to a :term:`family` by "inheriting" from
      it.

      For example the :term:`task` ``task`` "belongs" to the :term:`family`
      ``FAMILY`` in the following snippet:

      .. code-block:: cylc

         [runtime]
             [[FAMILY]]
                 [[[environment]]]
                     FOO = foo
             [[task]]
                 inherit = FAMILY

      A task can inherit from multiple families by writing a comma-separated
      list e.g:

      .. code-block:: cylc

         inherit = foo, bar, baz

      See also:

      * `Cylc User Guide`_
      * :term:`family`
      * :term:`family trigger`

   family trigger
      :term:`Tasks <task>` which "belong" to
      (:term:`inherit <family inheritance>` from) a :term:`family` can be
      referred to collectively in the :term:`graph` using a family trigger.

      A family trigger is written using the name of the family followed by a
      special qualifier i.e. ``FAMILY_NAME:qualifier``. The most commonly used
      qualifiers are:

      ``succeed-all``
          The dependency will only be met when **all** of the tasks in the
          family have **succeeded**.
      ``succeed-any``
          The dependency will be met as soon as **any one** of the tasks in the
          family has **succeeded**.
      ``finish-all``
          The dependency will only be met once **all** of the tasks in the
          family have **finished** (either succeeded or failed).

      See also:

      * `Cylc User Guide`_
      * :term:`family`
      * :term:`task trigger`
      * :term:`dependency`
      * :ref:`Family Trigger Tutorial <tutorial-cylc-family-triggers>`

   stalled suite
   stalled state
      If Cylc is unable to proceed running a workflow due to unmet dependencies
      the suite is said to be *stalled*.

      This usually happens because of a task failure as in the following
      diagram:

      .. digraph:: Example
         :align: center

         foo [style="filled" color="#ada5a5"]
         bar [style="filled" color="#ff0000" fontcolor="white"]
         baz [color="#88c6ff"]

         foo -> bar -> baz

      In this example the task ``bar`` has failed meaning that ``baz`` is
      unable to run as its dependency (``bar:succeed``) has not been met.

      When a Cylc detects that a suite has stalled an email will be sent to the
      user. Human interaction is required to escape a stalled state.

   Rose configuration
      Rose configurations are directories containing a Rose configuration
      file along with other optional files and directories.

      The two types of Rose configuration relevant to Cylc suites are:

      * :term:`Rose application configuration`
      * :term:`Rose suite configuration`

      See also:

      * :ref:`Rose Configuration Format`
      * :ref:`Rose Configuration Tutorial <tutorial-rose-configurations>`
      * :ref:`Optional Configuration Tutorial
        <rose-tutorial-optional-configurations>`

   Rose app
   Rose application
   Rose application configuration
      A Rose application configuration (or Rose app) is a directory containing
      a :rose:file:`rose-app.conf` file along with some other optional files
      and directories.

      An application can configure:

      * The command to run (:rose:conf:`rose-app.conf[command]`).
      * Any environment variables to provide it with
        (:rose:conf:`rose-app.conf[env]`)
      * Input files e.g. namelists (:rose:conf:`rose-app.conf[namelist:NAME]`)
      * Metadata for the application (:rose:file:`rose-meta.conf`).

      See also:

      * :ref:`Rose Applications`

   application directory
      The application directory is the folder in which the
      :rose:file:`rose-app.conf` file is located in a :term:`Rose application
      configuration`.

   Rose built-in application
      A Rose built-in application is a generic :term:`Rose application`
      providing common functionality which is provided in the Rose installation.

      See also:

      * :ref:`Rose Built-In Applications`

   Rose suite configuration
      A Rose suite configuration is a :rose:file:`rose-suite.conf` file along
      with other optional files and directories which configure the way in
      which a :term:`Cylc suite` is run. E.g:

      * Jinja2 variables to be passed into the ``suite.rc`` file (
        :rose:conf:`rose-suite.conf[jinja2:suite.rc]`).
      * Environment variables to be provided to ``cylc run`` (
        :rose:conf:`rose-suite.conf[env]`).
      * Installation configuration (e.g.
        :rose:conf:`rose-suite.conf|root-dir`,
        :rose:conf:`rose-suite.conf[file:NAME]`).

      See also:

      * :ref:`Rose Suites`

   metadata
   Rose metadata
      Rose metadata provides information about settings in
      :term:`Rose application configurations <Rose application configuration>`
      and :term:`Rose suite configurations <Rose suite configuration>`. This
      information is stored in a :rose:file:`rose-meta.conf` file in a
      ``meta/`` directory alongside the configuration it applies to.

      This information can include:

      * Documentation and help text, e.g.
        :rose:conf:`rose-meta.conf[SETTING]title`
        provides a short title to describe a setting.
      * Information about permitted values for the setting, e.g.
        :rose:conf:`rose-meta.conf[SETTING]type` can be used to specify the
        data type a setting requires (integer, string, boolean, etc).
      * Settings affecting how the configurations are displayed in
        :ref:`command-rose-config-edit` (e.g.
        :rose:conf:`rose-meta.conf[SETTING]sort-key`).
      * Metadata which defines how settings should behave in different states
        (e.g. :rose:conf:`rose-meta.conf[SETTING]trigger`).

      This information is used for:

      * Presentation and validation in the :ref:`command-rose-config-edit`
        GUI.
      * Validation using the :ref:`command-rose-macro` command.

      Metadata does not affect the running of an
      :term:`application <Rose app>` or :term:`Cylc suite`.

      See also:

      * :ref:`Metadata`

   Rosie Suite
      A Rosie suite is a :term:`Rose suite configuration` which is managed
      using the Rosie system.

      When a suite is managed using Rosie:

      * The :term:`suite directory` is added to version control.
      * The suite is registered in a database.

      See also:

      * :ref:`Rosie Tutorial <tutorial-rosie>`
