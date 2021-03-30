.. _rose_arch:

``rose_arch``
=============

This built-in application provides a generic solution to configure
site-specific archiving of suite files for use with
:ref:`command-rose-task-run`.

.. note::

   :rose:app:`rose_arch` is designed to work with suite files so runs under
   :ref:`command-rose-task-run`. It cannot run under
   :ref:`command-rose-app-run`.

The application is normally configured in a :rose:file:`rose-app.conf`. Global
settings may be specified in an :rose:conf:`rose_arch[arch]`
section. Each archiving target will have its own ``[arch:TARGET]``
section for specific settings, where ``TARGET`` would be a URI to
the archiving location on your site-specific archiving system. Settings
in a ``[arch:TARGET]`` section would override those in the global
:rose:conf:`rose_arch[arch]` section for the given ``TARGET``.

A target is considered compulsory, i.e. it must have at least one
source, unless it is specified with the syntax ``[arch:(TARGET)]``.
In which case, ``TARGET`` is considered optional. The application will
skip an optional target that has no actual source.

The application provides some useful functionalities:

* Incremental mode: store the archive target settings, checksums of
  source files and the return code of archive command. In a retry, it
  would only redo targets that did not succeed in the previous attempts.
* Rename source files.
* Tar-Gzip or Gzip source files before sending them to the archive.


Invocation
----------

In automatic selection mode, this built-in application will be invoked
automatically if a task has a name that starts with ``rose_arch*``.

This means that you can use Rose Arch with something like the example below
in your ``flow.cylc``:

.. code-block:: cylc

   [scheduling]
      # ...
      [[dependencies]]
          P1 = """
          all => the => tasks => rose_arch_archive
          """

   [runtime]
      # ...

      [[rose_arch_archive]]


Examples
--------

The following examples all form part of a single :rose:file:`rose-app.conf` file:

General Settings
^^^^^^^^^^^^^^^^
These settings are placed here to be inherited by other archive tasks in the
file: In this case we've set ``command format`` which sets how we are going
to copy the files to the archive location.
We've also set prefixes for the source and target locations, so that we
don't have repeatedly specify common locations.

.. code-block:: rose

   # General settings
   [arch]
   command-format=foo put %(sources)s %(target)s
   source-prefix=$ROSE_DATAC/
   target-prefix=foo://hello/

Archive a file to a file
^^^^^^^^^^^^^^^^^^^^^^^^
In this simplest use case rose arch is just moving a single file to another
location.

.. code-block:: rose

   # Archive a file to a file
   [arch:world.out]
   source=hello/world.out

Archiving directories
^^^^^^^^^^^^^^^^^^^^^
You can archive files matched by one or more glob expressions to a directory:

