Clock Triggered Tasks
=====================

Introduction
------------

This part of the Rose user guide walks you through using clock triggered tasks.

This allows you to trigger tasks based on the actual time.

Purpose
-------

The typical use of clock triggered tasks is to perform real-time data retrieval

In general, most tasks in a suite do not care about the wall clock time, simply running once their prerequisites are met. Clock triggered tasks, however, wait for a particular wall clock time to be reached in addition to their other prerequisites.

Clock triggering
----------------

When clock triggering tasks we can use different offsets to the cycle time as follows:

.. code-block:: cylc

   clock-trigger = taskname(CYCLE_OFFSET)

Note that, regardless of the offset used, the task still belongs to the cycle from which the offset has been applied.


Example
-------

Our example suite will simulate a clock chiming on the hour.

Create a new suite (or just a new directory somewhere - e.g. in your homespace) containing a blank ``rose-suite.conf`` and a ``suite.rc`` file with the following contents:


.. code-block:: cylc

   #!jinja2
   [cylc]
       UTC mode = True # Ignore DST
   [scheduling]
       initial cycle point = 
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
           script = printf 'bong%.0s\n' $(seq 1 $(rose date -c --format=%H))i

We now have a simple suite with a single task that prints "bong" a number of times equal to the (cycle time) hour.

Run your suite using:

.. code-block:: console

   rose suite-run

and stop it after a few cycles using the stop button in the ``cylc gui``. Notice how the tasks run as soon as possible rather than waiting for the actual time to be equal to the cycle time.

Use ``rose suite-log`` to view the suite logs and look at the output for one of the bell tasks to confirm it is behaving as expected. N.B. this particular clock is running in UTC so the number of "bong"s may vary from your local time.

Clock triggering tasks
----------------------

We want our clock to only ring in real time rather than the accelerated cycle time.

To do this, add the following lines to the ``[scheduling]`` section of your ``suite.rc``:

.. code-block:: cylc

   [[special tasks]]
       clock-trigger = bell(PT0M)


This tells the suite to clock trigger the ``bell`` task with a cycle offset of 0 hours.

Save your changes and run your suite.


Results
-------

Your suite should now be running the bell task in realtime. Any cycle times that have already passed (such as the one defined by ``initial cycle time``) will be run as soon as possible, while those in the future will wait for that time to pass.

At this point you may want to leave your suite running until the next hour has passed in order to confirm the clock triggering is working correctly. Once you are satisfied, stop your suite.

By making the ``bell`` task a clock triggered task we have made it run in realtime. Thus, when the time caught up with the cycle time, the bell task triggered.


Further clock triggering
------------------------

We will now modify our suite to run tasks at quarter-past, half-past and quarter-to the hour.

Open your ``suite.rc`` and modify the ``[runtime]`` section by adding the following:

.. code-block:: cylc

   [[quarter_past, half_past, quarter_to]]
       script = echo 'chimes'

Similarly, modify the ``[[scheduling]]`` section as follows:

.. code-block:: cylc

   [[special tasks]]
       clock-trigger = bell(PT0M), quarter_past(PT15M), half_past(PT30M), quarter_to(PT45M)
   [[dependencies]]
       [[[PT1H]]]
           graph = bell => quarter_past => half_past => quarter_to


Note the different values used for the cycle offsets of the clock-trigger tasks.

Save your changes and run your suite using:

.. code-block:: console

   rose suite-run now

which will run your suite using the current time as the initial cycle time.

Again, notice how the tasks trigger until the current time is reached.

Leave your suite running for a while to confirm it is working as expected and then shut it down using the stop button in the ``cylc gui``.


Summary
-------

You have now successfully created and run a suite that:

   - runs a bell task in realtime on the hour
   - runs different chiming tasks at quarter-past, half-past and quarter-to the hour

For more information see the `cylc User Guide`_.

.. _cylc User Guide: http://cylc.github.io/cylc/html/single/cug-html.html

 
