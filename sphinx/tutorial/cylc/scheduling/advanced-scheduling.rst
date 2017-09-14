Advanced Scheduling
===================

In this section we will quickly run through some of the more advanced features
of cylc's scheduling logic.


.. include:: ../../../hyperlinks.rst
   :start-line: 1


.. _tutorial-qualifiers:

Qualifiers
----------

So far we have written dependencies like ``foo => bar``. This is, in-fact,
shorthand for ``foo:succeed => bar``, it means that the task ``bar`` will run
once ``foo`` has finished successfully. If ``foo`` were to fail then ``bar``
would not run. We will talk more about these :term:`task states <task state>`
in the TODO:Runtime_Section.

We would refer to the ``:succeed`` as a :term:`qualifier`. There are qualifiers
for different :term:`task states <task state>` e.g:

``:start``
    When the task has started running.
``:fail``
    Occurs when the task finishes if it fails (non-zero return code).
``:finish``
    Occurs when the task has stopped running irrespective of whether it has
    succeeded or failed.

It is also possible to create your own custom :term:`qualifiers <qualifier>`
to handle events within your code (custom outputs).

*For more information see the* `cylc user guide`_.


Clock Triggers
--------------

In cylc :term:`cycle points <cycle point>` are just labels. When using datetime
cycling, clock triggers can be used to force cycles to wait for a particular
time before running. This is necessary for certain operational and monitoring
systems.

.. code-block:: cylc

   [scheduling]
       initial cycle point = 20000101T00Z
       [[special tasks]]
           clock-trigger = daily(-PT1H)
       [[dependencies]]
           [[[T12]]]
                graph = daily  # daily will run at the earliest, one hour
                               # before midday.

*See the TODO:clock trigger tutorial for more information.*


Alternative Calendars
---------------------

By default cylc uses the Gregorian calendar for :term:`datetime cycling`, cylc
also supports the 360 day calendar (12 months of 30 days each in a year).

.. code-block:: cylc

   [scheduling]
       cycling mode = 360day

*For more information see the* `cylc user guide`_.