.. code-block:: rose

   # A single glob
   [arch:worlds/]
   source=hello/worlds/*

   # Three globs
   [arch:worlds/]
   source=hello/worlds/* greeting/worlds/* hi/worlds/*

Missing files and directories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
It's also possibly to deal with a situation where one or more of the source
expressions might not return anything by putting brackets - ``()`` - around it:

.. code-block:: rose

   # If there isn't anything in greeting/worlds/ Rose Arch continues
   [arch:worlds/]
   source=hello/worlds/* (greeting/worlds/*) hi/worlds/*

You can even tell Rose Arch that there may be nothing to archive, but to carry
on:

.. code-block:: rose

   [arch:(black-box/)]
   source=cats.txt dogs.txt

Zipping files
^^^^^^^^^^^^^
There are multiple ways of specifying that you want your archive to be
compressed:

You can infer compression from the target extension:

.. code-block:: rose

   [arch:planet.gz]
   source=hello/planet.out

or manually specify a compression program. (In this case the ``out.gz`` is
not recognized by rose arch as an extension to be compressed.)

.. code-block:: rose

   [arch:planet.out.gz]
   compress=gz
   source=hello/planet.out

For more details see :rose:conf:`rose_arch[arch]compress`

Zipping directories
^^^^^^^^^^^^^^^^^^^
You can tar and zip entire directories - as with single files Rose Arch will
attempt to infer archive and compression from ``[arch:TARGET.extension]`` if it
can:

.. code-block:: rose

   [arch:galaxies.tar.gz]
   source-prefix=hello/
   source=galaxies/*
   # File with multiple galaxies may be large, don't do its checksum
   update-check=mtime+size

You might prefer to explicitly gzip each file in the source directory separately:

.. code-block:: rose

   # Force gzip each source file
   [arch:stars/]
   source=stars/*
   compress=gzip

Renaming files simply
^^^^^^^^^^^^^^^^^^^^^
You may wish to change the name of the archived files. By default the contents
of your app'a :rose:conf:`rose_arch[arch]source` and
``$CYLC_TASK_CYCLE_TIME`` are available to you as python formatting strings
``%(name)s`` and ``%(cycle)s``.

.. code-block:: rose

   [arch:moons.tar.gz]
   source=moons/*
   rename-format=%(cycle)s-%(name)s

.. warning::

   As ``%(name)s`` can be a path is may not always make sense to
   prepend ``%(cycle)s`` to it - consider ``01_/absolute/path/to/datafile``

Renaming using a ``rename-parser``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
See :rose:conf:`rose_arch[arch]rename-parser`.

This allows you to parse the the name you give in :rose:conf:`rose_arch[arch]source` using
regular expressions for use in ``rename-format``.

This is handy if you set a path to :rose:conf:`rose_arch[arch]source` but want the target
to just be a name - imagine a case where you wanted to collect a group of files
with names in the form ``data_001.txt``:

.. code-block:: rose

   [arch:Target]
   source=/some/path/data*.txt
   rename-parser=^//some//path//data_(?P<serial_number>[0-9]{3})(?P<name_tail>.*)$
   rename-format=hello/%(cycle)s-%(name_head)s%(name_tail)s

Output
------

On completion, :rose:app:`rose_arch` writes a status summary for each
target to the standard output, which looks like this:

.. code-block:: none

   0 foo:///fred/my-su173/output0.tar.gz [compress=tar.gz]
   + foo:///fred/my-su173/output1.tar.gz [compress=tar.gz, t(init)=2012-12-02T20:02:20Z, dt(tran)=5s, dt(arch)=10s, ret-code=0]
   +       output1/earth.txt (output1/human.txt)
   +       output1/venus.txt (output1/woman.txt)
   +       output1/mars.txt (output1/man.txt)
   = foo:///fred/my-su173/output2.tar.gz [compress=tar.gz]
   ! foo:///fred/my-su173/output3.tar.gz [compress=tar.gz]

The first column is a status symbol, where:

0\
   An optional target has no real source, and is skipped.
+\
   A target is added or updated.
=\
   A target is not updated, as it was previously successfully updated with
   the same sources.
!\
   Error updating this target.

If the first column and the second column are separated by a space character,
the second column is a target. If the first column and the second column are
separated by a tab character, the second column is a source in the target
above.

For a target line, the third column contains the compress scheme, the
initial time, the duration taken to transform the sources, the duration
taken to run the archive command and the return code of the archive
command. For a source line, the third column contains the original name of
the source.


Configuration
-------------

.. rose:app:: rose_arch

   .. rose:conf:: arch & arch:TARGET

      .. rose:conf:: command-format=FORMAT

         :compulsory: True

         A Pythonic ``printf``-style format string to construct the archive
         command. It must contain the placeholders ``%(sources)s``
         and ``%(target)s`` for substitution of the sources and the target
         respectively.

      .. rose:conf:: compress=pax|tar|pax.gz|tar.gz|tgz|gz

         If specified, compress source files scheme before sending them to the
         archive. If not set Rose Arch will attempt to set a compression scheme
         if the file extension of the target implies compression: For
         example, setting target as ``[arch:example.tar]`` is the same as
         setting ``compress=tar``.

         Each compression scheme works slightly differently:

         +------------------+-----------------------------------------------+
         |Compression Scheme|Behaviour                                      |
         +------------------+-----------------------------------------------+
         |``pax`` or ``tar``|Sources will be placed in a TAR archive before |
         |                  |being sent to the target.                      |
         +------------------+-----------------------------------------------+
         |``pax.gz``,       |Sources will be placed in a TAR-GZIP file      |
         |``tar.gz`` or     |before being sent to the target.               |
         |``tgz``           |                                               |
         +------------------+-----------------------------------------------+
         |``gz``            |Each source file will be compressed by GZIP    |
         |                  |before being sent to the target.               |
         +------------------+-----------------------------------------------+

      .. rose:conf:: rename-format

         If specified, the source files will be renamed according to the
         specified format. The format string should be a Pythonic
         ``printf``-style format string.

         By default the following variables are available:

         * ``%(cycle)s`` for the current :envvar:`ROSE_TASK_CYCLE_TIME`
         * ``%(name)s`` for the file or path set in :rose:conf:`source`

         You may also use :rose:conf:`rename-parser` to generate further fields
         from the input name.

         .. warning::

            As ``%(name)s`` can be a path, so that
            if ``rename-format="%(cycle)s_%(name)s"`` you can have destination
            paths such ``02_path/to/some.file``, which are unlikely to work. If
            you want to manipulate your source name in such cases
            should use :rose:conf:`rename-parser`.


      .. rose:conf:: rename-parser

         Ignored if :rose:conf:`rename-format` is not specified.

         Specify a regular expression to parse the name provided by :rose:conf:`source`,
         using the Python regex syntax ``(?P<label>what you want to capture)``

         For example, a regular expression in the form:

         .. code-block:: console

            ^\/home\/data\/(?P<filename>myfile)(?P<serialnumber>[0-9]{3}).someExtension$

         Will label the captured section using with the contents of ``<>``.
         In this example you would then have ``%(filename)s`` and
         ``%(serialnumber)`` to use in your :rose:conf:`rename-format` string.

      .. rose:conf:: source=NAME

         :compulsory: True

         Specify a list of source file names and/or globs
         for matching source file names. List items are separated by spaces.

         * File names with space or quote  characters can be escaped using quotes
           or backslashes, like in a shell.)
         * Paths, if not absolute (beginning with a ``/``), are
           assumed to be relative to :envvar:`ROSE_SUITE_DIR` or to
           ``$ROSE_SUITE_DIR/PREFIX`` if :rose:conf:`source-prefix` is specified.
         * If a name or glob is given in a pair of brackets,
           e.g.``(hello-world.*)``, the source is considered optional and will
           not cause a failure if it does not match any source file names.

         .. warning::

            If a target does not have ``()`` around it then is it compulsory
            and if no matching source is found then the archiving of that file
            will be considered a failure.


      .. rose:conf:: source-edit-format=FORMAT

         Construct a command to edit or modify the content of source files
         before archiving them. It uses a Pythonic ``printf``-style format
         string to describe inputs and outputs.

         It must contain the placeholders ``%(in)s`` and ``%(out)s`` for
         substitution of the path to the source file and the path to the
         modified source file (which will be created in a temporary working
         directory).

         For example you might wish to replace the word "Hello" with "Greet"
         using sed:

         .. code-block:: bash

            source-edit-format=sed 's/Hello/Greet/g' %(in)s >%(out)s


      .. rose:conf:: source-prefix=PREFIX

         Add a prefix to each value in a source declaration. A trailing
         slash should be added for a directory. Paths are assumed to be
         relative to :envvar:`ROSE_SUITE_DIR`. This setting serves two
         purposes:

         * It provides a way to avoid typing the name of the source directory
           repeatedly.
         * If you are using :rose:conf:`rename-format` or if the target is
           a compressed file your target's ``%(name)s`` will be the entirety
           of what you set in :rose:conf:`source`, so you may wish to avoid
           this being a full path.

      .. rose:conf:: target-prefix=PREFIX

         Add a prefix to each target declaration. This setting provides
         a way to avoid typing the same thing repeatedly. A trailing
         slash (or whatever is relevant for the archiving system) should
         be added for a directory.

      .. rose:conf:: update-check=mtime+size|md5|sha1|...

         .. _hashlib: https://docs.python.org/3/library/hashlib.html

         Specify the method for checking whether a source has changed
         since the previous run. If the value is mtime+size, the
         application will use the modified time and size of the source,
         which is useful for large files, but is less correct. Otherwise,
         the value, if specified, should be the name of a hash object in
         Python's `hashlib`_, such as ``md5`` (default), ``sha1``, etc.
         In this mode, the application will use the checksum (based on
         the specified hashing method) of the content of each source file
         to determine if it has changed or not.
