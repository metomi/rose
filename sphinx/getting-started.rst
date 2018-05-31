.. include:: hyperlinks.rst
   :start-line: 1


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
highlighting of Rose configuration files, located within the Rose installation:

* ``etc/rose-conf.lang``
* ``etc/rose-conf.xml``
* ``etc/rose-conf.vim``
* ``etc/rose-conf-mode.el``

The plugins contain setup instructions within.

.. _Pygments: http://pygments.org

Additionally there is a `Pygments`_ lexer located in
``sphinx/ext/rose_lang.py``.

.. hint::

   You can locate your Rose installation using::

      rose version --long


Bash Auto-Completion
--------------------

There is a Rose bash completion script that you can source to enhance the
Rose command line interface within an interactive Bash shell.

The script allows you to tab-complete Rose commands, options, and arguments.

You can find the script in the Rose installation ``etc/rose-bash-completion``.
The file contains the instructions for using it.


Configuring Cylc
----------------

See the "Installation" and "User Config File" sections of the
`Cylc User Guide`_.

.. warning::

   Do not modify the default values of the following cylc settings:
   
   * ``[hosts][HOST]run directory``
   * ``[hosts][HOST]work directory``
   
   Equivalent functionalities are provided by the
   :rose:conf:`rose.conf[rose-suite-run]root-dir` settings in the Rose
   site/user configuration.
