Upgrading Macro Development
===========================

Upgrade macros are used to upgrade :term:`Rose apps <Rose app>` to newer
metadata versions. They are intended to keep application configurations in
sync with changes to application inputs e.g. from new code releases.

You should already be familiar with using :ref:`command-rose-app-upgrade` (see
the :ref:`Upgrading tutorial <tutorial-rose-upgrade-macros>` and the concepts
in the reference material).


Example
-------

.. image:: http://upload.wikimedia.org/wikipedia/commons/b/b9/Proa1.jpg
   :align: right
   :width: 250px

In this example, we'll be upgrading a boat on a desert island.

Create a Rose application called ``make-boat-app``::

   mkdir -p ~/rose-tutorial/make-boat-app
   cd ~/rose-tutorial/make-boat-app


Create a ``rose-app.conf`` file with the following content:

.. code-block:: rose

   meta=make-boat/0.1

   [namelist:materials]
   hollow_tree_trunks=1
   paddling_twigs=1

You now have a Rose application configuration that configures our simple boat
(a dugout canoe). It references a meta flag (for which metadata is unlikely to
already exist), made up of a category (``make-boat``) at a particular
version (``0.1``). The meta flag is used by Rose to locate a configuration
metadata directory.

Make sure you're using ``make-boat`` and not ``make_boat`` - the hyphen
makes all the difference!

.. note::

   The version in the meta flag doesn't have to be numeric - it could be
   ``vn0.1`` or ``alpha`` or ``Crafty-Canoe``.

We need to create some metadata to make this work.


Example Metadata
----------------

We need a ``rose-meta/`` directory somewhere, to store our metadata -
for the purposes of this tutorial it's easiest to put in in your homespace,
but the location does not matter.

Create a ``rose-meta/make-boat/`` directory in your homespace::

   mkdir -p ~/rose-meta/make-boat/

This is the category (also called command) directory for the metadata,
which will hold sub-directories for actual configuration metadata
versions (each containing a :rose:file:`rose-meta.conf` file, etc).

N.B. Configuration metadata would normally be managed by whoever manages
Rose installation at your site.

We know we need some metadata for the ``0.1`` version, so create a
``0.1/`` subdirectory under ``rose-meta/make-boat/``::

   mkdir ~/rose-meta/make-boat/0.1/

We'll need a :rose:file:`rose-meta.conf` file there too, so create an empty
one in the new directory::

   touch ~/rose-meta/make-boat/0.1/rose-meta.conf

We can safely say that our two namelist inputs are essential for the
construction and testing of the boat, so we can paste the following into
the newly created :rose:file:`rose-meta.conf` file:

.. code-block:: rose

   [namelist:materials=hollow_tree_trunks]
   compulsory=true
   values=1

   [namelist:materials=paddling_twigs]
   compulsory=true
   range=1:
   type=integer

So far, we have a normal application configuration which references
some metadata, somewhere, for a category at a certain version.

Let's make another version to upgrade to.

The next version of our boat will have `outriggers`_ to make it more
stable. Some of the inputs in our application configuration will need
to change.

