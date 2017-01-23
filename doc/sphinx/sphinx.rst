Sphinx Readme
=============

This file is for rose developers writing documentation. It contains some useful
links and a quick description of the Sphinx documentation system.

Building Docs
-------------

.. code-block:: bash

    make -C doc  # will build: clean doctest html tidy

If ``sphinx-build`` is not installed (or is antiquated) ``make`` will install
sphinx in a virtualenv which it will then tidy.

For development purposes export
``SPHINX_DEV_MODE=true`` to prevent this virtualenv being rebuilt/destroyed
each time ``make`` is invoked.


reStructuredText
----------------

Sphinx uses the `reStructuredText markup language
<http://www.sphinx-doc.org/en/stable/rest.html>`_.

It is sensitive to indentation and sometimes requires three-space indentation
(e.g. lines following ``.. something::`` should be flush with the letter
``s``).


Writing Docstrings
------------------

Sphinx has been configured to use the `Napoleon
<http://www.sphinx-doc.org/en/1.5.1/ext/napoleon.html>`_ extension which
allows `autodoc <http://www.sphinx-doc.org/en/stable/ext/autodoc.html>`_
to work with docstrings in the `Google format
<http://google.github.io/styleguide/pyguide.html>`_ (`example module
<http://www.sphinx-doc.org/en/1.5.1/ext/example_google.html#example-google>`_).
Avoid convoluting docstrings with reStructuredText, if any un-expected
behaviour occurs when attempting to use reStructuredText in docstrings it will
likely be due to Napoleon.

Some quick examples:


.. code-block:: python

    def Some_Class(object):
        """Some summary.

        Note __init__ methods are not autodocumented, specify constructor
        parameters in the class docstring.

        Args:
            param1 (type): Description.
            param2 (type): Really really really really really really
                long description.
            kwarg (type - optional): Description.

        """  # Blank line.

        def __init(self, param1, param2, kwarg=None):
            pass

        def some_generator(self, param1, param2):
           """Some summary.

           Args:
               param1 (str/int): Argument can be of multiple types.
               param2 (obj): Argument can have many types.

           Yields:
               type: Some description, note that unlike the argument lines,
               continuation lines in yields/returns sections are not indented.
    
           """

        @classmethod
        def some_function_with_multiple_return_values(cls):
            """Some summary.

            Example:
               >>> # Some doctest code.
               >>> Some_Class().some_function_with_multiple_return_values()
               ('param1', 'param2')

            Returns:
                tuple - (param1, param2)
                    - param1 (str) - If a function returns a tuple you can if
                          desired list the components of the tuple like this.
                    - param2 (str) - Something else.

            """
            return ('param1', 'param2')


Writing Doctests
----------------

Examples [in docstrings] written in  `doctest format
<https://docs.python.org/2/library/doctest.html>`_ will appear nicely
formatted in the API docs, as an added bonus they are testable (``make -C doc
doctest``, incorporated in the rose test battery).

Use ``>>>`` for statements and ``...`` for continuation lines. Any return
values will have to be provided and should sit on the next newline.

.. code-block:: python

   >>> import rose.config
   >>> rose.config.ConfigNode()
   {'state': '', 'comments': [], 'value': {}}

If return values are not known in advance use ellipses:

.. code-block:: python

   >>> import time
   >>> print 'here', time.time(), 'there'
   here ... there

If return values are lengthy use ``NORMALIZE_WHITESPACE`` (see source code for
this page):

.. code-block:: python

   >>> print [1,2,3] # doctest: +NORMALIZE_WHITESPACE
   [1,
   2,
   3]

Note that you can ONLY break a line on a comma i.e. this wont work (note the
``+SKIP`` directive [in the source code for this page] prevents this doctest
from being run):

.. code-block:: python

   >>> print {'a': {'b': {}}} # doctest: +NORMALIZE_WHITESPACE, +SKIP
   {'a':
     {'b': {}
   }}

Doctests are performed in the doc/sphinx directory and any files created will
have to be `tidied up
<http://www.sphinx-doc.org/en/1.5.1/ext/doctest.html#directive-testcleanup>`_.

See `doctest <https://docs.python.org/3.3/library/doctest.html>`_ for more
details.
