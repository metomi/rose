Introduction
============


So far we have been working with the ``[scheduling]`` section. This is where
the workflow is defined in terms of :term:`tasks <task>` and
:term:`dependencies <dependency>`.

In order to make the workflow runnable we must associate tasks with scripts
or binaries to be executed when the task runs. This means working with the
``[runtime]`` section which determines what runs, where and how.


The Task Section
----------------

The runtime settings for each task are stored in a sub-section in the
``[runtime]`` section. E.G for a task called ``hello_world`` we would write
settings inside this section:

.. code-block:: cylc

   [runtime]
       [[hello_world]]

TODO: This better.


The ``script`` Setting
----------------------

We tell cylc what to execute when a task is run using the ``script`` setting.

This setting is interpreted as bash script, the following example defines a
task called ``hello_world`` which writes ``Hello World!`` to stdout upon
execution.

.. code-block:: cylc

   [runtime]
       [[hello_world]]
           script = echo 'Hello World!'

.. note::

   If you do not set the ``script`` for a task then nothing will be run.

We can also call other scripts or executables in this way e.g:

.. code-block:: cylc

   [runtime]
       [[hello_world]]
           script = ~/foo/bar/baz/hello_world

It is often a good idea to keep our scripts with the cylc suite rather than
leaving them somewhere else on the system. If you create a ``bin`` directory
within the :term:`suite directory` this directory will be added to the path
when tasks run. E.G:

.. code-block:: bash
   :caption: bin/hello-world

   #!/usr/bin/bash
   echo 'Hello World!'

.. code-block:: cylc
   :caption: suite.rc
   :emphasize-lines: 3

   [runtime]
       [[hello_world]]
           script = hello_world


Running A Suite
---------------

Before we run a suite we must register it with cylc. We do this using the
``cylc reg`` command which we supply with a name which will be used to refer to
the suite.

.. code-block:: bash

   cylc reg <name> <path>

It is a good idea to check the suite for errors before running it.
Cylc provides a command which automatically checks for obvious errors called
``cylc validate``.

.. code-block:: bash

   cylc validate <name>

Finally we run the suite using the ``cylc run`` command.

.. code-block:: bash

   cylc run <name>

.. _tutorial-tasks-and-jobs:

Tasks And Jobs
--------------

When a :term:`task` is "Run" is creates a :term:`job`. The job is a bash
file containing the script you have told the task to run along with
configuration and a system for trapping errors. It is this :term:`job`
which actually gets executed. This "job file" is called the :term:`job script`.

During its life a typical :term:`task` goes through the following states:

Waiting
   :term:`Tasks <task>` wait for their dependencies to be satisfied before
   running, in the mean time they are in the "Waiting" state.
Submitted
   When the :term:`task's <task>` dependencies have been met it is ready for
   submission. During this phase the :term:`job script` is created.
   The :term:`job` is then submitted to the specified batch system, more on
   this in the :ref:`next section <tutorial-batch-system>`.
Running
   A :term:`task` is in the "Running" state as soon as the :term:`job` is
   executed.
Succeeded
   If the :term:`job` the :term:`task` submitted has successfully completed
   (zero return code) then it is said to have succeeded.

These are called the :term:`task states <task state>` and there are a few more
(e.g. failed).


The cylc GUI
------------

To help you to keep track of a running suite cylc has a graphical user
interface (GUI) called ``gcylc`` which can be used for monitoring and
interaction.

The cylc gui looks quite like ``cylc graph`` but the tasks are colour-coded to
represent their state as in the following diagram.

.. digraph:: example
   :align: center

   bgcolor=none

   Waiting [color="#88c6ff"]
   Running [style="filled" color="#00c410"]
   Succeeded [style="filled" color="#ada5a5"]

.. minicylc::
   :align: center

    a => b => c
    b => d => f
    e => f

This is the "graph view". The cylc gui has two other views called "tree" and
"dot".

.. figure:: ../img/cylc-gui-graph.png
   :figwidth: 50%
   :align: center

   Screenshot of the cylc gui in "Graph View" mode.

.. figure:: ../img/cylc-gui-tree.png
   :figwidth: 50%
   :align: center

   Screenshot of the cylc gui in "Tree View" mode.

.. figure:: ../img/cylc-gui-dot.png
   :figwidth: 50%
   :align: center

   Screenshot of the cylc gui in "Dot View" mode.


Where Do All The Files Go
-------------------------

Cylc creates a directory for running suites in your homespace called
``cylc-run`` (``~/cylc-run``). When you run the ``cylc reg`` command it creates
a new directory for your suite within the ``cylc-run`` directory. This is
called the :term:`run directory`, all of the files created when the suite runs
are located within this directory and its subdirectories.

When a :term:`job` is executed cylc creates a directory for it to run in, this
is called the :term:`work directory`. The stdout and stderr of the job are
redirected into the ``job.out`` and ``job.err`` files which are stored in the
:term:`job log directory`.

TODO: Run Dir Overview


.. practical::

   .. rubric:: In this practical we will add ``runtime`` configuration to the
      :ref:`weather forecasting suite <tutorial-datetime-cycling-practical>`
      from the :ref:`scheduling tutorial <tutorial-scheduling>`.

   #. **Create A New Suite.**

      Create a new directory called "dummy-forecast" and paste the following
      code in the ``suite.rc`` file:

      .. code-block:: cylc

         [cylc]
             UTC mode = True
         [scheduling]
             initial cycle point = 20000101T00
             [[dependencies]]
                 [[[T00/PT3H]]]
                     graph = """
                         observations_camborne => gather_observations
                         observations_heathrow => gather_observations
                         observations_aberdeen => gather_observations
                     """
                 [[[T06/PT6H]]]
                     graph = """
                         gather_observations => forecast
                         gather_observations[-PT3H] => forecast
                         gather_observations[-PT6H] => forecast
                         forecast => process_exeter
                     """
                 [[[T12/PT6H]]]
                     graph = """
                         forecast[-PT6H] => forecast
                     """

   #. **Add Scripts To The Suite.**

      In the suite directory create a ``bin`` directory.

      TODO: Add scripts.

   #. **Add Runtime Configuration.**

      .. code-block:: cylc

         [runtime]
             [[observations_camborne]]
                 script = get-observations camborne
             [[observations_heathrow]]
                 script = get-observations_heathrow
             [[observations_aberdeen]]
                 script = get-observations aberdeen
             [[gather_observations]]
                 script = gather-observations
             [[forecast]]
                 script = forecast
             [[process_exeter]]
                 script = post-process exeter

   #. **Run The Suite.**

   #. **Open A Job Log / Script File.**
