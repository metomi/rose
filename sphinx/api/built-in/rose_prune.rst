.. _builtin.rose_prune:

``rose_prune``
==============

A framework for housekeeping files and directories created by tasks in a
cycling Cylc workflow.

When Cylc workflows run, jobs may create files and logs in multiple different
locations on the network. After a few cycles of the workflow, these files
can build up, however, older files might not be needed any more.

The ``rose_prune`` app can be used to remove files from older cycles from
wherever they are stored on the network in order to free up space for
later cycles.

.. important::

   The ``rose_prune`` app should be run on a "local" host (e.g. the Cylc
   server), it uses ``ssh`` to remove files on any "remote" hosts where tasks
   ran.


Local Vs Remote Hosts
---------------------

.. rubric:: Local hosts

When you start a Cylc workflow, a :term:`scheduler` is launched.

The host where the scheduler starts is the "local" host. Any other hosts which
share the same filesystem (i.e. which see the same ``$HOME`` directory) are
also "local".

The Cylc scheduler manages some files on the "local" filesystem, e.g. the
scheduler log. Cylc may be configured to copy remote job logs back to the
local filesystem.

.. rubric:: Remote hosts

Jobs are often configured to run on "remote" hosts which do not share the same
filesystem as the Cylc server (e.g. some HPC systems). The job logs and any
files these jobs create will be on the "remote" filesystem.


Invocation
----------

To write a ``rose_prune`` app, add these lines at the top of a
``rose-app.conf`` file:

.. code-block:: rose

   meta=rose_prune
   mode=rose_prune

Then run in a task in a Cylc workflow using ``rose task-run``.

.. note::

   If the ``mode`` is not specified, the ``rose_prune`` mode will be
   automatically selected if the app is run by a Cylc task with a name that
   starts with ``rose_prune``.


Example
-------

.. code-block:: rose

   meta=rose_prune
   mode=rose_prune

   [prune]
   # remove log files on remote filesystems from cycles which are 6 hours or
   # more before the current cycle
   # i.e. ssh <remote-host> rm -r ~/cylc-run/<workflow>/<log>/<job>/<cycle>
   prune-remote-logs-at=-PT6H

   # archive (e.g. "tar") local log files from cycles one day or more before
   # the current cycle
   # i.e. gzip cylc-run/<workflow>/<log>/<job>/<cycle>
   archive-logs-at=-P1D

   # remove local log files from cycles 7 days or more before the current cycle
   # i.e. ssh <remote-host> rm -r ~/cylc-run/<workflow>/<log>/<job>/<cycle>
   prune-server-logs-at=-P7D

   # remove files matching the globs from the Cylc work directory
   # i.e. ssh <local/remote-host> rm -r ~/cylc-run/<workflow>/work/<cycle>/<glob>
   prune{work}=-PT6H:task_x* -PT12H:*/other*.dat -PT18H:task_y* -PT24H

   # remove selected items from the share/cycle directory
   # ssh <local/remote-host> rm -r ~/cylc-run/<workflow>/share/cycle/<cycle>/<glob>
   prune{share/cycle}=-PT6H:foo* -PT12H:'bar* *.baz*' -P1D

   # remove selected paths from the share directory
   # i.e. ssh <local/remote-host> rm ~/cylc-run/<workflow>/share/hello-*-at-<cycle>.txt
   prune{share}=-P1D:hello-*-at-%(cycle)s.txt


Configuration
-------------

The application is configured in the :rose:conf:`rose_prune[prune]`
section in the :rose:file:`rose-app.conf` file.

All settings are expressed as a space delimited list of cycles, normally as
:term:`cycle points <cycle point>` or :term:`offsets
<ISO8601 duration>` relative to the current cycle.

.. list-table::

   * - Workflow Cycling Type
     - :term:`Datetime Cycling`
     - :term:`Integer Cycling`
   * - :term:`Cycle Point` format
     - :term:`ISO8601 datetime` (e.g. ``20000101T00Z`` - the 1st of Jan 2000)
     - Integer (e.g. ``2`` - the second cycle)
   * - Cycle offset format
     - :term:`ISO8601 duration` (e.g. ``-P1DT6H`` - one day and 6 hours before
       the current cycle point).
     - Integer duration (e.g. ``-P2`` - two cycles before the current cycle
       point)

