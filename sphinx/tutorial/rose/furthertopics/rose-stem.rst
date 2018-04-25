.. include:: ../../../hyperlinks.rst
   :start-line: 1

.. _Rose Stem:

Rose Stem
=========

Rose Stem is a testing system for use with Rose. It provides a user-friendly
way of defining source trees and tasks on the command line which are then
passed by Rose Stem to the suite as Jinja2 variables.

.. warning::

   Rose Stem requires the use of `FCM`_ as it requires some of the version
   control information.


Motivation
----------

Why do we test code?

Most people would answer something along the lines of "so we know it works".

However, this is really asking two related but separate questions.

#. Does the code do what I meant it to do?
#. Does the code do anything I didn't mean it to do?

Answering the first question may involve writing a bespoke test and checking
the results. The second question can at least partially be answered by using
an automated testing system which runs predefined tasks and presents the
answers. Rose Stem is a system for doing this.

N.B. When writing tests for new code, they should be added to the testing
system so that future developers can be confident that they haven't broken
the new functionality.


Rose Stem
---------

There are two components in Rose Stem:

:ref:`command-rose-stem`
   The command line tool which executes an appropriate suite.
:rose:app:`rose_ana`
   A Rose built-in application which can compare the result of a task against
   a control.

We will describe each in turn. It is intended that a test suite lives
alongside the code in the same version-controlled project, which should
encourage developers to update the test suite when they update the code.
This means that the test suite will always be a valid test of the code
it is accompanying.


Running A Suite With :ref:`command-rose-stem`
---------------------------------------------

The ``rose stem`` command is essentially a wrapper to
:ref:`command-rose-suite-run`, which accepts some additional arguments
and converts them to Jinja2 variables which the suite can interpret.

These arguments are:

``--source``
   Specifies a source tree to include in a suite.
``--group``
   Specifies a group of tasks to run.

A group is a set of Rose tasks which together test a certain configuration
of a program.


The ``--source`` Argument
-------------------------

The source argument provides a set of Jinja2 variables which can then be
included in any compilation tasks in a suite. You can specify multiple
``--source`` arguments on the command line. For example::

   rose stem --source=/path/to/workingcopy --source=fcm:other_project_tr@head

Each source tree is associated with a project (via an ``fcm`` command) when
:ref:`command-rose-stem` is run on the command line. This project name
is then used in the construction of the Jinja2 variable names.

Each project has a Jinja2 variable ``SOURCE_FOO`` where ``FOO`` is the
project name. This contains a space-separated list of all sourcetrees
belonging to that project, which can then be given to an appropriate
build task in the suite so it builds those source trees.

Similarly, a ``HOST_SOURCE_FOO`` variable is also provided. This is
identical to ``SOURCE_FOO`` except any working copies have the local
hostname prepended. This is to assist building on remote machines.

The first source specified must be a working copy which contains the
Rose Stem suite. The suite is expected to be in a
subdirectory named ``rose-stem`` off the top of the working copy. This
source is used to generate three additional variables:

``SOURCE_FOO_BASE``
   The base directory of the project
``HOST_SOURCE_FOO_BASE``
   The base directory of the project with the hostname prepended if it is a
   working copy
``SOURCE_FOO_REV``
   The revision of the project (if any)

These settings override the variables in the :rose:file:`rose-suite.conf` file.

These should allow the use of configuration files which control the build
process inside the working copy, e.g. you can refer to::

   {{HOST_SOURCE_FOO_BASE}}/fcm-make/configs/machine.cfg{{SOURCE_FOO_REV}}

If you omit the source argument, Rose Stem defaults to assuming that the
current directory is part of the working copy which should be added as a
source tree::

   rose stem --source=.

The project to which a source tree belongs is normally automatically
determined using `FCM`_ commands. However, in the case where the source tree
is not a valid FCM URL, or where you wish to assign it to another project,
you can specify this using the ``--source`` argument::

   rose stem --source=foo=/path/to/source

