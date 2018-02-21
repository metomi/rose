.. include:: hyperlinks.rst
   :start-line: 1

.. raw:: html

   <a href="https://github.com/metomi/rose"><img style="position: absolute; top: 0; right: 0; border: 0;" src="https://camo.githubusercontent.com/365986a132ccd6a44c23a9169022c0b5c890c387/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f6769746875622f726962626f6e732f666f726b6d655f72696768745f7265645f6161303030302e706e67" alt="Fork me on GitHub" data-canonical-src="https://s3.amazonaws.com/github/ribbons/forkme_right_red_aa0000.png"></a>


Rose Documentation
==================

Rose is a system for writing, editing and running application configurations.

.. TODO - Add "What Is Rose" link when written.

.. image:: img/rose-logo.png
   :width: 250px
   :align: center

Rose uses the `cylc`_ workflow engine for running suites of inter-dependent
applications. :ref:`What Is Cylc? <cylc-introduction>`

.. image:: img/cylc-logo.png
   :width: 250px
   :align: center
   :target: `cylc`_


.. toctree::
   :caption: Tutorial
   :name: tutorial-toc
   :maxdepth: 2

   tutorial/cylc/index
   tutorial/rose/index

.. toctree::
   :caption: User Guide
   :name: user-guide-toc
   :maxdepth: 1

   user-guide/installation
   user-guide/configuration
   user-guide/configuration-metadata
   glossary

.. toctree::
   :caption: Rose API Reference
   :name: api-toc
   :maxdepth: 1

   api/command-reference
   api/environment-variables
   api/config
   api/macros
   api/upgrader-macros
   api/bash
   api/gtk
   api/rosie-web


Indices
-------

* :ref:`genindex`
* :ref:`modindex`
