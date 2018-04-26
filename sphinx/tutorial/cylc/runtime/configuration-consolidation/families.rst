.. include:: ../../../../hyperlinks.rst
  :start-line: 1


.. _tutorial-cylc-families:

Families
========

:term:`Families <family>` provide a way of grouping tasks together so they can
be treated as one.


Runtime
-------

.. ifnotslides::

   :term:`Families <family>` are groups of tasks which share a common
   configuration. In the present example the common configuration is:

   .. code-block:: cylc

      script = get-observations
      [[[environment]]]
          API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb

   We define a family as a new task consisting of the common configuration. By
   convention families are named in upper case:

.. code-block:: cylc

   [[GET_OBSERVATIONS]]
       script = get-observations
       [[[environment]]]
           API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb

.. ifnotslides::

   We "add" tasks to a family using the ``inherit`` setting:

.. code-block:: cylc

   [[get_observations_heathrow]]
       inherit = GET_OBSERVATIONS
       [[[environment]]]
           SITE_ID = 3772

.. ifnotslides::

   When we add a task to a family in this way it :term:`inherits <family
   inheritance>` the configuration from the family, i.e. the above example is
   equivalent to:

.. code-block:: cylc

   [[get_observations_heathrow]]
       script = get-observations
       [[[environment]]]
           API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
           SITE_ID = 3772

.. nextslide::

.. ifnotslides::

   It is possible to override inherited configuration within the task. For
   example if we wanted the ``get_observations_heathrow`` task to use a
   different API key we could write:

.. code-block:: cylc
   :emphasize-lines: 4

   [[get_observations_heathrow]]
       inherit = GET_OBSERVATIONS
       [[[environment]]]
           API_KEY = special-api-key
           SITE_ID = 3772

.. nextslide::

.. ifnotslides::

   Using families the ``get_observations`` tasks could be written like so:

.. code-block:: cylc

   [runtime]
       [[GET_OBSERVATIONS]]
           script = get-observations
           [[[environment]]]
               API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb

   [[get_observations_heathrow]]
       inherit = GET_OBSERVATIONS
       [[[environment]]]
           SITE_ID = 3772
   [[get_observations_camborne]]
       inherit = GET_OBSERVATIONS
       [[[environment]]]
           SITE_ID = 3808
   [[get_observations_shetland]]
       inherit = GET_OBSERVATIONS
       [[[environment]]]
           SITE_ID = 3005
   [[get_observations_belmullet]]
       inherit = GET_OBSERVATIONS
       [[[environment]]]
           SITE_ID = 3976


Graphing
--------

.. ifnotslides::

   :term:`Families <family>` can be used in the suite's :term:`graph`, e.g:

.. code-block:: cylc-graph

   GET_OBSERVATIONS:succeed-all => gather_observations

.. ifnotslides::

   The ``:succeed-all`` is a special :term:`qualifier` which in this example
   means that the ``gather_observations`` task will run once *all* of the
   members of the ``GET_OBSERVATIONS`` family have succeeded. This is
   equivalent to:

.. code-block:: cylc-graph

   get_observations_heathrow => gather_observations
   get_observations_camborne => gather_observations
   get_observations_shetland => gather_observations
   get_observations_belmullet => gather_observations

.. ifnotslides::

   The ``GET_OBSERVATIONS:succeed-all`` part is referred to as a
   :term:`family trigger`. Family triggers use special qualifiers which are
   non-optional. The most commonly used ones are:

   ``succeed-all``
      Run if all of the members of the family have succeeded.
   ``succeed-any``
      Run as soon as any one family member has succeeded.
   ``finish-all``
      Run as soon as all of the family members have completed (i.e. have each
      either succeeded or failed).

   For more information on family triggers see the `Cylc User Guide`_.

.. ifslides::

   * ``succeed-all``
   * ``succeed-any``
   * ``finish-all``


The ``root`` Family
-------------------

.. ifnotslides::

   There is a special family called `root` (in lowercase) which is used only
   in the runtime to provide configuration which will be inherited by all
   tasks.

   In the following example the task ``bar`` will inherit the environment
   variable ``FOO`` from the ``[root]`` section:

.. code-block:: cylc

   [runtime]
       [[root]]
           [[[environment]]]
               FOO = foo
       [[bar]]
           script = echo $FOO


Families and ``cylc graph``
---------------------------

.. ifnotslides::

   By default, ``cylc graph`` groups together all members of a family
   in the :term:`graph`. To un-group a family right click on it and select
   :menuselection:`UnGroup`.

   For instance if the tasks ``bar`` and ``baz`` both
   inherited from ``BAR`` ``cylc graph`` would produce:

.. digraph:: Example
   :align: center

   subgraph cluster_1 {
      label = "Grouped"
      "foo.1" [label="foo"]
      "BAR.1" [label="BAR", shape="doubleoctagon"]
   }

   subgraph cluster_2 {
      label = "Un-Grouped"
      "foo.2" [label="foo"]
      "bar.2" [label="bar"]
      "baz.2" [label="baz"]
   }

   "foo.1" -> "BAR.1"
   "foo.2" -> "bar.2"
   "foo.2" -> "baz.2"

.. nextslide::

