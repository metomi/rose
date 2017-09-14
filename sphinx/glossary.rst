Glossary
========

.. glossary::
   :sorted:

   cylc suite
      A cylc suite is a directory containing a ``suite.rc`` file which contains
      :term:`graphing<graph>` representing a workflow.

   rose suite
      A rose suite is a :term:`cylc suite` which also contains a
      ``rose-suite.conf`` file and optionally :term:`rose apps<app>`,
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

   task
      TODO

   task state
      TODO

   app
   application
   rose application
      TODO

   metadata
   rose metadata
      TODO