The cycles of some settings also accept an optional argument followed
by a colon. In these, the argument should be globs for matching items
in the directory. If two or more globs are required, they should be
separated by a space. In which case, either the argument should be
quoted or the space should be escaped by a backslash.

.. _rose_prune.globs:

.. note::

   ``rose_prune`` uses Bash `extglob pattern matching`_ which supports simple
   (e.g. ``*``) and extended (e.g. ``!(foo)``) pattern matching.

   For more information see the ``shopt`` documentation for the version
   of bash you have installed (``$ man shopt``).

.. rose:app:: rose_prune

   .. rose:conf:: prune

      .. rose:conf:: cycle-format{key}=format

         Specify a key to a format string for use in conjunction with a
         :rose:conf:`prune{item-root}=cycle:globs` setting.

         For example, we may
         have something like ``cycle-format{cycle_year}=CCYY`` and
         ``prune{share}=-P1Y:xmas-present-%(cycle_year)s/``. If the
         current cycle point is ``20151201T0000Z``, it will clear out the
         directory ``share/xmas-present-2014/``.

         The ``key`` can be any string that can be used in a ``%(key)s``
         substitution, and format should be a a valid :ref:`command-rose-date`
         print format.

      .. rose:conf:: prune-remote-logs-at=cycle ...

         Remove remote job logs at these cycles.

      .. rose:conf:: prune-server-logs-at=cycle ...

         Remove logs on the suite server. Removes both log directories
         and archived logs.

      .. rose:conf:: archive-logs-at=cycle ...

         Archive all job logs at these cycles. Remove remote job logs on
         success.

      .. rose:conf:: prune{item-root}=cycle[:glob] ...

         Remove items from within a specified directory.

         ``item-root``
            A path within the workflow's :term:`run directory` e.g. ``work`` or
            ``share/cycle``.
         ``cycle``
            The cycle to remove items from or an offset from the current cycle.
         ``glob``
            Remove only files matching a :ref:`glob pattern <rose_prune.globs>`.

         By default ``rose_prune`` will remove files within a cycle
         subdirectory under ``item-root``,
         E.g. If current cycle is ``20141225T1200Z``,
         ``prune{work}=-PT12H`` will remove the ``work/20141225T0000Z/``
         directory.

         If you want to clear out paths that include a cycle, rather than a
         cycle subdirectory, you can template the path using the ``%(cycle)s``
         substitution,
         E.g. If current cycle is ``20141225T1200Z``, then
         ``prune{share}=-PT12H:%(cycle)s.txt`` will remove
         ``share/20141225T0000Z.txt``.

         To use different date-time formats, add custom subsitutions using
         :rose:conf:`cycle-format{key}=format`, E.g.
         ``cycle-format{cycle_year_month}=CCYYMM``.

         .. rubric:: Examples:

         If the current cycle is ``20141225T1200Z``:

         .. code-block:: rose

            # remove work/20141225T0000Z/
            prune{work}=-PT12H

            # remove work/20141225T0000Z/glob*
            prune{work}=-PT12H:glob*

            # remove share/hello-*-at-20141225T0000Z.txt
            prune{share}=-PT12H:hello-*-at-%(cycle)s.txt

            # remove share/hello-*-at-201412.txt
            cycle-format{cycle_year_month}=CCYYMM
            prune{share}=-PT12H:hello-*-at-%(cycle_year_month)s.txt

            # remove share/hello-*-at-2014.txt
            cycle-format{cycle_year}=CCYY
            prune{share}=-PT12H:hello-*-at-%(cycle_year)s.txt

            # remove share/cycle/<cycle>/<glob>
            prune{share/cycle}=-PT6H:foo* -PT12H:'bar* *.baz*' -P1D

      .. rose:conf:: prune-work-at=cycle[:globs] ...

         .. deprecated:: 2015.04.0
            Equivalent to ``prune{work}=cycle[:globs] ...``.

      .. rose:conf:: prune-datac-at=cycle[:globs] ...

         .. deprecated:: 2015.04.0
            Equivalent to ``prune{share/cycle}=cycle[:globs] ...``.
