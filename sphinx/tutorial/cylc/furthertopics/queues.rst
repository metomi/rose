Queues
======

Introduction
------------

This part of the Rose user guide walks you through using cylc queues.

These can limit the number of certain tasks that are submitted or run at any given time.

Purpose
-------

Queues are used to put a limit on the number of tasks that will be active at any one time, even if their dependencies are satisfied.

This avoids swamping systems with too many tasks at once.

Example
-------

In this example, our suite manages a particularly understaffed restaurant.

Create a new suite (or just a new directory somewhere - e.g. in your homespace) containing a blank ``rose-suite.conf`` and a ``suite.rc`` file with the following contents:


.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           graph = """
               open_restaurant => steak1 & steak2 & pasta1 & pasta2 & pasta3 & \
                                  pizza1 & pizza2 & pizza3 & pizza4
               steak1 => ice_cream1
               steak2 => cheesecake1
               pasta1 => ice_cream2
               pasta2 => sticky_toffee1
               pasta3 => cheesecake2
               pizza1 => ice_cream3
               pizza2 => ice_cream4
               pizza3 => sticky_toffee2
               pizza4 => ice_cream5
           """

We'll add some information in the ``[runtime]`` section:

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           graph = """
               open_restaurant => steak1 & steak2 & pasta1 & pasta2 & pasta3 & \
                                  pizza1 & pizza2 & pizza3 & pizza4
               steak1 => ice_cream1
               steak2 => cheesecake1
               pasta1 => ice_cream2
               pasta2 => sticky_toffee1
               pasta3 => cheesecake2
               pizza1 => ice_cream3
               pizza2 => ice_cream4
               pizza3 => sticky_toffee2
               pizza4 => ice_cream5
           """

Run the suite by changing directory to your new suite directory and invoking:

.. code-block:: console

   rose suite-run


When cylc gui starts up, you will see that all the ``steak``, ``pasta``, and ``pizza`` tasks are run at once, swiftly followed by all the ``ice_cream``, ``cheesecake``, ``sticky_toffee`` tasks as the customers order from the dessert menu.

This will overwhelm our restaurant staff! The chef responsible for ``MAINS`` can only handle 3 tasks at any given time, and the ``DESSERT`` chef can only handle 2.

We need to add some queues.

Replace the ``[scheduling]`` line with:

.. code-block:: cylc

   [scheduling]
       [[queues]]
           [[[mains_chef_queue]]]
               limit = 3  # Only 3 mains dishes at one time.
               members = MAINS
           [[[dessert_chef_queue]]]
               limit = 2  # Only 2 dessert dishes at one time.
               members = DESSERT

Make sure you are in the root directory of your suite.

Run the suite using:

.. code-block:: console

   rose suite-run

When ``cylc gui`` starts up, you can see that there are now never more than 3 active ``MAINS`` tasks running and never more than 2 active ``DESSERT`` tasks running.

The customers will obviously have to wait!

Further reading
---------------

For more information, see the `cylc User Guide`_.

.. _cylc User Guide: https://cylc.github.io/cylc/html/single/cug-html.html


