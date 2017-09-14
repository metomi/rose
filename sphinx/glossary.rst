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

      See also:

      * :term:`run directory`

   rose suite
      A rose suite is a :term:`cylc suite` which also contains a
      ``rose-suite.conf`` file and optionally :term:`rose apps<rose app>`,
      :term:`metadata` and other rose components.

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
             "baz.01T00" [label="bar\n2000-01-01T00:00Z"]
         }

         subgraph cluster_2 {
             label = "2000-01-01T12:00Z"
             style = dashed
             "baz.01T12" [label="bar\n2000-01-01T12:00Z"]
         }

         subgraph cluster_3 {
             label = "2000-01-02T00:00Z"
             style = dashed
             "foo.02T00" [label="foo\n2000-01-02T00:00Z"]
             "bar.02T00" [label="bar\n2000-01-02T00:00Z"]
             "baz.02T00" [label="bar\n2000-01-02T00:00Z"]
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

   cycle
      In a :term:`cycling suite<cycling>` one cycle is one repitition of the
      workflow.

      For example, in the following workflow each dotted box represents a cycle
      and the :term:`tasks<task>` within it are the :term:`tasks<task>`
      belonging to that cycle. The numbers (i.e. 1, 2, 3) are the
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
             "baz.1" [label="bar\n1"]
         }

         subgraph cluster_2 {
             label = "2"
             style = dashed
             "foo.2" [label="foo\n2"]
             "bar.2" [label="bar\n2"]
             "baz.2" [label="bar\n2"]
         }

         subgraph cluster_3 {
             label = "3"
             style = dashed
             "foo.3" [label="foo\n3"]
             "bar.3" [label="bar\n3"]
             "baz.3" [label="bar\n3"]
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
      the cycle points will be numbers e.g ``1``, ``2``, ``3``, etc. If the
      :term:`suite<cylc suite>` is using :term:`datetime cycling` then the
      labels will be :term:`ISO8601` datetimes e.g. ``2000-01-01T00:00Z``.

      See also:

      * :term:`initial cycle point`
      * :term:`final cycle point`

   initial cycle point
      In a :term:`cycling suite <cycling>` the initial cycle point is the point
      from which cycling begins.

      If the initial cycle point were 2000 then the first cycle would
      start on or after 2000.

      See also:

      * :term:`cycle point`
      * :term:`final cycle point`

   final cycle point
      In a :term:`cycling suite <cycling>` the final cycle point is the point
      at which cycling ends.

      If the final cycle point were 2001 then the final cycle would be on or
      before 2001.

      See also:

      * :term:`cycle point`
      * :term:`initial cycle point`

   integer cycling
      An integer cycling suite is a :term:`cycling suite<cycling>` which has
      been configured to use integer cycling. This is done using by setting
      ``[scheduling]cycling mode = integer`` in the ``suite.rc`` file.
      When a suite uses integer cycling the :term:`cycle points<cycle point>`
      will be integers and integer :term:`recurrences <recurrence>` may be used
      in the :term:`graph` e.g. ``P3`` means every third cycle.

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
      * `Wikipedia <https://en.wikipedia.org/wiki/ISO_8601>`_
      * `International Orginisation For Standardisation
        <https://www.iso.org/iso-8601-date-and-time-format.html>`_
      * `A summary of the international standard date and time notation
        <http://www.cl.cam.ac.uk/%7Emgk25/iso-time.html>`_

   ISO8601 datetime
      A date-time written in the ISO8601 format e.g:

      * ``2000-01-01T0000Z`` midnight on the 1st of January 2000

      See also:

      * :ref:`cylc tutorial <tutorial-iso8601-datetimes>`
      * :term:`ISO8601`

   ISO8601 duration
      A duration written in the ISO8601 format e.g:

      * ``PT1H30M`` one hour and thirty minutes.

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

      For example the in the following suite the task ``bar`` is dependent on
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
             "baz.1" [label="bar\n1"]
         }

         subgraph cluster_2 {
             label = "2"
             style = dashed
             "foo.2" [label="foo\n2"]
             "bar.2" [label="bar\n2"]
             "baz.2" [label="bar\n2"]
         }

         subgraph cluster_3 {
             label = "3"
             style = dashed
             "foo.3" [label="foo\n3"]
             "bar.3" [label="bar\n3"]
             "baz.3" [label="bar\n3"]
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
      A task represents an activity in a workflow, it is a specification of
      that activity, the script or executable to run and certain details of
      the environment it is run in.

      The task specification is used to create a :term:`job` which is executed
      on behalf of the task.

      Tasks submit :term:`jobs <job>`, each :term:`job` belongs to one task,
      each task can submit multiple :term:`jobs <job>`.

      See also:

      * :term:`job`
      * :term:`job script`

   task state
      During a :term:`task's <task>` life it will proceed through various
      states. These include:

      * Waiting
      * Running
      * Succeeded

      See also:

      * :ref:`cylc tutorial <tutorial-tasks-and-jobs>`
      * :term:`task`
      * :term:`job`
      * :term:`qualifier`

   run directory
      When a :term:`suite <cylc suite>` is run a directory is created for all
      of the files created whilst the suite is running. This is called the run
      directory and typically resides in the ``cylc-run`` directory:

      ``~/cylc-run/<suite-name>``

      The run directory can be accessed by a running suite using the
      environment variable ``CYLC_SUITE_RUN_DIR``.

      See also:

      * :term:`suite directory`
      * :term:`work directory`
      * :term`share directory`
      * :term`job log directory`

   work directory
      When cylc executes a :term:`job` it does so inside a suite's
      :term:`job's <job>` working directory. This directory is created by cylc
      and lies within the directory tree inside a suite's :term:`run directory`.

      ``<run directory>/work/<cycle>/<task-name>``

      The location of the work directory can be accessed by a :term:`job` via
      the environment variable ``CYLC_TASK_WORK_DIR``.

      Any files installed by :term:`rose apps <rose app>` will be placed within
      this directory.

      See also:

      * :term:`run directory`
      * :term:`share directory`

   share directory
      The share directory resides within a suite's :term:`run directory`, it
      serves the purpose of providing a storage place for any files which need
      to be shared between different tasks.

      ``<run directory>/share``

      The location of the share directory can be accessed by a :term:`job` via
      the environment variable ``CYLC_SUITE_SHARE_DIR``.

      In cycling suites files are typically stored in cycle sub-directories.

      See also:

      * :term:`run directory`
      * :term:`work directory`

   job log directory
      When cylc executes a :term:`job`, stdout and stderr are redirected to the
      ``job.out`` and ``job.err`` files which are stored in the job log
      directory.

      The job log directory lies within the :term:`run directory`:

      ``<run directory>/log/job/<cycle>/<task-name>/<submission-no>``

      Other files stored in the job log directory:

      * `job`: The :term:`job script`.
      * `job-activity.log`: A log file containing details of the
        :term:`jobs <job>` progress.
      * `job.status`: A file in which can be found cylc's most up-to-date
        understanding of the :term:`job's <job>` present status.

   job
      A job is a realisation of a :term:`task`. A job consists of a file called
      the :term:`job script` which is executed when the job "runs".

      See also:

      * :term:`task`
      * :term:`job script`

   job script
      A job script is the file containing bash script which is executed when a
      :term:`job` runs. A task's job script can be found in the
      :term:`job log directory`.

      See also:

      * :term:`task`
      * :term:`job`

   job host
      The job host is the compute platform that a :term:`job` runs on. For
      example ``some-host`` would be the job host for the task ``some-task`` in
      the following suite:

      .. code-block:: cylc

         [runtime]
             [[some-task]]
                 [[[remote]]]
                     host = some-host

   batch system
      A batch system or job scheduler is a system for submitting
      :term:`jobs <job>` onto a compute platform.

      See also:

      * `Wikipedia <https://en.wikipedia.org/wiki/Job_scheduler>`
      * :term:`directive`

   directive
      Directives are used by :term:`batch systems <batch system>` to determine
      what a :term:`jobs <job>` requirements are, e.g. how much memory it
      requires.

      Directives are set in the ``suite.rc`` file in the ``[runtime]`` section
      (``[runtime][<task-name>][directives]``).

      See also:

      * :term:`batch system`

   rose app
   rose application configuration
      TODO

   metadata
   rose metadata
      TODO
