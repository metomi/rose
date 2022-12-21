.. include:: ../../../hyperlinks.rst
   :start-line: 1

.. _tutorial-rose-fail-if-warn-if:

Fail-If, Warn-If
================

Basic validation can be achieved using metadata settings such as ``type`` and
``range``. The ``fail-if`` and ``warn-if`` metadata settings are scriptable
enabling more advanced validation. They evaluate logical expressions,
flagging warnings if they return false.

``fail-if`` and ``warn-if`` can be run on the command line using
:ref:`command-rose-macro` or on-demand in the :ref:`command-rose-config-edit`
GUI.

.. note::

   Simple metadata settings such as ``range`` can be evaluated on-the-fly when
   a value changes. As ``fail-if`` and ``warn-if`` can take longer to evaluate
   they must be done on-demand in the :ref:`command-rose-config-edit` GUI or
   on the command line.


Syntax
------

The syntax is Pythonic, and relies on `Jinja2`_ to actually evaluate
relationships between values, after some initial pre-processing.

You can reference setting values by using their IDs - for example:

.. code-block:: rose

   fail-if=namelist:coffee=cup_volume < namelist:coffee=machine_output_volume;

You can also use ``this`` as a shorthand for the current (metadata section)
ID - e.g.:

.. code-block:: rose

   [namelist:coffee=daily_amount]
   fail-if=this < namelist:coffee=daily_min or this >= namelist:coffee=daily_max;

There is also shorthand for arrays, which we'll demonstrate later.

