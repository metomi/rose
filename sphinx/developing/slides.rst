.. _Hieroglyph: http://docs.hieroglyph.io/en/latest/


Slides
======


Slides are built using the `Hieroglyph`_ extension.


Writing
-------

Hieroglyph automatically builds slides using the document structure, i.e. each
section gets put on a new slide. To break up long sections use ``..
nextslide::``. To control what content appears in the slides / regular output
use switches like so:

.. code-block:: rst

   Content which appears both in slides and regular output.

   .. ifnotslides::

      Content for the regular documentation only.

   .. ifslides::

      Content for the slides only.

In certain situations it may be necessary to manually build slides using the
``slide`` directive:

.. code-block:: rst

   .. slide:: Slide Title
      :level: 1
      :inline-contents:

      Level 1 means the slide has the same prominence as the title

      inline-contents means that the content of this directive also appears in
      the regular output.

Hieroglyph interprets the ``note`` admonition as presenters notes. Or to be
more technical Hieroglyph interprets anything with the ``admonition`` and
``note`` classes as a presenter note so you cannot get around it doing
something like this:

.. code-block:: rst

   .. admonition:: Note
      :class: note

To make the content appear in the slides you can do something like this:

.. code-block:: rst

   .. admonition:: Note
      :class: tip


Building
--------

Build using the ``slides`` builder i.e::

   rose make-docs slides

Note that if linking to the HTML version from within the slides you may be
restricted to using either the single page HTML or directory HTML builders but
not both.


Error
-----

Hieroglyph loves cryptic errors.


Losing "ids" Attribute
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: none

       'Losing "%s" attribute: %s' % (att, self[att])
   AssertionError: Losing "ids" attribute: ['cylc-file-format']

This is caused by a sphinx reference being broken by the ``slide``,
``ifnotslides`` or ``ifslides`` directives e.g:

.. code-block:: rst

   .. _bar:

   .. ifnotslides::

      Foo

   Bar

Fix by changing to:

.. code-block:: rst

   .. ifnotslides::

      Foo

   .. _bar:

   Bar


ValueError: <#text
^^^^^^^^^^^^^^^^^^

.. code-block:: none

   ValueError: <#text: "Special cases ARE special enough to break the rules"> is not in list

The ``..nextslide`` directive can be used a maximum of two times in a row.
