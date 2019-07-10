.. _tutorial-integer-cycling:

Basic Cycling
=============


In this section we will look at how to write :term:`cycling` (repeating)
workflows.


Repeating Workflows
-------------------

.. ifnotslides::

   Often, we will want to repeat the same workflow multiple times. In Cylc this
   "repetition" is called :term:`cycling` and each repetition of the workflow is
   referred to as a :term:`cycle`.

   Each :term:`cycle` is given a unique label. This is called a
   :term:`cycle point`. For now these :term:`cycle points<cycle point>` will be
   integers *(they can also be dates as we will see in the next section)*.

To make a workflow repeat we must tell Cylc three things:

.. ifslides::

   * :term:`recurrence`
   * :term:`initial cycle point`
   * :term:`final cycle point`

.. ifnotslides::

   The :term:`recurrence`
      How often we want the workflow to repeat.
   The :term:`initial cycle point`
      At what cycle point we want to start the workflow.
   The :term:`final cycle point`
      *Optionally* we can also tell Cylc what cycle point we want to stop the
      workflow.

.. nextslide::

.. ifnotslides::

   Let's take the bakery example from the previous section. Bread is
   produced in batches so the bakery will repeat this workflow for each
   batch of bread they bake. We can make this workflow repeat with the addition
   of three lines:

.. code-block:: diff

    [scheduling]
   +    cycling mode = integer
   +    initial cycle point = 1
        [[dependencies]]
   +        [[[P1]]]
                graph = """
                    purchase_ingredients => make_dough
                    pre_heat_oven & make_dough => bake_bread => sell_bread & clean_oven
                """

.. nextslide::

.. ifnotslides::

   * The ``cycling mode = integer`` setting tells Cylc that we want our
     :term:`cycle points <cycle point>` to be numbered.
   * The ``initial cycle point = 1`` setting tells Cylc to start counting
     from 1.
   * ``P1`` is the :term:`recurrence`. The :term:`graph` within the ``[[[P1]]]``
     section will be repeated at each :term:`cycle point`.

   The first three :term:`cycles<cycle>` would look like this, with the entire
   workflow repeated at each cycle point:

.. digraph:: example
   :align: center

   size = "7,15"

   subgraph cluster_1 {
       label = 1
       style = dashed
       "pur.1" [label="purchase_ingredients\n1"]
       "mak.1" [label="make_dough\n1"]
       "bak.1" [label="bake_bread\n1"]
       "sel.1" [label="sell_bread\n1"]
       "cle.1" [label="clean_oven\n1"]
       "pre.1" [label="pre_heat_oven\n1"]
   }

   subgraph cluster_2 {
       label = 2
       style = dashed
       "pur.2" [label="purchase_ingredients\n2"]
       "mak.2" [label="make_dough\n2"]
       "bak.2" [label="bake_bread\n2"]
       "sel.2" [label="sell_bread\n2"]
       "cle.2" [label="clean_oven\n2"]
       "pre.2" [label="pre_heat_oven\n2"]
   }

   subgraph cluster_3 {
       label = 3
       style = dashed
       "pur.3" [label="purchase_ingredients\n3"]
       "mak.3" [label="make_dough\n3"]
       "bak.3" [label="bake_bread\n3"]
       "sel.3" [label="sell_bread\n3"]
       "cle.3" [label="clean_oven\n3"]
       "pre.3" [label="pre_heat_oven\n3"]
   }

   "pur.1" -> "mak.1" -> "bak.1" -> "sel.1"
   "pre.1" -> "bak.1" -> "cle.1"
   "pur.2" -> "mak.2" -> "bak.2" -> "sel.2"
   "pre.2" -> "bak.2" -> "cle.2"
   "pur.3" -> "mak.3" -> "bak.3" -> "sel.3"
   "pre.3" -> "bak.3" -> "cle.3"

.. ifnotslides::

   Note the numbers under each task which represent the :term:`cycle point` each
   task is in.


Inter-Cycle Dependencies
------------------------

.. ifnotslides::

   We've just seen how to write a workflow that repeats every :term:`cycle`.

   Cylc runs tasks as soon as their dependencies are met so cycles are not
   necessarily run in order. This could cause problems, for instance we could
   find ourselves pre-heating the oven in one cycle whist we are still
   cleaning it in another.

   To resolve this we must add :term:`dependencies<dependency>` *between* the
   cycles. We do this by adding lines to the :term:`graph`. Tasks in the
   previous cycle can be referred to by suffixing their name with ``[-P1]``,
   for example. So to ensure the ``clean_oven`` task has been completed before
   the start of the ``pre_heat_oven`` task in the next cycle, we would write
   the following dependency:

   .. code-block:: cylc-graph

      clean_oven[-P1] => pre_heat_oven

   This dependency can be added to the suite by adding it to the other graph
   lines:

.. code-block:: diff

    [scheduling]
        cycling mode = integer
        initial cycle point = 1
        [[dependencies]]
            [[[P1]]]
                graph = """
                    purchase_ingredients => make_dough
                    pre_heat_oven & make_dough => bake_bread => sell_bread & clean_oven
   +                clean_oven[-P1] => pre_heat_oven
                """

.. nextslide::

.. ifnotslides::

   The resulting suite would look like this:

.. digraph:: example
   :align: center

   size = "7,15"

   subgraph cluster_1 {
       label = 1
       style = dashed
       "pur.1" [label="purchase_ingredients\n1"]
       "mak.1" [label="make_dough\n1"]
       "bak.1" [label="bake_bread\n1"]
       "sel.1" [label="sell_bread\n1"]
       "cle.1" [label="clean_oven\n1"]
       "pre.1" [label="pre_heat_oven\n1"]
   }

   subgraph cluster_2 {
       label = 2
       style = dashed
       "pur.2" [label="purchase_ingredients\n2"]
       "mak.2" [label="make_dough\n2"]
       "bak.2" [label="bake_bread\n2"]
       "sel.2" [label="sell_bread\n2"]
       "cle.2" [label="clean_oven\n2"]
       "pre.2" [label="pre_heat_oven\n2"]
   }

   subgraph cluster_3 {
       label = 3
       style = dashed
       "pur.3" [label="purchase_ingredients\n3"]
       "mak.3" [label="make_dough\n3"]
       "bak.3" [label="bake_bread\n3"]
       "sel.3" [label="sell_bread\n3"]
       "cle.3" [label="clean_oven\n3"]
       "pre.3" [label="pre_heat_oven\n3"]
   }

   "pur.1" -> "mak.1" -> "bak.1" -> "sel.1"
   "pre.1" -> "bak.1" -> "cle.1"
   "cle.1" -> "pre.2"
   "pur.2" -> "mak.2" -> "bak.2" -> "sel.2"
   "pre.2" -> "bak.2" -> "cle.2"
   "cle.2" -> "pre.3"
   "pur.3" -> "mak.3" -> "bak.3" -> "sel.3"
   "pre.3" -> "bak.3" -> "cle.3"

.. nextslide::

.. ifnotslides::

   Adding this dependency "strings together" the cycles, forcing them to run in
   order. We refer to dependencies between cycles as
   :term:`inter-cycle dependencies<inter-cycle dependency>`.

   In the dependency the ``[-P1]`` suffix tells Cylc that we are referring to a
   task in the previous cycle. Equally ``[-P2]`` would refer to a task two
   cycles ago.

   Note that the ``purchase_ingredients`` task has no arrows pointing at it
   meaning that it has no dependencies. Consequently the ``purchase_ingredients``
   tasks will all run straight away. This could cause our bakery to run into
   cash-flow problems as they would be purchasing ingredients well in advance
   of using them.

   To solve this, but still make sure that they never run out of
   ingredients, the bakery wants to purchase ingredients two batches ahead.
   This can be achieved by adding the following dependency:

.. ifslides::

   We need ``purchase_ingredients`` to be dependent on ``sell_bread`` from
   two cycles before.

.. nextslide::

.. code-block:: diff

    [scheduling]
        cycling mode = integer
        initial cycle point = 1
        [[dependencies]]
            [[[P1]]]
                graph = """
                    purchase_ingredients => make_dough
                    pre_heat_oven & make_dough => bake_bread => sell_bread & clean_oven
                    clean_oven[-P1] => pre_heat_oven
   +                sell_bread[-P2] => purchase_ingredients
                """

.. nextslide::

.. ifnotslides::

   This dependency means that the ``purchase_ingredients`` task will run after
   the ``sell_bread`` task two cycles before.

.. note::

   The ``[-P2]`` suffix is used to reference a task two cycles before. For the
   first two cycles this doesn't make sense as there was no cycle two cycles
   before, so this dependency will be ignored.

   Any inter-cycle dependencies stretching back to before the
   :term:`initial cycle point` will be ignored.

