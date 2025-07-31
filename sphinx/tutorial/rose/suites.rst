
.. _tutorial-rose-suites:

Rose Suite Configurations
=========================

.. note::

   The following documentation reflects installing and running a Cylc
   workflow, and assumes that you have `Cylc`_ and the
   `Cylc Rose`_ plugin installed.

   To check:

   .. code-block:: bash

      $ cylc version --long
      8.0.0 (/path/to/install)

      Plugins:
            cylc-rose       1.0.0   ~/cylc-rose
      ...

:term:`Rose application configurations <Rose application configuration>`
can be used to encapsulate the environment and resources required by a Cylc
:term:`task`.

Similarly :term:`Rose suite configurations <Rose suite configuration>` can
be used to do the same for a :term:`workflow`.


Configuration Format
--------------------

A Rose suite configuration is a Cylc :term:`source directory` containing a
:rose:file:`rose-suite.conf` file.

.. NOTE - The rose-suite.info is not mentioned here as it is really a rosie
          feature.

.. ifnotslides::

   The :rose:file:`rose-suite.conf` file is written in the same
   :ref:`format <tutorial-rose-configurations>` as the
   :rose:file:`rose-app.conf` file. Its main configuration sections are:

   :rose:conf:`rose-suite.conf[env]`
      Environment variables for use by the workflow :term:`scheduler`.
   :rose:conf:`rose-suite.conf[template variables]`
      Generic variables for use in the ``flow.cylc`` file.
   :rose:conf:`rose-suite.conf[file:NAME]`
      Files and resources to be installed in the :term:`run directory` when the
      suite is run.

   .. note::

      At Rose 2/Cylc 8, using the :rose:conf:`rose-suite.conf[template variables]`
      section is the recommended way of working. Cylc will select a templating
      language based on the hashbang line at the start of the the ``flow.cylc``
      file.

      At Rose 2019/Cylc 7, these variables were instead set in sections called

      * :rose:conf:`rose-suite.conf[jinja2:suite.rc]` is still supported
        to ease the transition to Rose 2, but should not be used for new
        suite configurations.

      * ``rose-suite.conf[empy:suite.rc]`` is no longer supported
        and should not be used. Cylc no longer uses the Empy templating
        language as of 8.4.0.

.. ifslides::

   * :rose:conf:`rose-suite.conf[env]`
   * :rose:conf:`rose-suite.conf[template variables]`
   * :rose:conf:`rose-suite.conf[file:NAME]`

.. nextslide::

.. ifnotslides::

   In the following example the template variable ``WORLD`` is set in
   the :rose:file:`rose-suite.conf` file.
   This can then be used in the ``flow.cylc`` file:

.. code-block:: rose
   :caption: rose-suite.conf

   [template variables]
   WORLD=Earth

.. code-block:: cylc
   :caption: flow.cylc

   #!jinja2
   [scheduling]
       [[graph]]
           R1 = hello_{{ WORLD }}

   [runtime]
       [[hello_{{ WORLD }}]]
           script = echo "hello {{ WORLD }}"

.. nextslide::

Using a Rose workflow configuration with Cylc 8
-----------------------------------------------

.. ifnotslides::

   .. seealso::

      This section acts to demonstrate how Cylc 8 can be used to install Rose
      configurations for Cylc workflows. It is not designed to comprehensively
      explain the usage of Cylc.

      - :ref:`cylc validate <Validation>`
      - :ref:`cylc install <Install-Workflow>`
      - :ref:`cylc play <WorkflowStartUp>`

   Rose configurations are installed alongside Cylc workflows by
   :ref:`cylc install <Install-Workflow>`, if a ``rose-suite.conf`` file is present.

.. code-block:: bash
   :caption: Using a Rose Configuration for a Cylc 8 workflow.

   # Assuming that the example above was developed in ~/cylc-src/my-workflow
   cylc validate my-workflow    # Checks that the workflow configuration is valid
   cylc install my-workflow     # Installs workflow to ~/cylc-run/my-workflow
   cylc play my-workflow        # Plays the workflow.
   cylc config my-workflow      # Look at the workflow with template vars filled in.

.. nextslide::

