Rose Configuration API
======================


CLI
---

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

Python
------

Rose provides a Python API for loading, processing, editing and dumping Rose
configurations via the :py:mod:`rose.config` module located within the Rose
Python library.

.. automodule:: rose.config
   :members:
