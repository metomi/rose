reStructuredText
================


.. _reStructuredText Markup Specification: http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html
.. _Sphinx Markup Documentation: http://www.sphinx-doc.org/en/stable/rest.html


Reference
---------

For reference material see:

* `reStructuredText Markup Specification`_
* `Sphinx Markup Documentation`_


Headings
--------

Headings are text lines which are underlined. The underline character can be
any of:

.. code-block:: none

   ! " # $ % & ' ( ) * + , - . / : ; < = > ? @ [ \ ] ^ _ ` { | } ~

Different characters are used to define different document levels e.g. section,
sub-section, etc. reStructuredText doesn't actually care which character you
use for each role, it infers precedence from the order of appearance.

For consistency this documentation has been written in the standard-ish manner
with:

.. code-block:: rst

   Heading
   =======

   Sub Heading
   -----------

   Sub-Sub Heading
   ^^^^^^^^^^^^^^^

   Totally Irrelevant Heading
   """"""""""""""""""""""""""

For consistency:

* Top level headings always appear at the top of the document (only one per
  document).
* First level headings are preceded by two blank lines and followed by one.
* Lower level headings are preceded and followed by a single blank line.


Indention
---------

reStructuredText uses adaptive indentation so that following lines are
flush with the directive or element which started them e.g:

* Directives are followed by three space indentation:

  .. code-block:: rst

     .. note::

        Foo
        Bar
        Baz

* Bullet Lists use two space indentation:

  .. code-block:: rst

     * Foo
       Bar
       Baz

* Numbered lists use three space indenation:

  .. code-block:: rst

     #. Foo
        Bar

     1. Bar
        Pub

For consistency with directives three space indentation is used with
definition lists:

.. code-block:: rst

   Item
      Description.
