.. include:: ../../hyperlinks.rst
   :start-line: 1

Summary
=======

Suite Structure
---------------

So far we have covered:

* Cylc suites.
* Rose suite configurations.
* Rosie suites.

The relationship between them is as follows:

.. graph:: Example
   :align: center

    ranksep = 0
    bgcolor = none
    size = "7, 5"

    node [shape="plaintext", fontcolor="#606060", fontname="sans"]
    edge [style="invis"]

    subgraph cluster_1 {
        label = "Cylc Suite"
        fontsize="20"
        fontcolor="#5050aa"
        fontname="sans"
        labelloc="r"
        "suite.rc" [fontsize="18", fontname="mono", fontcolor"black"]
        "rcinfo" [label="Defines the workflow\nin terms of tasks\nand dependencies"]
        "suite.rc" -- "rcinfo"

        subgraph cluster_2 {
            label = "Rose Suite Configuration"
            "rose-suite.conf" [fontsize="18", fontname="mono", fontcolor"black"]
            "confinfo" [label="Defines Jinja2 variables for\nthesuite.rc and environment\nvariable for use throughout\nthe suite"]
            "rose-suite.conf" -- "confinfo"

            subgraph cluster_3 {
                label = "Rosie Suite"
                "rose-suite.info" [fontsize="18", fontname="mono", fontcolor"black"]
                "infoinfo" [label="Contains basic information\nabout the suite used\nby Rosie for searching\nand version control purposes"]
                "rose-suite.info" -- "infoinfo"
            }
        }
    }

Cylc suites can have Rose applications. These are stored in an ``app``
directory and are configured using a :rose:file:`rose-app.conf` file.

.. TODO - A file tree for an example Rose suite + a full file tree showing
          all possible files and directories with descriptions, this will
          require an extension and some CSS magic to ensure viable output
          in HTML and PDF.


Suite Commands
--------------

.. rubric:: We have learned the following cylc commands:

``cylc graph``
   Draws the suite's :term:`graph`.
``cylc get-config``
   Processes the ``suite.rc`` file and prints it back out.
``cylc validate``
   Validate the cylc ``suite.rc`` file to check for any obvious errors.
``cylc run``
   Runs a suite.
``cylc stop``
   Stops a suite:

   ``--kill``
      Killing all running / submitted tasks
   ``--now --now``
      Leaving all running / submitted tasks running.

``cylc restart``
   Starts a suite picking up where it left off.

.. rubric:: We have learned the following Rose commands:

:ref:`command-rose-app-run`
   Runs a Rose application.
:ref:`command-rose-task-run`
   Used to run a Rose application from within a cylc suite.
:ref:`command-rose-suite-run`
   Runs a Rose suite.
:ref:`command-rose-suite-restart`
   Runs a Rose suite picking up where it left off.

The cylc commands do not know about the :rose:file:`rose-suite.conf` file
so for Rose suite configurations you will have to install the suite before
using commands such as ``cylc graph`` e.g:

.. code-block:: sub

   rose suite-run -l  # install the suite on the local host only - don't run it.
   cylc graph <suite> # run cylc graph using the installed version of the suite.


Rose Utilities
--------------

Rose contains some utilities to make life easier:

:ref:`command-rose-date`
   A utility for parsing, manipulating and formatting date-times which is
   useful for working with the cylc :term:`cycle point`:

   .. code-block:: console

      $ rose date 2000 --offset '+P1Y1M1D'
      2001-02-02T0000Z

      $ rose date $CYLC_TASK_CYCLE_POINT --format 'The month is %B.'
      The month is April.

   See the :ref:`date-time tutorial <rose-tutorial-datetime-manipulation>`
   for more information.

:ref:`command-rose-host-select`
   A utility for select a host from a group with the ability to rank choices
   based on server load or free memory.
   
   Groups are configured using the
   :rose:conf:`rose.conf[rose-host-select]group{NAME}` setting.
   For example to define a cluster called "mycluster" containing the hosts
   "computer1", "computer2" and "computer3".

   .. code-block:: rose

      [rose-host-select]
      group{mycluster}=computer1 computer2 computer3

   Hosts can then be selected from the cluster on the command line:

   .. code-block:: console

      $ rose host-select mycluster
      computer2

   The :ref:`command-rose-host-select` command can by used within cylc suites
   to determine which host a task runs on:

   .. code-block:: cylc

      [runtime]
         [[foo]]
            script = echo "Hello $(hostname)!"
            [[[remote]]]
               host = rose host-select mycluster

   See the :ref:`command line documentation <command-rose-host-select>` for
   more information.


Rose Built-In Applications
--------------------------

Along with the Rose utilities there are also the Rose built-in applications.

:rose:app:`fcm_make`
   A template for running the ``fcm make`` command.
:rose:app:`rose_ana`
   Runs the rose-ana analysis engine.
:rose:app:`rose_arch`
   Provides a generic solution to configure site specific archiving of suite
   files.
:rose:app:`rose_bunch`
   For the running of multiple command variants in parallel under a single job.
:rose:app:`rose_prune`
   A framework for housekeeping a cycling suite.

For more information on these applications and how to use them see the
:ref:`Rose Built-In Applications` section.


Next Steps
----------

:ref:`Rose Further Topics`
   Tutorials going over some of the more specific aspects of Rose not
   covered in the main tutorial.
:ref:`Cheat Sheet`
   A quick breakdown of the commands for running
   and interacting with suites using cylc and rose.
:ref:`Command Reference`
   Contains the command line documentation
   (also obtainable by calling ``rose --help``).
:ref:`Rose Configuration <rose-configuration>`
   The possible settings which can be used in the different Rose
   configuration files.
`cylc suite design guide`_
   Contains recommended best-practice for the style and structure of cylc
   suites.
