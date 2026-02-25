Rose Bash Library
=================

Rose includes some bash modules, they can be located by running::

    $ rose resource lib/bash

These modules can be invoked like so::

   . "$(rose resource lib/bash/rose_log)"

The modules are:

``rose_log``
    Provide functions to print log messages.
``rose_usage``
    If your script has a header similar to the ones used by a ``rose`` command
    line utility, you can use this function to print the synopsis section of
    the script header. 
