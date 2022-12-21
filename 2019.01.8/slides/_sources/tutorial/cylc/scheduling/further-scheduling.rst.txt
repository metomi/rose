.. include:: ../../../hyperlinks.rst
   :start-line: 1

.. _tutorial-cylc-further-scheduling:

Further Scheduling
==================

In this section we will quickly run through some of the more advanced features
of Cylc's scheduling logic.


.. _tutorial-qualifiers:

Qualifiers
----------

.. ifnotslides::

   So far we have written dependencies like ``foo => bar``. This is, in fact,
   shorthand for ``foo:succeed => bar``. It means that the task ``bar`` will run
   once ``foo`` has finished successfully. If ``foo`` were to fail then ``bar``
   would not run. We will talk more about these :term:`task states <task state>`
   in the `Runtime Section <tutorial-tasks-and-jobs>`_.

   We refer to the ``:succeed`` descriptor as a :term:`qualifier`.
   There are qualifiers for different :term:`task states <task state>` e.g:

.. ifslides::

   .. code-block:: cylc-graph

      foo => bar
      foo:succeed => bar
      foo:fail => bar

``:start``
   When the task has started running.
``:fail``
   When the task finishes if it fails (produces non-zero return code).
``:finish``
   When the task has completed (either succeeded or failed).

.. nextslide::

It is also possible to create your own custom :term:`qualifiers <qualifier>`
to handle events within your code (custom outputs).

.. ifnotslides::

   *For more information see the* `Cylc User Guide`_.


Clock Triggers
--------------

.. ifnotslides::

   In Cylc, :term:`cycle points <cycle point>` are just labels. Tasks are
   triggered when their dependencies are met irrespective of the cycle they are
   in, but we can force cycles to wait for a particular time before running
   using clock triggers. This is necessary for certain operational and
   monitoring systems.

   For example in the following suite the cycle ``2000-01-01T12Z`` will wait
   until 11:00 on the 1st of January 2000 before running:

.. code-block:: cylc

   [scheduling]
       initial cycle point = 2000-01-01T00Z
       [[special tasks]]
           clock-trigger = daily(-PT1H)
       [[dependencies]]
           [[[T12]]]
                graph = daily  # "daily" will run, at the earliest, one hour
                               # before midday.

.. tip::

   See the :ref:`tutorial-cylc-clock-trigger` tutorial for more information.


Alternative Calendars
---------------------

.. ifnotslides::

   By default Cylc uses the Gregorian calendar for :term:`datetime cycling`,
   but Cylc also supports the 360-day calendar (12 months of 30 days each in
   a year).

.. code-block:: cylc

   [scheduling]
       cycling mode = 360day

.. ifnotslides::

   *For more information see the* `Cylc User Guide`_.

.. nextslide::

.. ifslides::

   Next section: :ref:`Runtime Introduction
   <tutorial-cylc-runtime-introduction>`
