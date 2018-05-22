``rose_bunch``
==============

For the running of multiple command variants in parallel under a single
job, as defined by the application configuration.

Each variant of the command is run in the same working directory with
its output directed to separate ``.out`` and ``.err`` files of the form:

.. code-block:: sub

   bunch.<name>.out
   
Should you need separate working directories you should configure your
command to create the appropriate subdirectory for working in.

.. note::
   
   Under load balancing systems such as PBS or Slurm, you will need to
   set resource requests to reflect the resources required by running
   multiple commands at once e.g. if one command would require 1GB
   memory and you have configured your app to run up to four commands at
   once then you will need to request 4GB of memory.


Example
-------

.. code-block:: rose

   meta=rose_bunch
   mode=rose_bunch

   [bunch]
   command-format=echo arg1: %(arg1)s, arg2: %(arg2)s, command-instance: %(command-instances)s
   command-instances = 4
   fail-handle = abort
   incremental = True
   names = foo1 bar2 baz3 qux4
   pool-size=2

   [bunch-args]
   arg1=1 2 3 4
   arg2=foo bar baz qux


Configuration
-------------

The application is normally configured in the
:rose:conf:`rose_bunch[bunch]` and :rose:conf:`rose_bunch[bunch-args]`
sections of the :rose:file:`rose-app.conf` file.

.. rose:app:: rose_bunch

   .. rose:conf:: bunch

      .. rose:conf:: command-format=FORMAT

         :compulsory: True

         A Pythonic ``printf``-style format string to construct the commands
         to run. Insert placeholders ``%(argname)s`` for substitution of the
         arguments specified under :rose:conf:`[bunch-args]` to the invoked
         command. The placeholder ``%(command-instances)s`` is reserved for
         inserting an automatically generated index for the command
         invocation when using the command-instances setting.

      .. rose:conf:: command-instances=N

         Allows the user to specify an integer value for the number of
         instances of a command they want to run. This generates the values
         used by the ``%(command-instances)s`` value in command-format.
         Useful for cases where the only difference between invocations
         would be an index number e.g. ensemble members. Note indexes
         start at ``0``.

      .. rose:conf:: pool-size=N

         Allows the user to limit the number of concurrently running commands.
         If not specified then all command variations will be run at the same
         time.

      .. rose:conf:: fail-mode=continue|abort

         :default: continue
         
         Specify what action you want the job to take on the failure of a
         command that it is trying to run. If set to continue all command
         variants will be run by the job and the job will return a non-zero
         exit code upon completion e.g. if three commands are to be run and
         the second one fails, all three will be run and the job will exit
         with a return code of ``1``. Alternatively, if :rose:conf:`fail-mode`
         is set to abort then on failure of any one of the command variants
         it will stop trying to run any further variants N.B. the job will
         wait for any already running commands to finish before exiting.
         Commands that won't be run due to aborting will be reported in the
         job output with a ``[SKIP]`` prefix when running in verbose mode.
         For example in the case of three command variants with a
         :rose:conf:`pool-size` of ``1`` and :rose:conf:`fail-mode=abort`,
         if the second variant failed then the job would exit with a
         non-zero error code without having run the third variant.

      .. rose:conf:: incremental=true|false

         :default: true
         
         If set to ``true`` then only failed commands will be re-run on
         retrying running of the job. If any changes are made to the
         configuration being run then all variants will be re-run. Similarly,
         running the app with the ``--new`` option to
         :ref:`command-rose-task-run`
         will result in all commands being run. In verbose mode the app
         will report commands that won't be run due to previous successes
         in the job output with a ``[PASS]`` prefix.

      .. rose:conf:: names=name1 name2 ...

         Allows defining names for each of the command variants to be run,
         facilitating identification in logs. If not set then commands will
         be identified by their index. The number of entries in the names
         must be the same as the number of entries in each of the args to
         be used.

   .. rose:conf:: bunch-args

      This section is used to specify the various combinations of args to be
      passed to the :rose:conf:`rose-app.conf[command]` specified under
      :rose:conf:`[bunch]command-format`.

      .. rose:conf:: argname=val1 val2 ...

         Allows defining named lists of argument values to pass to
         :rose:conf:`[bunch]command-format`. Multiple named sets of
         arguments can be defined. Each argname can be referenced in the
         using ``%(argname)s``. The only disallowed name is
         ``command-instances``, which is reserved for the
         auto-generated list of instances when the
         :rose:conf:`[bunch]command-instances=N` option is used.
