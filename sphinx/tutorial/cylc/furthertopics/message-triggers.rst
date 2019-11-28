.. _tutorial-cylc-message-triggers:

Message Triggers
================

:term:`Message triggers <message trigger>` allow us to produce custom
outputs for tasks before they have fully completed. These are also known as
:term:`custom task outputs <message trigger>`.

Explanation
-----------

We have seen :ref:`before <tutorial-qualifiers>` that tasks can have 
:term:`qualifiers <qualifier>` for different 
:term:`task states <task state>`.
:term:`Message triggers <message trigger>` are essentially custom qualifiers.
We can produce a bespoke output while our task is still running.
This output could be, for example, a report or perhaps another task. 

Usage
-----

:term:`Message triggers <message trigger>` are particularily useful if we have
a long running task and we want to produce multiple tailored outputs whilst
this task is running, rather than having to wait for the task to fully
complete.

We could also set up :term:`message triggers <message trigger>` to, for example,
send an email to inform us that a submission has failed, making use of Cylc's 
task event handling system. More information is available on these in the 
`Cylc User Guide <https://cylc.github.io/doc/built-sphinx/task-implementation.html#task-messages>`_.


:term:`Message triggers <message trigger>` provide a superior solution to
the problem of file system polling. We could, for example, design our suite
such that we check if our task is finished by polling at intervals.
It is inefficient to 'spam' task hosts with polling commands, it is preferable
to set up a message trigger. 

How to create a message trigger
-------------------------------

In order to get our suite to trigger messages, we need to:

* specify our custom message in a section called ``[[outputs]]`` within the
     ``[runtime]`` section of our suite,

* add ``cylc message -- "${CYLC_SUITE_NAME}" "${CYLC_TASK_JOB}" "YOUR CHOSEN TRIGGER MESSAGE"``
     to the ``script`` section of ``[runtime]``, your chosen trigger message 
     should be unique and should exactly match the message defined in
     ``[[outputs]]``.  

* Refer to these messages in the ``[dependencies]`` section of our suite.

These outputs are then triggered during the running of the task.    
We can use these to manage tasks dependant on partially completed tasks.

So, a basic example, where we have a task foo, that when partially completed 
triggers another task bar and when fully completed triggers another task, baz. 

   .. code-block:: cylc

      [scheduling]
         [[dependencies]]
         graph = """foo:out1 => bar
                     foo => baz"""
      [runtime]
         [[foo]]
            script = """
               sleep 5
               cylc message -- "${CYLC_SUITE_NAME}" "${CYLC_TASK_JOB}" "file 1 done"
               sleep 10
                  """
            [[[outputs]]]
               out1 = "file 1 done"
                  
         [[bar, baz]]
            script = sleep 10

.. _message triggers practical:

.. practical::

   .. rubric:: In this practical we will create a suite to demonstrate
      :term:`message triggers <message trigger>`. We will use message triggers
      to both produce a report and trigger a new task from a partially completed
      task.

   #. **Create a new directory.**

      Within your ``~/cylc-run`` directory create a new directory called 

      ``message-triggers`` and move into it:

      .. code-block:: bash

         mkdir ~/cylc-run/message-triggers
         cd ~/cylc-run/message-triggers

   #. **Install the script needed for our suite**

      The suite we will be designing requires a bash script, ``random.sh``,
      to produce our report. It will simply create a text file ``report.txt``
      with some random numbers in it. This will be executed when the associated
      task is run. 

      Scripts should be kept in the ``bin`` sub-directory within the 
      :term:`suite directory <suite directory>`. If a ``/bin`` exists in the 
      suite directory, it will be prepended to the PATH at run time.
      
      Create a ``/bin`` directory and move into it.
      
      .. code-block:: bash

         mkdir ~/cylc-run/message-triggers/bin
             
      Create a bash script in the bin directory:    

      .. code-block:: bash

         touch bin/random.sh
 
      Open the file and paste the following basic bash script into it:

      .. code-block:: bash

         #!/usr/bin/env bash
         set -eu

         counter=1

         while [ $counter -le 10 ]; do
            newrand=$[ (( $RANDOM % 40) + 1 ) ];
            echo $newrand >> report.txt;
            counter=$[($counter + 1)];
         done


   #. **Create a new suite.**

      Create a ``suite.rc`` file and paste the following basic suite into it:

      .. code-block:: cylc

         [cylc]
             UTC mode = True

         [meta]
             title = "test suite to demo message triggers"

         [scheduling]
             initial cycle point = 2019-06-27T00Z
             final cycle point = 2019-10-27T00Z
                
             [[dependencies]]

                 [[[P2M]]]
                     graph = """
                         long_forecasting_task =>  another_weather_task
                         long_forecasting_task => different_weather_task 
                         long_forecasting_task[-P2M] => long_forecasting_task
                     """

      This is a basic suite, currently it does not have any message triggers
      attached to any task.


   #. **Define our tasks in the runtime section.**

      Next we want to create our ``runtime`` section of our suite.
      First we define what the tasks do. In this example 
      ``long_forecasting_task`` will sleep, create a file containing some
      random numbers and produce a message.
      (Note that the random number generator bash script has already been 
      preloaded into your ``bin`` directory.)
      ``another_weather_task`` and ``different_weather_task`` simply sleep.

      Add the following code to the  ``suite.rc`` file. 

      .. code-block:: cylc

         [runtime]

             [[long_forecasting_task]]
                 script = """
                         sleep 2
                         random.sh
                        
                         sleep 2
                         random.sh
                                            
                         sleep 2
                         random.sh
                     """

             [[another_weather_task, different_weather_task]]
                 script = sleep 1

      
   #. **Create message triggers.**

      We now have a suite with a task, ``long_forecasting_task`` which, after
      it has fully completed, triggers two more tasks, ``another_weather_task``
      and ``different_weather_task``.

      Suppose we want ``another_weather_task`` and ``different_weather_task``
      to start before ``long_forecasting_task`` has fully completed, perhaps
      after some data has become available. 
      
      In this case, we shall trigger ``another_weather_task`` after one set of 
      random numbers has been created
      and ``different_weather_task`` after a second set of random numbers has
      been created.    
      
      There are three aspects of creating messsage triggers. 
      The first is to create the messages within ``runtime`` in our suite
      - we need to create a sub-section called ``outputs``. Here we create
      our custom outputs.  

      .. code-block:: diff

         +        [[[outputs]]]
         +            update1 = "Task partially complete, report ready to view"
         +            update2 = "Task partially complete, report updated" 

      The second thing we need to do is to create a cylc message in our script.
      This should be placed where you want the message to be called. In our 
      case, this is after each of the first two set of random numbers are
      generated. 
      
      .. tip::
         Remember that the ``cylc message`` should exactly match the outputs 
         stated in our ``[[[outputs]]]`` section.

      Modify the ``[[long_forecasting_task]]`` script in the ``suite.rc`` file
      as follows:

      .. code-block:: diff

         [runtime]

             [[long_forecasting_task]]
                 script = """
                     sleep 2
                     random.sh
         +           cylc message -- "${CYLC_SUITE_NAME}" "${CYLC_TASK_JOB}" \
                         "Task partially complete, report ready to view"
                     sleep 2
                     random.sh
         +           cylc message -- "${CYLC_SUITE_NAME}" "${CYLC_TASK_JOB}" \
                         "Task partially complete, report updated"
                     sleep 2
                     random.sh
                 """

      Lastly, we need to do is to make reference to the messages in the
      graph section. 
      This will ensure our messages are triggered correctly. 
        
      Adapt the ``[[dependencies]]`` section in the ``suite.rc`` file to read as
      follows: 
      
      .. code-block:: diff

                  [[[P2M]]]
                      graph = """
         -               long_forecasting_task =>  another_weather_task
         -               long_forecasting_task => different_weather_task 
         +               long_forecasting_task:update1 =>  another_weather_task
         +               long_forecasting_task:update2 => different_weather_task 
                         long_forecasting_task[-P2M] => long_forecasting_task
                     """

      This completes our ``suite.rc`` file.

      Our final suite should look like this:

      .. spoiler:: Solution warning

         .. code-block:: cylc

            [cylc]
            UTC mode = True

            [meta]
            title = "test suite to demo message triggers"

            [scheduling]
                initial cycle point = 2019-06-27T00Z
                final cycle point = 2019-10-27T00Z
                
                [[dependencies]]

                    [[[P2M]]]
                        graph = """
                            long_forecasting_task:update1 =>  another_weather_task
                            long_forecasting_task:update2 => different_weather_task 
                            long_forecasting_task[-P2M] => long_forecasting_task
                        """

            [runtime]

                [[long_forecasting_task]]
                    script = """
                        sleep 2
                        random.sh
                        cylc message -- "${CYLC_SUITE_NAME}" "${CYLC_TASK_JOB}" \
                            "Task partially complete, report ready to view"
                        sleep 2
                        random.sh
                        cylc message -- "${CYLC_SUITE_NAME}" "${CYLC_TASK_JOB}" \
                            "Task partially complete, report updated"
                        sleep 2
                        random.sh
                    """

                    [[[outputs]]]
                        update1 = "Task partially complete, report ready to view"
                        update2 = "Task partially complete, report updated"

                [[another_weather_task, different_weather_task]]
                    script = sleep 1

   #. **Validate the suite.**

      It is a good idea to check that our ``suite.rc`` file does not have any
      configuaration issues. 

      Run `cylc validate` to check for any errors:

      .. code-block:: bash      

          cylc validate .
   
   #. **Run the suite.**

      Now we are ready to run our suite. Open the Cylc GUI by running the
      following command:

      .. code-block:: bash

         cylc gui message-triggers &

      Run the suite either by pressing the play button in the Cylc GUI or by
      running the command:

      .. code-block:: bash

         cylc run message-triggers

      Your suite should now run, the tasks should succeed. 

   #. **Inspect the work directory.**

      We can now check for our report outputs. These should appear in the 
      :term:`work directory` of the suite. All being well, our first cycle
      point should produce a test file with some random numbers, and each
      subsequent cycle point file should have more random numbers added.

   #. **Extension.**
      
      Suppose now we would like to send an email alerting us to the reports 
      being ready to view.

      We will need to add to our ``suite.rc`` file.

      In the ``runtime`` section, add a sub-section called ``[[[events]]]``. 
      Within this section we will make use of the built-in setting
      ``mail events``. 
      Here, we specify a list of events for which notifications should be sent.

      The events we are interested in are, in this case, our outputs.

      Add the following code to your ``[[[events]]]`` section.

        .. code-block:: cylc

           [[[events]]]
               mail events = update1, update2
      
        Our updated suite should look like this:

      .. spoiler:: Solution warning
         
         .. code-block:: cylc
   
            [cylc]
            UTC mode = True
            [meta]
            title = "test suite to demo message triggers"
            [scheduling]
                initial cycle point = 2019-06-27T00Z
                final cycle point = 2019-10-27T00Z
                
                [[dependencies]]

                    [[[P2M]]]
                        graph = """
                            long_forecasting_task:update1 =>  another_weather_task
                            long_forecasting_task:update2 => different_weather_task 
                            long_forecasting_task[-P2M] => long_forecasting_task
                        """
            [runtime]
                [[long_forecasting_task]]
                    script = """
                        sleep 2
                        random.sh
                        cylc message -- "${CYLC_SUITE_NAME}" "${CYLC_TASK_JOB}" \
                            "Task partially complete, report ready to view"
                        sleep 2
                        random.sh
                        cylc message -- "${CYLC_SUITE_NAME}" "${CYLC_TASK_JOB}" \
                            "Task partially complete, report updated"
                        sleep 2
                        random.sh
                    """
                  
                    [[[outputs]]]
                        update1 = "Task partially complete, report ready to view"
                        update2 = "Task partially complete, report updated"
                    
                    [[[events]]]
                        mail events = update1, update2    
                
                [[another_weather_task, different_weather_task]]
                    script = sleep 1

      Save your changes and run your suite. 
      Check your emails and you should have, one email for the first update and,
      a second email alerting you to the subsequent updated reports being ready.

      Note that the second email automatically bundles the messages to prevent
      your inbox from being flooded.
               