Note that the ``;`` at the end is optional when we only have one expression
(it's a delimiter), but it's better style to keep it.


Example
-------

We'll use the example of a rocket launch.

Create a new application called ``failif-warnif``::

   mkdir -p ~/rose-tutorial
   rose tutorial failif-warnif ~/rose-tutorial/failif-warnif
   cd ~/rose-tutorial/failif-warnif

You will now have a new Rose app with a :rose:file:`rose-app.conf` that
looks like this:

.. code-block:: rose

   [command]
   default=launch.exe

   [env]
   ORBITAL_SPEED_MS=1683.0

   [file:rocket_settings.nl]
   source=namelist:rocket

   [namelist:rocket]
   battery_levels=80, 60
   total_weight_kg=4700.0
   fuelless_weight_kg=2353.0
   specific_impulse_s=311.0

.. image:: http://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Apollo16LM.jpg/533px-Apollo16LM.jpg
   :align: right
   :alt: Apollo 11 Lunar Module, returning from the surface of the Moon
   :width: 250px

This app configuration controls the liftoff of a particular rocket -
in our case, the Lunar Module (Apollo Program spacecraft).

There is also metadata in the ``meta/rose-meta.conf`` file which provides the
application inputs with descriptions, help text and type information.

Try running :ref:`command-rose-config-edit` in the app directory. You should
be able to navigate between the pages and view the help and description for the
settings.


``fail-if``
-----------

If the ratio of rocket fuel to total weight is too high, or the efficiency
of the rocket (specific impulse) is too low, the Lunar Module will never
make it off the Moon.

We want to be able to flag an error based on a combination of the rocket
settings and the necessary orbital velocity (``env=ORBITAL_VELOCITY_MS``).
We need to set some ``fail-if`` metadata on one of these settings - as
it's evaluated on-demand, it doesn't matter which one we choose.

Open the ``meta/rose-meta.conf`` file in a text editor.

Add the following line to the metadata section
``[namelist:rocket=total_weight_kg]``:

.. code-block:: rose

   fail-if=this < namelist:rocket=fuelless_weight_kg * 2.7183**(env=ORBITAL_SPEED_MS / (9.8 * namelist:rocket=specific_impulse_s));

This states the relationship between these settings (a rearrangement
of the `Tsiolkovsky rocket equation`_). The rocket must have a
sufficient ratio of fuel to rocket mass, with a sufficiently fast
exhaust velocity (``=9.8 * namelist:rocket=specific_impulse_s``)
to get to the orbital speed ``env=ORBITAL_SPEED_MS``.

Save the metadata file and then reload the config editor metadata
(:menuselection:`Metadata -> Refresh Metadata`).

You now need to ask Rose to evaluate the ``fail-if`` condition, as
it's an on-demand process.

Either press the toolbar button :guilabel:`Check fail-if ...` or click
the menu item :menuselection:`Metadata --> Check fail-if, warn-if`.

Hopefully, this should not flag any errors, as these are the Apollo
mission parameters! A success message will appear in the bottom
right-hand corner of the window.

Try adding a few more moonrocks. Add ``1000`` to the values
of ``total_weight_kg`` and ``fuelless_weight_kg``.

Re-run the check by clicking
:menuselection:`Metadata --> Check fail-if, warn-if`. An error
dialog will appear, and the ``total_weight_kg`` setting will have
an error flag.

However, neither of these are very informative, other than quoting
the metadata.

Change the ``fail-if`` line to:

.. code-block:: rose

   fail-if=this < namelist:rocket=fuelless_weight_kg * 2.7183**(env=ORBITAL_SPEED_MS / (9.8 * namelist:rocket=specific_impulse_s));  # Fuel mass ratio or specific impulse too low to achieve orbit.

If you reload the metadata and run the check again, the error
message will include the helpful text.

You can also check the ``fail-if`` metadata by running
``rose macro --validate`` or ``rose macro -V`` in a terminal,
inside the app directory. Try saving the configuration in a failed
state, and then run the command.


``warn-if``
-----------

The ``warn-if`` metadata setting is exactly the same as ``fail-if``,
but is used to report non-critical concerns.

Let's try adding something for ``namelist:rocket=battery_levels``.

Open the metadata file ``meta/rose-meta.conf`` in a text editor,
and add this line to the ``[namelist:rocket=battery_levels]`` section:

.. code-block:: rose

   warn-if=namelist:rocket=battery_levels(1) < 75 or namelist:rocket=battery_levels(2) < 75;

This uses a special syntax for referencing the individual array
elements in ``battery_levels``.

If the first array element value and/or the second array element
value of ``battery_levels`` is less than 75% full, a warning will
be produced when the check is run.

We already know the shorthand syntax ``this``, so rephrase the metadata to:

.. code-block:: rose

   warn-if=this(1) < 75 or this(2) < 75;

Save the metadata file and then reload the config editor metadata.
Click :menuselection:`Metadata --> Check fail-if, warn-if` - a
warning should now appear for the ``battery_levels`` option.

For large arrays, it can sometimes be convenient to use whole-array
operations - the ``fail-if`` and ``warn-if`` syntax includes ``any()``
and ``all()``.

We can change the ``warn-if`` setting to:

.. code-block:: rose

   warn-if=any(this < 75);

which will flag a warning if any ``battery_levels`` array element
values are less than 75.


Multiple Expressions
--------------------

In both ``fail-if`` and ``warn-if``, expressions can be chained
using the Python operator ``or``, or you can separate them to give
clearer error/warning messages. Using our ``battery_levels`` example
again, change the setting to:

.. code-block:: rose

   warn-if=any(this < 75);
          =all(this > 95);

This will produce a warning if any elements are less than 75, and a
separate warning if all elements are greater than 95 (we don't
want to cook the batteries!).

You can add separate helper messages for each expression:

.. code-block:: rose

   warn-if=any(this < 75);   # Battery level low
          =all(this > 95);   # Don't over-charge!

Try adding the above lines to the metadata, saving and playing
about with the array numbers in the config editor and re-running
the ``fail-if``/``warn-if`` check.

.. tip::

   For more information, see :ref:`conf-meta`.


.. _Tsiolkovsky rocket equation: https://en.wikipedia.org/wiki/Tsiolkovsky_rocket_equation
