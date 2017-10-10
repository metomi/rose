Consolidating Configuration
===========================


Config duplication.


Families
--------

* Runtime
* Scheduling


Jinja2
------

* Repeated settings


Parameterised Tasks
-------------------

* Parameterisation


.. practical::

   .. rubric:: In this practical we will consolidate the configuration of the
      :ref`weather forecasting suite <tutorial-cylc-runtime-forecasting-suite>`
      from the previous section.

   #. **Create A New Suite.**

      To make a new copy of the forecasting suite run the following commands:

      .. code-block:: bash

         rose tutorial consolidation-tutorial
         cd ~/cylc-run/consolidation-tutorial

   #. **Move Site-Wide Settings Into The** ``root`` **Family.**

      The following three environment variables are used by multiple tasks.

      .. code-block:: none

         PYTHONPATH="$CYLC_SUITE_DEF_PATH/python_modules:$PYTHONPATH"
         RESOLUTION = 0.2
         DOMAIN = -12,48,5,61  # Do not change!

      Rather than manually adding them to each task individually we could put
      them in the ``root`` family making them accessible to all tasks.

      Add the following lines to the ``suite.rc`` file:

      .. code-block:: diff

          [runtime]
         +    [[root]]
         +        [[[environment]]]
         +            # Add the `python` directory to the PYTHONPATH.
         +            PYTHONPATH="$CYLC_SUITE_DEF_PATH/python_modules:$PYTHONPATH"
         +            # The dimensions of each grid cell in degrees.
         +            RESOLUTION = 0.2
         +            # The area to generate forecasts for (lng1, lat1, lng2, lat2)
         +            DOMAIN = -12,48,5,61  # Do not change!
         +
              [[get_observations_belmullet]]

   * Paramaterise the observations and post processing tasks (add a couple of
     new sites to each).
