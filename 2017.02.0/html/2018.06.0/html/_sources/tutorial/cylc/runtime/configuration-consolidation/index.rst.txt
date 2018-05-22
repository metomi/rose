.. include:: ../../../../hyperlinks.rst
  :start-line: 1


.. _tutorial-cylc-consolidating-configuration:

Consolidating Configuration
===========================

.. ifnotslides::

   In the last section we wrote out the following code in the ``suite.rc`` file:

.. slide:: Weather Forecasting Suite
   :level: 2
   :inline-contents: True

   .. code-block:: cylc

      [runtime]
          [[get_observations_heathrow]]
              script = get-observations
              [[[environment]]]
                  SITE_ID = 3772
                  API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
          [[get_observations_camborne]]
              script = get-observations
              [[[environment]]]
                  SITE_ID = 3808
                  API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
          [[get_observations_shetland]]
              script = get-observations
              [[[environment]]]
                  SITE_ID = 3005
                  API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
          [[get_observations_belmullet]]
              script = get-observations
              [[[environment]]]
                  SITE_ID = 3976
                  API_KEY = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

.. ifnotslides::

   In this code the ``script`` item and the ``API_KEY`` environment variable have
   been repeated for each task. This is bad practice as it makes the
   configuration lengthy and making changes can become difficult.

   Likewise the graphing relating to the ``get_observations`` tasks is highly
   repetitive:

.. ifslides::

   .. slide:: Weather Forecasting Suite
      :level: 2

      Repetition

      * ``script``
      * ``API_KEY``

.. slide:: Weather Forecasting Suite
   :level: 2
   :inline-contents: True

   .. code-block:: cylc

      [scheduling]
          [[dependencies]]
              [[[T00/PT3H]]]
                  graph = """
                      get_observations_belmullet => consolidate_observations
                      get_observations_camborne => consolidate_observations
                      get_observations_heathrow => consolidate_observations
                      get_observations_shetland => consolidate_observations
                  """

.. nextslide::

Cylc offers three ways of consolidating configurations to help improve the
structure of a suite and avoid duplication.

.. toctree::
   :maxdepth: 1

   families
   jinja2
   parameters


The ``cylc get-config`` Command
-------------------------------

.. ifnotslides::

   The ``cylc get-config`` command reads in then prints out the ``suite.rc`` file
   to the terminal.

   Throughout this section we will be introducing methods for consolidating
   the ``suite.rc`` file, the ``cylc get-config`` command can be used to
   "expand" the ``suite.rc`` file back to its full form.

   .. note::

      The main use of ``cylc get-config`` is inspecting the
      ``[runtime]`` section of a suite. The ``cylc get-config`` command does not
      expand :term:`parameterisations <parameterisation>` and
      :term:`families <family>` in the suite's :term:`graph`. To inspect the
      graphing use the ``cylc graph`` command.

   Call ``cylc get-config`` with the path of the suite (``.`` if you are already
   in the :term:`suite directory`) and the ``--sparse`` option which hides
   default values.

.. code-block:: sub

   cylc get-config <path> --sparse

.. ifnotslides::

   To view the configuration of a particular section or setting refer to it by
   name using the ``-i`` option (see :ref:`Cylc file format` for details), e.g:

.. code-block:: sub

   # Print the contents of the [scheduling] section.
   cylc get-config <path> --sparse -i '[scheduling]'
   # Print the contents of the get_observations_heathrow task.
   cylc get-config <path> --sparse -i '[runtime][get_observations_heathrow]'
   # Print the value of the script setting in the get_observations_heathrow task
   cylc get-config <path> --sparse -i '[runtime][get_observations_heathrow]script'

.. nextslide::

.. ifslides::

   Note that ``cylc get-config`` doesn't expand families or parameterisations
   in the :term:`graph`. Use ``cylc graph`` to visualise these.

   .. TODO - Raise and issue for this, note cylc get-config and cylc view.


The Three Approaches
--------------------

.. ifnotslides::

   The next three sections cover the three consolidation approaches and how we
   could use them to simplify the suite from the previous tutorial. *Work
   through them in order!*

* :ref:`families <tutorial-cylc-families>`
* :ref:`jinja2 <tutorial-cylc-jinja2>`
* :ref:`parameters <tutorial-cylc-parameterisation>`


.. _cylc-tutorial-consolidation-conclusion:

Which Approach To Use
---------------------

.. ifnotslides::

   Each approach has its uses. Cylc permits mixing approaches, allowing us to
   use what works best for us. As a rule of thumb:

   * :term:`Families <family>` work best consolidating runtime configuration by
     collecting tasks into broad groups, e.g. groups of tasks which run on a
     particular machine or groups of tasks belonging to a particular system.
   * `Jinja2`_ is good at configuring settings which apply to the entire suite
     rather than just a single task, as we can define variables then use them
     throughout the suite.
   * :term:`Parameterisation <parameterisation>` works best for describing tasks
     which are very similar but which have subtly different configurations
     (e.g. different arguments or environment variables).

.. ifslides::

   As a rule of thumb each method works best for:

   Families
      Collecting tasks into broad groups.
   Jinja2
      Configuration settings which apply to the entire suite.
   Parameterisation
      Tasks which are similar.

.. nextslide::

.. ifslides::

   Next section: :ref:`Rose Tutorial <tutorial-rose-configurations>`
