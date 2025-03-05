.. _rose-tutorial-datetime-manipulation:

Date and Time Manipulation
==========================

:term:`Datetime cycling <datetime cycling>` suites inevitably involve
performing some form of datetime arithmetic. For example, in a Cylc task we
can calculate the cycle point three hours before the
present cycle using::

   cylc cyclepoint --offset-hours=-3

The `isodatetime`_ command provides functionality
beyond ``cylc cyclepoint``. Cylc also provides the ``CYLC_TASK_SHARE_CYCLE_DIR``
environment variable which provides an easy way to get the path of the
``share/cycle/<point>`` directory.


The ``isodatetime`` Command
---------------------------

The ``isodatetime`` command provides functionality for:

* Parsing and formatting datetimes e.g:

  .. code-block:: console

     $ isodatetime 12-31-2000 --parse-format='%m-%d-%Y'
     12-31-2000
     $ isodatetime 12-31-2000 --parse-format='%m-%d-%Y' --format='DD-MM-CCYY'
     31-12-2000

* Adding offsets to datetimes e.g:

  .. code-block:: console

     $ isodatetime 2000-01-01T00:00Z --offset '+P1M'
     2000-02-01T00:00Z

* Calculating the duration between two datetimes e.g:

  .. code-block:: console

     $ isodatetime 2000 2001  # Note - 2000 was a leap year!
     P366D

See the ``isodatetime --help`` command reference for more information.


Using ``isodatetime`` In A Suite
--------------------------------

In datetime cycling suites, ``isodatetime`` can work with the
cyclepoint using the ``CYLC_TASK_CYCLE_POINT`` environment variable:

.. code-block:: cylc

   [runtime]
       [[hello_america]]
           script = isodatetime $CYLC_TASK_CYCLE_POINT --format='MM-DD-CCYY'

Alternatively, Cylc automatically sets the ``ISODATETIMEREF`` environment variable
which allows you to use the special ``ref`` argument:

.. code-block:: cylc

   [runtime]
       [[hello_america]]
           script = isodatetime ref --format='MM-DD-CCYY'


The ``ROSE_DATAC`` Environment Variable
---------------------------------------

.. note::

   From Cylc 8.5.0 the variable ``CYLC_TASK_SHARE_CYCLE_DIR`` should be preferred
   to ``ROSE_DATAC``.

There are two locations where task output is likely to be located:

The work directory
   Each task is executed within its :term:`work directory` which is located in:

   .. code-block:: sub

      <run directory>/work/<cycle>/<task-name>

   The path to a task's work directory can be obtained from the
   ``CYLC_TASK_WORK_DIR`` environment variable.

The share directory
   The :term:`share directory` serves the purpose of providing a storage place
   for any files which need to be shared between different tasks.

   Within the share directory data is typically stored within cycle
   subdirectories i.e:

   .. code-block:: sub

      <run directory>/share/cycle/<cycle>

   These are called the ``share/cycle`` directories.
   ``CYLC_SHARE_CYCLE_DIR`` provides the path to::

      "$CYLC_WORKFLOW_SHARE_DIR/cycle/$CYLC_TASK_CYCLE_POINT"


To get the path to a previous (or a future) ``share/cycle`` directory we can
provide an offset to isodatetime:

.. code-block:: bash

   isodatetime "${CYLC_TASK_CYCLE_POINT} --offset -P1D

Which can be used to provide custom offset directory locations:

.. code-block:: bash

   # Cylc task script
   CYCLE_POINT_MINUS_P1D=$(isodatetime "${CYLC_TASK_CYCLE_POINT} --offset -P1D)"

   TODAYS_DATA="${CYLC_WORKFLOW_SHARE_DIR}/cycle/${CYLC_TASK_CYCLE_POINT}/output.data"
   YESTERDAYS_DATA="${CYLC_WORKFLOW_SHARE_DIR}/cycle/${CYCLE_POINT_MINUS_P1D}/output.data"

   # Do something with "${YESTERDAYS_DATA}" and "${TODAYS_DATA}"

.. TODO - Write a short practical using ROSE_DATAC and isodatetime.