assigns the URL ``/path/to/source`` to the foo project, so the variables
``SOURCE_FOO`` and ``SOURCE_FOO_BASE`` will be set to ``/path/to/source``.


The ``--group`` Argument
------------------------

The group argument is used to provide a Pythonic list of groups in the
variable ``RUN_NAMES`` which can then be looped over in a suite to switch
sets of tasks on and off.

Each ``--group`` argument adds another group to the list. For example::

   rose stem --group=mygroup --group=myothergroup

runs two groups named ``mygroup`` and ``myothergroup`` with the current
working copy. The suite will then interpret these into a set of tasks which
build with the given source tree(s), run the program, and compare the output.


The ``--task`` Argument
-----------------------

The task argument is provided as a synonym for ``--group``. Depending on how
exactly the Rose Stem suite works users may find one of these arguments more
intuitive to use than the other.


Comparing Output With :rose:app:`rose_ana`
------------------------------------------

Any task beginning with ``rose_ana_`` will be interpreted by Rose as a Rose Ana
task, and run through the :rose:app:`rose_ana` built-in application.

A Rose Ana :rose:file:`rose-app.conf` file contains a series of blocks;
each one describing a different analysis task to perform. A common
task which Rose Ana is used for is to compare output contained in different
files (e.g. from a new test versus previous output from a control).
The analysis modules which provide these tasks are flexible and able to be
provided by the user; however there is one built-in module inside Rose Ana
itself.

An example based on the built-in ``grepper`` module:

.. code-block:: rose

   [ana:grepper.FilePattern(Compare data from myfile)]
   pattern='data value:(\d+)'
   files=/data/kgo/myfile
        =../run.1/myfile

