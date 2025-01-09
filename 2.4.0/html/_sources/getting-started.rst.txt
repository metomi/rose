Getting Started
===============

If you are working with a new installation of Rose you should look at the
:ref:`Site And User Configuration`.

Rose combines the settings in the site configuration and the user configuration
at run time. You can view the resultant configuration by issuing the command::

   rose config

Rose should work out of the box if it is configured correctly at your site.


Text Editor
-----------

* The default external text editor used by *GUIs* is ``gedit``.
* The default external text editor used by *CLI* commands is the value of
  the ``VISUAL`` or ``EDITOR`` environment variable, or ``vi`` if neither
  environment variable is set.

To change the default editor change the following settings in the user
configuration file ``~/.metomi/rose.conf``:

``[external]geditor``
   The external text editor used by GUIs
``[external]editor``
   The external text editor used by CLI commands

For emacs and most text editors, you can do something like:

.. code-block:: rose

   [external]
   editor=emacs
   geditor=emacs

For any text editor command that normally forks and detaches from the shell
it is started in, you should use an option to ensure that the text editor
runs in the foreground to allow Rose to wait for the edit session to
finish. E.g. for ``gvim``, you will do:

.. code-block:: rose

   [external]
   editor=gvim -f
   geditor=gvim -f


Editor Syntax Highlighting
--------------------------

There are ``gedit``, ``kate``, ``vim``, and ``emacs`` plugins for syntax
highlighting of Rose configuration files, located within the Rose installation.

Run the following command to see the available syntax files and their
locations::

   $ rose resource syntax

Each file contains setup instructions within.

.. _Pygments: https://pygments.org
.. _Rose Lang: https://github.com/metomi/rose/blob/master/sphinx/ext/rose_lang.py

Additionally there is a `Pygments`_ lexer located
`in the source code <https://github.com/metomi/rose/blob/master/sphinx/ext/rose_lang.py>`_


Configuring Cylc
----------------

See the "Installation" and "User Config File" sections of the
`Cylc User Guide`_.
