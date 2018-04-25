Auto CLI API
============


The Rose command line API is auto-documented by the extension ``auto-cli-api``.

This translates the Rose CLI help into reStructuredText. To keep the CLI docs
clean they are written in a plain format which has some reStructuredText
features built in.

Commands can be referenced throughout the documentation by prefixing their name
with ``command`` e.g for :ref:`command-rose-date`:

.. code-block:: rst

   :ref:`command-rose-date`


Basic Help Page
---------------

Help pages are written in sections with content indented four spaces after
section headings. Sections are separated by a single blank line.

The following sections are compulsory:

* ``NAME`` - This section is required but ignored by auto CLI API.
* ``SYNOPSIS`` - Rendered as a code-block with bash syntax.
* ``DESCRIPTION`` - Freeform reStructuredText section.

.. code-block:: none

   NAME
       foo

   SYNOPSIS
       foo <foo>

   DESCRIPTION
       Foo bar baz.

The reference is generated when the documentation is built. To see the
underlying reStructuredText try:

.. code-block:: bash

   python ext/auto-api-doc.py


reStructuredText Markup
-----------------------

The following reStructuredText markup elements are supported:

* Bullet Lists

  .. code-block:: rst

     * Foo
     * Bar
     * Baz

* Enumerated Lists

  .. code-block:: rst

     1. Foo
     2. Bar
     3. Baz

* Definition Lists

  .. code-block:: rst

     foo
        Foo foo foo.
     bar
        Bar bar bar.
     baz
        Baz baz baz.

.. note::

   In freeform reStructuredText blocks any valid markup *(except that
   involving backquotes)* can be used. To maintain clarity in CLI mode only the
   above is recommended.


Custom Markup
-------------

The following reStructuredText markup elements have been mutated for the
plain text format:

* Literals

  .. code-block:: none

     foo `bar` baz
     foo`bar`baz

  Which are translated as:

  .. code-block:: rst

     foo ``bar`` baz
     foo\ ``bar``\ baz

* Admonitions

  .. code-block:: none

     NOTE: Foo foo foo.

  Which are translated as:

  .. code-block:: rst

     .. note:: Foo foo foo.

* References

  Any recognised commands written in back quotes will result in references
  within the CLI API documentation.

  .. code-block:: none

     See also `rose app-run`.


Argument/Option Sections
------------------------

The following help sections will be interpreted as argument/option lists:

* ``OPTIONS``
* ``ARGUMENTS``
* ``ENVIRONMENT VARIABLES``
* ``JINJA2 VARIABLES``
* ``CONFIGURATION``

Such sections are written in the format:

.. code-block:: none

   ARGUMENTS
       Optional description line, only `inline markup` permitted.

       --option
          Description goes here.
       --another-option=VALUE, -a VALUE
          Description here.

          * Markup is permitted.
          * Provided the indentation level is correct.

       --further-option
          Note new-lines are not required unless a markup block is used (e.g.
          the bullet point list in the previous section).


Code Sections
-------------

The following sections will be interpreted as plain-text with bash syntax.

* ``SYNOPSIS``
* ``EXAMPLES``


User-Defined Sections
---------------------

Any user-defined sections will be interpreted as free-form reStructuredText.