.. ifslides::

   .. rubric:: In this practical we will consolidate the configuration of the
      :ref:`weather-forecasting suite <tutorial-cylc-runtime-forecasting-suite>`
      from the previous section.

   Next section: :ref:`Jinja2 <tutorial-cylc-jinja2>`


.. _cylc-tutorial-families-practical:

.. practical::

   .. rubric:: In this practical we will consolidate the configuration of the
      :ref:`weather-forecasting suite <tutorial-cylc-runtime-forecasting-suite>`
      from the previous section.

   1. **Create A New Suite.**

      To make a new copy of the forecasting suite run the following commands:

      .. code-block:: bash

         rose tutorial consolidation-tutorial
         cd ~/cylc-run/consolidation-tutorial

      Set the intial and final cycle points as you did in the
      :ref:`previous tutorial
      <tutorial-cylc-runtime-tutorial-suite-initial-and-final-cyle-points>`.

   2. **Move Site-Wide Settings Into The** ``root`` **Family.**

      The following three environment variables are used by multiple tasks:

      .. code-block:: none

         PYTHONPATH="$CYLC_SUITE_DEF_PATH/python_modules:$PYTHONPATH"
         RESOLUTION = 0.2
         DOMAIN = -12,48,5,61  # Do not change!

      Rather than manually adding them to each task individually we could put
      them in the ``root`` family, making them accessible to all tasks.

      Add a ``root`` section containing these three environment variables.
      Remove the variables from any other task's ``environment`` sections:

      .. code-block:: diff

          [runtime]
         +    [[root]]
         +        [[[environment]]]
         +            # Add the `python` directory to the PYTHONPATH.
         +            PYTHONPATH="$CYLC_SUITE_DEF_PATH/python_modules:$PYTHONPATH"
         +            # The dimensions of each grid cell in degrees.
         +            RESOLUTION = 0.2
         +            # The area to generate forecasts for (lng1, lat1, lng2, lat2).
         +            DOMAIN = -12,48,5,61  # Do not change!

          ...

           [[consolidate_observations]]
               script = consolidate-observations
         -     [[[environment]]]
         -         # Add the `python` directory to the PYTHONPATH.
         -         PYTHONPATH="$CYLC_SUITE_RUN_DIR/lib/python:$PYTHONPATH"
         -         # The dimensions of each grid cell in degrees.
         -         RESOLUTION = 0.2
         -         # The area to generate forecasts for (lng1, lat1, lng2, lat2).
         -         DOMAIN = -12,48,5,61  # Do not change!

           [[get_rainfall]]
               script = get-rainfall
               [[[environment]]]
                   # The key required to get weather data from the DataPoint service.
                   # To use archived data comment this line out.
                   API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
         -         # Add the `python` directory to the PYTHONPATH.
         -         PYTHONPATH="$CYLC_SUITE_RUN_DIR/lib/python:$PYTHONPATH"
         -         # The dimensions of each grid cell in degrees.
         -         RESOLUTION = 0.2
         -         # The area to generate forecasts for (lng1, lat1, lng2, lat2).
         -         DOMAIN = -12,48,5,61  # Do not change!

           [[forecast]]
               script = forecast 60 5  # Generate 5 forecasts at 60 minute intervals.
               [[[environment]]]
                   # List of cycle points to process wind data from.
                   WIND_CYCLES = """
                       $CYLC_TASK_CYCLE_POINT                # The current cycle point.
                       $(cylc cyclepoint --offset-hours=-3)  # The point 3 hours ago.
                       $(cylc cyclepoint --offset-hours=-6)  # The point 6 hours ago.
                   """
                   # The cyclepoint 3 hours before the present one.
                   PT3H = $(cylc cyclepoint --offset-hours=-3)
                   # The cyclepoint 6 hours before the present one.
                   PT6H = $(cylc cyclepoint --offset-hours=-6)
         -         # Add the `python` directory to the PYTHONPATH.
         -         PYTHONPATH="$CYLC_SUITE_RUN_DIR/lib/python:$PYTHONPATH"
         -         # The dimensions of each grid cell in degrees.
         -         RESOLUTION = 0.2
         -         # The area to generate forecasts for (lng1, lat1, lng2, lat2).
         -         DOMAIN = -12,48,5,61  # Do not change!

           [[post_process_exeter]]
               # Generate a forecast for Exeter 60 minutes into the future.
               script = post-process exeter 60
         -     [[[environment]]]
         -         # Add the `python` directory to the PYTHONPATH.
         -         PYTHONPATH="$CYLC_SUITE_RUN_DIR/lib/python:$PYTHONPATH"
         -         # The dimensions of each grid cell in degrees.
         -         RESOLUTION = 0.2
         -         # The area to generate forecasts for (lng1, lat1, lng2, lat2).
         -         DOMAIN = -12,48,5,61  # Do not change!

      To ensure that the environment variables are being inherited correctly
      by the tasks, inspect the ``[runtime]`` section using ``cylc get-config``
      by running the following command:

      .. code-block:: bash

         cylc get-config . --sparse -i "[runtime]"

      You should see the environment variables from the ``[root]`` section
      in the ``[environment]`` section for all tasks.

      .. tip::

         You may find it easier to open the output of this command in a text
         editor, e.g::

            cylc get-config . --sparse -i "[runtime]" | gvim -
