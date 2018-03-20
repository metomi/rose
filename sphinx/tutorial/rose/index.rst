 .. include:: ../../hyperlinks.rst
    :start-line: 1

Rose Tutorial
=============

.. _What Is Rose:

What Is Rose?
-------------

Rose is a system for creating, editing and running rose configurations.

Rose also contains other optional tools for:

* Version control.
* Suite discovery and management.
* Validating and tranforming rose configurations.
* Tools for interfacing with cylc.


What Is A Rose Configuration?
-----------------------------

:term:`rose configurations <rose configuration>` are directories containing a
rose configuration file along with other optional assets which define behaviour
such as:

* Executables.
* File installation.
* Environment variables.

Rose configurations may be used standalone or alternatively in combination with
the `cylc`_ workflow engine. There are two types of rose configuration for use
with `cylc`_:

:term:`rose application configuration`
   A runnable rose configuration which executes a defined command.
:term:`rose suite configuration`
   A rose configuration designed to run :term:`cylc suites <cylc suite>`.
   For instance it may be used to define Jinja2 variables for use in the
   ``suite.rc`` file.


Why Use Rose Configurations?
----------------------------

With rose configurations the inputs and environment required for a particular
purpose can be encapsulated in a simple human-readable configuration.

Configuration settings can have metadata associated with them which may be used
for multiple purposes including automatic checking and transforming.

Rose configurations can be edited either using a text editor or with
the :ref:`command-rose-config-edit` GUI which makes use of metadata for display
and on-the-fly validation purposes.

.. TODO - add rose edit screenshot.

.. TODO - rename rose config-edit to rose edit.


.. toctree::
   :name: rose-tutorial
   :caption: Contents
   :maxdepth: 1

   applications
   metadata
   furthertopics/index
