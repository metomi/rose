.. _DataPoint: https://www.metoffice.gov.uk/datapoint

.. _tutorial-cylc-runtime-configuration:

.. include:: ../../../hyperlinks.rst
  :start-line: 1

Runtime Configuration
=====================


In the last section we associated tasks with scripts and ran a simple suite. In
this section we will look at how we can configure these tasks.


Environment Variables
---------------------

We can specify environment variables in a task's ``[environment]`` section.
These environment variables are then provided to :term:`jobs <job>` when they
run.

.. code-block:: cylc

   [runtime]
       [[countdown]]
           script = seq $START_NUMBER
           [[[environment]]]
               START_NUMBER = 5

Each job is also provided with some standard environment variables e.g:

``CYLC_SUITE_RUN_DIR``
    The path to the suite's :term:`run directory`
    *(e.g. ~/cylc-run/suite)*.
``CYLC_TASK_WORK_DIR``
    The path to a task's :term:`work directory`
    *(e.g. run-directory/work/cycle/task)*.
``CYLC_TASK_CYCLE_POINT``
    The :term:`cycle point` for a task
    *(e.g. 20171009T0950)*.

There are many more environment variables, see the `cylc user guide`_ for more
information.


Job Submission
--------------

By default cylc runs :term:`jobs <job>` on the machine where the suite is
running. We can tell cylc to run jobs on other machines by setting the
``[remote]host`` setting to the name of the host. E.G To run a task on the host
``computehost`` you might write:

.. code-block:: cylc

   [runtime]
       [[hello_computehost]]
           script = echo "Hello Compute Host"
           [[[remote]]]
               host = computehost

.. _background processes: https://en.wikipedia.org/wiki/Background_process
.. _job scheduler: https://en.wikipedia.org/wiki/Job_scheduler

.. _tutorial-batch-system:

By default cylc runs executes jobs as `background processes`_.
When we are running jobs on other compute hosts we will often want to
use a :term:`batch system` (`job scheduler`_) to submit our job.
Cylc supports the following :term:`batch systems <batch system>`:

* loadleveler
* lsf
* pbs
* sge
* slurm

:term:`Batch systems <batch system>` typically require some form of
:term:`directives <directive>`. :term:`Directives <directive>` inform the
:term:`batch system` of the requirements of a :term:`job`, for example how much
memory it requires or how many CPUs it will run on. For example:

.. code-block:: cylc

   [runtime]
       [[big_task]]
           script = big-executable

           # Submit to the host "big-computer"
           [[[remote]]]
               host = big-computer

           # Submit the job using the "slurm" batch system.
           [[[job]]]
               batch system = slurm

           # Inform "slurm" that this job requires 500Mb of ram and 4 CPUs.
           [[[directives]]]
               --mem = 500
               --ntasks = 4


Timeouts
--------

We can specify a time limit after which a job will be terminated using the
``[job]execution time limit`` setting. The value of the setting is an
:term:`iso8601 duration`, cylc automatically inserts this into a job's
directives as appropriate.

.. code-block:: cylc

   [runtime]
       [[some_task]]
           script = some-executable
           [[[job]]]
               execution time limit = PT15M  # 15 minutes.


Retries
-------

Sometimes jobs fail, this can be caused by two factors:

* Something going wrong in the jobs execution e.g:

  * A bug.
  * A system error.
  * The job hitting the ``execution time limit``.

* Something going wrong in the job submission e.g:

  * A network problem.
  * The :term:`job host` becoming un-available or over-loaded.
  * An issue with the directives.

In the event of failure cylc can automatically re-submit (retry) jobs. We
configure retries using the ``[job]execution retry delays`` and
``[job]submission retry delays`` settings. These settings are both set to an
:term:`iso8601 duration` e.g setting ``execution retry delays`` to ``PT10M``
would cause the job to retry every 10 minutes in the event of an execution
failure.

We can limit the number of retries by writing a multiple in-front of the
duration e.g:

.. code-block:: cylc

   [runtime]
       [[some-task]]
           script = some-script
           [[[job]]]
               # In the event of execution failure, retry a maximum of three
               # times every 15 minutes.
               execution retry delays = 3 * PT15M
               # In the event of submission failure, retry a maximum of twice
               # every ten minutes and then every 30 minutes there after.
               submission retry delays = 2*PT10M, PT30M


Start, Stop, Restart
--------------------

We have seen how to start and stop cylc suites (``cylc run``, ``cylc stop``).
The ``cylc stop`` command causes cylc to wait for all running jobs to finish
before it stops the suite. There are two options which change this behaviour:

``cylc stop --kill``
   When the ``--kill`` option is used cylc will kill all running jobs
   before stopping. *Cylc can kill jobs on remote hosts and uses the appropriate
   command where a :term:`batch system` is used.*
``cylc stop --now --now``
   When the ``--now`` option is used twice cylc stops straight away leaving any
   jobs running.

Once a suite has stopped it is possible to restart it using the
``cylc restart`` command. When the suite restarts it picks up where it left
off and carries on as normal.

.. code-block:: bash

   # Run the suite "name".
   cylc run <name>
   # Stop the suite "name" killing any running tasks.
   cylc stop <name> --kill
   # Restart the suite "name", picking up where it left off.
   cylc restart <name>


