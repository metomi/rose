.. include:: ../../../hyperlinks.rst
   :start-line: 1

Retries
=======

Retries allow us to automatically re-submit tasks which have failed due to
failure in submission or execution.


Purpose 
-------

Retries can be useful for tasks that may occasionally fail due to external
events, and are routinely fixable when they do - an example would be a task
that is dependent on a system that experiences temporary outages.

If a task fails, the Cylc retry mechanism can resubmit it after a
pre-determined delay. An environment variable, ``$CYLC_TASK_TRY_NUMBER``
is incremented and passed into the task - this means you can write your
task script so that it changes behaviour accordingly.


Example
-------

.. image:: https://upload.wikimedia.org/wikipedia/commons/7/73/Double-six-dice.jpg
   :width: 200px
   :align: right
   :alt: Two dice both showing the number six

Create a new suite by running the following commands::

   rose tutorial retries-tutorial
   cd retries-tutorial

You will now have a suite with a ``roll_doubles`` task which simulates
trying to roll doubles using two dice:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST

   [scheduling]
       [[dependencies]]
           graph = start => roll_doubles => win

   [runtime]
       [[start]]
       [[win]]
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


Running Without Retries
-----------------------

Let's see what happens when we run the suite as it is. Open the ``cylc gui``::

   cylc gui retries-tutorial &

Then run the suite::

   cylc run retries-tutorial

Unless you're lucky, the suite should fail at the roll_doubles task.

Stop the suite::

   cylc stop retries-tutorial


Configuring Retries
-------------------

We need to tell Cylc to retry it a few times. To do this, add the following
to the end of the ``[[roll_doubles]]`` task section in the ``suite.rc`` file:

.. code-block:: cylc

   [[[job]]]
       execution retry delays = 5*PT6S

This means that if the ``roll_doubles`` task fails, Cylc expects to
retry running it 5 times before finally failing. Each retry will have
a delay of 6 seconds.

We can apply multiple retry periods with the ``execution retry delays`` setting
by separating them with commas, for example the following line would tell Cylc
to retry a task four times, once after 15 seconds, then once after 10 minutes,
then once after one hour then once after three hours.

.. code-block:: cylc

   execution retry delays = PT15S, PT10M, PT1H, PT3H


Running With Retries
--------------------

If you closed it, re-open the ``cylc gui``::

   cylc gui retries-tutorial &

Re-run the suite::

   cylc run retries-tutorial

What you should see is Cylc retrying the ``roll_doubles`` task. Hopefully,
it will succeed (there is only about a about a 1 in 3 chance of every task
failing) and the suite will continue.


Altering Behaviour
------------------

We can alter the behaviour of the task based on the number of retries, using
``$CYLC_TASK_TRY_NUMBER``.

Change the ``script`` setting for the ``roll_doubles`` task to this::

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

If your suite is still running, stop it, then run it again.

This time, the task should definitely succeed before the third retry.


Further Reading
---------------

For more information see the `Cylc User Guide`_.
