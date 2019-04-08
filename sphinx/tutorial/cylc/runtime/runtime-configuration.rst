.. include:: ../../../hyperlinks.rst
  :start-line: 1

.. _DataPoint: https://www.metoffice.gov.uk/datapoint


.. _tutorial-cylc-runtime-configuration:

Runtime Configuration
=====================

In the last section we associated tasks with scripts and ran a simple suite. In
this section we will look at how we can configure these tasks.


Environment Variables
---------------------

.. ifnotslides::

   We can specify environment variables in a task's ``[environment]`` section.
   These environment variables are then provided to :term:`jobs <job>` when they
   run.

.. code-block:: cylc

   [runtime]
       [[countdown]]
           script = seq $START_NUMBER
           [[[environment]]]
               START_NUMBER = 5

.. ifnotslides::

   Each job is also provided with some standard environment variables e.g:

   ``CYLC_SUITE_RUN_DIR``
       The path to the suite's :term:`run directory`
       *(e.g. ~/cylc-run/suite)*.
   ``CYLC_TASK_WORK_DIR``
       The path to the associated task's :term:`work directory`
       *(e.g. run-directory/work/cycle/task)*.
   ``CYLC_TASK_CYCLE_POINT``
       The :term:`cycle point` for the associated task
       *(e.g. 20171009T0950)*.

   There are many more environment variables - see the `Cylc User Guide`_ for more
   information.

.. ifslides::

   * ``CYLC_SUITE_RUN_DIR``
   * ``CYLC_TASK_WORK_DIR``
   * ``CYLC_TASK_CYCLE_POINT``


.. _tutorial-batch-system:

Job Submission
--------------

.. ifnotslides::

   By default Cylc runs :term:`jobs <job>` on the machine where the suite is
   running. We can tell Cylc to run jobs on other machines by setting the
   ``[remote]host`` setting to the name of the host, e.g. to run a task on the
   host ``computehost`` you might write:

.. code-block:: cylc

   [runtime]
       [[hello_computehost]]
           script = echo "Hello Compute Host"
           [[[remote]]]
               host = computehost

.. _background processes: https://en.wikipedia.org/wiki/Background_process
.. _job scheduler: https://en.wikipedia.org/wiki/Job_scheduler

.. nextslide::

.. ifnotslides::

   Cylc also executes jobs as `background processes`_ by default.
   When we are running jobs on other compute hosts we will often want to
   use a :term:`batch system` (`job scheduler`_) to submit our job.
   Cylc supports the following :term:`batch systems <batch system>`:

* at
* loadleveler
* lsf
* pbs
* sge
* slurm
* moab

.. nextslide::

.. ifnotslides::

   :term:`Batch systems <batch system>` typically require
   :term:`directives <directive>` in some form. :term:`Directives <directive>`
   inform the :term:`batch system` of the requirements of a :term:`job`, for
   example how much memory a given job requires or how many CPUs the job will
   run on. For example:

.. code-block:: cylc

   [runtime]
       [[big_task]]
           script = big-executable

           # Submit to the host "big-computer".
           [[[remote]]]
               host = big-computer

           # Submit the job using the "slurm" batch system.
           [[[job]]]
               batch system = slurm

           # Inform "slurm" that this job requires 500MB of RAM and 4 CPUs.
           [[[directives]]]
               --mem = 500
               --ntasks = 4


Timeouts
--------

.. ifnotslides::

   We can specify a time limit after which a job will be terminated using the
   ``[job]execution time limit`` setting. The value of the setting is an
   :term:`ISO8601 duration`. Cylc automatically inserts this into a job's
   directives as appropriate.

.. code-block:: cylc

   [runtime]
       [[some_task]]
           script = some-executable
           [[[job]]]
               execution time limit = PT15M  # 15 minutes.


Retries
-------

Sometimes jobs fail. This can be caused by two factors:

* Something going wrong with the job's execution e.g:

  * A bug;
  * A system error;
  * The job hitting the ``execution time limit``.

* Something going wrong with the job submission e.g:

  * A network problem;
  * The :term:`job host` becoming unavailable or overloaded;
  * An issue with the directives.

.. nextslide::

.. ifnotslides::

   In the event of failure Cylc can automatically re-submit (retry) jobs. We
   configure retries using the ``[job]execution retry delays`` and
   ``[job]submission retry delays`` settings. These settings are both set to an
   :term:`ISO8601 duration`, e.g. setting ``execution retry delays`` to ``PT10M``
   would cause the job to retry every 10 minutes in the event of execution
   failure.

   We can limit the number of retries by writing a multiple in front of the
   duration, e.g:

.. code-block:: cylc

   [runtime]
       [[some-task]]
           script = some-script
           [[[job]]]
               # In the event of execution failure, retry a maximum
               # of three times every 15 minutes.
               execution retry delays = 3*PT15M
               # In the event of submission failure, retry a maximum
               # of two times every ten minutes and then every 30
               # minutes thereafter.
               submission retry delays = 2*PT10M, PT30M


Start, Stop, Restart
--------------------

.. ifnotslides::

   We have seen how to start and stop Cylc suites with ``cylc run`` and
   ``cylc stop`` respectively. The ``cylc stop`` command causes Cylc to wait
   for all running jobs to finish before it stops the suite. There are two
   options which change this behaviour:

   ``cylc stop --kill``
      When the ``--kill`` option is used Cylc will kill all running jobs
      before stopping. *Cylc can kill jobs on remote hosts and uses the
      appropriate command when a* :term:`batch system` *is used.*
   ``cylc stop --now --now``
      When the ``--now`` option is used twice Cylc stops straight away, leaving
      any jobs running.

   Once a suite has stopped it is possible to restart it using the
   ``cylc restart`` command. When the suite restarts it picks up where it left
   off and carries on as normal.

   .. code-block:: bash

      # Run the suite "name".
      cylc run <name>
      # Stop the suite "name", killing any running tasks.
      cylc stop <name> --kill
      # Restart the suite "name", picking up where it left off.
      cylc restart <name>

.. ifslides::

   .. code-block:: sub

      cylc run <name>
      cylc stop <name>
      cylc restart <name>

      cylc stop <name> --kill
      cylc stop <name> --now --now

   .. nextslide::

   .. rubric:: In this practical we will add runtime configuration to the
      :ref:`weather-forecasting suite <tutorial-datetime-cycling-practical>`
      from the :ref:`scheduling tutorial <tutorial-scheduling>`.

   Next section: :ref:`tutorial-cylc-consolidating-configuration`


.. _tutorial-cylc-runtime-forecasting-suite:

.. practical::

   .. rubric:: In this practical we will add runtime configuration to the
      :ref:`weather-forecasting suite <tutorial-datetime-cycling-practical>`
      from the :ref:`scheduling tutorial <tutorial-scheduling>`.

   #. **Create A New Suite.**

      Create a new suite by running the command:

      .. code-block:: bash

         rose tutorial runtime-tutorial
         cd ~/cylc-run/runtime-tutorial

      You will now have a copy of the weather-forecasting suite along with some
      executables and python modules.

   #. **Set The Initial And Final Cycle Points.**

      We want the suite to run for 6 hours, starting at least 7 hours ago, on
      the hour.

      We could work out the dates and times manually, or we could let Cylc do
      the maths for us.

      Set the :term:`initial cycle point`:

      .. code-block:: cylc

         initial cycle point = previous(T-00) - PT7H

      * ``previous(T-00)`` returns the current time ignoring minutes and
        seconds.

        *e.g. if the current time is 12:34 this will return 12:00*

      * ``-PT7H`` subtracts 7 hours from this value.

      Set the :term:`final cycle point`:

      .. code-block:: cylc

         final cycle point = +PT6H

      This sets the :term:`final cycle point` six hours after the
      :term:`initial cycle point`.

      Run `cylc validate` to check for any errors::

          cylc validate .

   #. **Add Runtime Configuration For The** ``get_observations`` **Tasks.**

      In the ``bin`` directory is a script called ``get-observations``. This
      script gets weather data from the MetOffice `DataPoint`_ service.
      It requires two environment variables:

      ``SITE_ID``:
          A four digit numerical code which is used to identify a
          weather station, e.g. ``3772`` is Heathrow Airport.
      ``API_KEY``:
          An authentication key required for access to the service.

      .. TODO: Add instructions for offline configuration

      Generate a Datapoint API key::

         rose tutorial api-key

      Add the following lines to the bottom of the ``suite.rc`` file replacing
      ``xxx...`` with your API key:

      .. code-block:: cylc

         [runtime]
             [[get_observations_heathrow]]
                 script = get-observations
                 [[[environment]]]
                     SITE_ID = 3772
                     API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx


      Add three more ``get_observations`` tasks for each of the remaining
      weather stations.

      You will need the codes for the other three weather stations, which are:

      * Camborne - ``3808``
      * Shetland - ``3005``
      * Belmullet - ``3976``

      .. spoiler:: Solution warning

         .. code-block:: cylc

            [runtime]
                [[get_observations_heathrow]]
                    script = get-observations
                    [[[environment]]]
                        SITE_ID = 3772
                        API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                [[get_observations_camborne]]
                    script = get-observations
                    [[[environment]]]
                        SITE_ID = 3808
                        API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                [[get_observations_shetland]]
                    script = get-observations
                    [[[environment]]]
                        SITE_ID = 3005
                        API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                [[get_observations_belmullet]]
                    script = get-observations
                    [[[environment]]]
                        SITE_ID = 3976
                        API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

      Check the ``suite.rc`` file is valid by running the command:

      .. code-block:: bash

         cylc validate .

      .. TODO: Add advice on what to do if the command fails.

   #. **Test The** ``get_observations`` **Tasks.**

      Next we will test the ``get_observations`` tasks.

      Open the Cylc GUI by running the following command:

      .. code-block:: bash

         cylc gui runtime-tutorial &

      Run the suite either by pressing the play button in the Cylc GUI or by
      running the command:

      .. code-block:: bash

         cylc run runtime-tutorial

      If all goes well the suite will startup and the tasks will run and
      succeed. Note that the tasks which do not have a ``[runtime]`` section
      will still run though they will not do anything as they do not call any
      scripts.

      Once the suite has reached the final cycle point and all tasks have
      succeeded the suite will automatically shutdown.

      .. TODO: Advise on what to do if all does not go well.

      The ``get-observations`` script produces a file called ``wind.csv`` which
      specifies the wind speed and direction. This file is written in the task's
      :term:`work directory`.

      Try and open one of the ``wind.csv`` files. Note that the path to the
      :term:`work directory` is:

      .. code-block:: sub

         work/<cycle-point>/<task-name>

      You should find a file containing four numbers:

      * The longitude of the weather station;
      * The latitude of the weather station;
      * The wind direction (*the direction the wind is blowing towards*)
        in degrees;
      * The wind speed in miles per hour.

      .. spoiler:: Hint hint

         If you run ``ls work`` you should see a
         list of cycles. Pick one of them and open the file::

            work/<cycle-point>/get_observations_heathrow/wind.csv

   #. **Add runtime configuration for the other tasks.**

      The runtime configuration for the remaining tasks has been written out
      for you in the ``runtime`` file which you will find in the
      :term:`suite directory`. Copy the code in the ``runtime`` file to the
      bottom of the ``suite.rc`` file.

      Check the ``suite.rc`` file is valid by running the command:

      .. code-block:: bash

         cylc validate .

      .. TODO: Add advice on what to do if the command fails.

   #. **Run The Suite.**

      Open the Cylc GUI (if not already open) and run the suite.

      .. spoiler:: Hint hint

         .. code-block:: bash

            cylc gui runtime-tutorial &

         Run the suite either by:
          
         * Pressing the play button in the Cylc GUI. Then, ensuring that
           "Cold Start" is selected within the dialogue window, pressing the
           "Start" button.
         * Running the command ``cylc run runtime-tutorial``.

   #. **View The Forecast Summary.**

      The ``post_process_exeter`` task will produce a one-line summary of the
      weather in Exeter, as forecast two hours ahead of time. This summary can
      be found in the ``summary.txt`` file in the :term:`work directory`.

      Try opening the summary file - it will be in the last cycle. The path to
      the :term:`work directory` is:

      .. code-block:: sub

          work/<cycle-point>/<task-name>

      .. spoiler:: Hint hint

         * ``cycle-point`` - this will be the last cycle of the suite,
           i.e. the final cycle point.
         * ``task-name`` - set this to "post_process_exeter".

   #. **View The Rainfall Data.**

      .. TODO: Skip this if you don't have internet connection.

      The ``forecast`` task will produce a html page where the rainfall
      data is rendered on a map. This html file is called ``job-map.html`` and
      is saved alongside the :term:`job log`.

      Try opening this file in a web browser, e.g via:

      .. code-block:: sub

         firefox <filename> &

      The path to the :term:`job log directory` is:

      .. code-block:: sub

         log/job/<cycle-point>/<task-name>/<submission-number>

      .. spoiler:: Hint hint

         * ``cycle-point`` - this will be the last cycle of the suite,
           i.e. the final cycle point.
         * ``task-name`` - set this to "forecast".
         * ``submission-number`` - set this to "01".

