.. _Jinja2 Tutorial: .. http://jinja.pocoo.org/docs

.. include:: ../../../hyperlinks.rst
  :start-line: 1

Consolidating Configuration
===========================

In the last section we wrote out the following code in the ``suite.rc`` file:

.. code-block:: cylc

   [runtime]
       [[get_observations_heathrow]]
           script = get-observations
           [[[environment]]]
               SITE_ID = 3772
               API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
       [[get_observations_camborne]]
           script = get-observations
           [[[environment]]]
               SITE_ID = 3808
               API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
       [[get_observations_shetland]]
           script = get-observations
           [[[environment]]]
               SITE_ID = 3005
               API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
       [[get_observations_belmullet]]
           script = get-observations
           [[[environment]]]
               SITE_ID = 3976
               API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb

In this code the ``script`` item and the ``API_KEY`` environment variable have
been repeated for each task. This is bad practice as is makes the
configuration un-necessary complex and making changes difficult.

Likewise the graphing relating to the ``get_observations`` tasks is also
repetitive:

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           [[[T00/PT3H]]]
               graph = """
                   get_observations_belmullet => gather_observations
                   get_observations_camborne => gather_observations
                   get_observations_heathrow => gather_observations
                   get_observations_shetland => gather_observations
               """

Cylc offers three ways of consolidating configurations to help improve the
structure of your suite and avoid duplication.


The ``cylc get-config`` Command
-------------------------------

To help assist with consolidating configurations the ``cylc get-config``
command can be used to expand the ``suite.rc`` file back out into its full
form.

Call ``cylc get-config`` with the path of the suite (``.`` if you are in
the :term:`suite directory`) and the ``--sparse`` option (which hides default
values).

.. code-block:: sub

   cylc get-config <path> --sparse

To view the configuration of a particular section or setting refer to it by
name using the ``-i`` option (see :ref:`cylc file conf` for details) e.g:

.. code-block:: sub

   # Print the contents of the [scheduling] section.
   cylc get-config <path> --sparse -i '[scheduling]'
   # Print the contents of the get_observations_heathrow task.
   cylc get-config <path> --sparse -i '[runtime][get_observations_heathrow]'
   # Print the value of the script setting in the get_observations_heathrow task
   cylc get-config <path> --sparse -i '[runtime][get_observations_heathrow]script'

.. note::

   The main use for ``cylc get-config`` is for inspecting the
   ``[runtime]`` section of a suite. The ``cylc get-config`` command does not
   expand :term:`Parameterisations <parameterisation>` and
   :term:`families <family>` in the suite's :term:`graphing`. To inspect the
   graphing use the ``cylc graph`` command.


Families
--------

:term:`Families <family>` provide a way of grouping tasks together so they can
be treated as one.

Runtime
^^^^^^^

:term:`Families <family>` are groups of tasks which share a common
configuration. In this example the common configuration is:

.. code-block:: cylc

   script = get-observations
   [[[environment]]]
       API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb

We define a family as a new task consisting of the common configuration, by
convention families are named in upper case:

.. code-block:: cylc

   [[GET_OBSERVATIONS]]
       script = get-observations
       [[[environment]]]
           API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb

We "add" tasks to a family by using the ``inherit`` setting:

.. code-block:: cylc

   [[get_observations_heathrow]]
       inherit = GET_OBSERVATIONS
       [[[environment]]]
           SITE_ID = 3772

When we add a task to a family in this way it :term:`inherits <family
inheritance>` the configuration from the family i.e. the above example is
equivalent to:

.. code-block:: cylc

   [[get_observations_heathrow]]
       script = get-observations
       [[[environment]]]
           API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
           SITE_ID = 3772

It is possible to override inherited configuration within the task. For example
if we wanted the ``get_observations_heathrow`` task to use a different API key
we could write:

.. code-block:: cylc

   [[get_observations_heathrow]]
       inherit = GET_OBSERVATIONS
       [[[environment]]]
           API_KEY = special-api-key
           SITE_ID = 3772

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
^^^^^^^^

