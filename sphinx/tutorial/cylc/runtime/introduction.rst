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
Cylc provides a command which automatically checks for any obvious
configuration issues called
``cylc validate``.

.. code-block:: bash

   cylc validate <name>

Finally we run the suite using the ``cylc run`` command.

.. code-block:: bash

   cylc run <name>

.. _tutorial-tasks-and-jobs:

Tasks And Jobs
--------------

When a :term:`task` is "Run" it creates a :term:`job`. The job is a bash
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

The Work Directory
^^^^^^^^^^^^^^^^^^

When a :term:`task` is run cylc creates a directory for the :term:`job` to run
in, this is called the :term:`work directory`.

By default the work directory is in a directory structure under the
:term:`cycle point` and the :term:`task` name:

.. code-block:: sub

   ~/cylc-run/<suite-name>/work/<cycle-point>/<task-name>

The Job Log Directory
^^^^^^^^^^^^^^^^^^^^^

When a task is run cylc generates a :term:`job script`, this is stored in the
:term:`job log directory` as the file ``job``.

When the :term:`job script` is executed the stdout and stderr are redirected
into the ``job.out`` and ``job.err`` files which are also stored in the
:term:`job log directory`.

The :term:`job log directory` lives in a directory structure under the
:term:`cycle point`, :term:`task` name and the :term:`job submission number`:

.. code-block:: sub

   ~/cylc-run/<suite-name>/log/job/<cycle-point>/<task-name>/<job-submission-no>/

The :term:`job submission number` starts at 1 and increments each time a taks
is re-run.

.. practical::

   .. rubric:: In this practical we will add some scripts to and run the
      :ref:`weather forecasting suite <tutorial-datetime-cycling-practical>`
      from the :ref:`scheduling tutorial <tutorial-scheduling>`.

   #. **Create A New Suite.**

      The following command will copy some files for us to work with into a
      directory called ``dummy-suite``:

      .. code-block:: bash

         rose tutorial cylc-dummy dummy-suite

      In this directory we have the ``suite.rc`` file from the
      :ref:`weather forecasting suite <tutorial-datetime-cycling-practical>`
      with some runtime configuration added to it.

      These is also a script called ``get-observations`` located in a bin
      directory.

   #. **Add The Initial And Final Cycle Points.**

      TODO

   #. **Register The Suite.**

      Register and validate your suite by running the following commands:

      .. code-block:: bash

         cd dummy-forecast
         cylc reg dummy-forecast $PWD
         cylc validate dummy-forecast

   #. **Run The Suite.**

      Open the cylc GUI by running the following command:

      .. code-block:: bash

         gcylc dummy-forecast &

      Run the suite by executing the following command:

      .. code-block:: bash

         cylc run dummy-suite

      The tasks will start to run, you should see them going through the
      waiting, running and succeeded states.

      When the suite reaches the final cycle point and all tasks have succeeded
      it will shutdown automatically and the GUI will go blank.

      .. tip::

         You can also run a suite from the cylc gui by pressing the "play"
         button.

         .. image:: ../img/gcylc-play.png
            :align: center

         A box will appear, ensure that "Cold Start" is selected then press
         "Start".

         .. image:: ../img/cylc-gui-suite-start.png
            :align: center

   #. **Inspect A Job Log.**

      Cylc will have created a :term:`run directory` for this suite in the
      following location::

         ~/cylc-run/dummy-forecast/

      Try opening the ``job.out`` file for one of the ``get_observations``
      jobs. The file will be located within the :term:`run directory`:

      .. code-block:: sub

         <run-directory>/log/job/<cycle-point>/get_observations_heathrow/01/job.out

   #. **Inspect A Work Directory.**

      The ``get_rainfall`` task should create a file called ``rainfall`` in its
      :term:`work directory`. Try opening the file:

      .. code-block:: sub

         <run-directory>/work/<cycle-point>/get_rainfall/rainfall