.. ifslides::

   .. rubric:: In this tutorial we will create a Rose Suite Configuration for
      the
      :ref:`weather-forecasting workflow<tutorial-cylc-runtime-forecasting-workflow>`.

.. _suites-practical:

.. practical::

   .. rubric:: In this tutorial we will create a Rose Suite Configuration for
      the
      :ref:`weather-forecasting workflow<tutorial-cylc-runtime-forecasting-workflow>`.

   #. **Create a new Cylc workflow**

      Create a copy of the weather-forecasting workflow by running::

         rose tutorial rose-suite-tutorial ~/cylc-src/rose-suite-tutorial
         cd ~/cylc-src/rose-suite-tutorial

      .. tip::

         If you haven't ever used Cylc 8 you may need to create the
         :term:`source directory`. (``mkdir ~/cylc-src``)

   #. **Create a Rose suite configuration**

      Create a blank :rose:file:`rose-suite.conf` file::

         touch rose-suite.conf

      You now have a Rose suite configuration. A :rose:file:`rose-suite.conf`
      file does not need to have anything in it.

      There are three things defined in the ``flow.cylc`` file which it might be
      useful to be able to configure:

      ``station``
         The list of weather stations to gather observations from.
      ``RESOLUTION``
         The spatial resolution of the forecast model.
      ``DOMAIN``
         The geographical limits of the model.

      Define these settings in the :rose:file:`rose-suite.conf` file by adding
      the following lines:

      .. code-block:: rose

         [template variables]
         station="camborne", "heathrow", "shetland", "aldergrove"
         RESOLUTION=0.2
         DOMAIN=-12,48,5,61

      Note that template variable strings must be quoted.

   #. **Write suite metadata**

      Create a ``meta/rose-meta.conf`` file and write some metadata for the
      settings defined in the :rose:file:`rose-suite.conf` file.

      * ``station`` is a list of unlimited length.
      * ``RESOLUTION`` is a "real" number.
      * ``DOMAIN`` is a list of four integers.

      .. spoiler:: Solution warning

         .. code-block:: rose

            [template variables=station]
            length=:

            [template variables=RESOLUTION]
            type=real

            [template variables=DOMAIN]
            length=4
            type=integer

      Validate the metadata::

         rose metadata-check -C meta/

      Open the :ref:`command-rose-config-edit` GUI. You should see
      :guilabel:`suite conf` in the panel on the left-hand side of the window.
      This will contain the template variables we have just defined.

   #. **Use suite variables in the** ``flow.cylc`` **file**

      Next we need to make use of these settings in the ``flow.cylc`` file.

      We need to change the ``RESOLUTION`` and ``DOMAIN`` settings in the
      ``[runtime][root][environment]`` section which would otherwise override
      the variables we have just defined in the :rose:file:`rose-suite.conf`
      file, like so:

      .. code-block:: diff

          [runtime]
              [[root]]
                  # These environment variables will be available to all tasks.
                  [[[environment]]]
                      # The dimensions of each grid cell in degrees.
         -            RESOLUTION = 0.2
         +            RESOLUTION = {{ RESOLUTION }}
                      # The area to generate forecasts for (lng1, lat1, lng2, lat2).
         -            DOMAIN = -12,48,5,61  # Do not change!
         +            DOMAIN = {{ DOMAIN | join(", ") }}

      We have written out the ``DOMAIN`` list using the `Jinja2`_ ``join``
      filter to write the commas between the list items. We can do the same
      for ``station``:

      .. code-block:: diff

          [task parameters]
             # A list of the weather stations we will be fetching observations from.
         -   station = camborne, heathrow, shetland, aldergrove
         +   station = {{ station | join(", ") }}
             # A list of the sites we will be generating forecasts for.
             site = exeter

   #. **Install the workflow**

      This workflow is not ready to play yet but you can check that it is
      valid with :ref:`cylc validate <Validation>`::

         cylc validate .

      You can then install the workflow with :ref:`cylc install <Install-Workflow>`::

         cylc install rose-suite-tutorial

      Inspect the installed workflow, which you will find in
      the :term:`run directory`, i.e::

         ~/cylc-run/rose-suite-tutorial

      You should find all the files, plus the ``log`` directory,
      contained in the run directory.


Rose Applications In Rose Suite Configurations
----------------------------------------------

