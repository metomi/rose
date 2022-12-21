Inheritance
===========

We have seen in the :ref:`runtime tutorial <tutorial-cylc-families>` how
tasks can be grouped into families.

In this tutorial we will look at nested families, inheritance order and
multiple inheritance.


Inheritance Hierarchy
---------------------

Create a new suite by running the command::

   rose tutorial inheritance-tutorial
   cd ~/cylc-run/inheritance-tutorial

You will now have a ``suite.rc`` file that defines two tasks each representing
a different aircraft, the Airbus A380 jumbo jet and the Robson R44 helicopter:

.. image:: https://upload.wikimedia.org/wikipedia/commons/0/09/A6-EDY_A380_Emirates_31_jan_2013_jfk_%288442269364%29_%28cropped%29.jpg
   :width: 49%
   :alt: A380

.. image:: https://upload.wikimedia.org/wikipedia/commons/2/2f/Robinson-R44_1.jpg
   :width: 49%
   :alt: R44

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           graph = a380 & r44

   [runtime]
       [[VEHICLE]]
           init-script = echo 'Boarding'
           pre-script = echo 'Departing'
           post-script = echo 'Arriving'

       [[AIR_VEHICLE]]
           inherit = VEHICLE
           [[[meta]]]
               description = A vehicle which can fly.
       [[AIRPLANE]]
           inherit = AIR_VEHICLE
           [[[meta]]]
               description = An air vehicle with fixed wings.
           [[[environment]]]
               CAN_TAKE_OFF_VERTICALLY = false
       [[HELICOPTER]]
           inherit = AIR_VEHICLE
           [[[meta]]]
               description = An air vehicle with rotors.
           [[[environment]]]
               CAN_TAKE_OFF_VERTICALLY = true

       [[a380]]
           inherit = AIRPLANE
           [[[meta]]]
               title = Airbus A380 Jumbo-Jet.
       [[r44]]
           inherit = HELICOPTER
           [[[meta]]]
               title = Robson R44 Helicopter.

.. note::

   The ``[meta]`` section is a freeform section where we can define metadata
   to be associated with a task, family or the suite itself.

   This metadata should not be mistaken with Rose :ref:`conf-meta`.

.. admonition:: Reminder
   :class: hint

   By convention we write family names in upper case (with the exception of the
   special ``root`` family) and task names in lower case.

These two tasks sit at the bottom of an inheritance tree. The ``cylc graph``
command has an option (``-n``) for drawing such inheritance hierarchies::

   cylc graph -n . &

Running this command will generate the following output:

.. digraph:: Example
   :align: center

   AIRPLANE  [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   a380   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   AIRPLANE -> a380   [color=royalblue];
   HELICOPTER   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   r44    [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   HELICOPTER -> r44  [color=royalblue];
   root   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   VEHICLE   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   root -> VEHICLE    [color=royalblue];
   AIR_VEHICLE  [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   VEHICLE -> AIR_VEHICLE   [color=royalblue];
   AIR_VEHICLE -> AIRPLANE  [color=royalblue];
   AIR_VEHICLE -> HELICOPTER   [color=royalblue];

.. note::

   The ``root`` family sits at the top of the inheritance tree as all
   tasks/families automatically inherit it:

Cylc handles inheritance by starting with the root family and working down the
inheritance tree applying each section in turn.

To see the resulting configuration for the ``a380`` task use the
``cylc get-config`` command::

   cylc get-config . --sparse -i "[runtime][a380]"

You should see some settings which have been inherited from the ``VEHICLE`` and
``AIRPLANE`` families as well as a couple defined in the ``a380`` task.

.. code-block:: cylc

   init-script = echo 'Boarding'                       # Inherited from VEHICLE
   pre-script = echo 'Departing'                       # Inherited from VEHICLE
   post-script = echo 'Arriving'                       # Inherited from VEHICLE
   inherit = AIRPLANE                                  # Defined in a380
   [[[meta]]]
       description = An air vehicle with fixed wings.  # Inherited from AIR_VEHICLE - overwritten by AIRPLANE
       title = Airbus A380 Jumbo-Jet.                  # Defined in a380
   [[[environment]]]
       CAN_TAKE_OFF_VERTICALLY = false                 # Inherited from AIRPLANE

Note that the ``description`` setting is defined in the ``AIR_VEHICLE``
family but is overwritten by the value specified in the ``AIRPLANE`` family.


Multiple Inheritance
--------------------

Next we want to add a vehicle called the V-22 Osprey to the suite. The V-22
is a cross between a plane and a helicopter - it has wings but can take-off and
land vertically.

.. image:: https://upload.wikimedia.org/wikipedia/commons/e/e3/MV-22_mcas_Miramar_2014.JPG
   :width: 300px
   :align: center

As the V-22 can be thought of as both a plane and a helicopter we want it to
inherit from both the ``AIRPLANE`` and ``HELICOPTER`` families. In Cylc we can
inherit from multiple families by separating their names with commas:

Add the following task to your ``suite.rc`` file.

.. code-block:: cylc

       [[v22]]
           inherit = AIRPLANE, HELICOPTER
           [[[meta]]]
               title = V-22 Osprey Military Aircraft.

Refresh your ``cylc graph`` window or re-run the ``cylc graph`` command.

The inheritance hierarchy should now look like this:

.. digraph:: Example
   :align: center

   AIRPLANE  [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   v22    [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   AIRPLANE -> v22    [color=royalblue];
   a380   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   AIRPLANE -> a380   [color=royalblue];
   HELICOPTER   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   HELICOPTER -> v22  [color=royalblue];
   r44    [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   HELICOPTER -> r44  [color=royalblue];
   root   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   VEHICLE   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   root -> VEHICLE    [color=royalblue];
   AIR_VEHICLE  [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   VEHICLE -> AIR_VEHICLE   [color=royalblue];
   AIR_VEHICLE -> AIRPLANE  [color=royalblue];
   AIR_VEHICLE -> HELICOPTER   [color=royalblue];

Inspect the configuration of the ``v22`` task using the ``cylc get-config``
command.

.. spoiler:: Hint warning

   .. code-block:: bash

      cylc get-config . --sparse -i "[runtime][v22]"

You should see that the ``CAN_TASK_OFF_VERTICALLY`` environment variable has
been set to ``false`` which isn't right. This is because of the order in which
inheritance is applied.

Cylc handles multiple-inheritance by applying each family from right to left.
For the ``v22`` task we specified ``inherit = AIRPLANE, HELICOPTER`` so the
``HELICOPTER`` family will be applied first and the ``AIRPLANE`` family after.

The inheritance order would be as follows:

.. code-block:: bash

   root
   VEHICLE
   AIR_VEHICLE
   HELICOPTER   # sets "CAN_TAKE_OFF_VERTICALLY to "true"
   AIRPLANE     # sets "CAN_TAKE_OFF_VERTICALLY to "false"
   v22

We could fix this problem by changing the order of inheritance:

.. code-block:: cylc

   inherit = HELICOPTER, AIRPLANE

Now the ``HELICOPTER`` family is applied second so its values will override any
in the ``AIRPLANE`` family.

.. code-block:: bash

   root
   VEHICLE
   AIR_VEHICLE
   AIRPLANE     # sets "CAN_TAKE_OFF_VERTICALLY to "false"
   HELICOPTER   # sets "CAN_TAKE_OFF_VERTICALLY to "true"
   v22

Inspect the configuration of the ``v22`` task using ``cylc get-config`` to
confirm this.


More Inheritance
----------------

We will now add some more families and tasks to the suite.

Engine Type
^^^^^^^^^^^

Next we will define four families to represent three different types of engine.

.. digraph:: Example
   :align: center

   size = "5,5"

   ENGINE [color=royalblue, fillcolor=powderblue, shape=box, style=filled,
       margin="0.3,0.055"]
   TURBINE_ENGINE [color=royalblue, fillcolor=powderblue, shape=box,
       style=filled, margin="0.3,0.055"]
   INTERNAL_COMBUSTION_ENGINE [color=royalblue, fillcolor=powderblue,
       shape=box, style=filled, margin="0.3,0.055"]
   HUMAN_ENGINE [color=royalblue, fillcolor=powderblue, shape=box,
       style=filled, margin="0.3,0.055"]

   "ENGINE" -> "TURBINE_ENGINE"
   "ENGINE" -> "INTERNAL_COMBUSTION_ENGINE"
   "ENGINE" -> "HUMAN_ENGINE"

Each engine type should set an environment variable called ``FUEL`` which we
will assign to the following values:

* Turbine - kerosene
* Internal Combustion - petrol
* Human - pizza

Add lines to the ``runtime`` section to represent these four families.

.. spoiler:: Solution warning

   .. code-block:: cylc

          [[ENGINE]]
          [[TURBINE_ENGINE]]
              inherit = ENGINE
              [[[environment]]]
                  FUEL = kerosene
          [[INTERNAL_COMBUSTION_ENGINE]]
              inherit = ENGINE
              [[[environment]]]
                  FUEL = petrol
          [[HUMAN_ENGINE]]
              inherit = ENGINE
              [[[environment]]]
                  FUEL = pizza

We now need to make the three aircraft inherit from one of the three engines.
The aircraft use the following types of engine:

* A380 - turbine
* R44 - internal combustion
* V22 - turbine

Modify the three tasks so that they inherit from the relevant engine families.

.. spoiler:: Solution warning

   .. code-block:: cylc

         [[a380]]
             inherit = AIRPLANE, TURBINE_ENGINE
             [[[meta]]]
                 title = Airbus A380 Jumbo-Jet.
         [[r44]]
             inherit = HELICOPTER, INTERNAL_COMBUSTION_ENGINE
             [[[meta]]]
                 title = Robson R44 Helicopter.
         [[v22]]
             inherit = AIRPLANE, HELICOPTER, TURBINE_ENGINE
             [[[meta]]]
                 title = V-22 Ofsprey Military Aircraft.

Penny Farthing
^^^^^^^^^^^^^^

Next we want to add a new type of vehicle, an old-fashioned bicycle called a
penny farthing.

.. image:: https://upload.wikimedia.org/wikipedia/commons/a/a7/Ordinary_bicycle01.jpg
   :width: 300px
   :alt: Penny Farthing Bicycle
   :align: center

To do this we will need to add two new families, ``LAND_VEICHLE`` and
``BICYCLE`` as well as a new task, ``penny_farthing`` related in the
following manner:

.. digraph:: Example
   :align: center

   VEHICLE [color=royalblue, fillcolor=powderblue, shape=box, style=filled]
   LAND_VEHICLE [color=royalblue, fillcolor=powderblue, shape=box,
       style=filled]
   BICYCLE [color=royalblue, fillcolor=powderblue, shape=box, style=filled]
   HUMAN_ENGINE [color=royalblue, fillcolor=powderblue, shape=box,
       style=filled, margin="0.3,0.055"]
   penny_farthing [color=royalblue, fillcolor=powderblue, shape=box,
       style=filled, margin="0.3,0.055"]
   VEHICLE -> LAND_VEHICLE -> BICYCLE -> penny_farthing
   HUMAN_ENGINE -> penny_farthing

Add lines to the ``runtime`` section to represent the two new families and one
task outlined above.

Add a description (``[meta]description``) to the ``LAND_VEHICLE`` and
``BICYCLE`` families and a title (``[meta]title``) to the ``penny_farthing``
task.

.. spoiler:: Solution warning

   .. code-block:: cylc

         [[LAND_VEHICLE]]
             inherit = VEHICLE
             [[[meta]]]
                 description = A vehicle which can travel over the ground.

         [[BICYCLE]]
             inherit = LAND_VEHICLE
             [[[meta]]]
                 description = A small two-wheeled vehicle.

         [[penny_farthing]]
             inherit = BICYCLE, HUMAN_ENGINE
             [[[meta]]]
                 title = An old-fashioned bicycle.


Using ``cylc get-config`` to inspect the configuration of the ``penny_farthing``
task we can see that it inherits settings from the ``VEHICLE``,
``BICYCLE`` and ``HUMAN_ENGINE`` families.

.. code-block:: cylc

   inherit = BICYCLE, HUMAN_ENGINE
   init-script = echo 'Boarding'  # Inherited from VEHICLE
   pre-script = echo 'Departing'  # Inherited from VEHICLE
   post-script = echo 'Arriving'  # Inherited from VEHICLE
   [[[environment]]]
       FUEL = pizza               # Inherited from HUMAN_ENGINE
   [[[meta]]]
       description = A small two-wheeled vehicle.  # Inherited from LAND_VEHICLE - overwritten by BICYCLE
       title = An old-fashioned bicycle.           # Defined in penny_farthing

.. spoiler:: Hint hint

   .. code-block:: bash

      cylc get-config . --sparse -i "[runtime]penny_farthing"

Hovercraft
^^^^^^^^^^

We will now add a hovercraft called the Hoverwork BHT130, better known to some
as the Isle Of Wight Ferry.

.. image:: https://upload.wikimedia.org/wikipedia/commons/e/e7/Hovercraft_leaving_Ryde.JPG
   :width: 300px
   :align: center
   :alt: Hoverwork BHT130 Hovercraft

Hovercraft can move over both land and water and in some respects can be thought
of as flying vehicles.

.. digraph:: Example
   :align: center

   size = "7,5"

   VEHICLE [color=royalblue, fillcolor=powderblue, shape=box, style=filled]
   AIR_VEHICLE [color=royalblue, fillcolor=powderblue, shape=box, style=filled]
   LAND_VEHICLE [color=royalblue, fillcolor=powderblue, shape=box,
       style=filled]
   WATER_VEHICLE [color=royalblue, fillcolor=powderblue, shape=box,
       style=filled]
   HOVERCRAFT [color=royalblue, fillcolor=powderblue, shape=box, style=filled]
   bht130 [color=royalblue, fillcolor=powderblue, shape=box, style=filled]
   ENGINE [color=royalblue, fillcolor=powderblue, shape=box, style=filled]
   INTERNAL_COMBUSTION_ENGINE [color=royalblue, fillcolor=powderblue,
       shape=box, style=filled, margin="0.3,0.055"]
   VEHICLE -> AIR_VEHICLE -> HOVERCRAFT
   VEHICLE -> LAND_VEHICLE -> HOVERCRAFT
   VEHICLE -> WATER_VEHICLE -> HOVERCRAFT
   HOVERCRAFT -> bht130
   ENGINE -> INTERNAL_COMBUSTION_ENGINE -> bht130

Write new families and one new task to represent the above structure.

Add a description (``[meta]description``) to the ``WATER_VEHICLE`` and
``HOVERCRAFT`` families and a title (``[meta]title``) to the ``bht130`` task.

.. spoiler:: Solution warning

   .. code-block:: cylc

         [[WATER_VEHICLE]]
             inherit = VEHICLE
             [[[meta]]]
                 description = A vehicle which can travel over water.

         [[HOVERCRAFT]]
             inherit = LAND_VEHICLE, AIR_VEHICLE, WATER_VEHICLE
             [[[meta]]]
                 description = A vehicle which can travel over ground, water and ice.

         [[bht130]]
             inherit = HOVERCRAFT, INTERNAL_COMBUSTION_ENGINE
             [[[meta]]]
                 title = Griffon Hoverwork BHT130 (Isle Of Whight Ferry).


Finished Suite
--------------

You should now have a suite with an inheritance hierarchy which looks like
this:

.. digraph:: Example

   size = "7, 5"

   root   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   ENGINE    [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   root -> ENGINE  [color=royalblue];
   VEHICLE   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   root -> VEHICLE    [color=royalblue];
   INTERNAL_COMBUSTION_ENGINE  [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled,
      margin="0.3,0.055"];
   ENGINE -> INTERNAL_COMBUSTION_ENGINE    [color=royalblue];
   TURBINE_ENGINE  [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled,
      margin="0.3,0.055"];
   ENGINE -> TURBINE_ENGINE    [color=royalblue];
   HUMAN_ENGINE    [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled,
      margin="0.3,0.055"];
   ENGINE -> HUMAN_ENGINE   [color=royalblue];
   LAND_VEHICLE    [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   VEHICLE -> LAND_VEHICLE  [color=royalblue];
   WATER_VEHICLE   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   VEHICLE -> WATER_VEHICLE    [color=royalblue];
   AIR_VEHICLE  [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   VEHICLE -> AIR_VEHICLE   [color=royalblue];
   r44    [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   INTERNAL_COMBUSTION_ENGINE -> r44    [color=royalblue];
   bht130    [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   INTERNAL_COMBUSTION_ENGINE -> bht130    [color=royalblue];
   v22    [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   TURBINE_ENGINE -> v22    [color=royalblue];
   a380   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   TURBINE_ENGINE -> a380   [color=royalblue];
   penny_farthing  [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled,
      margin="0.3,0.055"];
   HUMAN_ENGINE -> penny_farthing    [color=royalblue];
   AIRPLANE  [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   AIRPLANE -> v22    [color=royalblue];
   AIRPLANE -> a380   [color=royalblue];
   HELICOPTER   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   HELICOPTER -> v22  [color=royalblue];
   HELICOPTER -> r44  [color=royalblue];
   HOVERCRAFT   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   HOVERCRAFT -> bht130  [color=royalblue];
   LAND_VEHICLE -> HOVERCRAFT  [color=royalblue];
   BICYCLE   [color=royalblue,
      fillcolor=powderblue,
      shape=box,
      style=filled];
   LAND_VEHICLE -> BICYCLE  [color=royalblue];
   WATER_VEHICLE -> HOVERCRAFT    [color=royalblue];
   AIR_VEHICLE -> AIRPLANE  [color=royalblue];
   AIR_VEHICLE -> HELICOPTER   [color=royalblue];
   AIR_VEHICLE -> HOVERCRAFT   [color=royalblue];
   BICYCLE -> penny_farthing   [color=royalblue];
