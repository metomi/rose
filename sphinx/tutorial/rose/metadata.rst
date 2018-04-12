.. _tutorial-rose-metadata:

Rose Metadata
=============

Metadata can be used to provide information about settings in rose
configurations. It is used for:

* Documenting settings.
* Performing automatic checking (e.g. type checking).
* Formatting the :ref:`command-rose-config-edit` GUI.

Metadata can be used to ensure that configurations are valid before they are
run and to assist those who are edit the configurations.


The Metadata Format
-------------------

Metadata is written in a :rose:file:`rose-meta.conf` file. This file can either
be stored inside a rose configuration in a ``meta/`` directory, or elsewhere
outside of the configuration.

The :rose:file:`rose-meta.conf` file uses the standard 
:ref:`Rose configuration format <tutorial-rose-configurations>`.

The metadata for a setting is written in a section named ``section=setting``
where ``setting`` is the name of the setting and ``section`` is the section to
which the setting belongs (leave blank if the setting does not belong to
a section).

For example take the following application configuration.

.. code-block:: rose
   :caption: rose-app.conf

   [command]
   default=echo "Hello ${WORLD}."

   [env]
   WORLD=Earth

If we were to write metadata for ``WORLD`` environment variable we
would create a section called ``[env=WORLD]``.

.. code-block:: rose
   :caption: meta/rose-meta.conf

   [env=WORLD]
   title=The name of the world to say hello to.
   values=Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune

This example gives the ``WORLD`` variable a title and a list of allowed values.


Metadata Commands
-----------------

The :ref:`command-rose-metadata-check` command can be used to check that
metadata is valid::

   rose metadata-check -C meta/

The configuration can be tested against the metadata using the
:ref:`command-rose-macro` command::

   rose macro -V

For example if we were to change the value of ``WORLD`` to ``Pluto`` then
``rose macro -V`` would return the following error message:

.. code-block:: none

   Value Pluto not in allowed values ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']


Metadata Items
--------------

There are many metadata items, here are some of the commonly used ones:

``title``
   Assign a title to the setting.
``description``
   Attach a short description to a setting.
``type``
   Specify the data type a setting expects, e.g. ``type=integer``.
``length``
   Specify the length of comma separated lists e.g. ``length=:`` for a
   limitless list.
``range``
   Specify numerical bounds for the value of a setting e.g. ``range=1, 10``
   for a value between 1 and 10.

For a full list of metadata items see :rose:conf:`rose-meta.conf[SETTING]`.


.. practical::

   .. rubric:: In this practical we will write metadata for the forecast app we
      wrote in the :ref:`rose application practical
      <rose-applications-practical>`.

   #. **Create the** ``forecast`` **app.**

      Create a new copy of the ``forecast`` app by running::

         rose tutorial metadata-tutorial ~/rose-tutorial/metadata-tutorial
         cd ~/rose-tutorial/metadata-tutorial

   #. **View the application in** :ref:`command-rose-config-edit`.

      The :ref:`command-rose-config-edit` command opens a GUI which displays
      rose configurations. Open the ``forecast`` app::

         rose config-edit &

      .. tip::

         Note :ref:`command-rose-config-edit` searches for rose configuration in
         the current directory, use the ``-C`` option to specify a directory.

      In the panel on the left you will see the different sections of the
      :rose:file:`rose-app.conf` file.

      Click on :guilabel:`env`, here you will find all of the environment
      variables. Each setting will have a hash symbol ``#`` next to its name,
      these are the comments defined in the :rose:file:`rose-app.conf` file.
      Hover the mouse over the hash to reveal the comment.

      Keep the :ref:`command-rose-config-edit` window open as we will use it
      throughout the rest of this practical.

   #. **Descriptions.**

      Now we will start writing some metadata.

      Create a ``meta/`` directory containing a :rose:file:`rose-meta.conf`
      file::

         mkdir meta
         touch meta/rose-meta.conf

      In the :rose:file:`rose-app.conf` file there are comments associated with
      each setting. Take these comments out of the :rose:file:`rose-app.conf`
      file and add them as descriptions in the metadata.

      E.g. for the ``INTERVAL`` environment variable we could create a metadata
      entry that looks like this:

      .. code-block:: rose

         [env=INTERVAL]
         description=The interval between forecasts.

      Longer settings can be split over multiple lines like so:

      .. code-block:: rose

         [env=INTERVAL]
         description=The interval
                    =between forecasts.

      Once you have finished save your work and validate the metadata using
      :ref:`command-rose-metadata-check`::

         rose metadata-check -C meta/
      
      Next reload the metadata in the :ref:`command-rose-config-edit` window
      using the :menuselection:`Metadata --> Refresh Metadata` menu item.
      The descriptions should now display under each environment variable.

      .. tip::

         If you don't see the description for a setting it is possible that you
         miss-spelt the name of the setting in the section heading.

   #. **Length.**

      The ``DOMAIN`` and ``WEIGHTING`` settings both accept comma separated
      lists of values. We can represent this in rose metadata using the
      :rose:conf:`rose-meta.conf[SETTING]length` setting.

      To represent the ``DOMAIN`` setting as a list of four elements add the
      following to the ``[env=DOMAIN]`` section:

      .. code-block:: rose

         length=4

      The ``WEIGHTING`` and ``WIND_CYCLES`` settings are different as we don't
      know how many items they will contain. For flexible lists we use a colon,
      add the following line to the ``[env=WEIGHTING]`` and
      ``[env=WIND_CYCLES`` sections:

      .. code-block:: rose

         length=:

      Validate the metadata::

         rose metadata-check -C meta/

      Refresh the metadata in the :ref:`command-rose-config-edit` window be
      selecting :menuselection:`Metadata --> Refresh Metadata`.
      The three settings we have edited should now appear as lists.

   #. **Types.**

      Next we will add type information to the metadata.

      The ``INTERVAL`` setting accepts an integer value. Add the following line
      to the ``[env=INTERVAL]`` section to enforce this:

      .. code-block:: rose

         type=integer

      Validate the metadata and refresh the :ref:`command-rose-config-edit`
      window. The ``INTERVAL`` setting should now appear as an integer
      rather than a text field.

      In the :ref:`command-rose-config-edit` window try changing the value of
      ``INTERVAL`` to a string, it shouldn't let you.

      Add similar ``type`` entries for the following settings:

      .. note that :align: center does not work with the `table` directive
         see https://github.com/sphinx-doc/sphinx/issues/3942

      ====================  =========================
      ``integer`` settings  ``real`` (float) settings
      ====================  =========================
      ``INTERVAL``          ``WEIGHTING``
      ``N_FORECASTS``       ``RESOLUTION``
      ====================  =========================

      Validate the metadata to check for errors.

      In the :ref:`command-rose-config-edit` window try changing the value of
      ``RESOLUTION`` to a string, it should be marked as an error.

   #. **Values.**

      We will now add a new input to our application called ``SPLINE_LEVEL``.
      This is a science setting used to determine the interpolation method
      used on the rainfall data. It accepts the following values

      * ``0`` - for nearest member interpolation.
      * ``1`` - for linear interpolation.

      Add this setting to the :rose:file:`rose-app.conf` file:

      .. code-block:: rose

         [env]
         SPLINE_LEVEL=0

      We can ensure that users stick to allowed values using the ``values``
      metadata item. Add the following to the :rose:file:`rose-meta.conf` file:

      .. code-block:: rose

         [env=SPLINE_LEVEL]
         values=0,1

      Validate the metadata.

      As we have made a change to the configuration (by editing the
      :rose:file:`rose-app.conf` file) we will need to close and reload
      the :ref:`command-rose-config-edit` GUI.
      The setting should appear as a radio-button with the options ``0`` and
      ``1``.

      Unfortunately ``0`` and ``1`` are not particularly descriptive, it might
      not be obvious that they mean "nearest" and "linear" respectively. The
      :rose:conf:`rose-meta.conf[SETTING]value-titles` metadata item can be
      used to add titles to such settings to make the values clearer.

      Add the following lines to the ``[env=SPLINE_LEVEL]`` section in the
      :rose:file:`rose-meta.conf` file:

      .. code-block:: rose

         value-titles=Nearest,Linear

      Validate the metadata and refresh the :ref:`command-rose-config-edit`
      window.
      The ``SPLINE_LEVEL`` options should now have titles which better convey
      the meaning of the options.

      .. tip::

         The :rose:conf:`rose-meta.conf[SETTING]value-hints` metadata option 
         can be used to provide a longer description of each option.

   #. **rose macro.**

      On the command line :ref:`command-rose-macro` can be used to check that
      the configuration is compliant with the metadata.
      Try editing the :rose:file:`rose-app.conf` file to introduce errors
      then validating the configuration by running::

         rose macro -V

      .. TODO - link / reference more information on rose macros.
