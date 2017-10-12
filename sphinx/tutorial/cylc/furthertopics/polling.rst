Polling
=======

Introduction
------------

This tutorial walks you through using polling.

Polling allows you to check for some condition to be met prior to running the main command in an app.

Purpose
-------

Polling can be used to have a task wait until a particular condition is met, without the need for additional entries in the dependencies graph. For example, you might want to run a polling command to check for the existence of a particular file before running the main command which requires said file.

Example
-------

Create a new cylc suite (or just a new directory somewhere - e.g. in your homespace) containing a blank ``rose-suite.conf`` and a ``suite.rc`` file that looks like this:

.. code-block:: cylc

   [cylc]
       UTC mode = True # Ignore DST
   [scheduling]
       [[dependencies]]
           graph = """compose_letter => send_letter
                      bob => read_letter"""


This sets up a simple suite which consists of the following:

    - a ``compose_letter`` task
    - a ``send_letter`` task which is run once the letter is composed
    - a ``bob`` task which we will be using to poll with
    - a ``read_letter`` task which will run once the polling task is complete

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


Adding polling
--------------

In the suite directory create an ``app`` directory.

In the ``app`` directory create a directory called ``bob``.

In the newly created ``bob`` directory, create a ``rose-app.conf`` file.

Edit the ``rose-app.conf`` file to look like this:

.. code-block:: rose

   [poll]
   delays=10*PT5S
   test=test -e $ROSE_DATA/letter.txt

   [command]
   default=echo 'Ooh, a letter!'

We now have an app that does the following:

   - has a polling ``test`` that checks for the existence of a file
   - polls up to 10 times with 5 second delays between each attempt
   - prints a message once the polling test succeeds

N.B. the ordering of the ``[poll]`` and ``[command]`` sections is not important. In practice, it may be preferable to have the ``[command]`` section at the top as that should contain the main command(s) being run by the app.

Save your changes and run the suite using ``rose suite-run``.

The suite should now run.

Notice that ``bob`` finishes and triggers ``read_letter`` before ``send_letter`` has completed. This is because the polling condition has been met, allowing the main command in ``bob`` to be run.

Improving the polling
---------------------

At present we have specified our own routine for testing for the existence of a particular file using the ``test`` option. However, rose provides a simpler method for doing this.

Edit the ``rose-app.conf`` in your ``bob`` app to look like the following:

.. code-block:: rose

   [poll]
   delays=10*PT5S
   all-files=$ROSE_DATA/letter.txt

   [command]
   default=echo 'Ooh, a letter!'

Polling is now making use of the ``all-files`` option, which allows you to specify a list of files to check the existence of. Save your changes and run the suite to confirm it still works.


Available polling types
-----------------------

test and all-files are just two of the available polling options:

   - all-files - a list of space delimited list of files which only passes if all file paths in the list exist.
   - any-files - a list of space delimited list of files which passes if any file path in the list exists.

   - file-test - allows you perform tests on a file if checking its existence is not enough e.g. perform a ``grep``.
   - test - a shell command which passes if the command returns a 0 (zero) return code.

For more details see the application configuration file section of: Configuration.


Possible uses for polling
-------------------------

Depending on your needs, possible uses for polling might include:

   - checking for required output from a long running task rather than waiting for the task to complete
   - monitoring output from another suite
   - checking if a file has required content before using it