.. digraph:: example
   :align: center

   size = "4.5,15"

   subgraph cluster_1 {
       label = 1
       style = dashed
       "pur.1" [label="purchase_ingredients\n1"]
       "mak.1" [label="make_dough\n1"]
       "bak.1" [label="bake_bread\n1"]
       "sel.1" [label="sell_bread\n1"]
       "cle.1" [label="clean_oven\n1"]
       "pre.1" [label="pre_heat_oven\n1"]
   }

   subgraph cluster_2 {
       label = 2
       style = dashed
       "pur.2" [label="purchase_ingredients\n2"]
       "mak.2" [label="make_dough\n2"]
       "bak.2" [label="bake_bread\n2"]
       "sel.2" [label="sell_bread\n2"]
       "cle.2" [label="clean_oven\n2"]
       "pre.2" [label="pre_heat_oven\n2"]
   }

   subgraph cluster_3 {
       label = 3
       style = dashed
       "pur.3" [label="purchase_ingredients\n3"]
       "mak.3" [label="make_dough\n3"]
       "bak.3" [label="bake_bread\n3"]
       "sel.3" [label="sell_bread\n3"]
       "cle.3" [label="clean_oven\n3"]
       "pre.3" [label="pre_heat_oven\n3"]
   }

   subgraph cluster_4 {
       label = 4
       style = dashed
       "pur.4" [label="purchase_ingredients\n4"]
       "mak.4" [label="make_dough\n4"]
       "bak.4" [label="bake_bread\n4"]
       "sel.4" [label="sell_bread\n4"]
       "cle.4" [label="clean_oven\n4"]
       "pre.4" [label="pre_heat_oven\n4"]
   }

   "pur.1" -> "mak.1" -> "bak.1" -> "sel.1"
   "pre.1" -> "bak.1" -> "cle.1"
   "cle.1" -> "pre.2"
   "sel.1" -> "pur.3"
   "pur.2" -> "mak.2" -> "bak.2" -> "sel.2"
   "pre.2" -> "bak.2" -> "cle.2"
   "cle.2" -> "pre.3"
   "sel.2" -> "pur.4"
   "pur.3" -> "mak.3" -> "bak.3" -> "sel.3"
   "pre.3" -> "bak.3" -> "cle.3"
   "cle.3" -> "pre.4"
   "pur.4" -> "mak.4" -> "bak.4" -> "sel.4"
   "pre.4" -> "bak.4" -> "cle.4"


Recurrence Sections
-------------------

.. ifnotslides::

   In the previous examples we made the workflow repeat by placing the graph
   within the ``[[[P1]]]`` section. Here ``P1`` is a :term:`recurrence` meaning
   repeat every cycle, where ``P1`` means every cycle, ``P2`` means every
   *other* cycle, and so on. To build more complex workflows we can use multiple
   recurrences:

.. code-block:: cylc

   [scheduling]
       cycling mode = integer
       initial cycle point = 1
       [[dependencies]]
           [[[P1]]]  # Repeat every cycle.
               graph = foo
           [[[P2]]]  # Repeat every second cycle.
               graph = bar
           [[[P3]]]  # Repeat every third cycle.
               graph = baz

.. digraph:: example
   :align: center

   subgraph cluster_1 {
       label = 1
       style = dashed
       "foo.1" [label="foo\n1"]
       "bar.1" [label="bar\n1"]
       "baz.1" [label="baz\n1"]
   }

   subgraph cluster_2 {
       label = 2
       style = dashed
       "foo.2" [label="foo\n2"]
   }

   subgraph cluster_3 {
       label = 3
       style = dashed
       "foo.3" [label="foo\n3"]
       "bar.3" [label="bar\n3"]
   }

.. nextslide::

.. ifnotslides::

   By default recurrences start at the :term:`initial cycle point`, however it
   is possible to make them start at an arbitrary cycle point. This is done by
   writing the cycle point and the recurrence separated by a forward slash
   (``/``), e.g. ``5/P3`` means repeat every third cycle starting *from* cycle
   number 5.

   The start point of a recurrence can also be defined as an offset from the
   :term:`initial cycle point`, e.g. ``+P5/P3`` means repeat every third cycle
   starting 5 cycles *after* the initial cycle point.

.. ifslides::

   ``5/P3``
      Repeat every third cycle starting *from* cycle number 5.
   ``+P5/P3``
      Repeat every third cycle starting 5 cycles *after* the initial cycle
      point.

   .. nextslide::

   .. rubric:: In this practical we will take the :term:`suite <Cylc suite>`
      we wrote in the previous section and turn it into a
      :term:`cycling suite <cycling>`.

   Next section: :ref:`tutorial-datetime-cycling`

.. _basic cycling practical:

.. practical::

   .. rubric:: In this practical we will take the :term:`suite <Cylc suite>`
      we wrote in the previous section and turn it into a
      :term:`cycling suite <cycling>`.

   If you have not completed the previous practical use the following code for
   your ``suite.rc`` file.

   .. code-block:: cylc

      [scheduling]
          [[dependencies]]
              graph = """
                  foo & pub => bar => baz & wop
                  baz => qux
              """

   #. **Create a new suite.**

      Within your ``~/cylc-run/`` directory create a new (sub-)directory called
      ``integer-cycling`` and move into it:

      .. code-block:: bash

         mkdir -p ~/cylc-run/integer-cycling
         cd ~/cylc-run/integer-cycling

      Copy the above code into a ``suite.rc`` file in that directory.

   #. **Make the suite cycle.**

      Add in the following lines.

      .. code-block:: diff
   
          [scheduling]
         +    cycling mode = integer
         +    initial cycle point = 1
              [[dependencies]]
         +        [[[P1]]]
                      graph = """
                          foo & pub => bar => baz & wop
                          baz => qux
                      """

   #. **Visualise the suite.**

      Try visualising the suite using ``cylc graph``.

      .. code-block:: none

         cylc graph .

      .. tip::

         You can get Cylc graph to draw dotted boxes around the cycles by
         clicking the "Organise by cycle point" button on the toolbar:

         .. image:: ../img/cylc-graph-cluster.png
            :align: center

      .. tip::

         By default ``cylc graph`` displays the first three cycles of a suite.
         You can tell ``cylc graph`` to visualise the cycles between two points
         by providing them as arguments, for instance the following example
         would show all cycles between ``1`` and ``5`` (inclusive)::

            cylc graph . 1 5 &

   #. **Add another recurrence.**

      Suppose we wanted the ``qux`` task to run every *other* cycle as opposed
      to every cycle. We can do this by adding another recurrence.

      Make the following changes to your ``suite.rc`` file.

      .. code-block:: diff

          [scheduling]
              cycling mode = integer
              initial cycle point = 1
              [[dependencies]]
                  [[[P1]]]
                      graph = """
                          foo & pub => bar => baz & wop
         -                baz => qux
                      """
         +        [[[P2]]]
         +            graph = """
         +                baz => qux
         +            """

      Use ``cylc graph`` to see the effect this has on the workflow.

   #. **Inter-cycle dependencies.**

      Next we need to add some inter-cycle dependencies. We are going to add
      three inter-cycle dependencies:

      #. Between ``wop`` from the previous cycle and ``pub``.
      #. Between ``baz`` from the previous cycle and ``foo``
         *every odd cycle* (e.g. baz.2 => foo.3).
      #. Between ``qux`` from the previous cycle and ``foo``
         *every even cycle* (e.g. qux.1 => foo.2).

      Have a go at adding inter-cycle dependencies to your ``suite.rc`` file to
      make your workflow match the diagram below.

      .. hint::

         * ``P2`` means every odd cycle.
         * ``2/P2`` means every even cycle.

      .. digraph:: example
        :align: center

         size = "4.5,7"

         subgraph cluster_1 {
             label = 1
             style = dashed
             "foo.1" [label="foo\n1"]
             "bar.1" [label="bar\n1"]
             "baz.1" [label="baz\n1"]
             "wop.1" [label="wop\n1"]
             "pub.1" [label="pub\n1"]
             "qux.1" [label="qux\n1"]
         }

         subgraph cluster_2 {
             label = 2
             style = dashed
             "foo.2" [label="foo\n2"]
             "bar.2" [label="bar\n2"]
             "baz.2" [label="baz\n2"]
             "wop.2" [label="wop\n2"]
             "pub.2" [label="pub\n2"]
         }

         subgraph cluster_3 {
             label = 3
             style = dashed
             "foo.3" [label="foo\n3"]
             "bar.3" [label="bar\n3"]
             "baz.3" [label="baz\n3"]
             "wop.3" [label="wop\n3"]
             "pub.3" [label="pub\n3"]
             "qux.3" [label="qux\n3"]
         }

         "foo.1" -> "bar.1" -> "wop.1"
         "bar.1" -> "baz.1"
         "pub.1" -> "bar.1"
         "foo.2" -> "bar.2" -> "wop.2"
         "bar.2" -> "baz.2"
         "pub.2" -> "bar.2"
         "foo.3" -> "bar.3" -> "wop.3"
         "bar.3" -> "baz.3"
         "pub.3" -> "bar.3"
         "baz.1" -> "qux.1" -> "foo.2"
         "baz.3" -> "qux.3"
         "baz.2" -> "foo.3"
         "wop.1" -> "pub.2"
         "wop.2" -> "pub.3"

      .. spoiler:: Solution warning

         .. code-block:: cylc


            [scheduling]
                cycling mode = integer
                initial cycle point = 1
                [[dependencies]]
                    [[[P1]]]
                        graph = """
                            foo & pub => bar => baz & wop
                            wop[-P1] => pub  # (1)
                        """
                    [[[P2]]]
                        graph = """
                            baz => qux
                            baz[-P1] => foo  # (2)
                        """
                    [[[2/P2]]]
                        graph = """
                            qux[-P1] => foo  # (3)
                        """
