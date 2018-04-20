Rose Arch
=========

:rose:app:`rose_arch` is a built-in :term:`Rose app` that provides a generic
solution to the archiving of suite files.

.. admonition:: Good Practice
   :class: hint

   Only archive the minimum files needed at each cycle of your suite. Run
   the archiving task before any housekeeping in the graph.


Example
-------

Create a new Rose suite configuration::

   mkdir -p ~/rose-tutorial/rose-arch-tutorial

Create a blank :rose:file:`rose-suite.conf` and a ``suite.rc``
file that looks like this:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST
       [[events]]
           abort on timeout = True
           timeout = PT1H
   [scheduling]
       [[dependencies]]
           graph = make_files => archive_files_rsync => archive_files_scp
   [runtime]
       [[root]]
           env-script = eval $(rose task-env)
           script = rose task-run

       [[make_files]]
           script = """
               echo 'zip' >> $ROSE_DATAC/file_zip
               echo 'solo' >> $ROSE_DATAC/file_solo
               echo 'list1' >> $ROSE_DATA/file_list1
               echo 'list2' >> $ROSE_DATA/file_list2
               echo 'list3' >> $ROSE_DATA/file_list3
               mkdir -p $ROSE_DATA/ARCHIVING || true
               mkdir -p $ROSE_DATA/ARCHIVING/rename || true
           """
       [[archive_files_rsync]]
       [[archive_files_scp]]

In the suite directory create an ``app/`` directory::

   mkdir app

In the app directory create an ``archive_files_rsync/`` directory::

   cd app
   mkdir archive_files_rsync

In the ``app/archive_files_rsync/`` directory create a
:rose:file:`rose-app.conf` file. This example uses ``vi``, but please use your
editor of choice::

   cd archive_files_rsync
   vi rose-app.conf

Paste in the following lines:

.. code-block:: rose

   mode=rose_arch

   [env]
   ARCH_TARGET=$ROSE_DATA/ARCHIVING

   [arch]
   command-format=rsync -a %(sources)s %(target)s
   source-prefix=$ROSE_DATAC/
   target-prefix=$ARCH_TARGET/
   update-check=mtime+size

   [arch:solo.file]
   source=file_solo

   [arch:files]
   source=file_list1 file_list3
   source-prefix=$ROSE_DATA/

   [arch:dir]
   source=file*
   source-prefix=$ROSE_DATA/

   [arch:file_zipped.tar]
   source=file_zip

Move to the ``app/`` directory::

   cd ..
   ls

The following should be returned:

.. code-block:: none

   archive_files_rsync

Create an ``archive_files_scp/`` directory::

   mkdir archive_files_scp

In the ``archive_files_scp/`` directory create a :rose:file:`rose-app.conf`
file. This example uses ``vi``, but please use your editor of choice::

   cd archive_files_scp
   vi rose-app.conf

Paste in the following lines:

.. code-block:: rose

   mode=rose_arch

   [env]
   ARCH_TARGET=$ROSE_DATA/ARCHIVING

   [arch]
   command-format=scp %(sources)s %(target)s
   source-prefix=$ROSE_DATA/
   target-prefix=$ARCH_TARGET/
   update-check=mtime+size

   [arch:rename/]
   rename-format=%(cycle)s_%(tag)s_%(name)s
   rename-parser=^.*list(?P<tag>.*)$
   source=file_list?


Description
-----------

You have now created a suite that defines three tasks:

``make_files``
   Sets up the files and ``ARCHIVING/`` directory for ``archive_files_rsync/``
   and ``archive_files_scp/`` to "archive", move, data to.
``archive_files_rsync``
   "Archives" (``rsync``'s) files to the ``ARCHIVING/`` folder in the
   ``$ROSE_DATA/`` directory.
``archive_files_scp``
   "Archives" (``scp``'s) the renamed files and moves them to the ``ARCHIVING/``
   folder in the ``$ROSE_DATA/`` directory.

Save your changes and run the suite::

   rose suite-run

View the suite output using :ref:`command-rose-suite-log` and inspect the
output of the ``make_files``, ``archive_files_rsync`` and ``archive_files_scp``
tasks.


Results Of "Archiving"
----------------------

Change to the ``$ROSE_DATA/ARCHVING/`` directory of the suite i.e:

.. code-block:: sub

   cd ~/cylc-run/<SUITE_ID>/share/data/ARCHIVING/

List the directory by typing::

   ls

You should see the following returned:

.. code-block:: none

   dir  file_zipped.tar  files  rename  solo.file

Change directory to ``files/`` and list the files::

   cd files
   ls

The following should be returned:

.. code-block:: none

   file_list1  file_list3

Change directory to ``ARCHIVING/dir/`` and list the files::

   cd ..
   cd dir
   ls

The following should be returned:

.. code-block:: none

   file_list1  file_list2 file_list3

.. note::

   These were all of the files in the ``$ROSE_DATA/`` directory.

Change diectory to ``ARCHIVING/rename/`` and list the files::

   cd ..
   cd rename
   ls

The following should be returned:

.. code-block:: none

   1_1_file_list1 1_2_file_list2 1_3_file_list3 

These are the renamed files.

.. _rsync: https://linux.die.net/man/1/rsync
.. _scp: https://www.lifewire.com/rcp-scp-ftp-commands-for-copying-files-3971107

Most users will have their own system or location that they wish to archive
their data to. Here the example shown uses `rsync`_ and `scp`_.
Please refer your own site specific archiving solutions and seek site
specfic advice.


Arch Settings
-------------

Some settings that can be used are described below. See the :ref:`rose_arch`
documentation for more information:

Above ``.tar`` was used to compress the file. However, ``compress=gzip``
can also be used. Note either of these commands can be used to compress a
file or a folder/directory.

In the above example a regular expression 'reg exp' was used by the
``rename-parser``, for example, ``^.*list(?P<tag>.*)$``, where:

.. _greedy: https://stackoverflow.com/questions/2301285/what-do-lazy-and-greedy-mean-in-the-context-of-regular-expressions

* ``^`` = start of a string.
* ``$`` = end of a string.
* ``.`` = any character.
* ``*`` = `greedy`_ (all).
* ``?P<NAME>`` = named group.

.. note::

   .. _Python flavor: https://docs.python.org/2/howto/regex.html

   ``rose arch`` uses the `Python flavor`_ for regular expressions.

In the above example source was used to accept a list of glob patterns.
For example, ``file_list?`` was used where the ``?`` relates to one unknown
character.

.. note::

   These examples are just some possible examples and not a full list.

As well as :rose:conf:`rose_arch[arch]` and ``[arch:TARGET]`` other options
can be provided to the app, for example:

``[env]``
   Can be defined near the top of the app to allow an environment variable
   to be available to the ``[arch:]`` commands in the app.

   Also see :rose:conf:`rose-app.conf[env]` and the suite example above.
``[poll]``
   Polling can be defined, and is often near the bottom of the app. This
   will allow the app to poll with a defined delay, e.g.
   :rose:conf:`rose-app.conf[poll]delays=5`.
``[file:TARGET]``
   This option allows the user to, for example, make the directory
   ``TARGET``, e.g. :rose:conf:`*[file:TARGET]mode=mkdir`.

For more information, see the :ref:`rose_arch` documentation.
