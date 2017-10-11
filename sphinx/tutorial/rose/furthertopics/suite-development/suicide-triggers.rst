Suicide Triggers
================

Introduction
------------

This tutorial walks you through using suicide triggers.

Suicide triggers allow you to remove tasks from the suite during runtime.

Purpose
-------

Suicide triggers can be used to remove any task from a suite while it is running.

They work much like any other type of trigger in a suite, except that rather than running a particular task once the triggering condition is met, the task is instead removed from the suite.

Example
-------

Create a new suite (or just a new directory somewhere - e.g. in your homespace) containing a blank ``rose-suite.conf`` and a ``suite.rc`` file that looks like this:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST
   [scheduling]
       [[dependencies]]
           graph = """
               bake_cake:fail => purchase_cake
               bake_cake | purchase_cake => eat_cake
               """

This sets up a simple suite which consists of the following:

   - a ``bake_cake`` task which either succeeds or fails
   - a ``purchase_cake`` "recovery" task which is run if ``bake_cake`` fails
   - an ``eat_cake`` task which runs once cake has been obtained i.e. once ``bake_cake`` or ``purchase_cake`` has succeeded

For purposes of this tutorial ``purchase_cake`` will always succeed as cake should be available to buy somewhere.

It will need some runtime. Add the following to your ``suite.rc`` file:

.. code-block:: cylc

   [runtime]
       [[bake_cake]]
           script = """
   sleep 10;
   if (($RANDOM % 2)); then
       echo 'Success'; true;
   else
       echo 'Burned the cake!'; false;
   fi
   """
       [[purchase_cake]]
           script = sleep 10; echo 'Off to the shops!'
       [[eat_cake]]
           script = sleep 10; echo 'Mmm cake!'


Save your changes and run the suite using ``rose suite-run``

The suite should now run. If ``bake_cake`` fails, ``purchase_cake`` is triggered which triggers ``eat_cake``. Otherwise, ``bake_cake`` triggers ``eat_cake``.

Notice that at once eat_cake has completed the suite does not shut down. This is because either ``bake_cake`` is in the failed state or ``purchase_cake`` is waiting to be triggered. Shut down the suite by pressing the stop button in the ``cylc gui``.

You may want to run the suite again to see both situations.


Adding suicide triggers
-----------------------

Since ``purchase_cake`` has corrected for the failure of ``bake_cake`` we don't need the suite to keep running - we would like the suite to be able to shutdown once the final cycle has completed.

We can make use of a suicide trigger to remove the failed ``bake_cake`` task.

Once ``purchase_cake`` has succeeded we no longer need ``bake_cake`` so we can use a suicide trigger to remove ``bake_cake`` from the suite.

Modify the ``[scheduling]`` section to look like the following:

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           graph = """
               bake_cake:fail => purchase_cake
               bake_cake | purchase_cake => eat_cake
               purchase_cake => !bake_cake
               """

The line ``purchase_cake => !bake_cake`` is the suicide trigger. When ``purchase_cake`` succeeds, ``bake_cake`` is removed from the suite.

We also need to remove the ``purchase_cake`` from the suite if it is not needed i.e. when ``bake_cake`` succeeds.

Add the ``line bake_cake => !purchase_cake`` to the dependencies graph.

Save your changes and run your suite. You should now be able to ``eat_cake`` and not worry about previous tasks keeping the suite from shutting down.

You can see the suicide trigger dependency in the ``cylc gui`` Graph View if you unselect ``View->1 - Options->Ignore Suicide Triggers``.


Note on suicide triggers
------------------------

While it is possible to have a task suicide triggering itself this is not recommended and may lead to difficulties if manual interaction with the suite is required to correct the problem (the task has been removed from the suite).

Depending on your needs, possible places to put the suicide trigger are:

   - triggering off the success of a recovery task
   - triggering off the final task in a cycle
   - triggering off a cleanup task in the suite


Advanced suicide triggers example
---------------------------------

Advanced example 1
^^^^^^^^^^^^^^^^^^

The first example checks the failure of an unreliable task, if it meets the criteria in the checking task then it tries a recovery task. If the recovery task succeeds then the suite carries on, else if it fails then the suite stops as it cannot be recovered.

