.. include:: ../../hyperlinks.rst
   :start-line: 1


.. _tutorial-rose-summary:

Summary
=======


Suite Structure
---------------

So far we have covered:

* Cylc suites.
* Rose suite configurations.
* Rosie suites.

.. ifnotslides::

   The relationship between them is as follows:

.. _cylc-rose-rosie-suite-relationship-diagram:

.. graph:: Example
   :align: center

    ranksep = 0
    size = "7, 5"

    node [shape="plaintext", fontcolor="#606060"]
    edge [style="invis"]

    subgraph cluster_1 {
        label = "Cylc Workflow"
        fontsize = "20"
        fontcolor = "#5050aa"
        labelloc = "r"
        "flow.cylc" [fontsize="18",
                    fontname="mono",
                    fontcolor="black"]
        "rcinfo" [label="Defines the workflow\nin terms of tasks\nand dependencies"]
        "flow.cylc" -- "rcinfo"

        subgraph cluster_2 {
            label = "Rose Suite Configuration"
            "rose-suite.conf" [fontsize="18",
                               fontname="mono",
                               fontcolor="black"]
            "confinfo" [label="Defines Jinja2 variables for\nthe flow.cylc and environment\nvariables for use throughout\nthe suite"]
            "rose-suite.conf" -- "confinfo"

            subgraph cluster_3 {
                label = "Rosie Suite"
                "rose-suite.info" [fontsize="18",
                                   fontname="mono",
                                   fontcolor="black"]
                "infoinfo" [label="Contains basic information\nabout the suite used\nby Rosie for searching\nand version control purposes"]
                "rose-suite.info" -- "infoinfo"
            }
        }
    }

.. ifnotslides::

   Cylc workflows can have Rose applications. These are stored in an ``app``
   directory and are configured using a :rose:file:`rose-app.conf` file.

.. ifslides::

   * :rose:file:`rose-app.conf`
   * :rose:file:`rose-meta.conf`

.. TODO - A file tree for an example Rose suite + a full file tree showing
          all possible files and directories with descriptions, this will
          require an extension and some CSS magic to ensure viable output
          in HTML and PDF.


Suite Commands
--------------

.. rubric:: We have learned the following Cylc commands:

.. ifnotslides::

   ``cylc graph``
      Draws the suite's :term:`graph`.
   ``cylc get-config``
      Processes the ``flow.cylc`` file and prints it back out.
   ``cylc validate``
      Validates the Cylc ``flow.cylc`` file to check for any obvious errors.
   ``cylc play``
      Runs a suite.
   ``cylc stop``
      Stops a suite, in a way that:

      ``--kill``
         Kills all running/submitted tasks.
      ``--now --now``
         Leaves all running/submitted tasks running.

   ``cylc restart``
      Starts a suite, picking up where it left off from the previous run.

.. ifslides::

   * ``cylc graph``
   * ``cylc get-config``
   * ``cylc validate``
   * ``cylc play``
   * ``cylc stop``
      * ``--kill``
      * ``--now --now``
   * ``cylc restart``

.. nextslide::

Rose Utilities
--------------

Rose contains some utilities to make life easier:

.. ifnotslides::

   :ref:`command-rose-date`
      A utility for parsing, manipulating and formatting date-times which is
      useful for working with the Cylc :term:`cycle point`:

      .. code-block:: console

         $ rose date 2000 --offset '+P1Y1M1D'
         2001-02-02T0000Z

         $ rose date $CYLC_TASK_CYCLE_POINT --format 'The month is %B.'
         The month is April.

      See the :ref:`date-time tutorial <rose-tutorial-datetime-manipulation>`
      for more information.

.. ifslides::

   ``rose date``

   .. code-block:: console

      $ rose date 2000 --offset '+P1Y1M1D'
      2001-02-02T0000Z

      $ rose date $CYLC_TASK_CYCLE_POINT --format 'The month is %B.'
      The month is April.

Rose Built-In Applications
--------------------------

.. ifnotslides::

   Along with Rose utilities there are also :ref:`Rose built-in applications
   <Rose Built-In Applications>`.

   :rose:app:`fcm_make`
      A template for running the ``fcm make`` command.
   :rose:app:`rose_ana`
      Runs the rose-ana analysis engine.
   :rose:app:`rose_arch`
      Provides a generic solution to configure site-specific archiving of suite
      files.
   :rose:app:`rose_bunch`
      For the running of multiple command variants in parallel under a single
      job.
   :rose:app:`rose_prune`
      A framework for housekeeping a cycling suite.

.. ifslides::

   * :rose:app:`fcm_make`
   * :rose:app:`rose_ana`
   * :rose:app:`rose_arch`
   * :rose:app:`rose_bunch`
   * :rose:app:`rose_prune`


Next Steps
----------

.. ifnotslides::

   :ref:`Rose Further Topics`
      Tutorials going over some of the more specific aspects of Rose not
      covered in the main tutorial.
   :ref:`Cheat Sheet`
      A quick breakdown of the commands for running
      and interacting with suites using Cylc and Rose.
   :ref:`Command Reference`
      Contains the command-line documentation
      (also obtainable by calling ``rose --help``).
   :ref:`Rose Configuration <rose-configuration>`
      The possible settings which can be used in the different Rose
      configuration files.
   `Cylc Suite Design Guide`_
      Contains recommended best practice for the style and structure of Cylc
      suites.

.. ifslides::

   * :ref:`Rose Further Topics`
   * :ref:`Cheat Sheet`
   * :ref:`Command Reference`
   * :ref:`Rose Configuration <rose-configuration>`
   * `Cylc Suite Design Guide`_

.. TODO - write some JS or python extension for representing definition
          lists as bullet lists for the slides builder.
