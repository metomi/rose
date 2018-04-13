.. _rose-tutorial-optional-configurations:

Optional Configurations
=======================

Optional configurations are configuration files which can add or overwrite
the default configuration. They can be used with :ref:`command-rose-app-run`
for :term:`Rose application configurations <Rose application configuration>`
and :ref:`command-rose-suite-run` for
:term:`Rose suite configurations <Rose suite configuration>`.


Example
-------

.. image:: https://upload.wikimedia.org/wikipedia/commons/a/ae/StrawberrySundae.jpg
   :align: right
   :width: 250px
   :alt: Ice Cream

Create a new :term:`Rose app` called ``rose-opt-conf-tutorial``::

   mkdir -p ~/rose-tutorial/rose-opt-conf-tutorial
   cd ~/rose-tutorial/rose-opt-conf-tutorial

Create a :rose:file:`rose-app.conf` file with the following contents:

.. code-block:: rose

   [command]
   default=echo "I'd like to order a $FLAVOUR ice cream in a $CONE_TYPE" \
          ="with $TOPPING."

   [env]
   CONE_TYPE=regular-cone
   FLAVOUR=vanilla
   TOPPING=no toppings

Test the app by running::

   rose app-run -q

You should see the following output:

.. code-block:: none

   I'd like to order a vanilla ice cream in a regular-cone with no toppings.


Adding Optional Configurations
------------------------------

Optional configurations are stored in the ``opt`` directory and are named the
same as the default configuration file but with the name of the optional
configuration before the ``.conf`` extension i.e:

.. code-block:: sub

   app/
    |-- rose-app.conf
    `-- opt/
         `-- rose-app-<optional-configuration-name>.conf

Next we will create a new optional configuration for chocolate ice cream. The
configuration will be called ``chocolate``.

Create an ``opt`` directory containing a ``rose-app-chocolate.conf`` file
containing the following configuration:

.. code-block:: rose

   [env]
   FLAVOUR=chocolate

Next we need to tell :ref:`command-rose-app-run` to use the ``chocolate``
optional configuration. We can do this in one of two ways:

1. Using the ``--opt-conf-key`` option.
2. Using the :envvar:`ROSE_APP_OPT_CONF_KEYS` environment variable.

Run the app using the ``chocolate`` optional configuration::

   rose app-run -q --opt-conf-key=chocolate

You should see the following output:

.. code-block:: none

   I'd like to order a chocolate ice cream in a regular-cone with no toppings.

The ``chocolate`` optional configuration has overwritten the ``FLAVOUR``
environment variable from the :rose:file:`rose-app.conf` file.


Using Multiple Optional Configurations
--------------------------------------

It is possible to use multiple optional configurations at the same time.

Create a new optional configuration called ``flake`` containing the following
configuration:

.. code-block:: rose

   [env]
   TOPPING=one chocolate flake

Run the app using both the ``chocolate`` and ``flake`` optional configurations::

   rose app-run -q --opt-conf-key=chocolate --opt-conf-key=flake

The ``FLAVOUR`` environment variable will be overwritten by the ``chocolate``
configuration and the ``TOPPING`` variable by the ``flake`` configuration.

Next create a new optional configuration called ``fudge-sundae`` containing the
following lines:

.. code-block:: rose

   [env]
   FLAVOUR=fudge
   CONE_TYPE=tub
   TOPPINGS=nuts

Run the app using both the ``chocolate`` and ``fudge-sundae`` optional
configurations::

   rose app-run -q --opt-conf-key=fudge-sundae --opt-conf-key=chocolate

You should see the following:

.. code-block:: none

   I'd like to order a chocolate icecream in a tub with nuts.

The ``chocolate`` configuration has overwritten the ``FLAVOUR`` environment
variable from the ``fudge sundae`` configuration. This is because optional
configurations as applied first to last so in this case the ``chocolate``
configuration was loaded last.

To see how the optional configurations would be applied use the
:ref:`command-rose-config` command providing the configuration files in the
order they would be loaded::

   rose config --file rose-app.conf --file opt/rose-app-fudge-sundae --file chocolate

You should see:

.. code-block:: rose

   [command]
   default=echo "I'd like to order a $FLAVOUR icecream in a $CONE_TYPE" \
          ="with $TOPPING toppings"

   [env]
   CONE_TYPE=tub
   FLAVOUR=chocolate
   TOPPING=nuts

.. note::

   Optional configurations specified using the :envvar:`ROSE_APP_OPT_CONF_KEYS`
   environment variable are loaded before those specified using the
   ``--opt-conf-key`` command line option.


Using Optional Configurations By Default
----------------------------------------

Optional configurations can be switched on by default using the ``opt`` setting.

Add the following line at the top of the :rose:file:`rose-app.conf` file:

.. code-block:: rose

   opts=chocolate

Now the ``chocolate`` optional configuration will *always* be turned on. For this
reason its generally better to use the ``--opt-conf-key`` setting or
:envvar:`ROSE_APP_OPT_CONF_KEYS` environment variable instead.


Other Optional Configurations
-----------------------------

All Rose configurations can have optional configurations, not just application
configurations.

* Suites can have optional configurations that override
  :rose:file:`rose-suite.conf` settings, controlled through
  :ref:`command-rose-suite-run`. Optional suite configurations
  can be used either using the ``--opt-conf-key`` option with
  :ref:`command-rose-suite-run` or the :envvar:`ROSE_SUITE_OPT_CONF_KEYS`
  environment variable.
* Metadata configurations can also have optional configurations, typically
  included via the ``opts`` top-level setting.

.. TODO - opts? this is not documented!
