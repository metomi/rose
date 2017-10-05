.. _tutorial-cylc-runtime-configuration:

Runtime Configuration
=====================


In the last section we associated tasks with scripts and ran a simple suite. In
this section we will look at how we can configure these tasks.


Environment Variables
---------------------

We can specify environment variables in a tasks ``[environment]`` section.
These environment variables are then provided to :term:`jobs <job>` when they
run.

.. code-block:: cylc

   [runtime]
       [[countdown]]
           script = for i in $(seq $START_NUMBER); do echo $i; done
           [[[environment]]]
               START_NUMBER = 5


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

.. _wiki_background_process: https://en.wikipedia.org/wiki/Background_process
.. _wiki_job_scheduler: https://en.wikipedia.org/wiki/Job_scheduler

.. _tutorial-batch-system:

By default cylc runs executes jobs as
`background processes <wiki_background_process>`_. When we are running
jobs on other compute hosts we will often want to use a :term:`batch system`
(`job scheduler <wiki_job_scheduler>`_) to submit our job. Cylc supports the
following :term:`batch systems <batch system>`:

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
  * The :term:`job host` becoming un-available.
  * The :term:`batch system` rejecting the job due to system load.

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

   .. rubric:: In this practical we will further develop the runtime of the
      weather forecasting suite from the previous section.

   #. **Upgrade The Forecast Task.**

      * Change executable to one which actually does something.
      * Add some environment variables.
      * Add an execution time limit
      * Add some retries

   #. **Add a visualisation task?**

   #. **Run, Stop and Restart The Suite.**
