.. _rose-configuration:

Rose Configuration
==================

Rose is configured by a collection of configuration files which all use the
same :ref:`Rose Configuration Format`. They are used for:

:ref:`Rose Applications`
  * :rose:file:`rose-app.conf`
:ref:`Rose Suites`
  * :rose:file:`rose-suite.conf`
  * :rose:file:`rose-suite.info`
:ref:`Site And User Configuration`
  * :rose:file:`rose.conf`
Suite/Application :ref:`Metadata`
  * :rose:file:`rose-meta.conf`

.. toctree::
   :name: configuration-toc
   :caption: More Information
   :maxdepth: 2

   configuration/rose-configuration-format
   configuration/file-creation


CLI API
-------

The :ref:`command-rose-config` command provides a command line tool for
reading, processing and dumping files written in the :ref:`Rose Configuration
Format`:

.. code-block:: console

   $ echo -e "
   > [foo]
   > bar=baz
   > " > rose.conf

   $ rose config foo --file rose.conf
   bar=baz

For more information see the :ref:`command-rose-config` command line reference.


.. _config-api:

Python API
----------

Rose provides a Python API for loading, processing, editing and dumping Rose
configurations via the :py:mod:`rose.config` module located within the Rose
Python library.

.. automodule:: rose.config
   :members:
