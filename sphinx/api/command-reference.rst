.. _Command Reference:

Command Reference
=================


Rose Commands
-------------

.. auto-cli-doc:: rose rose

----

.. _command-rose-config-edit:

rose config-edit
^^^^^^^^^^^^^^^^

.. warning::

   The Rose Edit GUI has not yet been reimplemented in Rose 2.

   The old Rose 2019 (Python 2) GUI remains compatible with Rose 2
   configurations.

.. _command-rose-suite-run:

rose suite-run
^^^^^^^^^^^^^^

This command has been replaced by ``cylc install ; cylc play``.

.. TODO: This is here to allow the documentation tests to pass

.. _command-rose-suite-restart:

rose suite-restart
^^^^^^^^^^^^^^^^^^

This command has been replaced by ``cylc play``.

.. TODO: This is here to allow the documentation tests to pass

.. _command-rose-stem:

rose stem
^^^^^^^^^

The ``rose stem`` command is now provided by :ref:`Cylc Rose`, see the
:ref:`Cylc documentation <rose-stem>` for details.

----

.. _command-rose-test-battery:

etc/bin/rose-test-battery
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   $ROSE_DEVELOPER_DIR/etc/bin/rose-test-battery

Run Rose self tests.

n.b. This will only work where a developer has downloaded and installed
their own copy of Rose using pip install -e .

Change directory to Rose source tree, and runs this shell command:

``exec prove -j "$NPROC" -s -r "${@:-t}"``

where ``NPROC`` is the number of processors on your computer (or the
setting ``[t]prove-options`` in the site/user configuration file). If you
do not want to run the full test suite, you can specify the names of
individual test files or their containing directories as extra arguments.

**EXAMPLES**

.. code-block:: bash

   # Run the full test suite with the default options.
   rose test-battery
   # Run the full test suite with 12 processes.
   rose test-battery -j 12
   # Run only tests under "t/rose-app-run/" with 12 processes.
   rose test-battery -j 12 t/rose-app-run
   # Run only "t/rose-app-run/07-opt.t" in verbose mode.
   rose test-battery -v t/rose-app-run/07-opt.t

**SEE ALSO**

* ``prove(1)``\

----


Rosie Commands
--------------

.. auto-cli-doc:: rose rosie