:term:`Families <family>` can be used in the suite's :term:`graphing` e.g:

.. code-block:: cylc-graph

   GET_OBSERVATIONS:succeed-all => gather_observations

The ``:succeed-all`` is a special :term:`qualifier` which in this example means
that the ``gather_observations`` task will run once **all** of the members of
the ``GET_OBSERVATIONS`` family have succeeded. This is equivalent to:

.. code-block:: cylc-graph

   get_observations_heathrow => gather_observations
   get_observations_camborne => gather_observations
   get_observations_shetland => gather_observations
   get_observations_belmullet => gather_observations

The ``GET_OBSERVATIONS:succeed-all`` part is referred to as a
:term:`family trigger`. Family triggers use special qualifiers which are
non-optional. The most commonly used ones are:

``succeed-all``
   Run if all of the members of the family have succeeded.
``succeed-any``
   Run as soon as any one family member has succeeded.
``finish-all``
   Run as soon as all of the family members have completed (i.e. have succeeded
   or failed).

For more information on family triggers see the `cylc user guide`_.

The root Family
^^^^^^^^^^^^^^^

There is a special family called `root` (lowercase) which is used only in the
runtime to provide configuration which will be inherited by all tasks.

In the following example the task ``bar`` will inherit the environment variable
``FOO`` from the ``[root]`` section:

.. code-block:: cylc

   [runtime]
       [[root]]
           [[[environment]]]
               FOO = foo
       [[bar]]
           script = echo $FOO

.. practical::

   .. rubric:: In this practical we will consolidate the configuration of the
      :ref:`weather forecasting suite <tutorial-cylc-runtime-forecasting-suite>`
      from the previous section.

   1. **Create A New Suite.**

      To make a new copy of the forecasting suite run the following commands:

      .. code-block:: bash

         rose tutorial consolidation-tutorial
         cd ~/cylc-run/consolidation-tutorial

   2. **Move Site-Wide Settings Into The** ``root`` **Family.**

      The following three environment variables are used by multiple tasks.

      .. code-block:: none

         PYTHONPATH="$CYLC_SUITE_DEF_PATH/python_modules:$PYTHONPATH"
         RESOLUTION = 0.2
         DOMAIN = -12,48,5,61  # Do not change!

      Rather than manually adding them to each task individually we could put
      them in the ``root`` family making them accessible to all tasks.

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
         +            # The area to generate forecasts for (lng1, lat1, lng2, lat2)
         +            DOMAIN = -12,48,5,61  # Do not change!

          ...

           [[consolidate_observations]]
               script = consolidate-observations
         -     [[[environment]]]
         -         # Add the `python` directory to the PYTHONPATH.
         -         PYTHONPATH="$CYLC_SUITE_RUN_DIR/lib/python:$PYTHONPATH"
         -         # The dimensions of each grid cell in degrees.
         -         RESOLUTION = 0.2
         -         # The area to generate forecasts for (lng1, lat1, lng2, lat2)
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
         -         # The area to generate forecasts for (lng1, lat1, lng2, lat2)
         -         DOMAIN = -12,48,5,61  # Do not change!

           [[forecast]]
               script = forecast 120 5  # Generate 5 forecasts at 60 minute intervals.
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
         -         # The area to generate forecasts for (lng1, lat1, lng2, lat2)
         -         DOMAIN = -12,48,5,61  # Do not change!

           [[post_process_exeter]]
               # Generate a forecast for Exeter 60 minutes in the future.
               script = post-process exeter 120
         -     [[[environment]]]
         -         # Add the `python` directory to the PYTHONPATH.
         -         PYTHONPATH="$CYLC_SUITE_RUN_DIR/lib/python:$PYTHONPATH"
         -         # The dimensions of each grid cell in degrees.
         -         RESOLUTION = 0.2
         -         # The area to generate forecasts for (lng1, lat1, lng2, lat2)
         -         DOMAIN = -12,48,5,61  # Do not change!

      To ensure that the environment variables are being inherited correctly
      by the tasks, inspect the ``[runtime]`` section using ``cylc get-config``
      by running the following command:

      .. code-block:: bash

         cylc get-config . --sparse -i "[runtime]"

      You should see the environment variables from the ``[root]`` section
      in the `[environment]` section for all tasks.


