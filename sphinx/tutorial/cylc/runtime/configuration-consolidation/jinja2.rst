.. _Jinja2 Tutorial: http://jinja.pocoo.org/docs
.. _shebang: https://en.wikipedia.org/wiki/Shebang_(Unix)


.. _tutorial-cylc-jinja2:

Jinja2
======

`Jinja2`_ is a templating language often used in web design with some
similarities to python. It can be used to make a suite definition more
dynamic.


The Jinja2 Language
-------------------

In Jinja2 statements are wrapped with ``{%`` characters, i.e:

.. code-block:: none

   {% ... %}

Variables are initiated using the ``set`` statement, e.g:

.. code-block:: css+jinja

   {% set foo = 3 %}

.. nextslide::

Expressions wrapped with ``{{`` characters will be replaced with the value of
the evaluation of the expression, e.g:

.. code-block:: css+jinja

   There are {{ foo }} methods for consolidating the suite.rc file

Would result in::

   There are 3 methods for consolidating the suite.rc file

.. nextslide::

Loops are written with ``for`` statements, e.g:

.. code-block:: css+jinja

   {% for x in range(foo) %}
      {{ x }}
   {% endfor %}

Would result in:

.. code-block:: none

      0
      1
      2

.. nextslide::

To enable Jinja2 in the ``suite.rc`` file, add the following `shebang`_ to the
top of the file:

.. code-block:: cylc

   #!Jinja2

For more information see the `Jinja2 Tutorial`_.


Example
-------

To consolidate the configuration for the ``get_observations`` tasks we could
define a dictionary of station and ID pairs:

.. code-block:: css+jinja

   {% set stations = {'belmullet': 3976,
                      'camborne': 3808,
                      'heathrow': 3772,
                      'shetland': 3005} %}

.. nextslide::

We could then loop over the stations like so:

.. code-block:: css+jinja

   {% for station in stations %}
       {{ station }}
   {% endfor %}

After processing, this would result in:

.. code-block:: none

       belmullet
       camborne
       heathrow
       shetland

.. nextslide::

We could also loop over both the stations and corresponding IDs like so:

.. code-block:: css+jinja

   {% for station, id in stations.items() %}
       {{ station }} - {{ id }}
   {% endfor %}

This would result in:

.. code-block:: none

       belmullet - 3976
       camborne - 3808
       heathrow - 3772
       shetland - 3005

.. nextslide::

.. ifnotslides::

   Putting this all together, the ``get_observations`` configuration could be
   written as follows:

.. code-block:: cylc

   #!Jinja2

   {% set stations = {'belmullet': 3976,
                      'camborne': 3808,
                      'heathrow': 3772,
                      'shetland': 3005} %}

   [scheduling]
       [[dependencies]]
           [[[T00/PT3H]]]
               graph = """
   {% for station in stations %}
                  get_observations_{{station}} => consolidate_observations
   {% endfor %}
               """

.. nextslide::

.. code-block:: cylc

   [runtime]
   {% for station, id in stations.items() %}
       [[get_observations_{{station}}]]
           script = get-observations
           [[[environment]]]
               SITE_ID = {{ id }}
               API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

   {% endfor %}

.. nextslide::

.. ifslides::

   .. rubric:: This practical continues on from the
      :ref:`families practical <cylc-tutorial-families-practical>`.

   Next section: :ref:`tutorial-cylc-parameterisation`


.. _cylc-tutorial-jinja2-practical:

.. practical::

   .. rubric:: This practical continues on from the
      :ref:`families practical <cylc-tutorial-families-practical>`.

   3. **Use Jinja2 To Avoid Duplication.**

      The ``API_KEY`` environment variable is used by both the
      ``get_observations`` and ``get_rainfall`` tasks. Rather than writing it
      out multiple times we will use Jinja2 to centralise this configuration.

      At the top of the ``suite.rc`` file add the Jinja2 shebang line. Then
      copy the value of the ``API_KEY`` environment variable and use it to
      define an ``API_KEY`` Jinja2 variable:

      .. code-block:: cylc

         #!Jinja2

         {% set API_KEY = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' %}

      Next replace the key, where it appears in the suite, with
      ``{{ API_KEY }}``:

      .. code-block:: diff

          [runtime]
              [[get_observations_heathrow]]
                  script = get-observations
                  [[[environment]]]
                      SITE_ID = 3772
         -            API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
         +            API_KEY = {{ API_KEY }}
              [[get_observations_camborne]]
                  script = get-observations
                  [[[environment]]]
                      SITE_ID = 3808
         -            API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
         +            API_KEY = {{ API_KEY }}
              [[get_observations_shetland]]
                  script = get-observations
                  [[[environment]]]
                     SITE_ID = 3005
         -            API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
         +            API_KEY = {{ API_KEY }}
              [[get_observations_belmullet]]
                  script = get-observations
                  [[[environment]]]
                      SITE_ID = 3976
         -            API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
         +            API_KEY = {{ API_KEY }}
             [[get_rainfall]]
                 script = get-rainfall
                 [[[environment]]]
                     # The key required to get weather data from the DataPoint service.
                     # To use archived data comment this line out.
         -            API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
         +            API_KEY = {{ API_KEY }}

      Check the result with ``cylc get-config``. The Jinja2 will be processed
      so you should not see any difference after making these changes.
