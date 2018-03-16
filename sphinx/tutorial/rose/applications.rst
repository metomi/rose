.. include:: ../../hyperlinks.rst
   :start-line: 1

Rose Applications
=================

The cylc ``suite.rc`` file allows us to define environment variables for use by
:term:`tasks <task>` e.g:

.. code-block:: cylc

   [runtime]
       [[hello_world]]
           script = echo "Hello ${WORLD}!"
           [[[environment]]]
               WORLD = Earth

As a task grows in complexity it could require:

* More environment variables.
* Input files.
* Scripts and libraries.

A rose application or rose app is a runnable :term:`rose configuration` which
executes a defined commmand.

Rose applications provide a convenient way to encapsulate all of this
configuration, storing it all in one place to make it easier to handle and
maintain.


.. _Rose Configurations:

Rose Configurations
-------------------

Rose configurations are directories containing a rose configuration file along
with other optional files and directories.

All rose configuration files use the same format which is based on the `INI`_
file format.

* Comments start with a ``#`` character.
* Settings are written as ``key=value`` pairs.
* Sections are written inside square brackets i.e. ``[section-name]``

Unlike the :ref:`cylc file format <cylc file format>`:

* Sections cannot be nested.
* Settings should not be indented.
* Comments must start on a new line (i.e. you cannot have inline comments).
* There should not be spaces around the ``=`` operator in a ``key=value`` pair.

.. code-block:: rose

   # Comment.
   setting=value

   [section]
   key=value
   multi-line-setting=multi
                     =line
                     =value

Throughout this tutorial we will refer to settings in the following format:

* ``file`` - would refer to a rose configuration file.
* ``file|setting`` - would refer to a setting in a rose configuration file.
* ``file[section]`` - would refer to a section in a rose configuration file.
* ``file[section]setting`` - would refer to a setting in a section in a rose
  configuration file.


Application Configurations
--------------------------

An application configuration is a directory containing a
:rose:file:`rose-app.conf` file. Application configurations are also refered to
as applications or apps.

The command to execute when the application is run is defined using the
:rose:conf:`rose-app.conf[command]default` setting e.g:

.. code-block:: rose

   [command]
   default=echo "Hello ${WORLD}!"

Environment variables are specified inside the :rose:conf:`rose-app.conf[env]`
section e.g:

.. code-block:: rose

   [env]
   WORLD=Earth

Scripts and executables can be placed in a ``bin/`` directory, they will be
automatically added to the ``PATH`` environment variable when the application
is run e.g.:

.. code-block:: bash
   :caption: bin/hello

   echo "Hello ${WORLD}!"

.. code-block:: rose
   :caption: rose-app.conf

   [command]
   default=hello

Any static input files can be placed in the ``file/`` directory.

An application can be run using the :ref:`command-rose-app-run` command:

.. code-block:: console

   $ rose app-run -q
   Hello Earth!


.. _rose-applications-practical:

.. practical::

   .. rubric:: In this practical we will convert the ``forecast`` task from the
      :ref:`weather-forecasting suite <tutorial-datetime-cycling-practical>`
      into a rose application.

   Create a directory on your filesystem called ``rose-tutorial``::

      mkdir ~/rose-tutorial
      cd ~/rose-tutorial

   #. **Create a rose application**

      Create a new directory called ``forecast``, this is to be our
      :term:`application directory`::

         mkdir application-tutorial
         cd application-tutorial

   #. **Move the required resources into the** ``forecast`` **application.**

      The ``forecast`` application requires three resources.

      * The ``bin/forecast`` script
      * The ``lib/python/util.py`` python library
      * The ``lib/template/map.html`` html template.

      Rather than leaving these resources scattered throughout the
      :term:`suite directory` we can encapsulate them into the ``forecast``
      application directory.

      Copy the ``forecast`` script and ``util.py`` library into the ``bin/``
      directory by running::

         rose tutorial forecast-script bin

      These file will be automatically added to the ``PATH`` when the
      application is run.

      Copy the html template into the ``file/`` directory by running::

         rose tutorial map-template file

   #. **Create the** :rose:file:`rose-app.conf` **file.**

      The :rose:file:`rose-app.conf` file needs to define the command to run.
      Create a :rose:file:`rose-app.conf` file containing the following:

      .. code-block:: rose

         [command]
         default=forecast $INTERVAL $N_FORECASTS

      The ``INTERVAL`` and ``N_FORECASTS`` environment variables need to be
      defined, to do this add an :rose:conf:`rose-app.conf[env]` section:

      .. code-block:: rose

         [env]
         # The interval between forecasts.
         INTERVAL=60
         # The number of forecasts to run.
         N_FORECASTS=5

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

      We will now move these into the application. This way all of the
      configuration speciffic to the forecast application lives within it.

      Add the following lines to the :rose:conf:`rose-app.conf[env]` section:

      .. code-block:: rose

         # The weighting to give to the wind file from each WIND_CYCLE
         # (should add up to 1).
         WEIGHTING=1
         # List of cycle points to get wind data from.
         WIND_CYCLES=0
         # Path to the wind files. {cycle}, {xy} will get filled in by the
         # forecast script
         WIND_FILE_TEMPLATE=test-data/wind_{cycle}_{xy}.csv
         # Path to the rainfall file.
         RAINFALL_FILE=test-data/rainfall.csv
         # The path to create the html map in.
         MAP_FILE=map.html
         # The path to the html map template file.
         MAP_TEMPLATE=map-template.html

      To start with we will run this application with test data outside of a
      suite so the ``WIND_FILE_TEMPLATE`` and ``RAINFALL_FILE`` environment
      variables have been set to point at files in the ``test-data`` directroy
      which we will create in the next step.

      To make this application work outside of a suite we will also need to
      provide the ``DOMAIN`` and ``RESOLUTION`` environment variables defined
      in the ``[runtime][root][environment]`` section of the ``suite.rc``
      file. Add the following lines to the :rose:file:`rose-app.conf`:

      .. code-block:: rose

         # The dimensions of each grid cell in degrees.
         RESOLUTION = 0.2
         # The area to generate forecasts for (lng1, lat1, lng2, lat2)
         DOMAIN = -12,48,5,61

   #. **Copy the test data.**

      Copy the test data files into the ``file/`` directory by running::

         rose tutorial test-data file/test-data

   #. **Run the application.**

      All of the scripts, libraries, files and environment variables required
      to make a forecast are now all provided inside this application directory.

      We should now be able to run the application. :ref:`command-rose-app-run`
      will run an application in the current directory so it is a good idea to
      move somewhere else before calling the command.

      Create a directory and run the application in it::

         mkdir run
         cd run
         rose app-run -C ../

      The ``-C`` argument to :ref:`command-rose-app-run` provides the path to
      the application directory.

      The application should run successuly leaving behind some files. Try
      opening the ``map.html`` file.
