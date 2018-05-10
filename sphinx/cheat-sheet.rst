.. _Cheat Sheet:

Cheat Sheet
===========

This page outlines how to perform suite operations for "pure" :term:`Cylc
suites <Cylc suite>` (*the Cylc way*) and those using :term:`Rose suite
configurations <rose suite configuration>` (*the Rose way*).

.. Use the "sub" lexer as the default for this file.

.. highlight:: sub


.. _Starting Suites:

Running/Interacting With Suites
--------------------------------

Starting Suites
^^^^^^^^^^^^^^^

.. list-table::
   :class: grid-table

   * - .. rubric:: The Cylc Way
     - .. rubric:: The Rose way
   * - ::

         cylc validate <name>
         cylc run <name>
     - ::

         # run the suite in the current directory:
         rose suite-run

         # run a suite in another directory:
         rose suite-run -C <path>

         # run using a custom name:
         rose suite-run --name <name>

.. _Stopping Suites:

Stopping Suites
^^^^^^^^^^^^^^^

::

   # Wait for running/submitted tasks to finish then shut down the suite:
   cylc stop <name>

   # Kill all running/submitted tasks then shut down the suite:
   cylc stop <name> --kill

   # Shut down the suite now leaving any running/submitted tasks behind.
   # If the suite is restarted Cylc will "re-connect" with these jobs,
   # continuing where it left off:
   cylc stop <name> --now --now

.. _Restarting Suites:

Restarting Suites (From Stopped)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pick up a suite where it left off after a shutdown. Cylc will "re-connect" with
any jobs from the previous run.

.. list-table::
   :class: grid-table

   * - .. rubric:: The Cylc Way
     - .. rubric:: The Rose Way
   * - ::

         cylc restart <name>
     - ::

         # Restart the suite from the run
         # directory (recommended):
         rose suite-restart

         # Re-install the suite from the suite
         # directory then restart:
         rose suite-run --restart

Restarting Suites (From Running)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*This might be needed, for instance, to upgrade a running suite to a
newer version of Cylc.*

Stop a suite leaving all running/submitted jobs unchanged, then restart the
suite without making any changes to the :term:`run directory`. Cylc will
"re-connect" with any jobs from the previous run.

.. list-table::
   :class: grid-table

   * - .. rubric:: The Cylc Way
     - .. rubric:: The Rose Way
   * - ::

         cylc stop <name> --now --now
         cylc restart <name>
     - ::

         cylc stop <name> --now --now
         rose suite-restart


.. _Reloading Suites:

Reloading Suites
^^^^^^^^^^^^^^^^

Change the configuration of a running suite.

.. list-table::
   :class: grid-table

   * - .. rubric:: The Cylc Way
     - .. rubric:: The Rose Way
   * - ::

         cylc reload <name>

     - ::

         # Re-install the suite run directory then
         # perform `cylc reload`:
         rose suite-run --reload


Scanning/Inspecting Suites
--------------------------

List Running Suites
^^^^^^^^^^^^^^^^^^^

::

   # On the command line:
   cylc scan

   # Via a GUI:
   cylc gscan

Visualise A Running Suite
^^^^^^^^^^^^^^^^^^^^^^^^^

::

   cylc gui <name>

Visualise A Suite's :term:`Graph`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :class: grid-table

   * - .. rubric:: The Cylc Way
     - .. rubric:: The Rose Way
   * - ::

         # No special steps required.
     - ::

         # Only if the suite is not running:
         rose suite-run -l

::

   cylc graph <name>

View A Suite's ``suite.rc`` Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :class: grid-table

   * - .. rubric:: The Cylc Way
     - .. rubric:: The Rose Way
   * - ::

         # No special steps required.
     - ::

         # Only if the suite is not running:
         rose suite-run -l

::

   cylc get-config --sparse <name or path-to-suite>

   # View the "full" configuration with defaults included:
   cylc get-config <name or path-to-suite>

   # View a specific configuration item (e.g. "[scheduling]initial cycle point"):
   cylc get-config <name or path-to-suite> -i <item>
