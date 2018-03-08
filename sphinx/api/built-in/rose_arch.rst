.. _rose_arch:

``rose_arch``
=============

This built-in application provides a generic solution to configure
site-specific archiving of suite files. It is designed to work under
:ref:`command-rose-task-run`.

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


Example
-------

.. code-block:: rose

   # General settings
   [arch]
   command-format=foo put %(target)s %(sources)s
   source-prefix=$ROSE_DATAC/
   target-prefix=foo://hello/

   # Archive a file to a file
   [arch:world.out]
   source=hello/world.out

   # Auto gzip
   [arch:planet.out.gz]
   source=hello/planet.out

   # Archive files matched by a glob to a directory
   [arch:worlds/]
   source=hello/worlds/*

   # Archive multiple files matched by globs or names to a directory
   [arch:worlds/]
   source=hello/worlds/* greeting/worlds/* hi/worlds/*

   # As above, but "greeting/worlds/*" may return an empty list
   [arch:worlds/]
   source=hello/worlds/* (greeting/worlds/*) hi/worlds/*

   # Target is optional, implied that sources may all be missing
   [arch:(black-box/)]
   source=cats.txt dogs.txt

   # Auto tar-gzip
   [arch:galaxies.tar.gz]
   source-prefix=hello/
   source=galaxies/*
   # File with multiple galaxies may be large, don't do its checksum
   update-check=mtime+size

   # Force gzip each source file
   [arch:stars/]
   source=stars/*
   compress=gzip

   # Source name transformation
   [arch:moons.tar.gz]
   source=moons/*
   rename-format=%(cycle)s-%(name)s
   source-edit-format=sed 's/Hello/Greet/g' %(in)s >%(out)s

   # Source name transformation with a rename-parser
   [arch:unknown/stuff.pax]
   rename-format=hello/%(cycle)s-%(name_head)s%(name_tail)s
   rename-parser=^(?P<name_head>stuff)ing(?P<name_tail>-.*)$
   source=stuffing-*.txt

   # ...


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

         If specified, compress source files to the given scheme before
         sending them to the archive. If not specified, the compress
         scheme is automatically determined by the file extension of
         the target, if it matches one of the allowed values. For the
         ``pax|tar`` scheme, the sources will be placed in a TAR archive
         before being sent to the target. For the ``pax.gz|tar.gz|tgz``
         scheme, the sources will be placed in a TAR-GZIP file before
         being sent to the target. For the ``gz`` scheme, each source
         file will be compressed by GZIP before being sent to the target.

      .. rose:conf:: rename-format

         If specified, the source files will be renamed according to the
         specified format. The format string should be a Pythonic
         ``printf``-style format string. It may contain the placeholder
         ``%(cycle)s`` (for the current :envvar:`ROSE_TASK_CYCLE_TIME`, the
         placeholder ``%(name)s`` for the name of the file, and/or named
         placeholders that are generated by :rose:conf:`rename-parser`.

      .. rose:conf:: rename-parser

         Ignored if ``rename-format`` is not specified. Specify a regular
         expression to parse the name of a source. The regular expression
         should do named captures of strings from source file names,
         which can then be used to substitute named placeholders in the
         corresponding :rose:conf:`rename-format`.

      .. rose:conf:: source=NAME

         :compolsory: True

         Specify a list of space delimited source file names and/or globs
         for matching source file names. (File names with space or quote
         characters can be escaped using quotes or backslashes, like in
         a shell.) Paths, if not absolute (beginning with a ``/``), are
         assumed to be relative to :envvar:`ROSE_SUITE_DIR` or to
         ``$ROSE_SUITE_DIR/PREFIX`` if
         :rose:conf:`source-prefix` is specified.
         If a name or glob is given in a pair of brackets, e.g.
         ``(hello-world.*)``, the source is considered optional and will
         not cause a failure if it does not match any source file names.
         However, a compulsory target that ends up with no matching source
         file will be considered a failure.

      .. rose:conf:: source-edit-format=FORMAT

         A Pythonic ``printf``-style format string to construct a command to
         edit or modify the content of source files before archiving them.
         It must contain the placeholders ``%(in)s`` and ``%(out)s`` for
         substitution of the path to the source file and the path to the
         modified source file (which will be created in a temporary working
         directory).

      .. rose:conf:: source-prefix=PREFIX

         Add a prefix to each value in a source declaration. A trailing
         slash should be added for a directory. Paths are assumed to be
         relative to :envvar:`ROSE_SUITE_DIR`. This setting serves two
         purposes. It provides a way to avoid typing the same thing
         repeatedly. It also modifies the name-spaces of the sources if
         the target is in a TAR or TAR-GZIP file. In the absence of this
         setting, the name of a source in a TAR or TAR-GZIP file is the
         path relative to :envvar:`ROSE_SUITE_DIR`. By specifying this
         setting, the source names in a TAR or TAR-GZIP file will be
         shortened by the prefix.

      .. rose:conf:: target-prefix=PREFIX

         Add a prefix to each target declaration. This setting provides
         a way to avoid typing the same thing repeatedly. A trailing
         slash (or whatever is relevant for the archiving system) should
         be added for a directory.

      .. rose:conf:: update-check=mtime+size|md5|sha1|...

         .. _hashlib: https://docs.python.org/2/library/hashlib.html

         Specify the method for checking whether a source has changed
         since the previous run. If the value is mtime+size, the
         application will use the modified time and size of the source,
         which is useful for large files, but is less correct. Otherwise,
         the value, if specified, should be the name of a hash object in
         Python's `hashlib`_, such as ``md5`` (default), ``sha1``, etc.
         In this mode, the application will use the checksum (based on
         the specified hashing method) of the content of each source file
         to determine if it has changed or not. 

