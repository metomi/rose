.. _Rose Built-In Applications:

Rose Built-In Applications
==========================

Rose contains a few built-in applications providing common functionality.

These applications can be run using :ref:`command-rose-task-run` or
:ref:`command-rose-app-run`.

To use a built-in application, add the :rose:conf:`rose-app.conf|mode=KEY`
setting in the application configuration, where ``KEY`` is the name of the
built-in application. For example to use the :rose:app:`rose_prune` built-in
application:

.. code-block:: rose
   :caption: rose-app.conf

   mode=rose_prune
   # There may also be metadata which can be picked up using the `meta` setting.
   meta=rose_prune

A built-in application would normally behave very much like running an
external command. The key differences are normally that:

* A built-in application may use a different working directory to a Rose
  application.
* A built-in application will run some pre-defined commands or logic
  instead of a command defined in the application configuration.

.. toctree::
   :caption: Built-in applications
   :name: built-in-toc
   :maxdepth: 1
   :glob:

   built-in/*