.. practical::

   .. rubric:: In this practical we will add runtime configuration to the
      :ref:`weather forecasting suite <tutorial-datetime-cycling-practical>`
      from the :ref:`scheduling tutorial <tutorial-scheduling>`.

   #. **Create A New Suite.**

      Create a new suite by running the command:

      .. code-block:: bash

         rose tutorial runtime-tutorial forecasting-suite

      You will now have a copy of the weather forecasting suite along with some
      executables and python modules.

      Register the suite by running:

      .. code-block:: bash

         cd forecasting-suite
         cylc reg forecasting-suite $PWD

   #. **Set The Initial And Final Cycle Points.**

      TODO

   #. **Add Runtime Configuration For The** ``get_observation`` **Tasks.**

      In the ``bin`` directory is a script called ``get-observations``. This
      script gets weather data from the MetOffice `DataPoint`_ service.
      This script requires two environment variables:

      ``SITE_ID``
          This is a four digit numerical code which is used to identify a
          weather station e.g. ``3772`` is Heathrow Airport.
      ``API_KEY``
          An authentication key required for access to the service.

      .. TODO: Add instructions for offline configuration

      Add the following lines to the bottom of the ``suite.rc`` file.

      .. code-block:: cylc

         [runtime]
             [[get_observations_heathrow]]
                 script = get-observations
                 [[[environment]]]
                     SITE_ID = 3772
                     API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb

      The codes for the other three weather stations are:

      * Camborne - ``3808``
      * Shetland - ``3005``
      * Belmullet - ``3976``

      Add three more ``get_observations`` tasks for each of the remaining
      weather stations.

      .. spoiler:: Solution warning

         .. code-block:: cylc

            [runtime]
                [[get_observations_heathrow]]
                    script = get-observations
                    [[[environment]]]
                        SITE_ID = 3772
                        API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
                [[get_observations_camborne]]
                    script = get-observations
                    [[[environment]]]
                        SITE_ID = 3808
                        API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
                [[get_observations_shetland]]
                    script = get-observations
                    [[[environment]]]
                        SITE_ID = 3005
                        API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
                [[get_observations_belmullet]]
                    script = get-observations
                    [[[environment]]]
                        SITE_ID = 3976
                        API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb

      Check the ``suite.rc`` file is valid by running the command:

      .. code-block:: bash

         cylc validate forecasting-suite

      .. TODO: Add advice on what to do if the command fails.

   #. **Test The** ``get_observations`` **Tasks.**

      Next we will test the ``get_observations`` tasks.

      Open the cylc GUI by running the following command:

      .. code-block:: bash

         gcylc forecasting-suite &

      Run the suite either by pressing the play button in the cylc GUI or by
      running the command:

      .. code-block:: bash

         cylc run forecasting-suite

      If all goes well you will see the ``get_observations`` tasks run and
      succeed in the cylc GUI. Once the suite has reached the final cycle point
      and all tasks have succeeded the suite will automatically shutdown.

      .. TODO: Advise on what to do if all does not go well.

      The ``get-observations`` script produces a file called ``wind.csv`` which
      contains the wind-speed and direction. This file is written in the task's
      :term:`work directory`.

      Try and open one of the ``wind.csv`` files. Note the path to the
      :term:`work directory` is:

      .. TODO: Move/Remove?

      .. code-block:: sub

         ~/cylc-run/<suite-name>/work/<cycle-point>/<task-name>

      You should find a file with four numbers:

      * The longitude of the weather station.
      * The latitude of the weather station.
      * The wind direction *[where the wind GOING]* (in degrees).
      * The wind speed in miles per hour.

      .. spoiler:: Hint hint

         If you run ``ls ~/cylc-run/forecasting-suite/work`` you should see a
         list of cycles. Pick one of them and open the file::

            ~/cylc-run/forecasting-suite/work/<cycle-point>/get_observations_heathrow

   #. **Add runtime configuration for the other tasks.**

      The runtime configuration for the remaining tasks has been written out
      for you in the ``runtime`` file which you will find in the
      :term:`suite directory`. Copy the code from the ``runtime`` file to the
      bottom of the ``suite.rc`` file.

      Check the ``suite.rc`` file is valid by running the command:

      .. code-block:: bash

         cylc validate forecasting-suite

      .. TODO: Add advice on what to do if the command fails.

   #. **Run The Suite.**

      Open the cylc GUI and run the suite.

      .. spoiler:: Hint hint

         .. code-block:: bash

            gcylc runtime-tutorial &

         Run the suite either by:
          
         * Press the play button in the cylc gui. Ensure "Cold Start" is
           selected from the dialogue window then press "Start"
         * Run the command ``cylc run forecasting-suite``.

   #. **View The Forecast Summnary.**

      The ``post_process_exeter`` task will produce a one line summary of the
      weather in Exeter as forecast two hours ahead of time. This summary can
      be found in the ``summary`` file in the :term:`work directory`.

      Try opening the summary file for the first cycle. The path to the
      :term:`work directory` is:

      .. code-block:: sub

          ~/cylc-run/<suite-name>/log/work/<cycle-point>/<task-name>

      .. spoiler:: Hint hint

         * ``suite-name`` - "forecasting-suite".
         * ``cyclc-point`` - This will be the first cycle of the suite.
           i.e. the intial cycle point.
         * ``task-name`` - "post_process_exeter".
         * ``submission-number`` - "00".

   #. **View The Rainfall Data.**

      .. TODO: Skip this if you don't have internet connection.

      The ``forecast`` task will produce an html page where the rainfall
      data is rendered on a map. This html file is called ``job-map.html`` and
      is saved alongside the :term:`job log`.

      Try opening this file in a web browser e.g::

         firefox filename

      The path to the :term:`job log directory` is:

      .. code-block:: sub

         ~/cylc-run/<suite-name>/log/job/<cycle-point>/<task-name>/<submission-number>

      .. spoiler:: Hint hint

         * ``suite-name`` - "forecasting-suite".
         * ``cyclc-point`` - This will be the last cycle of the suite.
           i.e. the final cycle point.
         * ``task-name`` - "forecast".
         * ``submission-number`` - "00".

