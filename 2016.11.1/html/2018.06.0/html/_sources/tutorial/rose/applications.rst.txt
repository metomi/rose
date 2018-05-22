.. include:: ../../hyperlinks.rst
   :start-line: 1


.. _tutorial-rose-applications:

Rose Applications
=================

.. ifnotslides::

   The Cylc ``suite.rc`` file allows us to define environment variables for
   use by :term:`tasks <task>` e.g:

.. slide:: Cylc Task Environment
   :level: 2
   :inline-contents: True

   .. code-block:: cylc

      [runtime]
          [[hello_world]]
              script = echo "Hello ${WORLD}!"
              [[[environment]]]
                  WORLD = Earth

.. slide:: Cylc Task Environment
   :level: 2
   :inline-contents: True

   As a task grows in complexity it could require:

   * More environment variables.
   * Input files.
   * Scripts and libraries.

.. slide:: Cylc Task Environment
   :level: 2
   :inline-contents: True

   A Rose application or "Rose app" is a runnable :term:`Rose configuration`
   which executes a defined commmand.

   Rose applications provide a convenient way to encapsulate all of this
   configuration, storing it all in one place to make it easier to handle and
   maintain.


.. _Application Configuration:

Application Configuration
-------------------------

.. ifnotslides::

   An application configuration is a directory containing a
   :rose:file:`rose-app.conf` file. Application configurations are also
   refered to as "applications" or "apps".

   The command to execute when the application is run is defined using the
   :rose:conf:`rose-app.conf[command]default` setting e.g:

.. ifslides::

   Specify the command to execute:

.. code-block:: rose

   [command]
   default=echo "Hello ${WORLD}!"

.. ifnotslides::

   Environment variables are specified inside the
   :rose:conf:`rose-app.conf[env]` section e.g:

.. ifslides::

   Specify environment variables:

.. code-block:: rose

   [env]
   WORLD=Earth

.. nextslide::

.. ifnotslides::

   Scripts and executables can be placed in a ``bin/`` directory. They will be
   automatically added to the ``PATH`` environment variable when the application
   is run, e.g.:

.. ifslides::

   The ``bin/`` directory:

.. code-block:: bash
   :caption: bin/hello

   echo "Hello ${WORLD}!"

.. code-block:: rose
   :caption: rose-app.conf

   [command]
   default=hello

Any static input files can be placed in the ``file/`` directory.


Running Rose Applications
-------------------------

An application can be run using the :ref:`command-rose-app-run` command:

.. code-block:: console

   $ rose app-run -q  # -q for quiet output
   Hello Earth!

.. ifnotslides::

   The Rose application will by default run in the current directory so it is a
   good idea to run it outside of the :term:`application directory` to keep run
   files separate, using the  ``-C`` option to provide the path to the
   application:

.. code-block:: console

   $ rose app-run -q -C path/to/application
   Hello Earth!

.. nextslide::

.. ifslides::

   .. rubric:: In this practical we will convert the ``forecast`` task from the
      :ref:`weather-forecasting suite <tutorial-datetime-cycling-practical>`
      into a Rose application.

   Next section: :ref:`tutorial-rose-metadata`


.. _rose-applications-practical:

.. practical::

   .. rubric:: In this practical we will convert the ``forecast`` task from the
      :ref:`weather-forecasting suite <tutorial-datetime-cycling-practical>`
      into a Rose application.

   Create a directory on your filesystem called ``rose-tutorial``::

      mkdir ~/rose-tutorial
      cd ~/rose-tutorial

   #. **Create a Rose application**

      Create a new directory called ``application-tutorial``, this is to be our
      :term:`application directory`::

         mkdir application-tutorial
         cd application-tutorial

   #. **Move the required resources into the** ``application-tutorial``
      **application.**

      The application requires three resources:

      * The ``bin/forecast`` script.
      * The ``lib/python/util.py`` Python library.
      * The ``lib/template/map.html`` HTML template.

      Rather than leaving these resources scattered throughout the
      :term:`suite directory` we can encapsulate them into the
      application directory.

      Copy the ``forecast`` script and ``util.py`` library into the ``bin/``
      directory by running::

         rose tutorial forecast-script bin

      These files will be automatically added to the ``PATH`` when the
      application is run.

      Copy the HTML template into the ``file/`` directory by running::

         rose tutorial map-template file

   #. **Create the** :rose:file:`rose-app.conf` **file.**

      The :rose:file:`rose-app.conf` file needs to define the command to run.
      Create a :rose:file:`rose-app.conf` file directly inside the
      :term:`application directory` containing the following:

      .. code-block:: rose

         [command]
         default=forecast $INTERVAL $N_FORECASTS

      The ``INTERVAL`` and ``N_FORECASTS`` environment variables need to be
      defined. To do this add a :rose:conf:`rose-app.conf[env]` section
      to the file:

      .. code-block:: rose

         [env]
         # The interval between forecasts.
         INTERVAL=60
         # The number of forecasts to run.
         N_FORECASTS=5

   #. **Copy the test data.**

      For now we will run the ``forecast`` application using some sample data
      so that we can run it outside of the weather forecasting suite.

      The test data was gathered in November 2017.

      Copy the test data files into the ``file/`` directory by running::

         rose tutorial test-data file/test-data

   #. **Move environment variables defined in the** ``suite.rc`` **file.** 

      In the ``[runtime][forecast][environment]`` section of the ``suite.rc``
      file in the
      :ref:`weather-forecasting suite <tutorial-datetime-cycling-practical>`
      we set a few environment variables:

      * ``WIND_FILE_TEMPLATE``
      * ``WIND_CYCLES``
      * ``RAINFALL_FILE``
      * ``MAP_FILE``
      * ``MAP_TEMPLATE``

      We will now move these into the application. This way, all of the
      configuration specific to the application live within it.

      Add the following lines to the :rose:conf:`rose-app.conf[env]` section:

      .. code-block:: rose

         # The weighting to give to the wind file from each WIND_CYCLE
         # (comma separated list, values should add up to 1).
         WEIGHTING=1
         # Comma separated list of cycle points to get wind data from.
         WIND_CYCLES=0
         # Path to the wind files. {cycle}, {xy} will get filled in by the
         # forecast script.
         WIND_FILE_TEMPLATE=test-data/wind_{cycle}_{xy}.csv
         # Path to the rainfall file.
         RAINFALL_FILE=test-data/rainfall.csv
         # The path to create the HTML map in.
         MAP_FILE=map.html
         # The path to the HTML map template file.
         MAP_TEMPLATE=map-template.html

      Note that the ``WIND_FILE_TEMPLATE`` and ``RAINFALL_FILE`` environment
      variables are pointing at files in the ``test-data`` directory.

      To make this application work outside of the weather forecasting suite
      we will also need to
      provide the ``DOMAIN`` and ``RESOLUTION`` environment variables defined
      in the ``[runtime][root][environment]`` section of the ``suite.rc``
      file as well as the ``CYLC_TASK_CYCLE_POINT`` environment variable
      provided by Cylc when it runs a task.

      Add the following lines to the :rose:file:`rose-app.conf`:

      .. code-block:: rose

         # The date when the test data was gathered.
         CYLC_TASK_CYCLE_POINT=20171101T0000Z
         # The dimensions of each grid cell in degrees.
         RESOLUTION=0.2
         # The area to generate forecasts for (lng1, lat1, lng2, lat2).
         DOMAIN=-12,48,5,61

   #. **Run the application.**

      All of the scripts, libraries, files and environment variables required
      to make a forecast are now provided inside this application directory.

      We should now be able to run the application.

      :ref:`command-rose-app-run` will run an application in the current
      directory so it is a good idea to move somewhere else before calling
      the command. Create a directory and run the application in it::

         mkdir run
         cd run
         rose app-run -C ../

      The application should run successfully, leaving behind some files. Try
      opening the ``map.html`` file in a web browser.