Possible Outcomes:

If ``flaky_activity`` fails then run ``check``, the ``check`` checks to see if the suite is recoverable, if it is then ``recovery`` succeeds and the suite can continue. If it is not recoverable, i.e., ``check`` fails then don't run housekeep as the suite cannnot carry on and needs human interaction to fix.

If ``flaky_activity`` succeeds the suite carries on as normal, i.e., going straight to housekeep and not running either of the check or recovery tasks.

Create a new suite (or just a new directory somewhere - e.g. in your homespace) containing a ``suite.rc`` file that looks like this:

.. code-block:: cylc

   # Check the failure of `flaky_activity` and if it meets the criteria in the 
   # `check` task then try a recovery task, `recovery`. If `recovery` succeeds 
   # then the suite carrys on else if it fails then the suite stops as it cannot 
   # be recovered.

   [cylc]
       UTC mode = True # Ignore DST

   [scheduling]
       [[dependencies]]
           graph = """
               start_install  => flaky_activity 

               flaky_activity => !check
               flaky_activity | recovery   => housekeep
               flaky_activity:fail         => check => recovery

               check:fail | flaky_activity => !recovery
               check:fail    => !housekeep
           """

   [runtime]
       [[root]]
           [[[job]]]
               execution time limit = PT3M
           [[[events]]]
               mail events = failed, submission failed, submission timeout, execution timeout
               submission timeout = PT24M

       [[check]]
           script = """
               sleep 10;
               echo ${CYLC_SUITE_LOG_DIR%suite}job/$CYLC_TASK_CYCLE_POINT/flaky_activity/NN/job.out
               grep -F 'Fail, but I can recover, try recovery.' ${CYLC_SUITE_LOG_DIR%suite}job/$CYLC_TASK_CYCLE_POINT/flaky_activity/NN/job.out
               if echo $? ; then
                   echo 'This may recover'; true;
               fi
           """

       [[flaky_activity]]
           script = """ 
               sleep 10;
               if (($RANDOM % 2)); then
                   echo 'Success'; true;
               else
                   if (($RANDOM % 2)); then
                       echo 'Fail, but I can recover, try recovery.'; false;
                   else
                       echo 'Fail, I will never figure this out!'; false;
                   fi
               fi
           """

       [[housekeep]]
           script = """ sleep 10;
               echo 'finishing, I always run as expected, usually a housekeeping task.'
           """

       [[recovery]]
           script = """
               sleep 10;
               if (($RANDOM % 2)); then
                   echo 'Success, I could be helped by the recovery task'; true;
               else
                   echo 'Fail, I could not be helped by the recovery task'; false;
               fi
          """

       [[start_install]]
           script = """ sleep 10;
               echo 'starting up, I always run as expected, usually an install task.'
          """

Advanced example 2
^^^^^^^^^^^^^^^^^^

In this example if a member of a specific family fails carry on. If a task important to that cycle fails go to the end of that cycle and remove the failed task from the task pool.

Possible Outcomes:

If ``sometimes_fail`` fails then go to the ``housekeep`` task.

If ``sometimes_fail`` succeeds and ``FAMILY_PASS`` all succeed and ``SOME_DO_SOME_DONT`` all finish no matter if they succeed or fail then then go to the ``housekeep`` task.

Create a new suite (or just a new directory somewhere - e.g. in your homespace) containing a ``suite.rc`` file that looks like this:

