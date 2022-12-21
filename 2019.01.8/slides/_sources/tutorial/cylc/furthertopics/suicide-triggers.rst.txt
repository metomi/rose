.. include:: ../../../hyperlinks.rst
   :start-line: 1


.. _tut-cylc-suicide-triggers:

Suicide Triggers
================

Suicide triggers allow us to remove a task from the suite's graph whilst the
suite is running.

The main use of suicide triggers is for handling failures in the workflow.


Stalled Suites
--------------

Imagine a bakery which has a workflow that involves making cake.

.. minicylc::
   :snippet:
   :theme: none

   make_cake_mixture => bake_cake => sell_cake

There is a 50% chance that the cake will turn out fine, and a 50% chance that
it will get burnt. In the case that we burn the cake the workflow gets stuck.

.. digraph:: Example
   :align: center

   make_cake_mixture [style="filled" color="#ada5a5"]
   bake_cake [style="filled" color="#ff0000" fontcolor="white"]
   sell_cake [color="#88c6ff"]

   make_cake_mixture -> bake_cake -> sell_cake

In this event the ``sell_cake`` task will be unable to run as it depends on
``bake_cake``. We would say that this suite has :term:`stalled <stalled suite>`.
When Cylc detects that a suite has stalled it sends you an email to let you
know that the suite has got stuck and requires human intervention to proceed.


Handling Failures
-----------------

In order to prevent the suite from entering a stalled state we need to handle
the failure of the ``bake_cake`` task.

At the bakery if they burn a cake they eat it and make another.

The following diagram outlines this workflow with its two possible pathways,
``:succeed`` in the event that ``bake_cake`` is successful and ``:fail``
otherwise.

.. digraph:: Example
   :align: center

   make_cake_mixture
   bake_cake

   subgraph cluster_1 {
      label = ":succeed"
      labelloc = "b"
      color = "green"
      fontcolor = "green"
      style = "dashed"
      sell_cake
   }

   subgraph cluster_2 {
      label = ":fail"
      labelloc = "b"
      color = "red"
      fontcolor = "red"
      style = "dashed"
      eat_cake
   }

   make_cake_mixture -> bake_cake
   bake_cake -> sell_cake
   bake_cake -> eat_cake

We can add this logic to our workflow using the ``fail`` :term:`qualifier`.

.. code-block:: cylc-graph

   bake_cake => sell_cake
   bake_cake:fail => eat_cake

.. admonition:: Reminder
   :class: hint

   If you don't specify a qualifier Cylc assumes you mean ``:succeed`` so the
   following two lines are equivalent:

   .. code-block:: cylc-graph

      foo => bar
      foo:succeed => bar


Why Do We Need To Remove Tasks From The Graph?
----------------------------------------------

Create a new suite called ``suicide-triggers``::

   mkdir -p ~/cylc-run/suicide-triggers
   cd ~/cylc-run/suicide-triggers

Paste the following code into the ``suite.rc`` file:

.. code-block:: cylc

   [scheduling]
      cycling mode = integer
      initial cycle point = 1
      [[dependencies]]
          [[[P1]]]
              graph = """
                  make_cake_mixture => bake_cake => sell_cake
                  bake_cake:fail => eat_cake
              """
   [runtime]
       [[root]]
           script = sleep 2
       [[bake_cake]]
           # Random outcome 50% chance of success 50% chance of failure.
           script = sleep 2; if (( $RANDOM % 2 )); then true; else false; fi

Open the ``cylc gui`` and run the suite::

   cylc gui suicide-triggers &
   cylc run suicide-triggers

The suite will run for three cycles then get stuck. You should see something
similar to the diagram below. As the ``bake_cake`` task fails randomly what
you see might differ slightly. You may receive a "suite stalled" email.

