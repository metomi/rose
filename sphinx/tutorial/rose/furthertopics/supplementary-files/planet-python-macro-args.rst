.. _planet-python-macro-args-file:

planet.py
=========

.. code-block:: python

   class PlanetChanger(rose.macro.MacroBase):

       """Switch between planets."""

       change_text = '{0} to {1}'
       opts_to_change = [("env", "WORLD")]
       planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn",
                   "Uranus", "Neptune", "Eris"]

       def transform(self, config, meta_config=None, planet_name=None):
           """Transform configuration and return it with a list of changes."""
           for section, option in self.opts_to_change:
               node = config.get([section, option])
               if node is None or node.is_ignored():
                   continue
               old_planet = node.value
               if planet_name is None:
                   try:
                       index = self.planets.index(old_planet)
                   except (IndexError, ValueError):
                       new_planet = self.planets[0]
                   else:
                       new_planet = self.planets[(index + 1) % len(self.planets)]
               else:
                   new_planet = planet_name
               config.set([section, option], new_planet)
               message = self.change_text.format(old_planet, new_planet)
               self.add_report(section, option, new_planet, message)
           return config, self.reports
