Polling
=======

Polling allows you to check for some condition to be met prior to running the
main command in an app without the need for additional entries in the
dependencies graph.

For example, you might want to run a polling command to check for the
existence of a particular file before running the main command which
requires said file.


Example
-------

Create a new Rose suite configuration::

   mkdir -p ~/rose-tutorial/polling
   cd ~/rose-tutorial/polling

Create a blank :rose:file:`rose-suite.conf` and a ``suite.rc``
file that looks like this:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST
   [scheduling]
       [[dependencies]]
           graph = """compose_letter => send_letter
                      bob => read_letter"""

This is a simple suite which consists of the following:

* A ``compose_letter`` task.
* A ``send_letter`` task which is run once the letter is composed.
* A ``bob`` task which we will be using to poll with.
* A ``read_letter`` task which will run once the polling task is complete.

It will need some runtime. Add the following to your ``suite.rc`` file:

.. code-block:: cylc

   [runtime]
       [[root]]
           script = sleep 10
       [[compose_letter]]
           script = sleep 5; echo 'writing a letter to Bob...'
       [[send_letter]]
           env-script = eval `rose task-env`
           script = """
                    sleep 5
                    echo 'Hello Bob' > $ROSE_DATA/letter.txt
                    sleep 10
                    """

       [[bob]]
           script = rose task-run
       [[read_letter]]
           env-script = eval `rose task-env`
           script = sleep 5; cat $ROSE_DATA/letter.txt
           post-script = rm $ROSE_DATA/letter.txt


Adding Polling
--------------

In the suite directory create an ``app`` directory.

In the ``app`` directory create a directory called ``bob``.

In the newly-created ``bob`` directory, create a :rose:file:`rose-app.conf`
file.

Edit the :rose:file:`rose-app.conf` file to look like this:

.. code-block:: rose

   [poll]
   delays=10*PT5S
   test=test -e $ROSE_DATA/letter.txt

   [command]
   default=echo 'Ooh, a letter!'

We now have an app that does the following:

* Has a polling ``test`` that checks for the existence of a file.
* Polls up to 10 times with 5 second delays between each attempt.
* Prints a message once the polling test succeeds.

.. note::

   The ordering of the ``[poll]`` and ``[command]`` sections is not important.
   In practice, it may be preferable to have the ``[command]`` section at
   the top as that should contain the main command(s) being run by the app.

Save your changes and run the suite using :ref:`command-rose-suite-run`.

The suite should now run.

Notice that ``bob`` finishes and triggers ``read_letter`` before
``send_letter`` has completed. This is because the polling condition has
been met, allowing the main command in ``bob`` to be run.


Improving The Polling
---------------------

At present we have specified our own routine for testing for the existence
of a particular file using the ``test`` option. However, Rose provides a
simpler method for doing this.

Edit the :rose:file:`rose-app.conf` in your ``bob`` app to look like the
following:

.. code-block:: rose

   [poll]
   delays=10*PT5S
   all-files=$ROSE_DATA/letter.txt

   [command]
   default=echo 'Ooh, a letter!'

Polling is now making use of the ``all-files`` option, which allows you to
specify a list of files to check the existence of. Save your changes and
run the suite to confirm it still works.


Available Polling Types
-----------------------

Test and all-files are just two of the available polling options:

``all-files``
   Tests if all of the files in a list exist.
``any-files``
   Tests if any of the files in a list exist.
``file-test``
   Changes the test used to evaluate the ``any-files`` and ``all-files`` lists
   to a shell script to be run on each file (e.g. ``grep``). Passes if the
   command exits with a zero return code.
``test``
   Tests using a shell script, passes if the command exits with a zero return
   code. *Note this is separate from the* ``all-files``, ``any-files`` *testing
   logic.*

.. tip::

   For more details see :ref:`Rose Applications`.


Possible Uses For Polling
-------------------------

Depending on your needs, possible uses for polling might include:

* Checking for required output from a long-running task rather than waiting
  for the task to complete.
* Monitoring output from another suite.
* Checking if a file has required content before using it.
