.. include:: hyperlinks.rst
   :start-line: 1

Glossary
========

.. glossary::
   :sorted:

   cylc suite
      A cylc suite is a directory containing a ``suite.rc`` file which contains
      :term:`graphing<graph>` representing a workflow.

   suite directory
      The suite directory contains all of the configuration for a suite (e.g.
      the ``suite.rc`` file and for rose suites the ``rose-suite.conf`` file).

      This is the directory which is registered using ``cylc reg`` or, for rose
      suites, it is the one in which the ``rose suite-run`` command is
      executed.

      .. note::

         If a suite is written in the ``cylc-run`` directory the suite
         directory is also the :term:`run directory`.

      See also:

      * :term:`run directory`

   rose suite
      A rose suite is a :term:`cylc suite` which also contains a
      ``rose-suite.conf`` file and optionally :term:`rose apps<rose app>`,
      :term:`metadata` and/or other rose components.

   graph
      The graph of a :term:`suite<cylc suite>` refers to the
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

         bgcolor=none
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

         bgcolor=none
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
      A cycling :term:`suite<cylc suite>` is one in which the workflow repeats.

      See also:

      * :term:`cycle`
      * :term:`cycle point`

   cycle point
      A cycle point is the unique label given to a particular :term:`cycle`.
      If the :term:`suite<cylc suite>` is using :term:`integer cycling` then
      the cycle points will be numbers e.g. ``1``, ``2``, ``3``, etc. If the
      :term:`suite<cylc suite>` is using :term:`datetime cycling` then the
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

      * :ref:`cylc tutorial <tutorial-integer-cycling>`

   datetime cycling
      A datetime cycling is the default for a :term:`cycling suite<cycling>`.
      When using datetime cycling :term:`cycle points<cycle point>` will be
      :term:`ISO8601 datetimes <ISO8601 datetime>` e.g. ``2000-01-01T00:00Z``
      and ISO8601 :term:`recurrences<recurrence>` can be used e.g. ``P3D``
      means every third day.

      See also:

      * :ref:`cylc tutorial <tutorial-datetime-cycling>`

   ISO8601
      ISO8601 is an international standard for writing dates and times which is
      used in cylc with :term:`datetime cycling`.

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

      * :ref:`cylc tutorial <tutorial-iso8601-datetimes>`
      * :term:`ISO8601`

   ISO8601 duration
      A duration written in the ISO8601 format e.g:

      * ``PT1H30M``: one hour and thirty minutes.

      See also:

      * :ref:`cylc tutorial <tutorial-iso8601-durations>`
      * :term:`ISO8601`

   recurrence
      A recurrence is a repeating sequence which may be used to define a
      :term:`cycling suite<cycling>`. Recurrences determine how often something
      repeats and take one of two forms depending on whether the
      :term:`suite<cylc suite>` is configured to use :term:`integer cycling`
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

         bgcolor=none
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

      * :ref:`cylc tutorial <tutorial-qualifiers>`
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

      * :ref:`cylc tutorial <tutorial-tasks-and-jobs>`
      * :term:`task`
      * :term:`job`
      * :term:`qualifier`

   run directory
      When a :term:`suite <cylc suite>` is run a directory is created for all
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
      * :term:`work directory`
      * :term:`share directory`
      * :term:`job log directory`

   work directory
      When cylc executes a :term:`job` it does so inside the
      :term:`job's <job>` working directory. This directory is created by cylc
      and lies within the directory tree inside the relevant suite's
      :term:`run directory`.

      .. code-block:: sub

         <run directory>/work/<cycle>/<task-name>

      The location of the work directory can be accessed by a :term:`job` via
      the environment variable ``CYLC_TASK_WORK_DIR``.

      Any files installed by :term:`rose apps <rose app>` will be placed within
      this directory.

      See also:

      * :term:`run directory`
      * :term:`share directory`

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
      A cylc suite logs events and other information to the suite log files
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
      When cylc executes a :term:`job`, stdout and stderr are redirected to the
      ``job.out`` and ``job.err`` files which are stored in the job log
      directory.

      The job log directory lies within the :term:`run directory`:

      .. code-block:: sub

         <run directory>/log/job/<cycle>/<task-name>/<submission-no>

      Other files stored in the job log directory:

      * `job`: the :term:`job script`.
      * `job-activity.log`: a log file containing details of the
        :term:`job's <job>` progress.
      * `job.status`: a file holding cylc's most up-to-date
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
      task failed and was re-tried). Each time cylc runs a :term:`job` it is
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

   parameterisation
      Parameterisation is a way to consolidate configuration in the cylc
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

      * :ref:`cylc tutorial <tutorial-cylc-parameterisation>`

   family
      In cylc a family is a collection of :term:`tasks <task>` which share a
      common configuration and which can be referred to collectively in the
      :term:`graph`.

      By convention families are named in upper case with the exception of the
      special ``root`` family from which all tasks inherit.

      See also:

      * :ref:`cylc tutorial <tutorial-cylc-families>`
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

      * `cylc user guide`_
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

      * `cylc user guide`_
      * :term:`family`
      * :term:`task trigger`
      * :term:`dependency`
      * :ref:`Family Trigger Tutorial <tutorial-cylc-family-triggers>`

   rose app
   rose application configuration
      TODO

   rose suite configuration
      TODO

   metadata
   rose metadata
      TODO
