.. _rose-upgr-macros:

Rose Upgrade Macro API
======================

Rose upgrade macros are used to upgrade application configurations between
metadata versions. They are classes, very similar to
:ref:`transformer macros <api-rose-macro>`, but with a few differences:

* An ``upgrade`` method instead of a ``transform`` method
* An optional ``downgrade`` method, identical in API to the ``upgrade``
  method, but intended for performing the reverse operation
* A more helpful API via :py:class:`rose.upgrade.MacroUpgrade` methods
* ``BEFORE_TAG`` and ``AFTER_TAG`` attributes - the version of metadata they
  apply to (``BEFORE_TAG``) and the version they upgrade to (``AFTER_TAG``)

An example upgrade macro might look like this:

.. code-block:: python

   class Upgrade272to273(rose.upgrade.MacroUpgrade):

   """Upgrade from 27.2 to 27.3."""

   BEFORE_TAG = "27.2"
   AFTER_TAG = "27.3"

   def upgrade(self, config, meta_config=None):
       self.add_setting(config, ["env", "NEW_VARIABLE"], "0")
       self.remove_setting(config, ["namelist:old_things", "OLD_VARIABLE"])
       return config, self.reports

.. note::
   The class name is unimportant - the ``BEFORE_TAG`` and ``AFTER_TAG``
   identify the macro.

Metadata versions are usually structured in a ``rose-meta/CATEGORY/VERSION/``
hierarchy - where ``CATEGORY`` denotes the type or family of application
(sometimes it is the command used), and ``VERSION`` is the particular version 
e.g. ``27.2`` or ``HEAD``.

Upgrade macros live under the ``CATEGORY`` directory in a ``versions.py``
file - ``rose-meta/CATEGORY/versions.py``.

.. tip::
   If you have many upgrade macros, you may want to separate them into
   different modules in the same directory. You can then import from those
   in ``versions.py``, so that they are still exposed in that module. You'll
   need to make your directory a package by creating an ``__init__.py`` file,
   which should contain the line ``import versions``. To avoid conflict with
   other ``CATEGORY`` upgrade modules (or other Python modules), please name
   these very modules carefully or use absolute or package level imports like
   this: ``from .versionXX_YY import FooBar``.

Upgrade macros are subclasses of :py:class:`rose.upgrade.MacroUpgrade`. They
have all the functionality of the :ref:`transformer macros <api-rose-macro>`.

.. autoclass:: rose.upgrade.MacroUpgrade
   :members:
