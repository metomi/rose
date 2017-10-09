.. _planet-python-reporter:

planet.py
=========

.. code-block:: python

   class PlanetReporter(rose.macro.MacroBase):

       """Creates a report on the value of env=WORLD."""

       GENERIC_HOROSCOPE_STATEMENTS = [
           'be cautious', 'remain indoors', 'expect the unexpected',
           'not walk under ladders', 'seek new opportunities']

       def report(self, config, meta_config=None):
           world_node = config.get(["env", "WORLD"])
           if world_node is None or world_node.is_ignored():
               return
           planet = world_node.value
           if planet.lower() == 'earth':
               print 'Please choose a planet other than Earth.'
               return
           constellation = self.get_planet_info(planet)
           if not constellation:
               print 'Could not find horoscope entry for {0}'.format(planet)
               return
           else:
               print (
                   '{planet} is currently passing through {constellation}.\n'
                   'You should {generic_message} today.'
               ).format(
                   planet = planet,
                   constellation = constellation,
                   generic_message = random.choice(
                     self.GENERIC_HOROSCOPE_STATEMENTS)
               )

       def get_planet_info(self, planet_name):
           cmd_strings = ["curl", "-s",
                          "http://www.heavens-above.com/planetsummary.aspx"]
           p = subprocess.Popen(cmd_strings, stdout=subprocess.PIPE)
           text = p.communicate()[0]
           planets = re.findall("(\w+)</td>",
                                re.sub(r'(?s)^.*(<thead.*?ascension).*$',
                                       r"\1", text))
           constellations = re.findall("(\w+)</a>",
                                  re.sub('(?s)^.*(Constellation.*?Meridian).*$',
                                         r"\1", text))
           for planet, constellation in zip(planets, constellations):
               if planet.lower() == planet_name.lower():
                   return constellation
           return None


