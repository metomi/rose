Lexers
======


rose-app.conf / rose-suite.conf
-------------------------------

.. only:: builder_html

    More complex example: `mi-ai111_rose`_

    .. _mi-ai111_rose: ../_static/snippets/mi-ai111-gl-um-fcst-rose-app.conf

.. code-block:: rose

   # Comment
   top-level-settinng = value
   top-level-settinng = value  # Invalid inline comment
   multi-line-setting = value 1
                      = value 2
                      = value 3

   # Sections
   [section]
   foo=bar
   foo=bar  # baz

   # Ignores
   setting=value
   !user-ignored-setting=value
   !!trigger-ignored-setting=value

   [section]
   setting=value
   !user-ignored-setting=value
   !!trigger-ignored-setting=value

   # User ignored section
   [!user-ignored-section]
   setting=value
   !user-ignored-setting=value
   !!trigger-ignored-setting=value

   # Trigger ignored section
   [!!trigger-ignored-section]
   setting=value
   !user-ignored-setting=value
   !!trigger-ignored-setting=value

   # Top level section
   []
   foo = bar

   # Section with nasty characters
   [section:some-mess.here]
   foo=bar


suite.rc
--------

.. only:: builder_html

   More complex example: `mi-ai111_cylc`_

   .. _mi-ai111_cylc: ../_static/snippets/mi-ai111-suite-rc.html

.. code-block:: cylc

   # Basic
   [section]
       key = value
       [[sub-section]]
           key = value
   [section]  # Comment.
       key = """
           multi
           line
           value
       """
       [[Invalid]

   # Parameterisation.
   [foo<bar>]
   [foo< bar >]
   [foo<bar=1>]]
   [foo<bar+1>]]
   [foo<bar-1>]]
   [foo<bar, baz>]
   [foo<bar=1, baz>]
   [foo<bar=1, baz=1>]
   [foo<bar, baz, pub, quz>]
   [foo<bar=1+1, baz=1>]  # Invalid
   [foo<bar+1-1>]]  # Invalid
   [foo<bar=1-1>]]  # Invalid

   # Graph strings - basic.
   graph = foo => bar => baz  # Comment
   graph = """
       foo => bar => baz  # Comment
   """

   # Graph strings - operators.
   graph = foo & (bar | baz) => pub
   graph = """
       foo & (bar | baz) => pub
   """

   # Graph string - intercycle offsets.
   graph = foo[-P] => bar  # Invlaid
   graph = foo[-P1] => bar
   graph = foo[-P1Y1M1D] => bar
   graph = foo[-PT1H1M1S] => bar
   graph = foo[-P1Y1M1DT1H1M1S] => bar
   graph = foo[-P00010000T010000] => bar
   graph = foo[-P0001-00-00T01:00:00] => bar
   graph = foo[-P1W] => bar
   graph = foo[^] => bar
   graph = foo[$] => bar
   graph = foo[-P1Y1D1MT1H1M1S] => bar  # Invalid
   graph = foo[-P1H1M1S] => bar  # Invalid
   graph = foo[12] => bar  # Invalid
   graph = foo[2000-01-01] => bar  # Invalid

   # Graph string - parameterisation.
   graph = foo<bar>
   graph = """
       foo<bar>
       foo< bar >
       foo<bar=1>
       foo<bar+1>
       foo<bar-1>
       foo<bar, baz>
       foo<bar=1, baz>
       foo<bar=1, baz=1>
       foo<bar, baz, pub, quz>
       foo<bar+1+1>  # Invalid.
       foo<bar=1-1>  # Invalid.
       foo<bar=1+1, baz=1>  # Invalid
   """

   # Jinja2
   #!Jinja2
   {{ here }}
   {% hare %}
   {# here #}
   {% multi
      line
      section %}

   # Jinja2 - settings.
   foo = {{ bar }}
   {{ foo }} = bar

   # Jinja2 - sections.
   [ {{ foo }} ]

   # Jinja2 - graph strings.
   graph = foo => {{ bar }} => baz
   graph = """
       foo => {{ bar }} => baz
   """

