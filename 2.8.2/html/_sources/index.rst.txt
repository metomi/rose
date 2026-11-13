Rose Documentation
==================

Rose is a toolkit for writing, editing and running application configurations.
:ref:`What Is Rose <Rose Tutorial>`?

.. image:: img/rose-logo.png
   :width: 250px
   :align: center

.. nextslide::

Rose uses the `Cylc`_ workflow engine for running suites of inter-dependent
applications. :ref:`What Is Cylc? <Cylc-introduction>`

.. image:: img/cylc-logo.png
   :width: 250px
   :align: center
   :target: `Cylc`_

.. nextslide::

.. ifslides::

   * :ref:`Cylc Tutorial <cylc-introduction>`
   * :ref:`Rose Tutorial <tutorial-rose-configurations>`

.. nextslide::

.. toctree::
   :caption: User Guide
   :name: tutorial-toc
   :maxdepth: 1

   installation
   getting-started
   tutorial/rose/index
   glossary


.. toctree::
   :caption: Rose API Reference
   :name: api-toc
   :maxdepth: 1
   :glob:

   api/configuration/index
   api/*


Other
-------

* :ref:`genindex`
* :ref:`terms`

.. toctree::
   :hidden:
   :name: hidden-index
   :glob:

   terms
   course/*