Our application configuration might need to look something like this,
after any upgrade (don't change it yet!):

.. code-block:: rose

   meta=make-boat/0.2

   [namelist:materials]
   hollow_tree_trunks=1
   misc_branches=4
   outrigger_tree_trunks=2
   paddling_branches=1

It looks like we've added the inputs ``misc_branches``,
``outrigger_tree_trunks`` and ``paddling_branches``. ``paddling_twigs``
is now no longer there (now redundant), so we can remove it from the
configuration when we upgrade.

Let's create the new metadata version, to document what we need and
don't need.

Create a new subdirectory under ``make-boat/`` called ``0.2/`` containing
a :rose:file:`rose-meta.conf` file that looks like this:

.. code-block:: rose

   [namelist:materials=hollow_tree_trunks]
   compulsory=true
   values=1

   [namelist:materials=misc_branches]
   compulsory=true
   range=4:

   [namelist:materials=paddling_branches]
   compulsory=true
   range=1:
   type=integer

   [namelist:materials=outrigger_tree_trunks]
   compulsory=true
   values=2

You can check that everything is OK so far by changing directory to the
``make-boat/`` directory and running ``find`` - it should look
something like:

.. code-block:: none

   .
   ./0.1
   ./0.1/rose-meta.conf
   ./0.2
   ./0.2/rose-meta.conf

We now want to automate the process of updating our app config from
``make-boat/0.1`` to the new ``make-boat/0.2`` version.


``versions.py``
---------------

Upgrade macros are invoked through a Python module, ``versions.py``,
that doesn't live with any particular version metadata - it should be
present at the root of the category directory.

Create a new file ``versions.py`` under ``make-boat/``
(``~/rose-meta/make-boat/versions.py``). We'll add a macro to it in a
little bit.

Upgrade Macros Explained
^^^^^^^^^^^^^^^^^^^^^^^^

Upgrade macros are Python objects with a ``BEFORE_TAG`` (e.g. ``"0.1"``)
and an ``AFTER_TAG`` (e.g. ``"0.2"``). The ``BEFORE_TAG`` is the 'start'
version (if upgrading) and the ``AFTER_TAG`` is the 'destination' version.

When a user requests an upgrade for their configuration (e.g. by running
:ref:`command-rose-app-upgrade`), the ``versions.py`` file will be searched
for a macro whose ``BEFORE_TAG`` matches the ``meta=...`` version.

For example, for our ``meta=make-boat/0.1`` flag, we'd need a macro whose
``BEFORE_TAG`` was ``"0.1"``.

When a particular upgrade macro is run, the version in the app
configuration will be changed from ``BEFORE_TAG`` to ``AFTER_TAG`` (e.g.
``meta=make-boat/0.1`` to ``meta=make-boat/0.2``), as well as making
other changes to the configuration if needed, like adding/removing the
right variables.

If the user wanted to upgrade across multiple versions - e.g. ``0.1`` to
``0.4`` - there would need to be a chain of objects whose ``BEFORE_TAG``
was equal to the last ``AFTER_TAG``, ending in an ``AFTER_TAG`` of
``0.4``.

We'll cover multiple version upgrading later in the tutorial.

Upgrade Macro Skeleton
^^^^^^^^^^^^^^^^^^^^^^

Upgrade macros are bits of Python code that essentially look like this:

.. code-block:: python

   class Upgrade272to273(rose.upgrade.MacroUpgrade):

       """Upgrade from 27.2 to 27.3."""

       BEFORE_TAG = "27.2"
       AFTER_TAG = "27.3"

       def upgrade(self, config, meta_config=None):
           """Upgrade the application configuration (config)."""
           # Some code doing something to config goes here.
           return config, self.reports

They are sub-classes of a particular class,
:py:class:`rose.upgrade.MacroUpgrade`,
which means that some of the Python functionality is done 'under the hood'
to make things easier.

You shouldn't need to know very much Python to get most things done.

Example Upgrade Macro
^^^^^^^^^^^^^^^^^^^^^

Paste the following into your ``versions.py`` file:

.. code-block:: python

   import rose.upgrade


   class MyFirstUpgradeMacro(rose.upgrade.MacroUpgrade):

       """Upgrade from 0.1 (Canonical Canoe) to 0.2 (Outrageous Outrigger)."""

       BEFORE_TAG = "0.1"
       AFTER_TAG = "0.2"

       def upgrade(self, config, meta_config=None):
           """Upgrade the boat!"""
           # Some code doing something to config goes here.
           return config, self.reports

This is already a functional upgrade macro - although it won't do anything.

.. note::

   The name of the class (``MyFirstUpgradeMacro``) doesn't need to
   be related to the versions - the only identifiers that matter are the
   ``BEFORE_TAG`` and the ``AFTER_TAG``.

We need to get the macro to do the following:

* add the option ``namelist:materials=misc_branches``
* add the option ``namelist:materials=outrigger_tree_trunks``
* add the option ``namelist:materials=paddling_branches``
* remove the option ``namelist:materials=paddling_twigs``

We can use the :ref:`rose-upgr-macros` provided to express this in Python code.
Replace the ``# Some code doing something...`` line with:

.. code-block:: python

   self.add_setting(config, ["namelist:materials", "misc_branches"], "4")
   self.add_setting(
            config, ["namelist:materials", "outrigger_tree_trunks"], "2")
   self.add_setting(
            config, ["namelist:materials", "paddling_branches"], "1")
   self.remove_setting(config, ["namelist:materials", "paddling_twigs"])

This changes the app configuration (``config``) in the way we want, and
(behind the scenes) adds some things to the ``self.reports`` list
mentioned in the ``return config, self.reports`` line.

.. note::

   When we add options like ``misc_branches``, we must specify default values
   to assign to them.

.. tip::

   Values should always be specified as strings e.g. (``"1"`` rather than
   ``1``).

Customising the Output
^^^^^^^^^^^^^^^^^^^^^^

The methods ``self.add_setting`` and ``self.remove_setting`` will provide
a default message to the user about the change (e.g.
``"Added X with value Y"``), but you can customise them to add your own
using the info 'keyword argument' like this:

.. code-block:: python

   self.add_setting(
       config, ["namelist:materials", "outrigger_tree_trunks"], "2",
       info="This makes it into a trimaran!")

If you want to, try adding your own messages.

Running ``rose app-upgrade``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Our upgrade macro will now work - change directory to the application
directory and run::

   rose app-upgrade --meta-path=~/rose-meta/

This should display some information about the current and available
versions - see the help by running ``rose help app-upgrade``.

``--meta-path`` equals the path to the ``rose-meta/`` directory you
created - as this path isn't configured in the site/user configuration,
we need to set it manually. This won't normally be the case for users,
if the metadata is centrally managed.

Let's upgrade to ``0.2``. Run::

   rose app-upgrade --meta-path=~/rose-meta/ 0.2

This should provide you with a summary of changes (including any custom
messages you may have added) and prompt you to accept them. Accept them
and have a look at the app config file - it should have been changed
accordingly.

Using Patch Configurations
^^^^^^^^^^^^^^^^^^^^^^^^^^

For relatively straightforward changes like the one above, we can
configure a macro to apply patches to the configuration without having
to write setting-specific Python code.

We'll add a rudder option for our ``0.3`` version, with a
``namelist:materials=l_rudder_branch``.

Create a ``0.3`` directory in the same way that you created the ``0.1``
and ``0.2`` metadata directories. Add a :rose:file:`rose-meta.conf` file that
looks like this:

.. code-block:: rose

   [namelist:materials=hollow_tree_trunks]
   compulsory=true
   values=1

   [namelist:materials=l_rudder_branch]
   compulsory=true
   type=logical

   [namelist:materials=misc_branches]
   compulsory=true
   type=integer
   range=4:

   [namelist:materials=outrigger_tree_trunks]
   compulsory=true
   values=2

   [namelist:materials=paddling_branches]
   compulsory=true
   range=1:
   type=integer

We need to write another macro in ``versions.py`` - append the following
code:

.. code-block:: python

   class MySecondUpgradeMacro(rose.upgrade.MacroUpgrade):

       """Upgrade from 0.2 (Outrageous Outrigger) to 0.3 (Amazing Ama)."""

       BEFORE_TAG = "0.2"
       AFTER_TAG = "0.3"

       def upgrade(self, config, meta_config=None):
           """Upgrade the boat!"""
           self.act_from_files(config)
           return config, self.reports

The ``self.act_from_files`` line tells the macro to look for patch
configuration files - two files called ``rose-macro-add.conf`` and
``rose-macro-remove.conf``, under an ``etc/BEFORE_TAG/`` subdirectory -
in our case, ``~/rose-meta/make-boat/etc/0.2/``.

Whatever is found in ``rose-macro-add.conf`` will be added to the
configuration, and whatever is found in ``rose-macro-remove.conf`` will
be removed. If the files don't exist, nothing will happen.

Let's configure what we want to happen. Create a directory
``~/rose-meta/make-boat/etc/0.2/``, containing a ``rose-macro-add.conf``
file that looks like this:

.. code-block:: rose

   [namelist:materials]
   l_rudder_branch=.true.

.. note::

   If a ``rose-macro-add.conf`` setting is already defined, the
   value of ``l_rudder_branch`` will not be overwritten. In our case, we
   don't need a ``rose-macro-remove.conf`` file.

Go ahead and upgrade the app configuration to ``0.3``, as you did before.

The :rose:file:`rose-app.conf` should now contain the new option,
``l_rudder_branch``.

More Complex Upgrade Macros
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :ref:`rose-upgr-macros` gives us quite a bit of power without having to
write too much Python.

For our ``1.0`` release we want to make some improvements to out sailing
equipment:

* We want to increase the number of ``misc_branches`` to be at least 6.
* We want to add a ``sail_canvas_sq_m`` option.

We may want to issue a warning for a deprecated option
(``paddle_branches``) so that the user can decide whether to remove it.

Create the file ``~/rose-meta/make-boat/1.0/rose-meta.conf``
and paste in the following configuration:

.. code-block:: rose

   [namelist:materials=hollow_tree_trunks]
   compulsory=true
   values=1

   [namelist:materials=l_rudder_branch]
   compulsory=true
   type=logical

   [namelist:materials=misc_branches]
   compulsory=true
   range=6:
   type=integer

   [namelist:materials=outrigger_tree_trunks]
   compulsory=true
   values=2

   [namelist:materials=paddling_branches]
   range=0:
   type=integer
   warn-if=True # Deprecated - real sailors don't use engines

   [namelist:materials=sail_canvas_sq_m]
   range=4:
   type=real

We need to write a macro that reflects these changes.

We need to start with appending the following code to ``versions.py``:

.. code-block:: python

   class MyMoreComplexUpgradeMacro(rose.upgrade.MacroUpgrade):

       """Upgrade from 0.3 (Amazing Ama) to 1.0 (Tremendous Trimaran)."""

       BEFORE_TAG = "0.3"
       AFTER_TAG = "1.0"

       def upgrade(self, config, meta_config=None):
           """Upgrade the boat!"""
           # Some code doing something to config goes here.
           return config, self.reports

We already know how to add an option, so replace
``# Some code going here...`` with
``self.add_setting(config, ["namelist:materials", "sail_canvas_sq_m"], "5")``

To perform the check/change in the number of ``misc_branches``, we can
insert the following lines after the one we just added:

.. code-block:: python

           branch_num = self.get_setting_value(
                  config, ["namelist:materials", "misc_branches"])
           if branch_num.isdigit() and float(branch_num) < 6:
               self.change_setting_value(
                        config, ["namelist:materials", "misc_branches"], "6")

This extracts the value of ``misc_branches`` (as a string!) and if the
value represents a positive integer that is less than 6, changes it to
``"6"``. It's good practice to guard against the possibility that a user
might have set the value to a non-integer representation like ``'many'``
- if we don't do this, the macro may crash out when running things like
``float``.

In a similar way, to flag a warning, insert:

.. code-block:: python

           paddles = self.get_setting_value(
                          config, ["namelist:materials", "paddling_branches"])
           if paddles is not None:
               self.add_report("namelist:materials", "paddling_branches",
                               paddles, info="Deprecated - probably not needed.",
                               is_warning=True)

This calls ``self.add_report`` if the option ``paddling_branches`` is
present. This is a method that notifies the user of actions and issues
by appending things to the ``self.reports`` list which appears on the
``return ...`` line.

Run ``rose app-upgrade --meta-path=~/rose-meta/ 1.0`` to see the effect of
your changes. You should see a warning message for
``namelist:materials=paddling_branches`` as well.

Upgrading Many Versions at Once
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We've kept in step with the metadata by upgrading incrementally, but
typically users will need to upgrade across multiple versions. When this
happens, the relevant macros will be applied in turn, and their changes
and issues aggregated.

Turn back the clock by reverting your application configuration to look
like it was at ``0.1``:

.. code-block:: rose

   meta=make-boat/0.1

   [namelist:materials]
   hollow_tree_trunks=1
   paddling_twigs=1

Run ``rose app-upgrade --meta-path=~/rose-meta/`` in the application
directory. You should see that the version has been downgraded to 0.1,
the available versions to upgrade to should also be listed - let's
choose ``1.0``. Run::

   rose app-upgrade --meta-path=~/rose-meta/ 1.0

This should aggregate all the changes that our macros make - if you
accept the changes, it will upgrade all the way to the ``1.0`` version we
had before.


.. tip::

   See also:

   * :ref:`rose-upgr-macros`
   * :ref:`api-rose-macro`


.. _outriggers: https://en.wikipedia.org/wiki/Outrigger_canoe
