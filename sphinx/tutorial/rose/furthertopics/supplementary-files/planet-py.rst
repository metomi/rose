.. _planet-python-file:

planet.py
=========

.. code-block:: python

   #!/usr/bin/env python
   # -*- coding: utf-8 -*-

   import re
   import subprocess

   import rose.macro


   class PlanetChecker(rose.macro.MacroBase):

       """Checks option values that refer to planets."""

       opts_to_check = [("env", "WORLD")]

       def validate(self, config, meta_config=None):
           """Return a list of errors, if any."""
           for section, option in self.opts_to_check:
               node = config.get([section, option])
               if node is None or node.is_ignored():
                   continue
               # Check the option value (node.value) here
           return self.reports


