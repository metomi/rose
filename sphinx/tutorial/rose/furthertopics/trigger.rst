Trigger
=======

The ``trigger`` metadata item can be used to cut down the amount of irrelevant
settings presented to the user in the :ref:`command-rose-config-edit` GUI by
hiding any settings which are not relevant based on the value or state of other
settings.

Irrelevant (``ignored`` or ``trigger-ignored``) settings do not get
included in output files at runtime. In effect, they are commented
out (``!`` or ``!!`` prefix in Rose configurations).


Example
-------

In this example, we'll be ordering pizza.

Create a new Rose application called ``trigger``::

   mkdir -p ~/rose-tutorial/trigger
   cd ~/rose-tutorial/trigger

Create a :rose:file:`rose-app.conf` file that looks like this:

.. TODO - Perhaps move these large code blocks out of this file using
          the Rose tutorial command.

.. code-block:: rose

   [command]
   default=order.exe

   [env]
   BUDGET=10

   [file:order.nl]
   source=namelist:pizza_order namelist:side_order

   [namelist:pizza_order]
   extra_chicken=.false.
   pepperoni_multiple=1
   no_mushrooms=.false.
   pizza_type='Veggie Supreme'
   truffle='none'

   [namelist:side_order]
   garlic_bread=.false.
   soft_drink=.false.

We'll add some metadata to make it nice. Create a ``meta/``
sub-directory with a :rose:file:`rose-meta.conf` file that looks like this:

.. code-block:: rose

   [env]

   [env=BUDGET]
   type=integer

   [file:order.nl]

   [namelist:pizza_order]

   [namelist:pizza_order=extra_chicken]
   type=logical

   [namelist:pizza_order=pepperoni_multiple]
   values=1,2,3

   [namelist:pizza_order=no_mushrooms]
   type=logical

   [namelist:pizza_order=pizza_type]
   sort-key=00-type
   values='Veggie Supreme', 'Pepperoni', 'BBQ Chicken'

   [namelist:pizza_order=truffle]
   values='none', 'white', 'black'

   [namelist:side_order]

   [namelist:side_order=garlic_bread]
   type=logical

   [namelist:side_order=soft_drink]
   type=logical

Once you've done that, run :ref:`command-rose-config-edit` in the application
directory and navigate around the pages.

There are quite a lot of settings that are only relevant in certain
contexts - for example, ``namelist:pizza_order=extra_chicken`` is
pretty irrelevant if we're ordering a ``'Veggie Supreme'``.


Adding Triggers
---------------

Let's add some trigger information.

In the :rose:file:`rose-meta.conf` file, under
``[namelist:pizza_order=pizza_type]``, add:

.. code-block:: cylc

   trigger=namelist:pizza_order=extra_chicken: 'BBQ Chicken';
           namelist:pizza_order=pepperoni_multiple: 'Pepperoni', 'BBQ Chicken';

This states which values of ``pizza_type`` are relevant for which
settings. This means that ``extra_chicken`` is only relevant when
``pizza_type`` is ``'BBQ Chicken'`` - otherwise, it should be in
an ignored state. ``pepperoni_multiple`` is relevant for more than
one value of ``pizza_type``.

We should also make sure we don't order over our budget, especially
by splashing out on truffles. Add the following to ``[env=BUDGET]``:

.. code-block:: cylc

   trigger=namelist:pizza_order=truffle: this > 25;
           namelist:side_order: this >= 10;

See :ref:`app-meta-mini-lang` for details on this syntax.

What we've done here is use a small subset of the Rose configuration
metadata logical syntax to specify a range of allowed values (the
``this > 25`` part). Here, ``this`` is a placeholder for the value of
``env=BUDGET``; the expression syntax is essentially Pythonic.

We've also specified a section ``namelist:side_order`` in the trigger,
which is perfectly valid - this means that the whole section and its
options will be ignored when the value of ``env=BUDGET`` is below 10.
The truffle option will be ignored unless ``env=BUDGET`` is more than
25.


Fixing Trigger Errors
---------------------

If we load the config editor (or reload the metadata) again, we
should get some trigger errors. These essentially say that some of
our settings are in the wrong state now - in our case, they should
be ``trigger-ignored``.

You can fix them on the command line by running ``rose macro --fix``
or ``rose macro -F`` in the app directory (one level up from the
meta directory) - this is what you would do if you were working with
a text editor and made changes to values.

Similarly, you can run "Autofix" in the config editor. You can do this
in three ways:

* By clicking the :menuselection:`Metadata --> Autofix all configurations`
  menu.
* Using the :guilabel:`Auto-fix` toolbar button.
* Or via the right-click menu for the root page in the left-hand tree panel,
  in this case ``pizza_order``.

Run "Autofix" in one of the above ways.

Results
^^^^^^^

If you accept the changes, the state of these settings will be corrected
- if you go to the page, you'll see that they've vanished! They're
actually just commented out, and viewable via the menu
:menuselection:`View --> View All Ignored Variables`.

Try altering the values of ``namelist:pizza_order=pizza_type`` and
``env=BUDGET`` with :menuselection:`View --> View All Ignored Variables`
on and off. This should enable and ``trigger-ignore`` different settings.

When ``env=BUDGET`` is below 10, the ``namelist:side_order`` section will
be ``trigger-ignored``, and the ``garlic_bread`` and ``soft_drink`` will
be ``section-ignored`` - ignored because their parent section is ignored.

You can get more information about why an option is ignored in the config
editor by hovering over its ignored flag, or looking at the option's menu
button ``Info`` entry.

Setting ids mentioned in the ``Info`` dialog are usually clickable links, so
you can go directly to the relevant id.


Multiple Inheritance
--------------------

More than one setting can decide whether something is relevant. In that
case, the subject is relevant only if all the parents agree that it is -
an AND relationship.

For example, we already have one trigger for
``namelist:pizza_order=truffle`` (``env=BUDGET``) - but it should also only
be relevant when ``namelist:pizza_order=no_mushrooms`` is ``.false.``.

Open the metadata file in a text editor, and add the following to the
``[namelist:pizza_order=no_mushrooms]`` metadata section:

.. code-block:: cylc

   trigger=namelist:pizza_order=truffle: .false.

This means that the ``namelist:pizza_order=truffle`` option will only
be enabled when ``env=BUDGET`` is greater than 25 (our older trigger)
and ``namelist:pizza_order=no_mushrooms`` is ``.false.``.

Save the metadata file and reload the metadata in the config editor, and
test it for yourself.


Cascading Triggering
--------------------

Triggering is not just based on values - if a setting is missing or
``trigger-ignored``, any settings that it triggers will be
``trigger-ignored`` by default i.e. triggers can
act in a cascade - A triggers B triggers C.

We can see this by replacing the ``env=BUDGET`` trigger with:

.. code-block:: cylc

   trigger=namelist:pizza_order=truffle: this > 25;
           namelist:side_order: this >= 10;
           namelist:pizza_order=pizza_type: this >= 5;

When ``env=BUDGET`` is less than 5, ``namelist:pizza_order=pizza_type``
will be ``trigger-ignored``. This means that all of its triggered
settings like ``namelist:pizza_order=extra_chicken`` are irrelevant and
will also be ``trigger-ignored``.

We need to add ``no_mushrooms`` to the ``[namelist:pizza_order=pizza_type]``
section so that it is ``trigger-ignored`` when no pizza can be ordered -
replace the ``[namelist:pizza_order=pizza_type]`` trigger with:

.. code-block:: cylc

   trigger=namelist:pizza_order=extra_chicken: 'BBQ Chicken';
           namelist:pizza_order=pepperoni_multiple: 'Pepperoni', 'BBQ Chicken';
           namelist:pizza_order=no_mushrooms;

Save, reload, and try changing ``env=BUDGET`` below 5 to see what it does
to the options in ``namelist:pizza_order``.


Triggering Based On State
-------------------------

There's also another way to express a trigger - you don't have to express
a value or range of values in a trigger expression.

Quite often you only want a setting to be ``trigger-ignored`` or enabled
purely based on the availability of another setting - whether it is present
and whether it is ``trigger-ignored``. You might not care what particular
value it has.

This can be expressed by adding a trigger but omitting the value part of
the syntax. Let's add an option that we can use.

Add a new variable in the metadata by adding these lines to the metadata
file:

.. code-block:: cylc

   [namelist:pizza_order=dip_type]
   values='Garlic','Sour Cream','Salsa','Brown Sauce','Mustard'

We should add a trigger expression as well - replace the
``[namelist:pizza_order=pizza_type]`` trigger with:

.. code-block:: cylc

   trigger=namelist:pizza_order=extra_chicken: 'BBQ Chicken';
           namelist:pizza_order=pepperoni_multiple: 'Pepperoni', 'BBQ Chicken';
           namelist:pizza_order=no_mushrooms;
           namelist:pizza_order=dip_type;

This means that ``namelist:pizza_order=dip_type`` is dependent on
``namelist:pizza_order=pizza_type``, and will only be ignored when that
is ignored - but the value of ``pizza_type`` doesn't matter to it.

.. TODO - Rephrase this ^

Save the file and reload the metadata in the config editor. We'll need to
add the ``namelist:pizza_order=dip_type`` to use it properly - you can do
this from the ``namelist:pizza_order`` page via:

* The :guilabel:`Add` toolbar button.
* The right-click page menu.
* The :menuselection:`View --> View Latent Variables` menu.

After enabling the view, you should see ``dip_type`` appear as an option
that could be added. It will already have the correct triggered state (the
same state as ``namelist:pizza_order=pizza_type``) - verify for yourself
that this works! You can then just add it via the menu button for the
option.


Further Reading
---------------

For more informaiton see :ref:`Metadata`.
