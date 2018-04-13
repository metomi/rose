Rose Bash Library
=================

The Rose bash library lives in ``lib/bash/``. To import a module, load the file
into your script. E.g. To load ``rose_usage``, you would do::

   . $ROSE_HOME/lib/bash/rose_usage

The modules are:

``rose_init``
    Called by ``rose`` on initialisation. This is not meant to be for general
    use.
``rose_log``
    Provide functions to print log messages.
``rose_usage``
    If your script has a header similar to the ones used by a ``rose`` command
    line utility, you can use this function to print the synopsis section of
    the script header. 
