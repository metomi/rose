Glossary
========

.. glossary::
   :sorted:

   Rose configuration
      Rose configurations are directories containing a Rose configuration
      file along with other optional files and directories.

      The two types of Rose configuration relevant to Cylc workflows are:

      * :term:`Rose application configuration`
      * :term:`Rose suite configuration`

      See also:

      * :ref:`Rose Configuration Format`
      * :ref:`Rose Configuration Tutorial <tutorial-rose-configurations>`
      * :ref:`Optional Configuration Tutorial
        <rose-tutorial-optional-configurations>`

   Rose app
   Rose application
   Rose application configuration
      A Rose application configuration (or Rose app) is a directory containing
      a :rose:file:`rose-app.conf` file along with some other optional files
      and directories.

      An application can configure:

      * The command to run (:rose:conf:`rose-app.conf[command]`).
      * Any environment variables to provide it with
        (:rose:conf:`rose-app.conf[env]`)
      * Input files e.g. namelists (:rose:conf:`rose-app.conf[namelist:NAME]`)
      * Metadata for the application (:rose:file:`rose-meta.conf`).

      See also:

      * :ref:`Rose Applications`

   application directory
      The application directory is the folder in which the
      :rose:file:`rose-app.conf` file is located in a :term:`Rose application
      configuration`.

   Rose built-in application
      A Rose built-in application is a generic :term:`Rose application`
      providing common functionality which is provided in the Rose installation.

      See also:

      * :ref:`Rose Built-In Applications`

   Rose suite configuration
      A Rose suite configuration is a :rose:file:`rose-suite.conf` file along
      with other optional files and directories which configure the way in
      which a :term:`workflow` is run. E.g:

      * Jinja2 variables to be passed into the ``flow.cylc`` file (
        :rose:conf:`rose-suite.conf[jinja2:suite.rc]`).
      * Environment variables to be provided to ``cylc play`` (
        :rose:conf:`rose-suite.conf[env]`).
      * Installation configuration (e.g.
        :rose:conf:`rose-suite.conf[file:NAME]`).

      See also:

      * :ref:`Rose Suites`

   metadata
   Rose metadata
      Rose metadata provides information about settings in
      :term:`Rose application configurations <Rose application configuration>`
      and :term:`Rose suite configurations <Rose suite configuration>`. This
      information is stored in a :rose:file:`rose-meta.conf` file in a
      ``meta/`` directory alongside the configuration it applies to.

      This information can include:

      * Documentation and help text, e.g.
        :rose:conf:`rose-meta.conf[SETTING]title`
        provides a short title to describe a setting.
      * Information about permitted values for the setting, e.g.
        :rose:conf:`rose-meta.conf[SETTING]type` can be used to specify the
        data type a setting requires (integer, string, boolean, etc).
      * Settings affecting how the configurations are displayed in
        :ref:`command-rose-config-edit` (e.g.
        :rose:conf:`rose-meta.conf[SETTING]sort-key`).
      * Metadata which defines how settings should behave in different states
        (e.g. :rose:conf:`rose-meta.conf[SETTING]trigger`).

      This information is used for:

      * Presentation and validation in the :ref:`command-rose-config-edit`
        GUI.
      * Validation using the :ref:`command-rose-macro` command.

      Metadata does not affect the running of an
      :term:`application <Rose app>` or :term:`workflow`.

      See also:

      * :ref:`Metadata`

   Rosie Suite
      A Rosie suite is a :term:`Rose suite configuration` which is managed
      using the Rosie system.

      When a suite is managed using Rosie:

      * The :term:`run directory` is added to version control.
      * The suite is registered in a database.

      See also:

      * :ref:`Rosie Tutorial <tutorial-rosie>`
