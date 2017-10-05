.. _nowcasting: https://www.metoffice.gov.uk/learning/science/hours-ahead/nowcasting

.. _tutorial-datetime-cycling:

Date-Time Cycling
=================


In the last section we looked at writing an :term:`integer cycling` workflow,
one where the :term:`cycle points <cycle point>` are numbered.

Typically workflows are repeated at a regular interval, say every day or every
few hours. To make this easier cylc has a date-time cycling mode where the
:term:`cycle points <cycle point>` use dates rather than numbers.

.. admonition:: Reminder
   :class: tip

   :term:`Cycle points <cycle point>` are labels, cylc runs tasks as soon as
   their dependencies are met so cycles do not necessarily run in order.


.. _tutorial-iso8601:

ISO8601
-------

In cylc dates, times and durations are written using the :term:`ISO8601` format
- an international standard for representing dates and times.

.. _tutorial-iso8601-datetimes:

Date-Times
^^^^^^^^^^

In ISO8601 datetimes are written from the largest unit to the smallest
(i.e: year, month, day, hour, minute, second) with the ``T`` character
separating the date and time components. For example, midnight on the 1st of
January 2000 is written ``20000101T000000``.

For brevity we may omit seconds (and minutes) from the time i.e:
``20000101T0000``.

For readability we may add hyphen ``-`` characters between the date components
and colon ``:`` characters between the time components i.e:
``2000-01-01T00:00``.

Time-zone information can be added onto the end. UTC is written ``Z``,
UTC+1 is written ``+01``, etc. E.G: ``2000-01-01T00:00Z``.

.. Diagram of an iso8601 datetime's components.

.. math::

   \color{blue}{\overbrace{
   \underbrace{\huge 1985}_{_{\text{Year}}}
   {\huge\text{-}}
   \underbrace{\huge 04}_{_{\text{Month}}}
   {\huge\text{-}}
   \underbrace{\huge 12}_{_{\text{Day}}}
   }^{\text{Date Components}}}
   \overbrace{\huge \text{T}}^{\text{Seperator}}
   \color{green}{\overbrace{
   \underbrace{\huge 23}_{_{\text{Hour}}}
   {\huge:}
   \underbrace{\huge 20}_{_{\text{Minute}}}
   {\huge:}
   \underbrace{\huge 30}_{_{\text{Second}}}
   \underbrace{\huge \text{Z}}_{_{\text{Time Zone}}}
   }^{\text{Time Components}}}

.. _tutorial-iso8601-durations:

Durations
^^^^^^^^^

In ISO8601 a duration prefixed with a ``P`` and are written with a character
following each unit:

* ``Y`` for year.
* ``M`` for month.
* ``D`` for day.
* ``W`` for week.
* ``H`` for hour.
* ``M`` for minute.
* ``S`` for second.

As with datetimes the components are written in order from largest to smallest
and the date and time components are separated by the ``T`` character. E.G:

* ``P1D`` one day.
* ``PT1H`` one hour.
* ``P1DT1H`` one day and one hour.
* ``PT1H30M`` one and a half hours.
* ``P1Y1M1DT1H1M1S`` a year and a month and a day and an hour and a
  minute and a second.


Date-Time Recurrences
---------------------

In :term:`integer cycling` suites recurrences are written ``P1``, ``P2``,
etc.

In :term:`date-time cycling <datetime cycling>` there are two ways to write
recurrences:

1. Using ISO8601 durations (e.g. ``P1D``, ``PT1H``).
2. Using ISO8601 date-times with inferred recurrence.

Inferred Recurrence
^^^^^^^^^^^^^^^^^^^

A recurrence can be interred from a date-time by omitting digits from the
front. For example if the year is omitted then the recurrence can be inferred
to be annual. E.G:

* ``01-01T00`` every year on the 1st of January.
* ``01T00`` every month on the first of the month.
* ``T00`` every day at midnight.
* ``T-00`` every hour at 0 minutes past (every hour on the hour).
  *Note that the ``-`` takes the place of the hour digits as we may not omit
  components after the ``T`` character.*

Recurrence Formats
^^^^^^^^^^^^^^^^^^

As with integer cycling, recurrences start, by default, at the
:term:`initial cycle point`. We can override this in one of two ways:

1. By defining an arbitrary cycle point (``datetime/recurrence``):

   * ``2000/P1Y`` every year starting with the year 2000.
   * ``2000-01-01T00/T00`` every day at midnight starting on the 1st of January
     2000
   * ``2000-01-01T12/T00`` every day at midnight starting at the first midnight
     after the 1st of January at 12:00 (i.e ``2000-01-02T00``).

.. _tutorial-cylc-datetime-offset-icp:

2. By defining an offset from the initial cycle point (``offset/recurrence``).
   This offset is an ISO8601 duration preceded by a plus character.

   * ``+P1Y/P1Y`` every year starting one year after the initial cycle point.
   * ``+PT1H/T00`` every day starting at the first midnight after the point one
     hour after the initial cycle point.

.. warning::

   When using durations beware that if the initial cycle point is changed then
   the recurrence might produce different results.

   For example if you set the initial cycle point to ``2000-01-01T00`` the
   recurrence ``P1D`` would yield:

   ``2000-01-01T00``, ``2000-01-02T00``, ``2000-01-03T00``, ...

   If, however the initial cycle point were changed from midnight to midday
   (``2000-01-01T12``) then the same recurrence would yield:

   ``2000-01-01T12``, ``2000-01-02T12``, ``2000-01-03T12``, ...

   This can be easily fixed. Both of the following recurrences mean start at
   the first midnight *after* the initial cycle point.

   * ``T00/P1D``
   * ``T00``

The Initial & Final Cycle Points
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two special recurrences for the initial and final cycle points:

* ``R1`` repeat once at the initial cycle point.
* ``R1/P0Y`` repeat once at the final cycle point.

Inter Cycle Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^

Inter-cycle dependencies are written as ISO8601 durations e.g:

* ``foo[-P1D]`` the task ``foo`` from the cycle one day before.
* ``bar[-PT1H30M]`` the task ``bar`` from the cycle 1 hour 30 minutes before.

The initial cycle point can be referenced using a caret character ``^`` e.g:

* ``baz[^]`` the task ``baz`` from the initial cycle point.


UTC Mode
--------