This tells Rose Ana to scan the contents of the file ``../run.1/myfile``
(which is relative to the Rose Ana task's work directory) and the contents of
``/data/kgo/myfile`` for the specified regular expression. Since the
pattern contains a group (in parentheses) so it is the contents of this
group which will be compared between the two files. The ``grepper.FilePattern``
analysis task can optionally be given a "tolerance" option for matching
numeric values, but without it the matching is expected to be exact.
If the pattern or group contents do not match the task will return a failure.

As well as sections defining analysis tasks, Rose Ana apps allow for one
additional section for storing global configuration settings for the app.
Just like the tasks themselves these options and their effects are
dependent on which analysis tasks are used by the app.

Therefore we will here present an example using the built-in ``grepper``
class. An app may begin with a section like this:

.. code-block:: rose

   [ana:config]
   grepper-report-limit=5
   skip-if-all-files-missing=.true.

Each of these modifies the behaviour of ``grepper``. The first option
suppresses printed output for each analysis task once the specified number
of lines have been printed (in this case 5 lines). The second option
causes Rose Ana to skip any ``grepper`` tasks which compare files in the
case that both files do not exist.

.. note::

   Any options given to this section may instead be specified in the
   :rose:conf:`rose.conf[rose-ana]` section of the user or site configuration.
   In the case that the same configuration option appears in both locations
   the one contained in the app file will take precedence.

It is possible to add additional analysis modules to Rose Ana by placing an
appropriately formatted python file in one of the following places (in order
of precedence):

#. The ``ana`` sub-directory of the Rose Ana application.
#. The ``ana`` sub-directory of the suite.
#. Any other directory which is accessible to the process running Rose Ana
   and is specified in the :rose:conf:`rose.conf[rose-ana]method-path`
   variable.

The only analysis module provided with Rose is
:py:mod:`rose.apps.ana_builtin.grepper`, it provides the following analysis
tasks and options:

.. autoclass:: rose.apps.ana_builtin.grepper.SingleCommandStatus
   :noindex:

.. autoclass:: rose.apps.ana_builtin.grepper.SingleCommandPattern
   :noindex:

.. autoclass:: rose.apps.ana_builtin.grepper.FilePattern
   :noindex:

.. autoclass:: rose.apps.ana_builtin.grepper.FileCommandPattern
   :noindex:

.. automodule:: rose.apps.ana_builtin.grepper
   :noindex:

The format for analysis modules themselves is relatively simple; the easiest
route to understanding how they should be arranged is likely to look at the
built-in ``grepper`` module. But the key concepts are as follows. To be
recognised as a valid analysis module, the Python file must contain at
least one class which inherits and extends
:py:mod:`rose.apps.rose_ana.AnalysisTask`:

.. autoclass:: rose.apps.rose_ana.AnalysisTask

For example:

.. code-block:: python

   from rose.apps.rose_ana import AnalysisTask

   class CustomAnalysisTask(AnalysisTask):
       """My new custom analysis task."""
       def run_analysis(self):
           print self.options  # Dictionary of options (see next slide)
           if self.options["option1"] == "5":
               self.passed = True

Assuming the above was saved in a file called ``custom.py`` and placed
into a folder suitable for analysis modules this would allow a Rose Ana
application to specify:

.. code-block:: rose

   [ana:custom.CustomAnalysisTask(Example rose-ana test)]
   option1 = 5
   option2 = test of Rose Ana
   option3 = .true.

.. note::

   The custom part of the filename appears at the start of the
   ``ana`` entry, followed by the name of the desired class (in the style
   of Python's own namespacing). All options specified by the app-task
   will be processed by Rose Ana into a dictionary and attached to the
   running analysis class instance as the options attribute. Hopefully you
   can see that in this case the task would pass because ``option1`` is set
   to 5 as required by the class.


.. _The Rose Ana Comparison Database:

The Rose Ana Comparison Database
--------------------------------

In addition to performing the comparisons each of the Rose Ana tasks in the
suite can be configured to append some key details about any comparisons
performed to an sqlite database kept in the suite's log directory (at
``log/rose-ana-comparisons.db``).

This is intended to provide a quick means to interrogate the suite for
information about the status of any comparisons it has performed. There are
2 tables present in the suite which contain the following:

.. TODO - migrate this documentation into the codebase?

tasks (TABLE)
   The intention of this table is to detect if any Rose Ana tasks have
   failed unexpectedly (or are still running).

   Contains an entry for each Rose Ana task, using the following columns:

   task_name (TEXT)
      The exact name of the Rose Ana task.
   completed (INT)
      Set to 1 when the task starts performing its comparisons then updated
      to 0 when the task has completed

      .. note::

         Task success is not related to the success/failed state of the
         comparisons).

comparisons (TABLE)
   The intention of this table is to provide a record of which files
   were compared by which tasks, how they were compared and what the
   result of the comparison was.

   Contains an entry for each individual comparison from every
   Rose Ana task, using the following columns:

   comp_task (TEXT)
      The comparison task name - by convention this is usually the
      comparison section name from the app defintion (including the
      part inside the brackets).
   kgo_file (TEXT)
      The full path to the file specified as the KGO file in
      the app definition.
   suite_file (TEXT)
      The full path to the file specified as the
      active test output in the app definition.
   status (TEXT)
      The status of the task (one of " OK ", "FAIL" or "WARN").
      comparison (TEXT) Additional details which may be provided
      about the comparison.

The database is entirely optional; by default is will not be produced; if
it is required it can be activated by setting
:rose:conf:`rose.conf[rose-ana]kgo-database=.true.`.

.. note::

   The system does not provide any direct methods for working with or
   interrogating the database - since there could be various reasons for
   doing so, and there may be other suite-design factors to consider.
   Users are therefore expected to provide this functionality separately
   based on their specific needs.


Summary
-------

From within a working copy, running ``rose stem`` is simple. Just run::

   rose stem --group=groupname

replacing the groupname with the desired task. Rose Stem should then
automatically pick up the working copy and run the requested tests on it.

Next see the :ref:`Rose Stem Tutorial`

.. toctree::
   :hidden:

   rose-stem/tutorial.rst
