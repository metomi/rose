.. include:: ../../../../hyperlinks.rst
  :start-line: 1

.. _tutorial-cylc-parameterisation:


Parameterised Tasks
===================

Parameterised tasks (see :term:`parameterisation`) provide a way of implicitly
looping over tasks without the need for Jinja2.


Cylc Parameters
---------------

.. ifnotslides::

   Parameters are defined in their own section, e.g:

.. code-block:: cylc

   [cylc]
       [[parameters]]
           param = foo, bar, baz

.. ifnotslides::

   They can then be referenced by writing the name of the parameter in angle
   brackets, e.g:

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           graph = start => task<param> => end
   [runtime]
       [[task<param>]]
           script = echo 'Hello World!'

.. nextslide::

.. ifnotslides::

   When the ``suite.rc`` file is read by Cylc, the parameters will be expanded.
   For example the code above is equivalent to:

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           graph = start => (task_foo & task_bar & task_baz) => end
   [runtime]
       [[task_foo]]
           script = echo 'Hello World!'
       [[task_bar]]
           script = echo 'Hello World!'
       [[task_baz]]
           script = echo 'Hello World!'

.. nextslide::

.. ifnotslides::

   We can refer to a specific parameter by writing it after an ``=`` sign:

.. code-block:: cylc

   [runtime]
       [[task<param=baz>]]
           script = 'Do something special for baz!'


Environment Variables
---------------------

.. ifnotslides::

   The name of the parameter is provided to the job as an environment variable
   called ``CYLC_TASK_PARAM_<parameter>`` where ``<parameter>`` is the name of
   the parameter (in the present case ``param``):

.. code-block:: cylc

   [runtime]
       [[task<param=bar>]]
           # This is equivalent to `echo 'bar'`
           script = echo $CYLC_TASK_PARAM_param


Parameter Types
---------------

Parameters can be either words or integers:

.. code-block:: cylc

   [cylc]
       [[parameters]]
           foo = 1..5
           bar = 1..5..2
           baz = pub, qux, bol

   [scheduling]
       [[dependencies]]
           graph = """
               task<foo>
               task<bar>
               task<baz>
           """

.. nextslide::

.. hint::

   Remember that Cylc automatically inserts an underscore between the task and
   the parameter, e.g. the following lines are equivalent:

   .. code-block:: cylc-graph

      task<baz=pub>
      task_pub

.. nextslide::

.. hint::

   .. ifnotslides::

      When using integer parameters, to prevent confusion, Cylc prefixes the
      parameter value with the parameter name. For example, the above code is
      equivalent to:

   .. ifslides::

      Cylc prefixes integer parameters with the parameter name:

   .. code-block:: cylc

      [scheduling]
          [[dependencies]]
              graph = """
                  task_foo1
                  task_foo2
                  task_foo3
                  task_foo4
                  task_foo5

                  task_bar1
                  task_bar3
                  task_bar5

                  task_pub
                  task_qux
                  task_bol
              """

.. nextslide::

.. ifnotslides::

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

.. nextslide::

.. ifnotslides::

   For more information see the `Cylc User Guide`_.

.. ifslides::

   .. rubric:: This practical continues on from the
      :ref:`Jinja2 practical <cylc-tutorial-jinja2-practical>`.

   Next section: :ref:`Which approach to use
   <cylc-tutorial-consolidation-conclusion>`


.. _cylc-tutorial-parameters-practical:

.. practical::

   .. rubric:: This practical continues on from the
      :ref:`Jinja2 practical <cylc-tutorial-jinja2-practical>`.

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

      Using ``cylc get-config`` you should see that Cylc replaces the
      ``<station>`` with each of the stations in turn, creating a new task for
      each:

      .. code-block:: bash

         cylc get-config . --sparse -i "[runtime]"

      The ``get_observations`` tasks are now missing the ``SITE_ID``
      environment variable. Add a new section for each station with a
      ``SITE_ID``:

      .. code-block:: cylc

         [[get_observations<station=heathrow>]]
             [[[environment]]]
                 SITE_ID = 3772

      .. hint::

         The relevant IDs are:

         * Belmullet - ``3976``
         * Camborne - ``3808``
         * Heathrow - ``3772``
         * Shetland - ``3005``

      .. spoiler:: Solution warning

         .. code-block:: cylc

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

      Using ``cylc get-config`` you should now see four ``get_observations``
      tasks, each with a ``script``, an ``API_KEY`` and a ``SITE_ID``:

      .. code-block:: bash

         cylc get-config . --sparse -i "[runtime]"

      Finally we can use this parameterisation to simplify the suite's
      graphing. Replace the ``get_observations`` lines in the graph with
      ``get_observations<station>``:

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

      .. hint::

         The first argument to the ``post-process`` task is the name of the
         site. We can use the ``CYLC_TASK_PARAM_site`` environment variable to
         avoid having to write out this section twice.

         .. TODO - use parameter environment templates instead of
            CYLC_TASK_PARAM.

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
            -    script = post-process exeter 60
            +    script = post-process $CYLC_TASK_PARAM_site 60
