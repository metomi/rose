.. include:: ../../../hyperlinks.rst
   :start-line: 1

.. _tutorial-cylc-clock-trigger:

Clock Triggered Tasks
=====================

.. TODO

   After #2423 has been finalised and merged this tutorial should be
   re-factored / re-written to incorporate the usage of ``cylc-graph``.

In a :term:`datetime cycling` suite the time represented by the
:term:`cycle points <cycle point>` bear no relation to the real-world time.
Using clock-triggers we can make tasks wait until their cycle point time before
running.

Clock-triggering effectively enables us to tether the "cycle time" to the
"real world time" which we refer to as the :term:`wall-clock time`.


Clock Triggering
----------------

When clock-triggering tasks we can use different
:ref:`offsets <tutorial-iso8601-durations>` to the cycle time as follows:

.. code-block:: cylc

   clock-trigger = taskname(CYCLE_OFFSET)

.. note::

   Regardless of the offset used, the task still belongs to the cycle from
   which the offset has been applied.


Example
-------

Our example suite will simulate a clock chiming on the hour.

Within your ``~/cylc-run`` directory create a new directory called
``clock-trigger``::

   mkdir ~/cylc-run/clock-trigger
   cd ~/cylc-run/clock-trigger

Paste the following code into a ``suite.rc`` file:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST

   [scheduling]
       initial cycle point = TODO
       final cycle point = +P1D # Run for one day
       [[dependencies]]
           [[[PT1H]]]
               graph = bell

   [runtime]
       [[root]]
           [[[events]]]
               mail events = failed
       [[bell]]
           env-script = eval $(rose task-env)
           script = printf 'bong%.0s\n' $(seq 1 $(cylc cyclepoint --print-hour))

Change the initial cycle point to 00:00 this morning (e.g. if it was
the first of January 2000 we would write ``2000-01-01T00Z``).

We now have a simple suite with a single task that prints "bong" a number
of times equal to the (cycle point) hour.

Run your suite using::

   cylc run clock-trigger

Stop the suite after a few cycles using the :guilabel:`stop` button in the
``cylc gui``. Notice how the tasks run as soon as possible rather than
waiting for the actual time to be equal to the cycle point.


Clock-Triggering Tasks
----------------------

We want our clock to only ring in real-time rather than the simulated
cycle time.

To do this, add the following lines to the ``[scheduling]`` section of
your ``suite.rc``:

.. code-block:: cylc

   [[special tasks]]
       clock-trigger = bell(PT0M)

This tells the suite to clock trigger the ``bell`` task with a cycle
offset of ``0`` hours.

Save your changes and run your suite.

Your suite should now be running the ``bell`` task in real-time. Any cycle times
that have already passed (such as the one defined by ``initial cycle time``)
will be run as soon as possible, while those in the future will wait for that
time to pass.

At this point you may want to leave your suite running until the next hour
has passed in order to confirm the clock triggering is working correctly.
Once you are satisfied, stop your suite.

By making the ``bell`` task a clock triggered task we have made it run in
real-time. Thus, when the wall-clock time caught up with the cycle time, the
``bell`` task triggered.


Adding More Clock-Triggered Tasks
---------------------------------

We will now modify our suite to run tasks at quarter-past, half-past and
quarter-to the hour.

Open your ``suite.rc`` and modify the ``[runtime]`` section by adding the
following:

.. code-block:: cylc

   [[quarter_past, half_past, quarter_to]]
       script = echo 'chimes'

Edit the ``[[scheduling]]`` section to read:

.. code-block:: cylc

   [[special tasks]]
       clock-trigger = bell(PT0M), quarter_past(PT15M), half_past(PT30M), quarter_to(PT45M)
   [[dependencies]]
       [[[PT1H]]]
           graph = """
               bell
               quarter_past
               half_past
               quarter_to
           """

Note the different values used for the cycle offsets of the clock-trigger tasks.

Save your changes and run your suite using::

   cylc run clock-trigger now

.. note::

   The ``now`` argument will run your suite using the current time for the
   initial cycle point.

Again, notice how the tasks trigger until the current time is reached.

Leave your suite running for a while to confirm it is working as expected
and then shut it down using the :guilabel:`stop` button in the ``cylc gui``.


Summary
-------

* Clock triggers are a type of :term:`dependency` which cause
  :term:`tasks <task>` to wait for the :term:`wall-clock time` to reach the
  :term:`cycle point` time.
* A clock trigger applies only to a single task.
* Clock triggers can only be used in datetime cycling suites.

For more information see the `Cylc User Guide`_.