.. digraph:: Example
   :align: center

   size = "7,5"

   subgraph cluster_1 {
      label = "1"
      style = "dashed"
      "make_cake_mixture.1" [
         label="make_cake_mixture\n1",
         style="filled",
         color="#ada5a5"]
      "bake_cake.1" [
         label="bake_cake\n1",
         style="filled",
         color="#ada5a5"]
      "sell_cake.1" [
         label="sell_cake\n1",
         style="filled",
         color="#ada5a5"]
      "eat_cake.1" [
         label="eat_cake\1",
         color="#88c6ff"]
   }

   subgraph cluster_2 {
      label = "2"
      style = "dashed"
      "make_cake_mixture.2" [
         label="make_cake_mixture\n2",
         style="filled",
         color="#ada5a5"]
      "bake_cake.2" [
         label="bake_cake\n2",
         style="filled",
         color="#ff0000",
         fontcolor="white"]
      "sell_cake.2" [
         label="sell_cake\2",
         color="#88c6ff"]
      "eat_cake.2" [
         label="eat_cake\n2",
         color="#888888",
         fontcolor="#888888"]
   }

   subgraph cluster_3 {
      label = "3"
      style = "dashed"
      "make_cake_mixture.3" [
         label="make_cake_mixture\n3",
         style="filled",
         color="#ada5a5"]
      "bake_cake.3" [
         label="bake_cake\n3",
         style="filled",
         color="#ff0000",
         fontcolor="white"]
      "sell_cake.3" [
         label="sell_cake\n3",
         color="#888888",
         fontcolor="#888888"]
      "eat_cake.3" [
         label="eat_cake\3",
         color="#888888",
         fontcolor="#888888"]
   }

   "make_cake_mixture.1" -> "bake_cake.1" -> "sell_cake.1"
   "bake_cake.1" -> "eat_cake.1"

   "make_cake_mixture.2" -> "bake_cake.2" -> "sell_cake.2"
   "bake_cake.2" -> "eat_cake.2"

   "make_cake_mixture.3" -> "bake_cake.3" -> "sell_cake.3"
   "bake_cake.3" -> "eat_cake.3"

The reason the suite stalls is that, by default, Cylc will run a maximum of
three cycles concurrently. As each cycle has at least one task which hasn't
either succeeded or failed Cylc cannot move onto the next cycle.

.. tip::
   
   For more information search ``max active cycle points`` in the
   `Cylc User Guide`_.

You will also notice that some of the tasks (e.g. ``eat_cake`` in cycle ``2``
in the above example) are drawn in a faded gray. This is because these tasks
have not yet been run in earlier cycles and as such cannot run.

.. TODO - Spawn On Demand!


Removing Tasks From The Graph
-----------------------------

In order to get around these problems and prevent the suite from stalling we
must remove the tasks that are no longer needed. We do this using suicide
triggers.

A suicide trigger is written like a normal dependency but with an exclamation
mark in-front of the task on the right-hand-side of the dependency meaning
*"remove the following task from the graph at the current cycle point."*

For example the following :term:`graph string` would remove the task ``bar``
from the graph if the task ``foo`` were to succeed.

.. code-block:: cylc-graph

   foo => ! bar

There are three cases where we would need to remove a task in the cake-making
example:

#. If the ``bake_cake`` task succeeds we don't need the ``eat_cake`` task so
   should remove it.

   .. code-block:: cylc-graph

      bake_cake => ! eat_cake

#. If the ``bake_cake`` task fails we don't need the ``sell_cake`` task so
   should remove it.

   .. code-block:: cylc-graph

      bake_cake:fail => ! sell_cake

#. If the ``bake_cake`` task fails then we will need to remove it else the
   suite will stall. We can do this after the ``eat_cake`` task has succeeded.

   .. code-block:: cylc-graph

      eat_cake => ! bake_cake

Add the following three lines to the suite's graph:

.. code-block:: cylc-graph

   bake_cake => ! eat_cake
   bake_cake:fail => ! sell_cake
   eat_cake => ! bake_cake

We can view suicide triggers in ``cylc graph`` by un-selecting the
:guilabel:`Ignore Suicide Triggers` button in the toolbar. Suicide triggers
will then appear as dashed lines with circular endings. You should see
something like this:

.. digraph:: Example
   :align: center

   make_cake_mixture -> bake_cake
   bake_cake -> sell_cake [style="dashed" arrowhead="dot"]
   bake_cake -> eat_cake [style="dashed" arrowhead="dot"]
   eat_cake -> bake_cake [style="dashed" arrowhead="dot"]


Downstream Dependencies
-----------------------

If we wanted to make the cycles run in order we might write an
:term:`inter-cycle dependency` like this:

.. code-block:: cylc-graph

   sell_cake[-P1] => make_cake_mixture

In order to handle the event that the ``sell_cake`` task has been removed from
the graph by a suicide trigger we can write our dependency with an or
symbol ``|`` like so:

