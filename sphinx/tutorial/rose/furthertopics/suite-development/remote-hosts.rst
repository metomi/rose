Remote Hosts
============

Introduction
------------

This tutorial walks you through using remote hosts.

Remote settings let you run tasks on different machines.

Purpose
-------

Remote settings are used to specify the machine on which to run a task.

Remote names can either be hard coded or automatically selected for you via ``rose host-select``. Remote settings should be used to send tasks off to be run on remote machines rather than running on your cylc server.

Example
-------

Create a new suite (or just a new directory somewhere - e.g. in your homespace) containing a blank ``rose-suite.conf`` and a ``suite.rc`` file that looks like this:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST
   [scheduling]
       [[dependencies]]
           graph = initialise => short & medium & long
   [runtime]
       [[root]]
           script = rose task-run
           [[[environment]]]
               ROSE_TASK_APP=calc_pi
   [[initialise]]
       script = "echo 'initialising...'; sleep 10"
   [[short]]
       [[[environment]]]
           NUM=50
   [[medium]]
       [[[environment]]]
           NUM=500
   [[long]]
       [[[environment]]]
           NUM=5000

In the suite directory create an ``app`` directory

In the app directory create a ``calc_pi`` directory

In the ``calc_pi`` directory create a ``rose-app.conf`` file and paste in the following lines:

.. code-block:: cylc

   [command]
   default=echo "scale=$NUM; 4*a(1)" | bc -l -q


Description
-----------

You have now created a suite that:

   - contains a ``calc_pi`` task that calculates pi to some number of decimal places as specified by ``$NUM``.
   - has an initialisation task
   - has short, medium and long tasks that use the ``calc_pi`` app to calculate pi to increasing numbers of decimal places

Save your changes and run the suite using ``rose suite-run``. Notice the different lengths of time it takes for each of the tasks to run.

View the suite output using rose suite-log and inspect the output of the ``short``, ``medium`` and ``long`` tasks. You should see pi printed to different numbers of decimal places.

Also, note the *task host* listed at the top of the output of each task, which should be the same as the *suite host*, also listed at the top.


Adding remote hosts
-------------------

As you will have noticed from examining the output, your tasks have been run on the machine hosting the suite. This may be undesireable, particularly when a suite host is used by multiple users. Additionally, we might want to run various tasks on particular machines or run more computationally intensive tasks on higher power servers.

We can address this by adding ``[[[remote]]]`` sections to the tasks in the ``suite.rc``.

Open your ``suite.rc`` file and add the following to the ``[[root]]`` task:

.. code-block:: cylc

   [[[remote]]]
      host = my-desktop

where ``my-desktop`` is the name of your desktop machine. This will result in all tasks running on your desktop machine. If you don't know the name of your desktop, type ``hostname`` into your terminal.

Save your changes and run your suite. Once it has completed, check the output from the tasks. Your should see your desktop being used as the task host

As our suites may be run by other people, or we may run them ourselves on different desktops we can have rose automatically insert the name of the desktop being used to launch the suite (i.e. the one on which ``rose suite-run`` is run.

To do this, change the ``[[[remote]]]`` section of ``[[root]]`` in the ``suite.rc`` file to look like this: 

.. code-block:: cylc

   [[[remote]]]
      host = {{ ROSE_ORIG_HOST }}

Save your changes, run your suite and examine the output to check this is working as expected.


Automating host selection
-------------------------

Rose also offers an in-built function for automatic host selection in the form of the ``rose host-select`` command. This will return a hostname from a set of pre-defined hosts in the ``rose.conf`` file.

To list the hostnames available through ``rose host-select`` type ``rose config rose-host-select`` into the command line.

Depending on your rose configuration you should see something along the lines of:

.. code-block:: console

   default=linux-servers
   group{linux-servers}=server01 server02 server03
   group{hpc}=node01 node02 node03

The ``default=`` entry identifies which group to return a hostname from if ``rose host-select`` is invoked without any arguments. Each ``group{groupname}`` entry lists the hosts from which one is returned when ``rose host-select groupname`` is run.

In your terminal, experiment with ``rose host-select`` and the names of the groups listed earlier to see what hostnames are returned e.g. if you discovered a group called "linux-servers" see what is returned when you run ``rose host-select linux-servers``.

We will now implement the use of ``rose host-select`` in our suite by adding ``[[[remote]]]`` sections to the medium and long tasks in our ``suite.rc`` file as follows, replacing *groupname* with an appropriate group you discovered previously:

.. code-block:: cylc

   [[medium]]
       [[[remote]]]
           host = `rose host-select`
       [[[environment]]]
           NUM=500
   [[long]]
       [[[remote]]]
           host = `rose host-select groupname`
       [[[environment]]]
           NUM=5000

Save your changes, run the suite and view the output. You should see the following in the task outputs:

   - The short task's host should be the machine you ran ``rose suite-run`` on.
   - The medium task's host should be one of the hosts from the default group.
   - The long task's host should be one of the hosts from the specified group.


Summary
-------

   - Use the ``[[[remote]]]`` section to specify a host so your task doesn't run on the suite host.
   - Use host = ``{{ ROSE_ORIG_HOST }}`` in the ``[[[remote]]]`` section of a task to have it run on the machine on which ``rose suite-run`` was invoked.
   - Make use of ``rose host-select`` to automatically select a host from an appropriate group rather than hard-coding host names where possible.


