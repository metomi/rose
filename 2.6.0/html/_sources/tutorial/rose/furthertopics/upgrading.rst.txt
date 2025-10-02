.. _tutorial-rose-upgrade-macros:

Upgrading
=========

As :term:`apps <Rose app>` are developed, newer metadata versions can be
created each time the application inputs are changed, or just between major
releases.

This may mean, for example, that a new compulsory option is added or an
old one is removed.

Upgrade macros may be written to automatically apply these changes.

Upgrade macros are used to upgrade :term:`Rose apps <Rose app>` to newer
metadata versions. They are intended to keep application configurations in
sync with changes to application inputs e.g. from new code releases.

This part tutorial walks you through upgrading applications.


Example
-------

Create a new Rose application called ``garden``::

   mkdir -p ~/rose-tutorial/garden
   cd ~/rose-tutorial/garden

Create within it a :rose:file:`rose-app.conf` file that looks like this:

.. code-block:: rose

   meta=rose-demo-upgrade/garden0.1

   [env]
   FOREST=true

   [namelist:features]
   rose_bushes=2

The ``meta=...`` line references a category (``rose-demo-upgrade``) at a
particular version (``garden0.1``). It's the version that we want to
change.


``rose app-upgrade``
--------------------

Change directory to your new application directory. You can see the
available upgrade versions for your new app config by running:

.. code-block:: bash

   rose app-upgrade

This gives you a list of versions to upgrade to - see the help for more
information (run ``rose help app-upgrade``).

There can often be more versions than you can see by just running
:ref:`command-rose-app-upgrade`. They will not have formal metadata, and
represent intermediary steps along the way between proper named versions. You
can see all the possible versions by running:

.. code-block:: bash

   rose app-upgrade --all-versions

You can upgrade directly to the latest (``garden0.9``) or to other
versions - let's choose ``garden0.2`` to start with. Run:

.. code-block:: bash

   rose app-upgrade garden0.2


Upgrade Changes
---------------

This will give you a list of changes that the upgrade will apply to your
configuration. Accept it, and your application configuration will be
upgraded, with a new option (``shrubberies``) and a new ``meta=...``
version of the metadata to point to. Have a look at the changed
:rose:file:`rose-app.conf` if you like.

Try repeating this by upgrading to ``garden0.3`` in the same way.
This time, you'll get a warning - warnings are used to point out
problems such as deprecated options when you upgrade.

We can upgrade over many versions at once - for example, directly
to ``garden0.9`` - and the changes between each version will be
aggregated into a single list of changes.

Try running:

.. code-block:: bash

   rose app-upgrade garden0.9

If you accept the changes, your app config will be upgraded through all
the intermediary versions to the new one. Have a look at the
:rose:file:`rose-app.conf` file.

If you run Rose :ref:`command-rose-app-upgrade` with no arguments, you can see
that you're using the latest version.


Downgrading
-----------

Some versions may support downgrading - the reverse operation to
upgrading. You can see if this is supported by running:

.. code-block:: bash

   rose app-upgrade --downgrade

You can then use it to downgrade by running:

.. code-block:: sub

   rose app-upgrade --downgrade <VERSION>

where ``VERSION`` is a lower supported version. This time, some settings
may be removed.


.. tip::

   See also:

   * :ref:`conf-meta`
   * :ref:`rose-upgr-macros`