.. ifnotslides::

   In Cylc workflows, Rose applications are placed in an ``app/`` directory which
   is copied across to the :term:`run directory` with the rest of the suite by
   :ref:`cylc install <Install-Workflow>` when the workflow configuration is installed.

   When we run Rose applications from within Cylc workflows we use the
   :ref:`command-rose-task-run` command rather than the
   :ref:`command-rose-app-run` command.

   When run, :ref:`command-rose-task-run` searches for an application with the
   same name as the Cylc task in the ``app/`` directory.

   The :ref:`command-rose-task-run` command also interfaces with Cylc to provide
   a few useful environment variables (see the
   :ref:`command-line reference <command-rose-task-run>` for details). The
   application will run in the :term:`work directory`, just like for a
   regular Cylc task.

   In this example the ``hello`` task will run the application located in
   ``app/hello/``:

.. ifslides::

   * :ref:`command-rose-app-run` - run an application standalone.
   * :ref:`command-rose-task-run` - run an application from a cylc task.

   The ``app/`` directory
     * Installed by :ref:`cylc install <Install-Workflow>`.
     * :ref:`command-rose-task-run` searches for applications here.

   :ref:`command-rose-task-run` runs applications in :term:`work directory`
   the same as for a cylc :term:`task`.

.. nextslide::

.. code-block:: cylc
   :caption: flow.cylc

   [runtime]
       [[hello]]
           script = rose task-run

.. code-block:: rose
   :caption: app/hello/rose-app.conf

   [command]
   default=echo "Hello World!"

.. nextslide::

.. ifnotslides::

   The name of the application to run can be overridden using the ``--app-key``
   command-line option or the :envvar:`ROSE_TASK_APP` environment variable. For
   example the ``greetings`` :term:`task` will run the ``hello``
   :term:`app <Rose app>` in the task defined below.

.. code-block:: cylc
   :caption: flow.cylc

   [runtime]
       [[greetings]]
           script = rose task-run --app-key hello

.. ifslides::

   Or alternatively using :envvar:`ROSE_TASK_APP`.


   Next section: :ref:`tutorial-rosie`


.. _task run practical:

.. practical::

   .. rubric:: In this practical we will take the ``forecast`` Rose application
      that we developed in the :ref:`Metadata Tutorial <tutorial-rose-metadata>`
      and integrate it into the weather-forecasting workflow.

   Move into the workflow source directory from the previous practical::

      cd ~/cylc-src/rose-suite-tutorial

   You will find a copy of the ``forecast`` application located in
   ``app/forecast``.

   #. **Create a test configuration for the** ``forecast`` **application.**

      The ``forecast`` application comes with test data
      (in ``file/test-date``), and is currently set up to work with
      this data.

      We will now adjust this configuration to make it work with
      real data generated by the Cylc workflow. It is useful to keep
      the ability to run the application using test data, so we won't
      delete this configuration. Instead we will move it into an
      :ref:`Optional Configuration` so that we can run the
      application in "test mode" or "live mode".

      Optional configurations are covered in more detail in the
      :ref:`Optional Configurations
      Tutorial <rose-tutorial-optional-configurations>`. For now all we need to
      know is that they enable us to store alternative configurations.

      Create an optional configuration called ``test`` inside the ``forecast``
      application::

         mkdir app/forecast/opt
         touch app/forecast/opt/rose-app-test.conf

      This optional configuration is a regular Rose configuration file. Its
      settings will override those in the :rose:file:`rose-app.conf` file if
      requested.

      .. tip::

         Take care not to confuse the ``rose-app.conf`` and
         ``rose-app-test.conf`` files used within this practical.

      Move the following environment variables from the
      ``app/forecast/rose-app.conf`` file into an ``[env]``
      section in the ``app/forecast/opt/rose-app-test.conf`` file:

      * ``WEIGHTING``
      * ``WIND_CYCLES``
      * ``WIND_FILE_TEMPLATE``
      * ``RAINFALL_FILE``
      * ``MAP_FILE``
      * ``CYLC_TASK_CYCLE_POINT``
      * ``RESOLUTION``
      * ``DOMAIN``

      .. spoiler:: Solution warning

         The ``rose-app-test.conf`` file should look like this:

         .. TODO - load this file from the tutorials directory

         .. code-block:: rose

            [env]
            WEIGHTING=1
            WIND_CYCLES=0
            WIND_FILE_TEMPLATE=test-data/wind_{cycle}_{xy}.csv
            RAINFALL_FILE=test-data/rainfall.csv
            MAP_FILE=map.html
            CYLC_TASK_CYCLE_POINT=20171101T0000Z
            RESOLUTION=0.2
            DOMAIN=-12,48,5,61

      Run the application in "test mode" by providing the option
      ``--opt-conf-key=test`` to the :ref:`command-rose-app-run` command::

         mkdir app/forecast/run
         cd app/forecast/run
         rose app-run --opt-conf-key=test -C ../
         cd ../../../

      You should see the stdout output of the Rose application. If there are
      any errors they will be marked with the ``[FAIL]`` prefix.

   #. **Integrate the** ``forecast`` **application into the suite.**

      We can now configure the ``forecast`` application to work with real data.

      We have moved the map template file (``map-template.html``) into the
      ``forecast`` application so we can delete the ``MAP_TEMPLATE``
      environment variable from the ``[runtime]forecast`` section of the
      ``flow.cylc`` file.

      Copy the remaining environment variables defined in the ``forecast``
      task within the ``flow.cylc`` file into the :rose:file:`rose-app.conf`
      file of the ``forecast`` application, replacing any values already
      specified if necessary. Remove the lines from the ``flow.cylc`` file
      when you are done.

      .. important::

         Remember, in Rose configuration files:

         * Spaces are not used around the equals (``=``) operator.
         * Ensure the environment variables are not quoted.

      The ``[env]`` section of your :rose:file:`rose-app.conf` file should now
      look like this:

      .. code-block:: rose

         [env]
         INTERVAL=60
         N_FORECASTS=5
         MAP_TEMPLATE=map-template.html
         SPLINE_LEVEL=0
         WIND_FILE_TEMPLATE=$CYLC_WORKFLOW_WORK_DIR/{cycle}/consolidate_observations/wind_{xy}.csv
         WIND_CYCLES=0, -3, -6
         RAINFALL_FILE=$CYLC_WORKFLOW_WORK_DIR/$CYLC_TASK_CYCLE_POINT/get_rainfall/rainfall.csv
         MAP_FILE=${CYLC_TASK_LOG_ROOT}-map.html

      Finally we need to change the ``forecast`` task to run
      :ref:`command-rose-task-run`. The ``[runtime]forecast`` section of the
      ``flow.cylc`` file should now look like this:

      .. code-block:: cylc

         [[forecast]]
             script = rose task-run

   #. **Make changes to the configuration.**

      Open the :ref:`command-rose-config-edit` GUI and navigate to the
      :guilabel:`suite conf > template variables` panel.

      Change the ``RESOLUTION`` variable to ``0.1``

      Navigate to the :guilabel:`forecast > env` panel.

      Edit the ``WEIGHTING`` variable so that it is equal to the following
      list of values::

         0.7, 0.2, 0.1

      .. tip::

         Click the "Add array element" button (:guilabel:`+`) to extend the
         number of elements assigned to ``WEIGHTING``.

      Finally, save these settings via :guilabel:`File > Save` in the menu.

   #. **Run the workflow.**

      Validate, install, run and examine the workflow
      (use :ref:`tutorial.gui` or :ref:`tutorial.tui`)::

         cylc validate ~/cylc-src/rose-suite-tutorial
         cylc install rose-suite-tutorial
         cylc play rose-suite-tutorial


   #. **View output in Cylc Review.**

      .. note::

         ``cylc review`` replaces the Rose Bush utility. It is a Cylc 7
         command that can view Cylc 7 and Cylc 8 workflows.

      Either navigate to your site's Cylc Review page if one has been set up, or
      start a Cylc Review server by running the following command and open
      the printed URL::

         cylc review start

      Navigate to your latest rose-suite-tutorial run and click
      the "task jobs list".
      On this page you will see the tasks run by the suite, ordered from most
      to least recent. Near the top you should see an entry for the
      ``forecast`` task. On the right-hand side of the screen click
      :guilabel:`job-map.html`.

      As this file has a ``.html`` extension Cylc Review will render it.
      The raw text would be displayed otherwise.