Due to all of the difficulties that time-zones can cause, particularly with
daylight savings, we typically use UTC (that's the ``+00`` time zone) in cylc
suites.

When a suite uses UTC all of the cycle points will be written in the
``+00`` time zone.

To make your suite use UTC set the ``[cylc]UTC mode`` setting to ``True``, i.e:

.. code-block:: cylc

   [cylc]
       UTC mode = True


Putting It All Together
-----------------------

Cylc was originally developed for running operational weather forecasting, in
this section we will outline a basic (dummy) weather forecasting suite and how
to implement it in cylc.

.. note::

   Technically the suite outlined in this section is a `nowcasting`_ suite.
   We will refer to it as forecasting for simplicity.

A basic weather forecasting workflow contains three main steps:

1. Gathering Observations
^^^^^^^^^^^^^^^^^^^^^^^^^

We gather observations from different weather stations and use them to
build a picture of the current weather. Our dummy weather forecast
will get wind observations from four weather stations:

* Belmullet
* Camborne
* Heathrow
* Shetland

The tasks which get observation data will be called
``get_observations_<site>`` where ``site`` is the name of a weather
station.

Next we need to consolidate these observations so that our forecasting
system can work with them, to do this we have a
``consolidate_observations`` task.

We will fetch wind observations **every three hours starting from the initial
cycle point**.

The ``consolidate_observations`` task must run after the
``get_observations<site>`` tasks.

.. digraph:: example
   :align: center

   size = "5,4"
   bgcolor=none

   get_observations_camborne -> consolidate_observations
   get_observations_heathrow -> consolidate_observations
   get_observations_aberdeen -> consolidate_observations

We will also use the UK radar network to get rainfall data with a task
called ``get_rainfall``.

We will fetch rainfall data **every six hours starting from six hours after the
initial cycle point**.

2. Running computer models to generate forecast data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will do this with a task called ``forecast`` which will run
**every six hours starting six hours after the initial cycle point**.
The ``forecast`` task will be dependent on:

* The ``consolidate_observations`` tasks from the previous two as well as
  the present cycles.
* The ``get_rainfall`` task from the present cycle.

.. digraph:: example
   :align: center

   size = "5,4"
   bgcolor=none

   subgraph cluster_T00 {
       label="+PT0H"
       style="dashed"
       "observations.t00" [label="consolidate observations\n+PT0H"]
   }

   subgraph cluster_T03 {
       label="+PT3H"
       style="dashed"
       "observations.t03" [label="consolidate observations\n+PT3H"]
   }

   subgraph cluster_T06 {
       label="+PT6H"
       style="dashed"
       "forecast.t06" [label="forecast\n+PT6H"]
       "get_rainfall.t06" [label="get_rainfall\n+PT6H"]
       "observations.t06" [label="consolidate observations\n+PT6H"]
   }

   "observations.t00" -> "forecast.t06"
   "observations.t03" -> "forecast.t06"
   "observations.t06" -> "forecast.t06"
   "get_rainfall.t06" -> "forecast.t06"

3. Processing the data output to produce user-friendly forecasts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This will be done with a task called ``post_process_<location>`` where
``location`` is the place we want to generate the forecast for. For
the moment we will use Exeter.

The ``post_process_exeter`` task will run **every six hours starting six hours
after the initial cycle point** and will be dependent on the ``forecast`` task.

.. digraph:: example
   :align: center

   size = "1.5,1"
   bgcolor=none

   "forecast" -> "post_process_exeter"

.. practical::

   .. rubric:: In this practical we will create a dummy forecasting suite
      using date-time cycling.

   #. **Create A New Suite.**

      Create a new directory called ``datetime-cycling`` and paste the
      following code into a ``suite.rc`` file.

      .. code-block:: cylc

         [cylc]
             UTC mode = True
         [scheduling]
             initial cycle point = 20000101T00
             [[dependencies]]

   #. **Add The Recurrences.**

      This suite will require two recurrences. Add sections under the
      dependencies section for these.

      .. hint::

         See :ref:`Date-Time Recurrences<tutorial-cylc-datetime-offset-icp>`.

      .. spoiler:: Solution warning

         The two recurrences you need are

         * ``PT3H`` repeat every three hours starting from the initial cycle
           point.
         * ``+PT6H/PT6H`` repeat every six hours starting six hours after the
           initial cycle point

         .. code-block:: diff

             [cylc]
                 UTC mode = True
             [scheduling]
                 initial cycle point = 20000101T00Z
                 [[dependencies]]
            +        [[[PT3H]]]
            +        [[[+PT6H/PT6H]]]

   #. **Write The Graphing.**

      With the help of the graphs and the information above add dependencies to
      your suite to implement the weather forecasting workflow.

      You will need to consider the inter-cycle dependencies between tasks.

      Use ``cylc graph`` to inspect your work.

      .. spoiler:: Hint hint

         The dependencies you will need to write are:

         * The ``consolidate_observations`` task is dependent on the
           ``get_observations_<site>`` tasks.
         * The ``forecast`` task is dependent on:

           * The ``get_rainfall`` task.
           * The ``consolidate_observations`` tasks from:

             * The present cycle.
             * The cycle 3 hours before (``-PT3H``).
             * The cycle 6 hours before (``-PT6H``).

         * The ``post_process_exeter`` task is dependent on the ``forecast``
           task.

      .. spoiler:: Solution warning

         .. code-block:: cylc

           [cylc]
               UTC mode = True
           [scheduling]
               initial cycle point = 20000101T00
               [[dependencies]]
                   [[[PT3H]]]
                       graph = """
                           get_observations_belmullet => consolidate_observations
                           get_observations_camborne => consolidate_observations
                           get_observations_heathrow => consolidate_observations
                           get_observations_shetland => consolidate_observations
                       """
                   [[[+PT6H/PT6H]]]
                       graph = """
                           consolidate_observations => forecast
                           consolidate_observations[-PT3H] => forecast
                           consolidate_observations[-PT6H] => forecast
                           get_rainfall => forecast => process_exeter
                       """

   #. **Inter-Cycle Offsets.**

      To ensure the ``forecast`` tasks run in order the ``forecast`` task will
      also need to be dependent on its previous run.

      .. digraph:: example
         :align: center

         size = "4,1.5"
         bgcolor=none
         rankdir=LR

         subgraph cluster_T06 {
             label="T06"
             style="dashed"
             "forecast.t06" [label="forecast\nT06"]
         }

         subgraph cluster_T12 {
             label="T12"
             style="dashed"
             "forecast.t12" [label="forecast\nT12"]
         }

         subgraph cluster_T18 {
             label="T18"
             style="dashed"
             "forecast.t18" [label="forecast\nT18"]
         }

         "forecast.t06" -> "forecast.t12" -> "forecast.t18"

      We can express this dependency as ``forecast[-PT6H] => forecast``.

      Try adding this line to your suite then visualising it with ``cylc
      graph``.

      You will notice that there is a dependency which looks like this:

      .. digraph:: example
        :align: center

         size = "4,1"
         bgcolor=none
         rankdir=LR

         "forecast.t00" [label="forecast\n20000101T0000Z"
                         color="#888888"
                         fontcolor="#888888"]
         "forecast.t06" [label="forecast\n20000101T0600Z"]


         "forecast.t00" -> "forecast.t06"

      Note that the ``forecast`` task in the 00:00 cycle is gray. The reason
      for this is that this task does not exist. Remember the forecast task runs
      every six hours **starting 6 hours after the initial cycle point**.

      The dependency is only valid from 12:00 onwards so to fix the problem we
      must add a new dependency section which repeats every six hours
      **starting 12 hours after the initial cycle point**.

      Make the following changes to your suite, the gray task should now
      disappear:

      .. code-block:: diff

                    [[[+PT6H/PT6H]]]
                        graph = """
                            ...
         -                  forecast[-PT6H] => forecast
                        """
         +          [[[+PT12H/PT6H]]]
         +              graph = """
         +                  forecast[-PT6H] => forecast
         +              """
