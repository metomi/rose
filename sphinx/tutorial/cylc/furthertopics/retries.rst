Retries
=======

Introduction
------------

This part of the Rose user guide walks you through using cylc retries.

This allows tasks to be automatically resubmitted after failure, after a certain delay, and even with different behaviour.

Purpose 
-------

Retries can be useful for tasks that may occasionally fail due to external events, and are routinely fixable when they do - an example would be a task that is dependent on a system that experiences temporary outages.

If a task fails, the cylc retry mechanism can resubmit it after a pre-determined delay. An environment variable, ``$CYLC_TASK_TRY_NUMBER`` is incremented and passed into the task - this means you can write your task script so that it changes behaviour accordingly.

Example
-------

Our example suite will simulate trying to roll doubles using two dice.

Create a new suite (or just a new directory somewhere - e.g. in your homespace) containing a blank ``rose-suite.conf`` and a ``suite.rc`` file with the following contents:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST
   [scheduling]
       [[dependencies]]
           graph = start => roll_doubles => win

We'll add some standard information in the ``[runtime]`` section:

.. code-block:: cylc

   [runtime]
       [[start]]
       [[win]]

We need to add a rolling doubles task - add these lines to the end of your ``suite.rc`` file:

.. code-block:: cylc

   [[roll_doubles]]
       script = """
   sleep 10
   RANDOM=$$  # Seed $RANDOM
   DIE_1=$((RANDOM%6 + 1))
   DIE_2=$((RANDOM%6 + 1))
   echo "Rolled $DIE_1 and $DIE_2..."
   if (($DIE_1 == $DIE_2)); then
       echo "doubles!"
   else
       exit 1
   fi
   """

Running it without retries
--------------------------

Let's see what happens when we run the suite as it is.

Make sure you are in the root directory of your suite.

Run the suite using:

.. code-block:: console

   rose suite-run 


Results
-------

What you should see is cylc retrying the ``roll_doubles`` task. Hopefully, it will succeed (about a 1 in 3 chance of every task failing) and the suite will continue.

If you go to the suite output (run ``rose suite-log`` in your root suite directory), you can see the separate retry instances of the task.


Altering behaviour
------------------

We can alter the behaviour of the task based on the number of retries, using ``$CYLC_TASK_TRY_NUMBER``:

.. code-block:: cylc

        script = """
   sleep 10
   RANDOM=$$  # Seed $RANDOM
   DIE_1=$((RANDOM%6 + 1))
   DIE_2=$((RANDOM%6 + 1))
   echo "Rolled $DIE_1 and $DIE_2..."
   if (($DIE_1 == $DIE_2)); then
       echo "doubles!"
   elif (($CYLC_TASK_TRY_NUMBER >= 2)); then
       echo "look over there! ..."
       echo "doubles!"  # Cheat!
   else
       exit 1
   fi
        """

If your suite is still running, stop it. Run it again using:

.. code-block:: console

   rose suite-run

This time, the task should definitely succeed before the third retry.

Further reading
---------------

For more information see the `cylc User Guide`_.

.. _cylc User Guide: https://cylc.github.io/cylc/html/single/cug-html.html








