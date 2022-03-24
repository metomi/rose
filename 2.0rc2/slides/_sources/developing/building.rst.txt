Building & Testing
==================

The documentation is built using Make.

Whenever making changes to the sphinx infrastructure use a clean build e.g:

.. code-block:: bash

   make -C sphinx clean html

The following builders are useful for development:

``linkcheck``
   Check external links (internal links are checked by a regular build).
``doctest``
   Run any doctests contained within documented code
   (e.g. see :py:mod:`metomi.rose.config`).

Additionally, if you are not using an editor with a spellchecker you may
wish to use aspell/ispell/hunspell to check any changed docs:

.. code-block:: bash

   hunspell path/to/changed.rst
   # or
   aspell check path/to/changed.rst
