Jinja2 Templating
=================

Introduction
------------

This part of the Rose user guide walks you through using templating and ``rose-suite.conf`` variables in your ``suite.rc``, using `Jinja2`_.

This allows you to collapse repeated configuration, and move commonly used settings to a central place. It is particularly useful for suites with many, very similar tasks.


Example
-------

We'll demonstrate templating by using the finale of a firework display as an example.

Large firework displays can have sophisticated time-sensitive scheduling with a large number of similar 'tasks'.

We'll start out by looking at a ``suite.rc`` file that doesn't use any templating.

Create a new suite (or just a new directory somewhere - e.g. in your homespace) containing a blank ``rose-suite.conf`` and a ``suite.rc`` file that looks like this: `rocket-suite-python`.

This ``suite.rc`` has two families of tasks - tasks within a family are either identical (``IGNITE`` family) or variations on a theme (``DETONATE`` family). There are clear patterns in both the dependency graph and the ``[runtime]`` section.

We want to collapse most of this down with Jinja2.

Starting out
^^^^^^^^^^^^

The first thing to do is to mark the ``suite.rc`` as a jinja2 file by adding this shebang line to the top of the file:

.. code-block:: cylc

   #!jinja2

For loops
^^^^^^^^^

Let's have a look at using a ``for`` loop in Jinja2.

The dependency graph for the ignition tasks follows a simple pattern for the first 16 tasks.

We can replace the lines:

.. code-block:: cylc

   ignite_rocket_00 => \
   ignite_rocket_01 => \
   ignite_rocket_02 => \
   # continues...
   ignite_rocket_15 => \

with:

.. code-block:: cylc

   {%- for num in range(16) %}
           ignite_rocket_{{ num }} => \
   {%- endfor %}


We've used Jinja2 blocks ({% to %}) to template the ignite_rocket... line 16 times, substituting ({{ to }}) a number num in the line each time.

When evaluated, it will produce something that is very nearly correct:

.. code-block:: cylc

   ignite_rocket_0 => \
   ignite_rocket_1 => \
   ignite_rocket_2 => \
   ignite_rocket_3 => \
   # etc...

Variable assignment
^^^^^^^^^^^^^^^^^^^

This doesn't have properly formatted number suffixes like the original text - the original formatting would sort correctly in ``cylc gui`` (``_00``, ``_01``) and other output.

We can produce nicely formatted numbers by creating another variable in Jinja2, inside the for loop. Replace the for loop text with:

.. code-block:: cylc

   {%- for num in range(16) %}
   {%- set num_label = '%02d' % num %}
              ignite_rocket_{{ num_label }} => \
   {%- endfor %}

This would produce output like this:

.. code-block:: cylc

   ignite_rocket_00 => \
   ignite_rocket_01 => \
   ignite_rocket_02 => \
   # etc...

We can template away the rest of the graph in exactly the same way. Replace ``ignite_rocket_16 & \`` to ``ignite_rocket_28 & \`` with:

.. code-block:: cylc

   {%- for num in range(16, 29) %}
   {%- set num_label = '%02d' % num %}
      ignite_rocket_{{ num_label }} & \
   {%- endfor %}

However, this doesn't handle the special case of the ``ignite_rocket_29`` line, and it feels redundant to have an almost duplicated loop below our first one.


If blocks
^^^^^^^^^

Jinja2 supports if blocks, so we can actually change what we do based on the value of a Jinja2 variable. Replace the first and second loops and the ``ignite_rocket_29`` line with:

.. code-block:: cylc

   {%- for num in range(30) %}
   {%- set num_label = '%02d' % num %}
   {%- if num <= 15 %}
               ignite_rocket_{{ num_label }} => \
   {%- elif num == 29 %}
                             ignite_rocket_{{ num_label }}
   {%- else %}
                             ignite_rocket_{{ num_label }} & \
   {%- endif %}
   {%- endfor %}


We can also replace the last part of the dependency graph. Replace the whole ``ignite_rocket_00 => detonate_rocket_00`` to ``ignite_rocket_29 => detonate_rocket_29`` loop with:




.. _Jinja2: http://jinja.pocoo.org/docs/templates/ 