.. code-block:: cylc-graph

   eat_cake[-P1] | sell_cake[-P1] => make_cake_mixture

Now the ``make_cake_mixture`` task from the next cycle will run after whichever
of the ``sell_cake`` or ``eat_cake`` tasks is run.

.. digraph:: Example
   :align: center

   subgraph cluster_1 {
      style="dashed"
      label="1"
      "make_cake_mixture.1" [label="make_cake_mixture\n1"]
      "bake_cake.1" [label="bake_cake\n1"]
      "make_cake_mixture.1" -> "bake_cake.1"
      "bake_cake.1" -> "sell_cake.1" [style="dashed" arrowhead="dot"]
      "bake_cake.1" -> "eat_cake.1" [style="dashed" arrowhead="dot"]
      "eat_cake.1" -> "bake_cake.1" [style="dashed" arrowhead="dot"]
      subgraph cluster_a {
         label = ":fail"
         fontcolor = "red"
         color = "red"
         style = "dashed"
         "eat_cake.1" [label="eat_cake\n1" color="red" fontcolor="red"]
      }
      subgraph cluster_b {
         label = ":success"
         fontcolor = "green"
         color = "green"
         style = "dashed"
         "sell_cake.1" [label="sell_cake\n1" color="green" fontcolor="green"]
      }
   }

   subgraph cluster_2 {
      style="dashed"
      label="2"
      "make_cake_mixture.2" [label="make_cake_mixture\n2"]
      "bake_cake.2" [label="bake_cake\n2"]
      "make_cake_mixture.2" -> "bake_cake.2"
      "bake_cake.2" -> "sell_cake.2" [style="dashed" arrowhead="dot"]
      "bake_cake.2" -> "eat_cake.2" [style="dashed" arrowhead="dot"]
      "eat_cake.2" -> "bake_cake.2" [style="dashed" arrowhead="dot"]
      subgraph cluster_c {
         label = ":fail"
         fontcolor = "red"
         color = "red"
         style = "dashed"
         "eat_cake.2" [label="eat_cake\n2" color="red" fontcolor="red"]
      }
      subgraph cluster_d {
         label = ":success"
         fontcolor = "green"
         color = "green"
         style = "dashed"
         "sell_cake.2" [label="sell_cake\n2" color="green" fontcolor="green"]
      }
   }

   "eat_cake.1" -> "make_cake_mixture.2" [arrowhead="onormal"]
   "sell_cake.1" -> "make_cake_mixture.2" [arrowhead="onormal"]

Add the following :term:`graph string` to your suite.

.. code-block:: cylc-graph

   eat_cake[-P1] | sell_cake[-P1] => make_cake_mixture

Open the ``cylc gui`` and run the suite. You should see that if the
``bake_cake`` task fails both it and the ``sell_cake`` task disappear and 
are replaced by the ``eat_cake`` task.


Comparing "Regular" and "Suicide" Triggers
------------------------------------------

In Cylc "regular" and "suicide" triggers both work in the same way. For example
the following graph lines implicitly combine using an ``&`` operator:

.. highlight:: cylc-graph

.. list-table::
   :class: grid-table

   * - ::

           foo => pub
           bar => pub
     - ::

           foo & bar => pub

Suicide triggers combine in the same way:

.. list-table::
   :class: grid-table

   * - ::

           foo => !pub
           bar => !pub
     - ::

           foo & bar => !pub

.. highlight:: python

This means that suicide triggers are treated as "invisible tasks" rather than
as "events". Suicide triggers can have pre-requisites just like a normal task.


Variations
----------

The following sections outline examples of how to use suicide triggers.

Recovery Task
^^^^^^^^^^^^^

A common use case where a ``recover`` task is used to handle a task failure.

.. digraph:: Example
   :align: center

   subgraph cluster_1 {
      label = ":fail"
      color = "red"
      fontcolor = "red"
      style = "dashed"
      recover
   }

   foo -> bar
   bar -> recover
   recover -> baz [arrowhead="onormal"]
   bar -> baz [arrowhead="onormal"]

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           graph = """
               # Regular graph.
               foo => bar

               # The fail case.
               bar:fail => recover

               # Remove the "recover" task in the success case.
               bar => ! recover

               # Remove the "bar" task in the fail case.
               recover => ! bar

               # Downstream dependencies.
               bar | recover => baz
           """
   [runtime]
       [[root]]
           script = sleep 1
       [[bar]]
           script = false

Branched Workflow
^^^^^^^^^^^^^^^^^

A workflow where sub-graphs of tasks are to be run in the success and or fail
cases.

.. digraph:: Example
   :align: center

   foo -> bar
   bar -> tar -> par
   bar -> jar -> par
   bar -> baz -> jaz

   subgraph cluster_1 {
      label = ":success"
      fontcolor = "green"
      color = "green"
      style = "dashed"
      tar
      jar
      par
   }

   subgraph cluster_2 {
      label = ":fail"
      fontcolor = "red"
      color = "red"
      style = "dashed"
      baz
      jaz
   }

   tar -> pub [arrowhead="onormal"]
   jaz -> pub [arrowhead="onormal"]

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           graph = """
               # Regular graph.
               foo => bar

               # Success case.
               bar => tar & jar

               # Fail case.
               bar:fail => baz => jaz

               # Remove tasks from the fail branch in the success case.
               bar => ! baz & ! jaz

               # Remove tasks from the success branch in the fail case.
               bar:fail => ! tar & ! jar & ! par

               # Remove the bar task in the fail case.
               baz => ! bar

               # Downstream dependencies.
               tar | jaz => pub
           """
   [runtime]
       [[root]]
           script = sleep 1
       [[bar]]
           script = true

Triggering Based On Other States
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In these examples we have been using suicide triggers to handle task failure.
The suicide trigger mechanism works with other qualifiers as well for example:

.. code-block:: cylc-graph

   foo:start => ! bar

Suicide triggers can also be used with custom outputs. In the following example
the task ``showdown`` produces one of three possible custom outputs, ``good``,
``bad`` or ``ugly``.

.. TODO - link to custom task outputs / write an advanced tutorial for them.

.. digraph:: Example
   :align: center

   subgraph cluster_1 {
      label = ":good"
      color = "green"
      fontcolor = "green"
      style = "dashed"
      good
   }
   subgraph cluster_2 {
      label = ":bad"
      color = "red"
      fontcolor = "red"
      style = "dashed"
      bad
   }
   subgraph cluster_3 {
      label = ":ugly"
      color = "purple"
      fontcolor = "purple"
      style = "dashed"
      ugly
   }
   showdown -> good
   showdown -> bad
   showdown -> ugly
   good -> fin [arrowhead="onormal"]
   bad -> fin [arrowhead="onormal"]
   ugly -> fin [arrowhead="onormal"]

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
            graph = """
                # The "regular" dependencies
                showdown:good => good
                showdown:bad => bad
                showdown:ugly => ugly
                good | bad | ugly => fin

                # The "suicide" dependencies for each case
                showdown:good | showdown:bad => ! ugly
                showdown:bad | showdown:ugly => ! good
                showdown:ugly | showdown:good => ! bad
            """
   [runtime]
       [[root]]
           script = sleep 1
       [[showdown]]
           # Randomly return one of the three custom outputs.
           script = """
               SEED=$RANDOM
               if ! (( $SEED % 3 )); then
                   cylc message 'The-Good'
               elif ! (( ( $SEED + 1 ) % 3 )); then
                   cylc message 'The-Bad'
               else
                   cylc message 'The-Ugly'
               fi
           """
           [[[outputs]]]
               # Register the three custom outputs with cylc.
               good = 'The-Good'
               bad = 'The-Bad'
               ugly = 'The-Ugly'

Self-Suiciding Task
^^^^^^^^^^^^^^^^^^^

An example of a workflow where there are no tasks which are dependent on the
task to suicide trigger.

.. digraph:: Example
   :align: center

   subgraph cluster_1 {
      label = "Faulty\nTask"
      color = "orange"
      fontcolor = "orange"
      style = "dashed"
      labelloc = "b"
      pub
   }

   foo -> bar -> baz
   bar -> pub


It is possible for a task to suicide trigger itself e.g:

.. code-block:: cylc-graph

   foo:fail => ! foo

.. warning::

   This is usually not recommended but in the case where there are no tasks
   dependent on the one to remove it is an acceptable approach.

.. code-block:: cylc

   [scheduling]
       [[dependencies]]
           graph = """
               foo => bar => baz
               bar => pub

               # Remove the "pub" task in the event of failure.
               pub:fail => ! pub
           """
   [runtime]
       [[root]]
           script = sleep 1
       [[pub]]
           script = false
