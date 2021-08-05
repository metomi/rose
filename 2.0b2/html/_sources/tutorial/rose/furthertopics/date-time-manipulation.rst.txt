.. _rose-tutorial-datetime-manipulation:

Date and Time Manipulation
==========================

:term:`Datetime cycling <datetime cycling>` suites inevitably involve
performing some form of datetime arithmetic. In the
:ref:`weather forecasting suite <tutorial-datetime-cycling-practical>` we wrote
in the Cylc tutorial this arithmetic was done using the ``cylc cyclepoint``
command. For example we calculated the cycle point three hours before the
present cycle using::

   cylc cyclepoint --offset-hours=-3

Rose provides the :ref:`command-rose-date` command which provides functionality
beyond ``cylc cyclepoint`` as well as the :envvar:`ROSE_DATAC` environment
variable which provides an easy way to get the path of the ``share/cycle``
directory.


The ``rose date`` Command
-------------------------

The :ref:`command-rose-date` command provides functionality for:

* Parsing and formatting datetimes e.g:

  .. code-block:: console

     $ rose date '12-31-2000' --parse-format='%m-%d-%Y' 
     12-31-2000
     $ rose date '12-31-2000' --parse-format='%m-%d-%Y' --format='DD-MM-CCYY'
     31-12-2000

* Adding offsets to datetimes e.g:

  .. code-block:: console

     $ rose date '2000-01-01T0000Z' --offset '+P1M'
     2000-02-01T0000Z

* Calculating the duration between two datetimes e.g:

  .. code-block:: console

     $ rose date '2000' '2001'  # Note - 2000 was a leap year!
     P366D

See the :ref:`command-rose-date` command reference for more information.


Using ``rose date`` In A Suite
------------------------------

In datetime cycling suites :ref:`command-rose-date` can work with the
cyclepoint using the ``CYLC_TASK_CYCLE_POINT`` environment variable:

.. code-block:: cylc

   [runtime]
       [[hello_america]]
           script = rose date $CYLC_TASK_CYCLE_POINT --format='MM-DD-CCYY'

Alternatively, if you are providing the standard Rose task environment using
:ref:`command-rose-task-env` then :ref:`command-rose-date` can use the ``-c``
option to pick up the cycle point:

.. code-block:: cylc

   [runtime]
       [[hello_america]]
           env-script = eval $(rose task-env)
           script = rose date -c --format='MM-DD-CCYY'


The ``ROSE_DATAC`` Environment Variable
---------------------------------------

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

      <run directory>/share/<cycle>

   These are called the ``share/cycle`` directories.

   The path to the root of the share directory is provided by the
   ``CYLC_SUITE_SHARE_DIR`` environment variable so the path to the cycle
   subdirectory would be::

      "$CYLC_SUITE_SHARE_DIR/$CYLC_SUITE_CYCLE_POINT"

The :ref:`command-rose-task-env` command provides the environment variable
:envvar:`ROSE_DATAC` which is a more convenient way to obtain the path of the
``share/cycle`` directory.

To get the path to a previous (or a future) ``share/cycle`` directory we can
provide an offset to :ref:`command-rose-task-env` e.g::

   rose task-env --cycle-offset=PT1H

The path is then made available as the ``ROSE_DATACPT1H`` environment variable.

.. TODO - Write a short practical using ROSE_DATAC and rose-date.
