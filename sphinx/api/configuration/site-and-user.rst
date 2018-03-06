.. _Site And User Configuration:

Site And User Configuration
---------------------------

Aspects of some Rose utilities can be configured per installation via the
site configuration file and per user via the user configuration file. Any
configuration in the site configuration overrides the default, and any
configuration in the user configuration overrides the site configuration and
the default. Rose expects these files to be in the modified INI format
described above. Rose utilities search for its site configuration at
``$ROSE_HOME/etc/rose.conf`` where ``$ROSE_HOME/bin/rose`` is the location of
the ``rose`` command, and they search for the user configuration at
``$HOME/.metomi/rose.conf`` where ``$HOME`` is the home directory of the
current user.

.. note::
   Allowed settings in the site and user configuration files will be
   documented in a future version of this document. In the mean time, the
   settings are documented as comments in the ``etc/rose.conf.example``
   file of each distribution of Rose.

You can also override many internal constants of the ``rose config edit`` and
``rosie go``. To change the keyboard shortcut of the ``Find Next`` action in
the config editor to ``F3``, put the following lines in your user config file,
and the setting will apply the next time you run ``rose config-edit``:

.. code-block:: rose

   [rose-config-edit]
   accel-find-next=F3

.. rose:file:: rose.conf

   TODO - The API!

   .. rose:conf:: meta-path

      TODO

   .. rose:conf:: [rosie-id]

      TODO

   .. rose:conf:: [rosie-db]

      TODO

   .. rose:conf:: [rosie-ws]

      TODO

   .. rose:conf:: rose-stem

      TODO

      .. rose:conf:: automatic-options

         TODO