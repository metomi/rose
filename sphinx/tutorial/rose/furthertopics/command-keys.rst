.. _rose-tutorial-command-keys:

Command Keys
============

This tutorial walks you through using command keys.

Command keys allow you to specify and run different commands for a
:term:`Rose app`.

They work just like the default command for an app but have to be specified
explicitly as an option of :ref:`command-rose-task-run`.


Example
-------

Create a new Rose suite configuration called ``command-keys``::

   mkdir -p ~/rose-tutorial/command-keys
   cd ~/rose-tutorial/command-keys

Create a blank :rose:file:`rose-suite.conf` and a ``suite.rc`` file that
looks like this:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST
   [scheduling]
       [[dependencies]]
           graph = gather_ingredients => breadmaker

   [runtime]
       [[gather_ingredients]]
           script = sleep 10; echo 'Done'
       [[breadmaker]]
           script = rose task-run

In your suite directory create an ``app`` directory.

In the ``app`` directory create a new directory called ``breadmaker``.

In the ``breadmaker`` directory create a :rose:file:`rose-app.conf` file that
looks like this:

.. code-block:: rose

   [command]
   default=sleep 10; echo 'fresh bread'

This sets up a simple suite that contains the following:

* A ``breadmaker`` app
* A ``gather_ingredients`` task
* A ``breadmaker`` task that runs the ``breadmaker`` app

Save your changes then run the suite using :ref:`command-rose-suite-run`.

Once it has finished use :ref:`command-rose-suite-log` to view the suite log.
In the page that appears, click the "out" link for the breadmaker task. In the
page you are taken to you should see a line saying "fresh bread".


Adding Alternative Commands
---------------------------

Open the :rose:file:`rose-app.conf` file and edit to look like this:

.. code-block:: rose

   [command]
   default=sleep 10; echo 'fresh bread'
   make_dough=sleep 8; echo 'dough for later'
   timed_bread=sleep 15; echo 'fresh bread when you want it'

Save your changes and open up your ``suite.rc`` file. Alter the
``[[breadmaker]]`` task to look like this:

.. code-block:: cylc

   [[breadmaker]]
       script=rose task-run --command-key=make_dough

Save your changes and run the suite. If you inspect the output from the
breadmaker task you should see the line "dough for later".

Edit the script for the ``[[breadmaker]]`` task to change the command key to
``timed_bread``. Run the suite and confirm the timed_bread command has been
run.


Summary
-------

You have successfully made use of command keys to run alternate commands in
an app.

Possible uses of command keys might be:

* Running an app in different modes of verbosity
* Running an app in different configurations
* Specifying different options to an app
* During suite development to aid in debugging an app
