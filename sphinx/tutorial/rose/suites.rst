.. include:: ../../hyperlinks.rst
   :start-line: 1

Rose Suites
===========

:term:`Rose application configurations <rose application configuration>`
can be used to encapsulate the environment and resources required by a cylc
:term:`task`.

Similarly :term:`rose suite configurations <rose suite configuration>` can
be used to do the same for a :term:`cylc suite`.


Configuration Format
--------------------

A rose suite configuration is a cylc :term:`suite directory` containing a
:rose:file:`rose-suite.conf` file.

.. NOTE - The rose-suite.info is not mentioned here as it is really a rosie
          feature.

The :rose:file:`rose-suite.conf` file is written in the same
:ref:`format <tutorial-rose-configurations>` as the :rose:file:`rose-app.conf`
file. It is used to configure:

Its main configuration sections are:

:rose:conf:`rose-suite.conf[env]`
   Environment variables for use by the whole suite.
:rose:conf:`rose-suite.conf[jinja2:suite.rc]`
   `Jinja2`_ variables for use in the ``suite.rc`` file.
:rose:conf:`rose-suite.conf[file:NAME]`
   Files and resources to be installed in the :term:`run directory` when the
   suite is run.

In the following example the environment variable ``GREETING`` and the
Jinja2 variable ``WORLD`` are both set in the :rose:file:`rose-suite.conf`
file. These variables can then be used in the ``suite.rc`` file:

.. code-block:: rose
   :caption: *rose-suite.conf*

   [env]
   GREETING=Hello

   [jinja2:suite.rc]
   WORLD=Earth

.. code-block:: cylc
   :caption: *suite.rc*

   [scheduling]
      [[dependencies]]
         graph = hello_{{WORLD}}

   [runtime]
      [[hello_{{WORLD}}]]
          script = echo "$GREETING {{WORLD}}"


.. _Suite Directory Vs Run Directory:

Suite Directory Vs Run Directory
--------------------------------

:term:`suite directory`
   The directory in which the suite is written, the ``suite.rc`` and
   :rose:file:`rose-suite.conf` files live here.
:term:`run directory`
   The directory in which the suite runs, the ``work``, ``share`` and ``log``
   directories live here.

Throughout the :ref:`Cylc Tutorial` we wrote suites in the ``cylc-run``
directory. As cylc runs suites in the ``cylc-run`` directory the
:term:`suite directory` is also the :term:`run directory` i.e. the suite runs
in the same directory in which it is written.

With Rose we develop suites in a separate directory to the one in which they
run meaning that the :term:`suite directory` is separate from the
:term:`run directory`. This helps keep the suite separate from its output and
means that you can safely work on a suite and its resources whilst it is
running.

.. note::

   Using cylc it is possible to separate the :term:`suite directory` and
   :term:`run directory` using the ``cylc register`` command. Note though
   that suite resources e.g. scripts in the ``bin/`` directory will remain in
   the :term:`suite directory` so cannot safely be edited whilst the suite is
   running.


Running Rose Suite Configurations
---------------------------------

Rose :ref:`Application Configurations <Application Configuration>` are run using
:ref:`command-rose-app-run`, Rose Suite Configurations are run using
:ref:`command-rose-suite-run`.

When a suite configuration is run:

* The :term:`suite directory` is coppied into the ``cylc-run`` directory where
  it becomes the :term:`run directory`.
* Any files defined in the :rose:file:`rose-suite.conf` file are installed.
* Jinja2 variables defined in the :rose:file:`rose-suite.conf` file are added
  to the top of the ``suite.rc`` file.
* The cylc suite is run.

.. digraph:: Example
   :align: center

    graph [rankdir="LR", fontname="sanz"]
    node [fontname="sanz", shape="none"]
    edge [color="blue"]

    bgcolor="none"
    size="7,5"
    ranksep=0.75

    subgraph cluster_suite_directory {
        label="Suite Directory"
        fontsize=17
        fontname="sanz bold"
        style="dashed"
        suite_rc_suite_dir [label="suite.rc"]
        rose_suite_conf_suite_dir [label="rose-suite.conf"]
        bin_suite_dir [label="bin/"]
    }

    subgraph cluster_run_directory {
        label="Run Directory"
        fontsize=17
        fontname="sanz bold"
        style="dashed"
        suite_rc_run_dir [label="suite.rc"]
        rose_suite_conf_run_dir [label="rose-suite.conf"]
        files_run_dir [label="installed files"]
        bin_run_dir [label="bin/"]
        work [label="work/"]
        share [label="share/"]
        log [label="log/"]
    }

    jinja2 [label="Prepend Jinja2",
            shape="box",
            fontcolor="blue",
            color="blue"]
    install_files [label="Install Files",
                   shape="box",
                   fontcolor="blue",
                   color="blue"]

    suite_rc_suite_dir -> jinja2 -> suite_rc_run_dir
    rose_suite_conf_suite_dir -> jinja2 [style="dashed", arrowhead="empty"]
    rose_suite_conf_suite_dir -> rose_suite_conf_run_dir
    rose_suite_conf_suite_dir -> install_files [style="dashed",
                                                arrowhead="empty"]
    install_files -> files_run_dir
    bin_suite_dir -> bin_run_dir

Like :ref:`command-rose-app-run`, :ref:`command-rose-suite-run` will look for a
configuration to run in the current directory. The command can be run
from other locations using the ``-C`` argument::

   rose suite-run -C /path/to/suite/configuration/


Rose Applications In Rose Suite Configurations
----------------------------------------------

In cylc suites, rose applications are placed in an ``app/`` directory which
is copied across to run directory with the rest of the suite by
:ref:`command-rose-suite-run` when the suite configuration is run.

When we run rose applications in cylc suites we use the
:ref:`command-rose-task-run` command rather than the
:ref:`command-rose-app-run` command.

When run, :ref:`command-rose-task-run` searches for an application with the same
name as the cylc task in the ``app/`` directory.

The :ref:`command-rose-task-run` command also interfaces with cylc to provide
a few useful environment variables (see the
:ref:`command line reference <command-rose-task-run>` for details). The
application will run in the :term:`work directory` the same as a regular cylc
task.

In this example the ``hello`` task will run the application located in
``app/hello/``:

.. code-block:: cylc
   :caption: *suite.rc*

   [runtime]
      [[hello]]
         script = rose task-run

.. code-block:: rose
   :caption: *app/hello/rose-app.conf*

   [command]
   default=echo "Hello World!"

The name of the application to run can be overridden using the ``--app-key``
command line option or the :envvar:`ROSE_TASK_APP` environment variable. For 
example the ``greetings`` :term:`task` will run the ``hello`` :term:`app <rose
app>` in the task defined below.

.. code-block:: cylc
   :caption: *suite.rc*

   [runtime]
      [[greetings]]
         script = rose task-run --app-key hello


Start, Stop, Restart
--------------------

Under rose, suites will run using the name of the suite directory. For instance
if you run :ref:`command-rose-suite-run` on a suite in the directory
``~/foo/bar`` then it will run with the name ``bar``.

The name can be overridden using the ``--name`` option i.e:

.. code-block:: sub

   rose suite-run --name <SUITE_NAME>

Start
   Suites must be run using the :ref:`command-rose-suite-run` command which
   in turn calls the ``cylc run`` command. 
Stop
   Suites can be stopped using the ``cylc stop <SUITE_NAME>`` as for regular
   cylc suites.
Restart
   There are two options for restarting:
   
   * To pick up where the suite left off use :ref:`command-rose-suite-restart`,
     No changes will be made to the run directory. *This is usually the
     recommended option.*
   * To restart picking up changes made in the suite directory use the
     ``--restart`` option with :ref:`command-rose-suite-run`.

.. note::

   :ref:`command-rose-suite-run` installs suites to the run directory
   incrementally so if you change a file and restart the suite using
   ``rose suite-run --restart`` only the changed file will be re-installed.
   This process is strictly constructive, any files deleted in the suite
   directory will *not* be removed from the run directory. To force
   :ref:`command-rose-suite-run` to perform a complete rebuild, use the
   ``--new`` option.

.. highlight:: bash


Rose Bush
---------


.. practical::

   foo