Jinja2
------

`Jinja2`_ is a templating language often used in web-design with some
similarities with python. It can be used to make your suite definition more
dynamic.

The Jinja2 Language
^^^^^^^^^^^^^^^^^^^

In Jinja2 statements are wrapped with ``{%`` characters i.e:

.. code-block:: none

   {% ... %}

Variables are initiated using the ``set`` statement e.g:

.. code-block:: none

   {% set foo = 3 %}

Expressions wrapped with ``{{`` characters will be replaced with the value of
the evaluation of the expression e.g:

.. code-block:: none

   foo {{ foo }} foo

Would result in::

   foo 3 foo

Loops are written with ``for`` statements e.g:

.. code-block:: none

   {% for x in range(foo) %}
      foo {{ x }}
   {% endfor %}

Would result in:

.. code-block:: none

      foo 0
      foo 1
      foo 2

To enable Jinja2 in the ``suite.rc`` file add the following shebang at the top
of the file:

.. code-block:: none

   #!Jinja2

For more information see the `Jinja2 Tutorial`_.

Example
^^^^^^^

To consolidate the configuration for the ``get_observations`` tasks we could
define a dictionary of station, id pairs:

.. code-block:: none

   {% set stations = {'belmullet: 3976,
                      'camborne': 3808,
                      'heathrow': 3772,
                      'shetland': 3005} %}

We could then loop over the stations like so:

.. code-block:: none

   {% for station in stations %}
       {{ station }}
   {% endfor %}

Which would result in:

.. code-block:: none

       belmullet
       camborne
       heathrow
       shetland

We could loop over both station and ids like so:

.. code-block:: none

   {% for station, id in stations.items() %}
       {{ station }} - {{ id }}
   {% endfor %}

Which would result in:

.. code-block:: none

       belmullet - 3976
       camborne - 3808
       heathrow - 3772
       shetland - 3005

Putting this all together the ``get_observations`` configuration could be
written like so:

.. code-block:: cylc

   #!Jinja2

   {% set stations = {'belmullet: 3976,
                      'camborne': 3808,
                      'heathrow': 3772,
                      'shetland': 3005} %}

   [scheduling]
       [[dependencies]]
           [[[T00/PT3H]]]
               graph = """
   {% for station in stations %}
                  get_observations_{{station}} => gather_observations
   {% endfor %}
               """

   [runtime]
   {% for station, id in stations.items() %}
       [[get_observations_{{station}}]]
           script = get-observations
           [[[environment]]]
               SITE_ID = {{ id }}
               API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
   {% endfor %}

.. practical::

   3. **Use Jinja2 To Avoid Duplication.**

      The ``API_KEY`` environment variable is used by both the
      ``get_observations`` and ``get_rainfall`` tasks. Rather than writing it
      out multiple times we will use Jinja2 to centralise this configuration.

      At the top of the ``suite.rc`` file add the Jinja2 shebang line and set
      the ``API_KEY`` variable:

      .. code-block:: cylc

         #!Jinja2

         {% set API_KEY = 'd6bfeab3-3489-4990-a604-44acac4d2dfb' %}

      Next replace the key where it appears in the suite with
      ``{{ API_KEY }}``:

      .. code-block:: diff

          [runtime]
              [[get_observations_heathrow]]
                  script = get-observations
                  [[[environment]]]
                      SITE_ID = 3772
         -            API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
         +            API_KEY = {{ API_KEY }}
              [[get_observations_camborne]]
                  script = get-observations
                  [[[environment]]]
                      SITE_ID = 3808
         -            API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
         +            API_KEY = {{ API_KEY }}
              [[get_observations_shetland]]
                  script = get-observations
                  [[[environment]]]
                     SITE_ID = 3005
         -            API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
         +            API_KEY = {{ API_KEY }}
              [[get_observations_belmullet]]
                  script = get-observations
                  [[[environment]]]
                      SITE_ID = 3976
         -            API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
         +            API_KEY = {{ API_KEY }}
             [[get_rainfall]]
                 script = get-rainfall
                 [[[environment]]]
                     # The key required to get weather data from the DataPoint service.
                     # To use archived data comment this line out.
         -            API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb
         +            API_KEY = {{ API_KEY }}

      Check the result with ``cylc get-config``, the Jinja2 will be processed
      so you should not see any difference after making these changes:

Parameterised Tasks
-------------------

Parameterised tasks (or :term:`parameterisation`) provides a way of implicitly
looping over tasks without the need for Jinja2.

Parameters are defined in their own section e.g:

.. code-block:: cylc

   [cylc]
       [[parameters]]
           stations = belmullet, camborne, heathrow, shetland

They can then be referenced by writing the name of the parameter in angle
brackets e.g:

.. code-block:: cylc-graph

   get_observations<station>

Would result in:

.. code-block:: cylc-graph

   get_observations_belmullet
   get_observations_camborne
   get_observations_heathrow
   get_observations_shetland

We can refer to a particular value in a parametrisation by writing its name
after an equals sign e.g:

.. code-block:: cylc-graph

   get_observations<station=heathrow>

Using parameters the ``get_observations`` configuration could be written like
so:

.. code-block:: cylc

   [scheduling]
      [[dependencies]]
          [[[T00/PT3H]]]
              graph = """
                  get_observations<station> => gather_observations
              """
   [runtime]
       [[get_observations<station>]]
           script = get-observations
           [[[environment]]]
               API_KEY = d6bfeab3-3489-4990-a604-44acac4d2dfb

       [[get_observations<station=belmullet>]]
           [[[environment]]]
               SITE_ID = 3976
       [[get_observations<station=camborne>]]
           [[[environment]]]
               SITE_ID = 3808
       [[get_observations<station=heathrow>]]
           [[[environment]]]
               SITE_ID = 3772
       [[get_observations<station=shetland>]]
           [[[environment]]]
               SITE_ID = 3005

.. warning::

   Remember that cylc automatically inserts an underscore between the task and
   the parameter. E.g. the following lines are equivalent:

   .. code-block:: cylc-graph

      get_observations<station=heathrow>
      get_observations_heathrow

.. practical::

   4. **Use Parameterisation To Consolidate The** ``get_observations``
      **Tasks**.

      Next we will parameterise the ``get_observations`` tasks.

      Add a parameter called ``station``:

      .. code-block:: diff

          [cylc]
              UTC mode = True
         +    [[parameters]]
         +        station = belmullet, camborne, heathrow, shetland

      Remove the four ``get_observations`` tasks and insert the following code
      in their place:

      .. code-block:: cylc

         [[get_observations<station>]]
             script = get-observations
             [[[environment]]]
                 API_KEY = {{ API_KEY }}

      Using ``cylc get-config`` you should see that cylc will replace the
      ``<station>`` with each of the stations in turn creating a new task for
      each:

      .. code-block:: bash

         cylc get-config . --sparse -i "[runtime]"

      The ``get_observations`` tasks are now missing the ``SITE_ID``
      environment variable. Add a new section for each station with a
      ``SITE_ID`` environment variable:

      .. code-block:: cylc

         [[get_observations<station=heathrow>]]
             [[[environment]]]
                 SITE_ID = 3772

      .. hint::

         The site-id's are:

         * Belmullet - ``3976``
         * Camborne - ``3808``
         * Heathrow - ``3772``
         * Shetland - ``3005``

      .. spoiler:: Solution warning

         .. code-block:: cylc

            [[get_observations<station=belmullet>]]
                [[[environment]]]
                    SITE_ID = 3772
            [[get_observations<station=camborne>]]
                [[[environment]]]
                    SITE_ID = 3772
            [[get_observations<station=heathrow>]]
                [[[environment]]]
                    SITE_ID = 3772
            [[get_observations<station=shetland>]]
                [[[environment]]]
                    SITE_ID = 3772

      Using ``cylc get-config`` you should now see four ``get_observations``
      tasks each with a ``script``, an ``API_KEY`` and a ``SITE_ID``:

      .. code-block:: bash

         cylc get-config . --sparse -i "[runtime]"

      Finally we can use this parameterisation to simplify the suite's
      graphing. Replace the ``get_observations`` lines in the graph with
      ``get_observations<station>``.

      .. code-block:: diff

          [[[PT3H]]]
              # Repeat every three hours starting at the initial cycle point.
              graph = """
         -        get_observations_belmullet => consolidate_observations
         -        get_observations_camborne => consolidate_observations
         -        get_observations_heathrow => consolidate_observations
         -        get_observations_shetland => consolidate_observations
         +        get_observations<station> => consolidate_observations
              """

      .. hint::

         The ``cylc get-config`` command does not expand parameters or families
         in the graph so you must use ``cylc graph`` to inspect changes to the
         graphing.

   #. **Use Parameterisation To Consolidate The** ``post_process`` **Tasks**.

      At the moment we only have one ``post_process`` task
      (``post_process_exeter``), but suppose we wanted to add a second task for
      Edinburgh.

      Create a new parameter called ``site`` and set it to contain ``exeter``
      and ``edinburgh``. Parameterise the ``post_process`` task using this
      parameter.

      .. spoiler:: Solution warning

         First we must create the ``site`` parameter:

         .. code-block:: diff

             [cylc]
                 UTC mode = True
                 [[parameters]]
                     station = belmullet, camborne, heathrow, shetland
            +        site = exeter, edinburgh

         Next we parameterise the task:

         .. code-block:: diff

            -[[post_process_exeter]]
            +[[post_process<site>]]
                 # Generate a forecast for Exeter 60 minutes in the future.
                 script = post-process exeter 120


Which Approach To Use
---------------------

Each approach has its uses, cylc permits mixing approaches allowing us to use
what works best for us. As a rule of thumb:

* :term:`Families <family>` work best consolidating runtime configuration by
  collecting tasks into broad groups e.g. tasks which run on a particular
  machine or tasks belonging to a particular system.
* `Jinja2`_ is good at configuring things which apply to the entire suite
  rather than just a single task as we can define variables then use them
  throughout the suite.
* :term:`Parameterisation <parameterisation>` works best for describing tasks
  which are very similar but which have subtly different configuration
  (e.g. different arguments or environment variables).


The ``cylc get-config`` Command
-------------------------------

To help assist with consolidating configurations the ``cylc get-config``
command can be used to expand the ``suite.rc`` file back out into its full
form.

Call ``cylc get-config`` with the path of the suite (``.`` if you are in
the :term:`suite directory`) and the ``--sparse`` option (which hides default
values).

.. code-block:: sub

   cylc get-config <path> --sparse

To view the configuration of a particular section or setting refer to it by
name using the ``-i`` option (see :ref:`cylc file conf` for details) e.g:

.. code-block:: sub

   # Print the contents of the [scheduling] section.
   cylc get-config <path> --sparse -i '[scheduling]'
   # Print the contents of the get_observations_heathrow task.
   cylc get-config <path> --sparse -i '[runtime][get_observations_heathrow]'
   # Print the value of the script setting in the get_observations_heathrow task
   cylc get-config <path> --sparse -i '[runtime][get_observations_heathrow]script'

The ``cylc get-config`` will expand:

* Inheritance in families.
* All Jinja2.
* All parameters in the ``[runtime]`` section.