.. code-block:: cylc

   # If a member of family `SOME_DO_SOME_DONT` fails then carry on regardless.
   # If then the `sometimes_fail` task fails go to the end of that cycle and 
   # remove the failed task from the task pool.

   [cylc]
       UTC mode = True # Ignore DST

   [scheduling]
       [[dependencies]]
           graph = """
               start_install                => sometimes_fail => FAMILY_PASS
               FAMILY_PASS:succeed-all      => SOME_DO_SOME_DONT
               SOME_DO_SOME_DONT:finish-all => dependent_on_families
               sometimes_fail:fail          => !sometimes_fail &\
               !FAMILY_PASS & !SOME_DO_SOME_DONT & !dependent_on_families
               dependent_on_families | sometimes_fail:fail => housekeep
           """

   [runtime]
       [[root]]
           [[[job]]]
               execution time limit = PT3M
           [[[events]]]
               mail events = failed, submission failed, submission timeout, execution timeout
               submission timeout = PT24M

       [[FAMILY_PASS]]
           script = sleep 10;

       [[SOME_DO_SOME_DONT]]
           script = sleep 5;

       [[bar]]
           inherit = FAMILY_PASS
           script = echo 'bar always succeeds'

       [[dependent_on_families]]
          script = """
              sleep 10;
              echo 'I can only run if all FAMILY_PASS succeed and 
                    SOME_DO_SOME_DONT finish'
              """

       [[foo]]
           inherit = FAMILY_PASS
           script = echo 'foo always succeeds'
                              
       [[flaky_member]]
           inherit = SOME_DO_SOME_DONT
           script = """
               echo 'flaky member is going to:'
               sleep 10;
               if (($RANDOM % 2)); then
                   echo 'Success'; true; 
               else
                   echo 'Fail'; false;
               fi
           """

       [[housekeep]]
           script = """ sleep 10;
               echo 'finishing, I always run as expected, usually a housekeeping task.'
           """

       [[sometimes_fail]]
          script = """
              sleep 10;
              if (($RANDOM % 2)); then
                  echo 'Success'; true;
              else
                  echo 'Fail'; false;
              fi
          """

       [[start_install]]
           script = """ sleep 10;
               echo 'starting up, I always run as expected, usually an install task.'
           """

       [[stable_member]]
           inherit = SOME_DO_SOME_DONT
           script = echo 'stable member always succeeds'


Advanced example 3
^^^^^^^^^^^^^^^^^^

For the third example if a specified task fails go to the end of the cycle. If the next task fails go to the second from last task and then to the end of that cycle.

Possible Outcomes:

If ``check_files_exist`` fails then go to the housekeep task.

If ``check_files_exist`` succeeds but ``generate_plots`` fails go to ``move_data`` then go to the housekeep.

If ``check_files_exist`` succeeds go to ``generate_plots`` if that succeeds go to ``raise_alert`` if that succeeds go to ``move_data`` then go to the ``housekeep`` task.

Create a new suite (or just a new directory somewhere - e.g. in your homespace) containing a ``suite.rc`` file that looks like this:

.. code-block:: cylc

   # If the `check_files_exist` task fails go to the end of the cycle and only do
   # the `housekeep` task, or if `generate_plots` task fails go to the second 
   # from last task, `raise_alert` and then to the end of that cycle and do the 
   # `housekeep` task.

   [cylc]
       UTC mode = True # Ignore DST

   [scheduling]
       [[dependencies]]
            graph = """
                start_install          => check_files_exist
                check_files_exist      => generate_plots
                check_files_exist:fail => !generate_plots & !move_data
                check_files_exist:fail | move_data => housekeep

                generate_plots:fail | check_files_exist:fail => !raise_alert
                generate_plots:fail | raise_alert => move_data
                generate_plots         => raise_alert
            """

   [runtime]
       [[root]]
           [[[job]]]
               execution time limit = PT3M
           [[[events]]]
               mail events = failed, submission failed, submission timeout, execution timeout
               submission timeout = PT24M

       [[check_files_exist]]
           script = """
               echo 'Do the files exist?'
               sleep 10;
               if (($RANDOM % 2)); then
                   echo 'Yes, then success'; true; 
               else
                   echo 'No, then fail'; false;
               fi
           """

       [[generate_plots]]
           script = """
               echo 'You could run a script to plot data, but did they finish?'
               sleep 10;
               if (($RANDOM % 2)); then
                   echo 'Yes, then success'; true; 
               else
                   echo 'No, then fail'; false;
               fi
           """

       [[housekeep]]
           script = """ sleep 10;
               echo 'finishing, I always run as expected, usually a housekeeping task.'
           """

       [[move_data]]
           script = """
               sleep 10;
               echo 'You could run a script to move data'
           """

       [[raise_alert]]
           script = """
               sleep 10;
               echo 'You need to raise an alert: ALERT!'
           """

       [[start_install]]
           script = """ sleep 10;
               echo 'starting up, I always run as expected, usually an install task.'
           """





