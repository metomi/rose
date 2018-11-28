.. _tutorial-cylc-family-triggers:

Family Triggers
===============

To reduce duplication in the :term:`graph` is is possible to write
:term:`dependencies <dependency>` using collections of tasks called
:term:`families <family>`).

This tutorial walks you through writing such dependencies using family
:term:`triggers <task trigger>`.


Explanation
-----------

Dependencies between tasks can be written using a :term:`qualifier` to describe
the :term:`task state` that the dependency refers to (e.g. ``succeed``
``fail``, etc). If a dependency does not use a qualifier then it is assumed
that the dependency refers to the ``succeed`` state e.g:

.. code-block:: cylc-graph

   bake_bread => sell_bread          # sell_bread is dependent on bake_bread succeeding.
   bake_bread:succeed => sell_bread  # sell_bread is dependent on bake_bread succeeding.
   sell_bread:fail => through_away   # through_away is dependent on sell_bread failing.

The left-hand side of a :term:`dependency` (e.g. ``sell_bread:fail``) is
referred to as the :term:`trigger <task trigger>`.

When we write a trigger involving a family, special qualifiers are required
to specify whether the dependency is concerned with *all* or *any* of the tasks
in that family reaching the desired :term:`state <task state>` e.g:

* ``succeed-all``
* ``succeed-any``
* ``fail-all``

Such :term:`triggers <task trigger>` are referred to as
:term:`family triggers <family trigger>`

Foo ``cylc gui`` bar


Example
-------

Create a new suite called ``tutorial-family-triggers``::

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

   cylc gui tutorial-family-triggers &

You should see the ``visit_mine`` task run, then trigger the members of the
``MINERS`` family. Note that some of the ``MINERS`` tasks may fail so you
will need to stop your suite using the "stop" button in the ``cylc gui`` in
order to allow it to shutdown.


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

.. tip::

   See the :ref:`tut-cylc-suicide-triggers` tutorial for handling task
   failures.


Different Triggers
------------------

Other family :term:`qualifiers <qualifier>` beyond those covered in the
example are also available.

The following types of "all" qualifier are available:

* ``:start-all`` - all the tasks in the family have started
* ``:succeed-all`` - all the tasks in the family have succeeded
* ``:fail-all`` - all the tasks in the family have failed
* ``:finish-all`` - all the tasks in the family have finished

The following types of "any" qualifier are available:

* ``:start-any`` - at least one task in the family has started
* ``:succeed-any`` - at least one task in the family has succeeded
* ``:fail-any`` - at least one task in the family has failed
* ``:finish-any`` - at least one task in the family has finished


Summary
-------

* Family triggers allow you to write dependencies for collections of tasks.
* Like :term:`task triggers <task trigger>`, family triggers can be based on
  success, failure, starting and finishing of tasks in a family.
* Family triggers can trigger off either *all* or *any* of the tasks in a
  family.
