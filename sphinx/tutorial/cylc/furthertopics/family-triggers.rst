Family Triggers
===============

This tutorial walks you through using family :term:`triggers <task trigger>`.

Family triggers allow you to build dependencies based on sets of tasks
sharing the same namespace, referred to as
:ref:`families <tutorial-cylc-families>`.


Purpose
-------

Family triggers are used to specify a condition to be met by a set of tasks
in a particular :term:`family` that will :term:`trigger <task trigger>`
the next task(s) in the :term:`graph`.

Like regular task triggers, family triggers can depend on the success or
failure of tasks. However, because a family can contain multiple tasks, you
need to specify whether you are concerned with all or any of the tasks in
that family reaching the desired state.


Example
-------

Create a new suite called tutorial-family-triggers::

   mkdir ~/cylc-run/tutorial-family-triggers
   cd ~/cylc-run/tutorial-family-triggers

Paste the following configuration into the ``suite.rc`` file:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST
   [scheduling]
       [[dependencies]]
           graph = visit_mine => MINERS
   [runtime]
       [[visit_mine]]
           script = sleep 5; echo 'off to work we go'

       [[MINERS]]
           script = """
   sleep 5;
   if (($RANDOM % 2)); then
       echo 'Diamonds!'; true;
   else
       echo 'Nothing...'; false;
   fi
   """
       [[doc, grumpy, sleepy, happy, bashful, sneezy, dopey]]
           inherit = MINERS

You have now created a suite that:

* Has a ``visit_mine`` task that sleeps for 5 seconds then outputs a
  message.
* Contains a ``MINERS`` family with a command in it that randomly succeeds
  or fails.
* Has 7 tasks that inherit from the ``MINERS`` family.

Open the ``cylc gui`` then run the suite by pressing the "play" button
(top left hand corner) then clicking :guilabel:`Start`::

   gcylc tutorial-family-triggers &

You should see the ``visit_mine`` task run, then trigger the members of the
``MINERS`` family. Note that some of the ``MINERS`` tasks may fail so you
will need to stop your suite using the "stop" button in the cylc gui in order
to allow it to shutdown.


Family Triggering: Success
--------------------------

As you will have noticed by watching the suite run, some of the tasks in the
``MINERS`` family succeed and some fail.

We would like to add a task to sell any diamonds we find, but wait for all
the miners to report back first so we only make the one trip.

We can address this by using *family triggers*. In particular, we are going
to use the ``finish-all`` trigger to check for all members of the ``MINERS``
family finishing, and the ``succeed-any`` trigger to check for any of the
tasks in the ``MINERS`` family succeeding.

Open your ``suite.rc`` file and change the ``[[dependencies]]`` to look like
this:

.. code-block:: cylc

   [[dependencies]]
       graph = """visit_mine => MINERS
                  MINERS:finish-all & MINERS:succeed-any => sell_diamonds"""

Then, add the following task to the ``[runtime]`` section:

.. code-block:: cylc

   [[sell_diamonds]]
      script = sleep 5

These changes add a ``sell_diamonds`` task to the suite which is run once
all the ``MINERS`` tasks have finished and if any of them have succeeded.

Save your changes and run your suite. You should see the new
``sell_diamonds`` task being run once all the miners have finished and at
least one of them has succeeded. As before, stop your suite using the "stop"
button in the ``cylc gui``.


Family Triggering: Failure
--------------------------

Cylc also allows us to trigger off failure of tasks in a particular family.

We would like to add another task to close down unproductive mineshafts once
all the miners have reported back and had time to discuss their findings.

To do this we will make use of family triggers in a similar manner to before.

Open your ``suite.rc`` file and change the ``[[dependencies]]`` to look like
this:

.. code-block:: cylc

   [[dependencies]]
       graph = """visit_mine => MINERS
                  MINERS:finish-all & MINERS:succeed-any => sell_diamonds
                  MINERS:finish-all & MINERS:fail-any => close_shafts
                  close_shafts => !MINERS
                  """

Alter the ``[[sell_diamonds]]`` section to look like this:

.. code-block:: cylc

   [[close_shafts, sell_diamonds]]
       script = sleep 5

These changes add a ``close_shafts`` task which is run once all the
``MINERS`` tasks have finished and any of them have failed. On completion
it applies a *suicide trigger* to the ``MINERS`` family in order to allow
the suite to shutdown.

Save your changes and run your suite. You should see the new
``close_shafts`` run should any of the ``MINERS`` tasks be in the failed
state once they have all finished.


Different Triggers
------------------

Other types of triggers beyond those covered in the example are also available.

The following types of "all" type triggers are available:

* ``FAM:start-all`` - all the tasks in FAM have started
* ``FAM:succeed-all`` - all the tasks in FAM have succeeded
* ``FAM:fail-all`` - all the tasks in FAM have failed
* ``FAM:finish-all`` - all the tasks in FAM have finished

The following types of "any" type triggers are available:

* ``FAM:start-any`` - at least one task in FAM has started
* ``FAM:succeed-any`` - at least one task in FAM has succeeded
* ``FAM:fail-any`` - at least one task in FAM has failed
* ``FAM:finish-any`` - at least one task in FAM has finished


Summary
-------

* Family triggers allow you to create dependencies on particular families.
* Like task triggers, family triggers can be based on success, failure,
  starting and finishing of tasks in a family.
* Family triggers can trigger off either *all* or *any* of the tasks in a family.




