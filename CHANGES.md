# Rose Changes

Go to https://github.com/metomi/rose/milestones?state=closed
for a full listing of issues for each release.

--------------------------------------------------------------------------------

## 2016.11.1 (2016-11-29)

Rose release 46. This release works best with
[cylc-6.11.2](https://github.com/cylc/cylc/releases/tag/6.11.2) and
[fcm-2016.10.0](https://github.com/metomi/fcm/releases/tag/2016.10.0).

### Noteworthy Changes

[#2020](https://github.com/metomi/rose/pull/2020):
Rose Bush: fix task/job status filter for the pager widget.

[#2018](https://github.com/metomi/rose/pull/2018):
rose macro: new `--transform` option to prepend all transformer macros to the
argument list. The existing `--fix` option will still prepend all internal
transformer (fixer) macros to the argument list.

[#2014](https://github.com/metomi/rose/pull/2014):
Rosie Disco: now respect space characters in individual search terms.

[#2013](https://github.com/metomi/rose/pull/2013):
rose config-edit: improve spin button widget behaviour when value is an
environment variable syntax.

[#2011](https://github.com/metomi/rose/pull/2011):
rose_bunch: now provide an environment variable `ROSE_BUNCH_LOG_PREFIX` for
each bunch instance at runtime to identify the log prefix that will be used for
output.

--------------------------------------------------------------------------------

## 2016.11.0 (2016-11-11)

Rose release 45. This release works best with
[cylc-6.11.2](https://github.com/cylc/cylc/releases/tag/6.11.2) and
[fcm-2016.10.0](https://github.com/metomi/fcm/releases/tag/2016.10.0).

### Highlighted Changes

[#1996](https://github.com/metomi/rose/pull/1996):
rose_ana: new version.
* Analysis logic is now specified via external modules, which in general are
  expected to be written or supplied by the user.
* One such method is built into Rose (`rose.apps.ana_builtin.grepper`),
  it handles comparisons of text contents between different files or the output
  from simple commands.
* Change in formatting of `rose_ana` app files (though apps in old format 
  will fall-back to the deprecated behaviour; to be retired in a future release).
* Failure of a single analysis sub-task no longer forces a fatal error in the 
  main task.
* Hopeful resolution of database locking issues (KGO database functionality is
  now *opt-in*, and the locking mechanism has been changed).

[#1994](https://github.com/metomi/rose/pull/1994):
rose bush: improve tasks and jobs filtering:
* Cycles list now displays number of tasks and jobs.
* Cycles list now provides download links to those cycles with a
  `log/job-CYCLE.tar.gz`.
* Jobs list can now be filtered by job status combinations and individual
  cylc task statuses.
* Job list cycles filter can now use syntax such as
  `<CYCLE` (currently `before CYCLE`), `>CYCLE` (currently `after CYCLE`).
* Improve display for screens with smaller width.

### Noteworthy Changes

[#2010](https://github.com/metomi/rose/pull/2010):
rose config-edit: better behaviour for environment variables in `values`
metadata. Always display such settings as a radio/combobox (do not try to
change to a textbox).

[#2009](https://github.com/metomi/rose/pull/2009):
rose macro: add reporter macros. Adds a new Reporter macro type.

[#2008](https://github.com/metomi/rose/pull/2008):
rose config-edit: fix macro optional_config_name kwarg (broken since
2016.07.0).

[#2007](https://github.com/metomi/rose/pull/2007):
rose config-edit: change default to show fixed variables.

[#2006](https://github.com/metomi/rose/pull/2006):
rose config-edit: extended multiple selection to groups. Stash entries can now
be ignored/deleted for a tree of entries (i.e. in group view). If a parent
section is ignored/deleted then this action will apply (recursively) to all
child sections.

[#2005](https://github.com/metomi/rose/pull/2005):
rose file install: new `symlink+` mode that checks for existence of the link
target.

[#2004](https://github.com/metomi/rose/pull/2004):
rose config-edit: fixed integer widget updating.

[#2003](https://github.com/metomi/rose/pull/2003):
rose config-edit: allow removal of empty elements in compulsory arrays.

[#2002](https://github.com/metomi/rose/pull/2002):
rose config-edit: allow newline separators in space-separated list.

[#2001](https://github.com/metomi/rose/pull/2001):
rose macro: don't run transform macros in validate mode.

[#2000](https://github.com/metomi/rose/pull/2000):
rose macro: new `--suite-only` option.

[#1998](https://github.com/metomi/rose/pull/1998):
rose_prune: fix bad fail message on non-suite host.

[#1995](https://github.com/metomi/rose/pull/1995):
rose bush and rosie disco: ad hoc server can now have service name in URL.

[#1990](https://github.com/metomi/rose/pull/1990),
[#1993](https://github.com/metomi/rose/pull/1993):
User guide and tutorial updated to latest cylc usage.

[#1988](https://github.com/metomi/rose/pull/1988):
rose bush: jobs list: fix paths in tar links. Previously a link to a log in a
tar archive may take users to a random path.

[#1987](https://github.com/metomi/rose/pull/1987):
rose config-edit: fixes an inflexibility in the third-party UM STASH widget
when importing packages from metadata (a demo piece of functionality). It also
fixes a problem with duplicated attempts at adding sections.

--------------------------------------------------------------------------------

## 2016.09.0 (2016-09-14)

Rose release 44. This release works best with
[cylc-6.11.0](https://github.com/cylc/cylc/releases/tag/6.11.0) and
[fcm-2016.05.1](https://github.com/metomi/fcm/releases/tag/2016.05.1),
or their successors.

### Noteworthy Changes

[#1982](https://github.com/metomi/rose/pull/1982):
rosa svn-post-commit: fix handling of settings with `!` ignored flags in
`rose-suite.info`.

[#1976](https://github.com/metomi/rose/pull/1976):
Rose Bush: job logs listing: now accepts log files with names in these patterns
`*.NNN.*`, `*.KEY.*` as sequetial files.

[#1972](https://github.com/metomi/rose/pull/1972):
Rose Bush: cycles list: only count cycles with non-waiting tasks.

[#1970](https://github.com/metomi/rose/pull/1970):
rose config-edit: fix info dialog for variables.

[#1968](https://github.com/metomi/rose/pull/1968):
Rose Bush: use file system listing for job logs listing - no longer rely on the
`task_job_logs` table in the cylc runtime database.

[#1965](https://github.com/metomi/rose/pull/1965):
rose metadata-check: add index entry.

[#1963](https://github.com/metomi/rose/pull/1963):
Rose Bush: jobs list: use muted text style for zero size file links.

[#1962](https://github.com/metomi/rose/pull/1962):
rose config-edit: fix source file page widget traceback.

[#1959](https://github.com/metomi/rose/pull/1959):
rosie go, rosie ls: handle corrupt working copy edge case.

[#1957](https://github.com/metomi/rose/pull/1957):
rose config, rose config-edit: reduce memory usage.

[#1956](https://github.com/metomi/rose/pull/1956):
rose app-upgrade: speed up adding or renaming for large configurations.

[#1955](https://github.com/metomi/rose/pull/1955):
rose bush: add rotated log files to the `cylc files` menu.

[#1951](https://github.com/metomi/rose/pull/1951):
rose config-edit, rosie go: handle site/user incorrect value types.

[#1950](https://github.com/metomi/rose/pull/1950):
rose config-edit: clearer exception handling on startup.

--------------------------------------------------------------------------------

## 2016.07.0 (2016-07-22)

Rose release 43. This release works best with
[cylc-6.10.2](https://github.com/cylc/cylc/releases/tag/6.10.2) and
[fcm-2016.05.0](https://github.com/metomi/fcm/releases/tag/2016.05.0).

### Noteworthy Changes

[#1947](https://github.com/metomi/rose/pull/1947):
rose app-run, task-run, suite-run, etc: file install: reduce commits to sqlite
database that is used to store the state of file install sources and targets.
If you are installing a large number of files, this change should offer
significant improvement to the elasped time of the command.

[#1943](https://github.com/metomi/rose/pull/1943):
rose metadata: fix referring to top-level-option ids in the fail-if and warn-if
rules.

[#1939](https://github.com/metomi/rose/pull/1939):
Rosie discovery service clients: on authentication failure, the clients will
now keep retrying as long as the user enters entering different credentials
from the previous attempt.

[#1933](https://github.com/metomi/rose/pull/1933):
rose suite-run: `log-*.tar.gz`: is now created by a single `tar` command. For
reference, the original inefficient logic was required because we had to
support running Rose on old Unix systems that do not have access to a modern
`tar` command that has the `-z` option. The old logic used Python's `tarfile`
module to TAR up the log directory and then used the `gzip` command to compress
the resulting TAR file (to avoid inefficient when using Python's built-in
`gzip` logic with the `tarfile` module).  It is now highly unlikely that we had
to support running Rose systems that do not have access to a modern `tar`
command.

[#1932](https://github.com/metomi/rose/pull/1932):
Rose Bush: use `os.stat` to get `last_activity_time` in all Rose Bush pages,
instead of performing an expensive query.

[#1931](https://github.com/metomi/rose/pull/1931):
Rose Bush: remove a remaining Bootstrap 2 class from template.

[#1929](https://github.com/metomi/rose/pull/1929):
rose config-edit: fix an error in the `PageArrayTable` widget, which fails when
it attempts to display an array variable (i.e. a variable with the length
metadata set).

[#1928](https://github.com/metomi/rose/pull/1928):
rose config-edit: fix trigger latent section traceback.

[#1915](https://github.com/metomi/rose/pull/1915):
rose macro: removed un-necessary prompting with optional configuration.
* Allow macros to have a keyword argument `optional_config_name` which will be
  set to the name of the optional configuration used, if any.
* Now only prompts once for unknown values when using optional configurations.

--------------------------------------------------------------------------------

## 2016.06.1 (2016-06-23)

Rose release 42. This release works best with
[cylc-6.10.2](https://github.com/cylc/cylc/releases/tag/6.10.2) and
[fcm-2016.05.0](https://github.com/metomi/fcm/releases/tag/2016.05.0).

### Noteworthy Changes

[#1925](https://github.com/metomi/rose/pull/1925):
rose web services: document new requirement on cherrypy 3.2.2.

[#1921](https://github.com/metomi/rose/pull/1921):
Rose Bush: view search: fix incorrect URL that causes server to return 500.

[#1920](https://github.com/metomi/rose/pull/1920):
rose.reporter: better unicode handling.

[#1918](https://github.com/metomi/rose/pull/1918):
rose config-edit: fix right click menu segfault in summary panel.

[#1917](https://github.com/metomi/rose/pull/1917):
rose documentation: fix oddity with the scroll spy widget when viewing the
documentation as a single page.

--------------------------------------------------------------------------------

## 2016.06.0 (2016-06-10)

Rose release 41. This release works best with
[cylc-6.10.2](https://github.com/cylc/cylc/releases/tag/6.10.2) and
[fcm-2016.05.0](https://github.com/metomi/fcm/releases/tag/2016.05.0).

### Highlighted Changes

[#1905](https://github.com/metomi/rose/pull/1905):
rose macro, app-upgrade: fix section comment removal of options bug. This
meant that on upgrade or macro change, some optional configurations could
lose options from their sections. This happened only if the sections were
also present in the main configuration and if they had a differing comment
or ignored state in the optional configuration. Please check if you think
this may have happened to you.

[#1891](https://github.com/metomi/rose/pull/1891):
rose documentation: restyled with Bootstrap 3.
User guide is now available in a single page as well as in multiple pages.

### Noteworthy Changes

[#1913](https://github.com/metomi/rose/pull/1913):
rose configuration: allows a greater range of characters in the indices for
duplicate settings. This is prompted by the move towards including profile
names in the indices for UM STASH namelists - many of these have characters
like `+`, etc.

[#1911](https://github.com/metomi/rose/pull/1911):
rose config-edit: cylc gui launcher: gracefully handle suites that are not
running.

[#1909](https://github.com/metomi/rose/pull/1909):
rose config-edit: don't show `old_value` in info dialog.

[#1906](https://github.com/metomi/rose/pull/1906):
rose config-edit and rose macro: new `--no-warn=version` option to suppress
default version to HEAD warnings.

[#1903](https://github.com/metomi/rose/pull/1903):
rose app-upgrade: fix `change_setting_value` with `forced=True`.

[#1902](https://github.com/metomi/rose/pull/1902):
rose-meta.conf: url: add section or ns root

[#1900](https://github.com/metomi/rose/pull/1900):
rose config-edit: new menu item to rename a section.

[#1898](https://github.com/metomi/rose/pull/1898):
rose-stem: prepend hostname to working copies in source trees.

[#1895](https://github.com/metomi/rose/pull/1895):
rose bush: view: fixed search failure if service is not served under the root
of a server.

--------------------------------------------------------------------------------

## 2016.05.1 (2016-05-19)

Rose release 40. This release works best with
[cylc-6.10.1](https://github.com/cylc/cylc/releases/tag/6.10.1) and
[fcm-2016.05.0](https://github.com/metomi/fcm/releases/tag/2016.05.0).

### Highlighted Changes

[#1884](https://github.com/metomi/rose/pull/1884):
rose macro: can now be used on a whole suite. Previously, it only worked at
the level of an application configuration.

[#1883](https://github.com/metomi/rose/pull/1883):
rose bush and rosie disco: web pages have been upgraded from Bootstrap 2.X to
Bootstrap 3.3.6.

### Noteworthy Changes

[#1892](https://github.com/metomi/rose/pull/1892):
rose date: enable `--as-total=TIME_FORMAT` option when printing durations.

[#1887](https://github.com/metomi/rose/pull/1887):
rose bush: view: will now serve a file in a tar-gzip archive automatically in
raw mode if it contains Unicode characters. Previously, it would incorrectly
serve the whole tar archive.

--------------------------------------------------------------------------------

## 2016.05.0 (2016-05-05)

Rose release 39. This release works best with
[cylc-6.10.0](https://github.com/cylc/cylc/releases/tag/6.10.0) and
[fcm-2016.05.0](https://github.com/metomi/fcm/releases/tag/2016.05.0).

### User Interface Changes

[#1867](https://github.com/metomi/rose/pull/1867):
rose app-run: fix file installation clash. Suppose we have both
`file/whatever.txt` and `[file:whatever.txt]source=somewhere/whatever.txt`,
the setting in the `rose-app.conf` should take precedence. A bug in the logic
meant that this was not the case. This has now been fixed.

### Highlighted Changes

[#1808](https://github.com/metomi/rose/pull/1808):
rose bush: view: new search functionality.

[#1879](https://github.com/metomi/rose/pull/1879):
rose config-diff: support optional configurations

[#1870](https://github.com/metomi/rose/pull/1870):
rosie graph --text: new option print graph results as text.

[#1863](https://github.com/metomi/rose/pull/1863):
rose app-upgrade: allow multi depth value for `meta=value`.

### Noteworthy Changes

[#1882](https://github.com/metomi/rose/pull/1882):
rose stem: improve handling of project not found error.

[#1881](https://github.com/metomi/rose/pull/1881):
rose macro: fix trigger transform order-sensitivity bug.

[#1880](https://github.com/metomi/rose/pull/1880):
rose metadata-check: now check for invalid namespace settings.

[#1877](https://github.com/metomi/rose/pull/1877):
rose_bunch: bunch task result counts at end of job.

[#1875](https://github.com/metomi/rose/pull/1875):
rosie go: cylc gui launcher: gracefully handle suites that are not running.

[#1872](https://github.com/metomi/rose/pull/1872):
rose bush: job entry: link 0-size file any way.

[#1871](https://github.com/metomi/rose/pull/1871):
rose bush: cycles: don't display cycles with no active or completed tasks.

[#1869](https://github.com/metomi/rose/pull/1869):
rose stem: fix incorrect mirror variable when run within subdirectory.

[#1866](https://github.com/metomi/rose/pull/1866):
rose suite-run --reload: skip logic that invokes `cylc refresh`.

[#1865](https://github.com/metomi/rose/pull/1865):
rose_bunch: remove any existing database entries on first submit.

[#1864](https://github.com/metomi/rose/pull/1864):
rose config-edit: add ability to specify initial namespaces.

[#1861](https://github.com/metomi/rose/pull/1861):
rosie go: fix crash when all sources were unchecked.

[#1859](https://github.com/metomi/rose/pull/1859):
rose config-edit: keyboard shortcuts for multi section summary panel.

[#1858](https://github.com/metomi/rose/pull/1858):
rosie go: better gpg-agent cache expiry handling.

[#1856](https://github.com/metomi/rose/pull/1856):
rose config-edit: add GUI dialog to manage metadata search path.

[#1855](https://github.com/metomi/rose/pull/1855):
rose config-edit: show full traceback on macro crash.

--------------------------------------------------------------------------------

## 2016.03.0 (2016-03-11)

Rose release 38. This release works best with
[cylc-6.9.1](https://github.com/cylc/cylc/releases/tag/6.9.1) and
[fcm-2016.02.0](https://github.com/metomi/fcm/releases/tag/2016.02.0).

### Highlighted Changes

[#1824](https://github.com/metomi/rose/pull/1824):
rose suite- wrappers: make use of host information in cylc port files to detect
whether suites are running or not. Delete a cylc port file and/or a rose suite
host file if the system is able to detect that no process associated with the
suite is running on the recorded host. This allows suite-run, suite-clean, etc
to proceed if a suite is terminated with a left-over port file.

### Noteworthy Changes

[#1847](https://github.com/metomi/rose/pull/1847):
rose config-edit: fix other namespace state display on trigger. It could get a
target namespace (page/panel) ignored state incorrect following triggering from
another page. This fixes the issue.

[#1845](https://github.com/metomi/rose/pull/1845):
rose task-env: fix alternate calendar mode issue. It was not using the
setting in `CYLC_CALENDAR_MODE`. This fixes the issue.

[#1843](https://github.com/metomi/rose/pull/1843):
rose config-edit: fix left hand tree panel error icons for macros.

[#1841](https://github.com/metomi/rose/pull/1841):
rose bush: suites list and cycles list: fix fuzzy time logic. Restored display
of time using fuzzy time for suites list and cycles list, broken by
[#1791](https://github.com/metomi/rose/pull/1791). A toogle delta time button
will now be displayed in suites list and cycles list for users to toggle
between fuzzy time and ISO8601 date-time stamp.

[#1836](https://github.com/metomi/rose/pull/1836):
rose_arch: status string for targets with bad statuses will now be printed to
STDERR as well as STDOUT.

[#1835](https://github.com/metomi/rose/pull/1835):
rose config-edit: fix crash on ignore/remove/disable multiple sections.

[#1834](https://github.com/metomi/rose/pull/1834):
rose config-edit: fix upgrade button sensitivity and instructions.

[#1833](https://github.com/metomi/rose/pull/1833):
rose_ana: value of `tolerance` setting can now contain environment variable
substitution syntax.

[#1832](https://github.com/metomi/rose/pull/1832):
rose bush: view text mode: fix internal server error when viewing files with
Unicode characters. This fixes the problem by outputing the file in download
mode.

[#1806](https://github.com/metomi/rose/pull/1806):
rose date: new functionality to parse and convert ISO8601 durations.

--------------------------------------------------------------------------------

## 2016.02.1 (2016-02-25)

Rose release 37. This release works best with
[cylc-6.8.1](https://github.com/cylc/cylc/releases/tag/6.8.1) and
[fcm-2016.02.0](https://github.com/metomi/fcm/releases/tag/2016.02.0).

### Highlighted Changes

[#1814](https://github.com/metomi/rose/pull/1814):
rose macro: fix nested triggers for duplicate section options. The logic for
triggering options in duplicate namelists was not right under certain
circumstances. Some namelist:domain options in UM apps had incorrect
trigger-ignored statuses. Some apps will have new, correct error statuses for
these options when this version of Rose is used.

--------------------------------------------------------------------------------

## 2016.02.0 (2016-02-11)

Rose release 36. This release works best with
[cylc-6.8.1](https://github.com/cylc/cylc/releases/tag/6.8.1) and
[fcm-2016.02.0](https://github.com/metomi/fcm/releases/tag/2016.02.0).

### Noteworthy Changes

[#1825](https://github.com/metomi/rose/pull/1825):
rose_arch: fix incorrect behaviour on retry. If the previous attempt to archive
was killed, a subsequent retry would do nothing, due to the premature insertion
of the target in the rose_arch database. This is now fixed.

[#1823](https://github.com/metomi/rose/pull/1823):
rose.config.ConfigNode: fix incorrect behaviour of the `__iter__` method.

[#1822](https://github.com/metomi/rose/pull/1822):
rose app-upgrade: fix trigger conflict with namelist prettification.

[#1820](https://github.com/metomi/rose/pull/1820):
rose bush: view: fix internal server error caused by missing items in the job
entry associated with the log.

[#1819](https://github.com/metomi/rose/pull/1819):
rose CLI commands will now report information with a time stamp on `-v -v`
verbosity.

[#1811](https://github.com/metomi/rose/pull/1811):
rosie copy: on suite copy between 2 repositories, ensure that the destination
prefix is used to determine the value of owner, etc.

[#1809](https://github.com/metomi/rose/pull/1809):
Rose Bush: view: text mode is now the default, which means HTML tags will be
escaped by default. Previously, it would render HTML tags in text files by
default. You can continue to render HTML tags by using the tags mode.

[#1807](https://github.com/metomi/rose/pull/1807):
rosa svn-pre-commit: should now stop trunk replace.

[#1804](https://github.com/metomi/rose/pull/1804):
rose_ana: extra retry database operations on failure.

[#1802](https://github.com/metomi/rose/pull/1802):
rose host-select: improve parser for ranking and threshold commands output, and
in particular, the parser for the `free -m` command.

[#1758](https://github.com/metomi/rose/pull/1758):
rose config-edit: speed up adding/deleting sections.

--------------------------------------------------------------------------------

## 2016.01.0 (2016-01-15)

Rose release 35. This release works best with
[cylc-6.8.0](https://github.com/cylc/cylc/releases/tag/6.8.0) and
[fcm-2015.12.0](https://github.com/metomi/fcm/releases/tag/2015.12.0).

### Noteworthy Changes

[#1799](https://github.com/metomi/rose/pull/1799),
[#1795](https://github.com/metomi/rose/pull/1795):
rose_prune: shuffle job hosts to allow job hosts with share file systems to
share load on `rm -fr` commands.

[#1797](https://github.com/metomi/rose/pull/1797):
rosa svn-post-commit: ensure that all strings passed to the discovery database
are UTF-8 strings.

[#1792](https://github.com/metomi/rose/pull/1792):
rose stem: allow manual overriding of project.

[#1791](https://github.com/metomi/rose/pull/1791):
rose bush: jobs list: improve hyperlinks and layout:
* Fuzzy time toggle is now preserved when paging.
* A submit number badge is now:
  * a link to select all jobs of a given point/task.
  * displaying the number of jobs in a given point/task.
  * displaying the task status by colour of the point/task.

[#1787](https://github.com/metomi/rose/pull/1787):
rose bush: configurable logo.

[#1786](https://github.com/metomi/rose/pull/1786):
rose bush: improve paging and sorting:
* suites list and cycles list: added *Display Option* box, like in a jobs list
  page.
* suites list and cycles list: entries per page can now be configured.
* suites list: can now filter by suite name.
* suites list: can now order by suite name, as well as activity time.

[#1785](https://github.com/metomi/rose/pull/1785):
rose bush: cycles list and jobs list: display suite's `host:port` for suites
running cylc-6.8.0 or later.

[#1783](https://github.com/metomi/rose/pull/1783):
rose_bunch: process environment variable substitution in configuration file.

[#1780](https://github.com/metomi/rose/pull/1780):
rose_prune: support custom format for cycle string in substitution.

[#1779](https://github.com/metomi/rose/pull/1779):
rose bush: cycles list: fix counting of failed task jobs.

[#1777](https://github.com/metomi/rose/pull/1777):
rose bush: jobs list: can now sort in descending or ascending order by:
* time submit
* time run start
* time run exit
* duration queue
* duration run
* duration queue+run

--------------------------------------------------------------------------------

## 2015.12.0 (2015-12-11)

Rose release 34. This release works best with
[cylc-6.7.4](https://github.com/cylc/cylc/releases/tag/6.7.4) and
[fcm-2015.12.0](https://github.com/metomi/fcm/releases/tag/2015.12.0).

### Noteworthy Changes

[#1776](https://github.com/metomi/rose/pull/1776):
rose_arch: include the source prefix in the exception message if a source glob
does not match anything.

[#1768](https://github.com/metomi/rose/pull/1768):
rose_arch: an archive target can now be optional.

[#1767](https://github.com/metomi/rose/pull/1767):
Rose Bush: jobs list: display links to `job.out` and `job.err` as long as
they exist in the file system.

[#1765](https://github.com/metomi/rose/pull/1765):
Rose documentation: updated to reflect the changes in cylc. E.g.:
* `command scripting` is now `script`.
* Most functionality provided by `rose suite-hook` has been absorbed by cylc,
  so we are no longer recommending usage of `rose suite-hook` for task events.

[#1764](https://github.com/metomi/rose/pull/1764):
Rose Bush: jobs list: no longer fails if the suite does not have a `log/job/`
sub-directory.

[#1762](https://github.com/metomi/rose/pull/1762):
Rose Bush: jobs list: fix query logic for filtering jobs by status.

[#1757](https://github.com/metomi/rose/pull/1757):
Rosie Discovery service clients: improve handling of situations when the user
is unable to access a keyring. The new behaviour is to disable prefixes before
use (and notify the user about it) if a hello call fails. This applies to other
authentication failures as well.

--------------------------------------------------------------------------------

## 2015.11.1 (2015-11-17)

Rose release 33. This release works best with
[cylc-6.7.3](https://github.com/cylc/cylc/releases/tag/6.7.3) and
[fcm-2015.11.0](https://github.com/metomi/fcm/releases/tag/2015.11.0).

### Noteworthy Changes

[#1753](https://github.com/metomi/rose/pull/1753):
rose.config: on loading a configuration file, check that section values contain
matching brackets and braces.

[#1752](https://github.com/metomi/rose/pull/1752):
fcm_make built-in application: fix permission mode of destination when using a
fast location. It was set to user-only read-write.

[#1751](https://github.com/metomi/rose/pull/1751):
rose_ana built-in application: now uses a database to store some key comparison
information to simplify the process for building up an understanding of what
files need updating.

--------------------------------------------------------------------------------

## 2015.11.0 (2015-11-06)

Rose release 32. This release works best with
[cylc-6.7.2](https://github.com/cylc/cylc/releases/tag/6.7.2) and
[fcm-2015.10.0](https://github.com/metomi/fcm/releases/tag/2015.10.0).

### User Interface Changes

[#1735](https://github.com/metomi/rose/pull/1735):
rose suite-hook: will no longer retrieve remote job logs by default, this can
now be handled by cylc. If this functionality is still required for whatever
reason, use the `--retrieve-job-logs` option.

[#1729](https://github.com/metomi/rose/pull/1729):
rose suite-scan: will now time out after 60s by default. This can be configured
via the `[rose-suite-scan]timeout=SECONDS` setting in the site/user
configuration.

### Highlighted Changes

[#1696](https://github.com/metomi/rose/pull/1696):
rose_bunch: new built-in application for running multiple related commands in a
single application configuration.

### Noteworthy Changes

[#1750](https://github.com/metomi/rose/pull/1750):
Rose Bush and Rosie Disco: can now be configured to display alternate titles
and/or host names.

[#1744](https://github.com/metomi/rose/pull/1744):
rosie co: new alias of `rosie checkout`.

[#1740](https://github.com/metomi/rose/pull/1740):
Rose configuration metadata: new `type=python_boolean` setting.

[#1738](https://github.com/metomi/rose/pull/1738):
rosie go: the create functionality was creating the meta suite ROSIE instead of
a normal suite. This fixes the problem.

[#1732](https://github.com/metomi/rose/pull/1732):
Rosie Disco Web: now uses similar style as Rose Bush.

[#1731](https://github.com/metomi/rose/pull/1731):
Rose Bush: jobs list: will now use the `task_job_logs` table in `cylc-suite.db`
to obtain a list of job logs generated by the suite.

[#1730](https://github.com/metomi/rose/pull/1730):
Rose Bush: file view: now recognises the `[DEBUG]` prefix in a line of text,
and will renders it in a different colour.

[#1729](https://github.com/metomi/rose/pull/1729):
rose test-battery: now runs correctly in the absence of site/user configuration
on recent Ubuntu distros.

[#1727](https://github.com/metomi/rose/pull/1727):
rosa svn-pre-commit: now validates `rose-suite.info` files of suites using site
configuration metadata. The pre-commit hook will reject a changeset that
contains a `rose-suite.info` file with invalidate entries.

--------------------------------------------------------------------------------

## 2015.10.1 (2015-10-15)

Rose release 31. This release works best with
[cylc-6.7.1](https://github.com/cylc/cylc/releases/tag/6.7.1) and
[fcm-2015.10.0](https://github.com/metomi/fcm/releases/tag/2015.10.0).

### Noteworthy Changes

[#1720](https://github.com/metomi/rose/pull/1720):
rose macro: fix parsing of blank value repeats in settings of a `namelist:`
section.

[#1718](https://github.com/metomi/rose/pull/1718):
rose suite-run: fix hang up of `svn diff`. Call to `svn diff` may hang if user
has an alternate `diff` command configured that hangs. This change should force
`svn diff` to use its internal diff logic, and should call the relevant `svn`
commands with the `--non-interactive` options.

[#1714](https://github.com/metomi/rose/pull/1714):
rose app-run, rose suite-run, rose_arch, etc: This change allows any hash
object in Python's `hashlib` to be used to calculate the check sum of a file.
(Only `md5` was allowed before.)

[#1728](https://github.com/metomi/rose/pull/1728),
[#1713](https://github.com/metomi/rose/pull/1713):
rosie copy/create: support copy to another repository.

--------------------------------------------------------------------------------

## 2015.10.0 (2015-10-07)

Rose release 30. This release works best with
[cylc-6.7.0](https://github.com/cylc/cylc/releases/tag/6.7.0) and
[fcm-2015.09.0](https://github.com/metomi/fcm/releases/tag/2015.09.0).

### Highlighted Changes

[#1633](https://github.com/metomi/rose/pull/1633):
rosie create and rosie copy: improve checking and generation of settings in
`rose-suite.info`:
* Settings can now be validated on known `project` values.
* New setting `copy-mode=never|clear` allows a more intelligent selection of
  settings on suite copy.

### Noteworthy Changes

[#1708](https://github.com/metomi/rose/pull/1708):
rose_arch: archive sources can now be optional. A source specified using the
`(source)` syntax will no longer result in a failure if it is missing.
(However, a target with no actual source will result in a failure.)

[#1705](https://github.com/metomi/rose/pull/1705):
rose bush and rosie disco: this change unifies the interface for starting up a
Rose Bush server and a Rosie discovery service server. The command `rosa ws`
has been rebranded as `rosie disco`. This change also fixes the problem in
`mod_wsgi` mode where a success request still results in an entry in the Apache
error log.

[#1701](https://github.com/metomi/rose/pull/1701):
rose app-run, rose suite-run, rose task-run: the `-O` option now accepts
`'(key)'` syntax to indicate that `key` can be a missing optional
configuration.

--------------------------------------------------------------------------------

## 2015.08.0 (2015-08-19)

Rose release 29. This release works best with
[cylc-6.6.0](https://github.com/cylc/cylc/releases/tag/6.6.0) and
[fcm-2015.08.0](https://github.com/metomi/fcm/releases/tag/2015.08.0).

### Highlighted Changes

[#1652](https://github.com/metomi/rose/pull/1652):
rosie graph: new command for plotting suite ancestry.

### Noteworthy Changes

[#1673](https://github.com/metomi/rose/pull/1673):
rose config-diff: fix crash when an input path is specified with no directory
name.

[#1670](https://github.com/metomi/rose/pull/1670):
rose suite-scan: handle new `cylc scan` output introduced by
[cylc/cylc#1480](https://github.com/cylc/cylc/pull/1480).

[#1669](https://github.com/metomi/rose/pull/1669):
rose config-edit: fix crash when attempting to close a page with a newly added
variable that is yet to be given a name.

[#1667](https://github.com/metomi/rose/pull/1667):
rosie go: fix crash on invalid search.

[#1666](https://github.com/metomi/rose/pull/1666):
rosie web service clients: display URL as well as prefix in authentication
prompts.

[#1664](https://github.com/metomi/rose/pull/1664):
rosie go: fix delete option sensitivity if current user ID is not the same as
the user ID of a web service location.

[#1658](https://github.com/metomi/rose/pull/1658):
rose suite-run --reload: new task hosts no longer cause the command to fail.

[#1657](https://github.com/metomi/rose/pull/1657):
rose suite-run: job hosts install: files and directories with colons in their
names no longer cause the command to fail.

[#1654](https://github.com/metomi/rose/pull/1654):
rose config-dump: don't prettify configuration metadata.

[#1674](https://github.com/metomi/rose/pull/1674),
[#1649](https://github.com/metomi/rose/pull/1649):
Take advantage of cylc event handler enhancements introduced at
[cylc/cylc#1503](https://github.com/cylc/cylc/pull/1503):
* `rose suite-hook`: don't pull remote log if `job.out` already in place.
* Rose Bush:
  * cycles list and jobs list: speed improvements.
  * broadcasts list: new page to display broadcast tates and events.

[#1644](https://github.com/metomi/rose/pull/1644):
rose suite-clean: will now clean empty suite directories.

[#1641](https://github.com/metomi/rose/pull/1641):
rose bush: no longer fail when it is unable to parse a bad `rose-suite.info`
file in a suite.

[#1640](https://github.com/metomi/rose/pull/1640):
rose config-edit: speed up macro changes.

[#1639](https://github.com/metomi/rose/pull/1639):
rose config-edit: array widgets: protect against unsaved null text.

[#1635](https://github.com/metomi/rose/pull/1635):
rosie go, and other rosie web service clients: now fail gracefully if it has
no site/user configuration settings.

--------------------------------------------------------------------------------

## 2015.06.0 (2015-06-17)

Rose release 28. This release works best with
[cylc-6.4.1](https://github.com/cylc/cylc/releases/tag/6.4.1) and
[fcm-2015.05.0](https://github.com/metomi/fcm/releases/tag/2015.05.0).

### Noteworthy Changes

[#1628](https://github.com/metomi/rose/pull/1628):
rose config-edit: source widget for displaying `file:*` sections: fix
traceback on initialisation.

[#1626](https://github.com/metomi/rose/pull/1626):
rose config-edit: fix value hints widget initialisation.

[#1615](https://github.com/metomi/rose/pull/1615):
rose bush: cycles: add `new->old`/`old->new` option.

--------------------------------------------------------------------------------

## 2015.05.0 (2015-05-28)

Rose release 27. This release works best with
[cylc-6.4.1](https://github.com/cylc/cylc/releases/tag/6.4.1) and
[fcm-2015.05.0](https://github.com/metomi/fcm/releases/tag/2015.05.0).

### Highlighted Changes

[#1621](https://github.com/metomi/rose/pull/1621),
[#1604](https://github.com/metomi/rose/pull/1604):
fcm_make built-in application: improve flexibility.
* Add `mirror.target=` to `fcm make` argument list as extra configuration.
* Support `-n 2` option where possible - this allows the continuation make to be
  in the same physical location.
* Allow flexible naming of the `mirror` step.
* Allow flexible mapping of the original and continuation task names.
* It is now possible to set:
  * the destination for both orig and cont runs.
  * fast locations for both orig and cont runs.
* `rose task-run --new` on orig will now:
  * clear orig and cont dests.
  * invoke `fcm make --new`.

See also
[metomi/fcm#188](https://github.com/metomi/fcm/pull/188),
[metomi/fcm#189](https://github.com/metomi/fcm/pull/189),
[metomi/fcm#190](https://github.com/metomi/fcm/pull/190).

[#1576](https://github.com/metomi/rose/pull/1576):
rose app-upgrade, rose macro: handle optional configurations.
If an application contains optional configurations, loop through each one,
combine with the main, upgrade it, and re-create it as a diff vs the upgraded
main configuration.

### Noteworthy Changes

[#1620](https://github.com/metomi/rose/pull/1620):
rose host-select: improve recognition for `localhost` - the logic will now
check for `localhost`, its hostname, its fqdn hostname, and the associated IP
addresses.

[#1618](https://github.com/metomi/rose/pull/1618):
rosie create/copy: fix malformed log message for the Subversion changeset on
suite copy.

[#1616](https://github.com/metomi/rose/pull/1616):
rose host-select: fix incorrect threshold logic introduced by
[#1588](https://github.com/metomi/rose/pull/1588).

[#1613](https://github.com/metomi/rose/pull/1613):
rosie go: display URLs of data sources.

[#1612](https://github.com/metomi/rose/pull/1612):
rose bush: page navigation always visible at the bottom of the window.

[#1611](https://github.com/metomi/rose/pull/1611):
rose.env.env_export: only report for 1st time and on change. This fixes, e.g.
`rose task-run` reporting `export PATH=...` twice.

--------------------------------------------------------------------------------

## 2015.04.1 (2015-04-28)

Rose release 26, bug fix 1. This release works best with
[cylc-6.4.0](https://github.com/cylc/cylc/releases/tag/6.4.0) and beyond.

### Bug Fixes

[#1605](https://github.com/metomi/rose/pull/1605):
rose config-edit: remove an obsolete import that was causing the program to
fail.

--------------------------------------------------------------------------------

## 2015.04.0 (2015-04-27)

Rose release 26. This release works best with
[cylc-6.4.0](https://github.com/cylc/cylc/releases/tag/6.4.0) and beyond.

### Suite Run Time Location Changes

[#1571](https://github.com/metomi/rose/pull/1571):
rose suite-run, rose suite-clean, rose-task-env, rose task-run:
* The `rose suite-run` command will now create the `share/cycle/` sub-directory
  of a suite. (The `rose suite-clean` command will do the reverse.)
* Commands such as `rose task-env` and `rose task-run` will now export
  `ROSE_DATAC` (and friends) to point to cycle point directories under the
  `share/cycle/` directory.
  E.g. If current cycle point is `20150430T0000Z`, `ROSE_DATAC` will become
  `$HOME/cylc-run/my-suite/share/cycle/20150430T0000Z`.
* The root of the real location of the `share/`, `share/cycle/`, and `work/`
  sub-directory of a suite can now be configured using the settings
  `root-dir{share}`, `root-dir{share/cycle}` and `root-dir{work}` in the
  `rose-suite.conf` file, or under the `[rose-suite-run]` section in the
  site/user configuration file. The `root-dir-share` and `root-dir-work`
  settings are deprecated and are equivalent to `root-dir{share}` and
  `root-dir{work}` respectively.
* The setting `root-dir{share/cycle}=HOST=share/data` can be used to provide
  backward compatibility for the location of `ROSE_DATAC`, if required. This
  setting will ensure that the `share/cycle/` directory is created as a
  symbolic link to the `share/data/` directory.

This change allows shared cycling data to be placed in a different file system
than shared non-cycling data. E.g. Shared cycling data are typically larger and
more regularly house-kept, and so are more suitable for a large file system
with a short retention period. On the other hand, shared non-cycling data will
typically be used by tasks throughout the life time of the suite, and so are
more suitable for a file system with a long or permanent retention period.

[#1593](https://github.com/metomi/rose/pull/1593):
rose_prune: can now prune any item with a cycle point in its path name.
* New `prune{ITEM}=CYCLE[:GLOBS] ...` setting allow prune of items under any
  sub-directories. The `prune-work-at` and `prune-datac-at` settings are
  deprecated and are equivalent to `prune{work}` and `prune{share/cycle}`
  respectively.
* Cycle points can now be date-time points or offsets of the current cycle
  point.
* Each glob in the GLOBS string can now contain a `%(cycle)s` substitution.
  When a glob is specified like so, the program will not add the cycle under
  `ITEM` as a sub-directory, but will substitute `%(cycle)s` in the glob with
  the cycle.
* The application will now fail if a cycle point in the configuration has a bad
  syntax.

### Highlighted Changes

[#1591](https://github.com/metomi/rose/pull/1591):
rose config-diff: new command to display the difference between 2 Rose
configuration files with annotated metadata.

### Noteworthy Changes

[#1602](https://github.com/metomi/rose/pull/1602):
rose macro: fail if uppercase namelist options are added.

[#1601](https://github.com/metomi/rose/pull/1601):
rosie go: create new suite: if multiple data sources are specified, display
dialog box for user to select a prefix from the prefixes associated with the
selected data sources; if a single data source is specified, automatically
select the prefix associated with the specified data source.

[#1600](https://github.com/metomi/rose/pull/1600):
rose bush: view: will now link to related job logs when viewing a job log file.

[#1594](https://github.com/metomi/rose/pull/1594):
rose suite-run: allow suite `bar` when suite `foo-bar` is also running.

[#1597](https://github.com/metomi/rose/pull/1597),
[#1592](https://github.com/metomi/rose/pull/1592):
Rosie Clients will now attempt to use gpg-agent before GnomeKeyring by default.
If this is not desirable, you can add the setting
`prefix-password-store.PREFIX=gnomekeyring` (where `PREFIX` is the prefix of a
Rosie web service that requires authentication by password) under the
`[rosie-id]` section of the site/user configuration file.

[#1590](https://github.com/metomi/rose/pull/1590):
rose suite-hook: `--shutdown` even if `--mail` fails

[#1589](https://github.com/metomi/rose/pull/1589):
rosie id: now accepts `~/cylc-run/SUITE/` as an argument.

[#1588](https://github.com/metomi/rose/pull/1588):
rose host-select: reinstate timeout for SSH commands - kill SSH commands if
they take too long to run - useful for catching situations not caught by the
`-oConnectTimeout=SECS` option. Improve random and no threshold selection
logic - run SSH commands in serial to reduce loads to the system.

[#1586](https://github.com/metomi/rose/pull/1586):
rose_ana: allow ignoring tasks.

[#1584](https://github.com/metomi/rose/pull/1584):
rose bush: now correctly returns HTTP 403 or 404 for relevant items.

[#1581](https://github.com/metomi/rose/pull/1581):
rosie go: rephrase *view all revisions* to *search all revisions*.

[#1580](https://github.com/metomi/rose/pull/1580):
rosa db-create: will no longer run `post-commit` hooks with unnecessary
notification.

[#1579](https://github.com/metomi/rose/pull/1579):
rose bush: jobs: Only hide the *Display Options* form if all options are set as
defaults.

[#1574](https://github.com/metomi/rose/pull/1574):
rose_ana: improve output and fix test on wallclock time.

[#1568](https://github.com/metomi/rose/pull/1568):
rose config-edit: better handling of file source. The page is now a normal page
with a special source value widget.

--------------------------------------------------------------------------------

## 2015.03.0 (2015-03-26)

Rose release 25. This release works best with
[cylc-6.3.1](https://github.com/cylc/cylc/releases/tag/6.3.1).

### Highlighted Changes

[#1541](https://github.com/metomi/rose/pull/1541):
rose suite-restart: the command is no longer an alias of
`rose suite-run --restart`. It now restarts a shutdown suite from its last
known state without reinstalling it.

### Noteworthy Changes

[#1565](https://github.com/metomi/rose/pull/1565):
rose suite-run --restart: export `CYLC_VERSION` to match that of the original
suite run.

[#1563](https://github.com/metomi/rose/pull/1563):
rose metadata: remove escape characters for `values`, `value-titles` and
`value-hints`.

[#1562](https://github.com/metomi/rose/pull/1562):
rosa svn-pre-commit: now prevents suite copy with bad owner.

[#1561](https://github.com/metomi/rose/pull/1561):
rose config-edit: improve handling of bad macro imports from metadata.

[#1560](https://github.com/metomi/rose/pull/1560):
rose config-edit: fix blank name-space for a trailing slash section.

[#1557](https://github.com/metomi/rose/pull/1557):
rose config-edit: improve page display.

[#1555](https://github.com/metomi/rose/pull/1555):
rose app-upgrade: allow upgrade category packages to avoid module name
conflicts.

[#1553](https://github.com/metomi/rose/pull/1553):
rose app-run: poll delays can now be specified as ISO8601 durations.

[#1550](https://github.com/metomi/rose/pull/1550):
rose app-upgrade: fix check for existing indexed variable.

[#1548](https://github.com/metomi/rose/pull/1548):
rose config-edit: fix incorrect added-section description.

[#1542](https://github.com/metomi/rose/pull/1542):
rose config-edit: now report errors from *metadata-graph*.

--------------------------------------------------------------------------------

## 2015.02.0 (2015-02-11)

Rose release 24. This release works best with
[cylc-6.1.2](https://github.com/cylc/cylc/releases/tag/6.1.2) and
[cylc-6.3.1](https://github.com/cylc/cylc/releases/tag/6.3.1).

### Noteworthy Changes

[#1537](https://github.com/metomi/rose/pull/1537):
rose config-edit: fix variable menu when it has a macro warning.

[#1535](https://github.com/metomi/rose/pull/1535):
rose_prune: prune command now uses `bash -O extglob`, which means that glob
patterns can now be any extended globs supported by `bash`.

[#1532](https://github.com/metomi/rose/pull/1532):
rosie go: fix suite ID pop up menu web browser menu item. The menu item is now
enabled only if a web URL is available for browsing the suite.

[#1530](https://github.com/metomi/rose/pull/1530):
rose app-run: file installation: correctly handle exception associated with the
source.

[#1529](https://github.com/metomi/rose/pull/1529):
rose_prune: added configuration metadata for server log pruning setting.

[#1522](https://github.com/metomi/rose/pull/1522):
rose bash completion: fix use of `getent` for user names.

[#1516](https://github.com/metomi/rose/pull/1516):
rosie create: improve prompt.

[#1513](https://github.com/metomi/rose/pull/1513):
Rosie web service clients: gracefully handle the `Cancel` key press event when
user is prompted for a password for a prefix. The client will now report the
event, but continue with other prefixes.

[#1511](https://github.com/metomi/rose/pull/1511):
rose stem: the command now works under the `rose-stem/` sub-directory of a
working copy of a branch.

[#1504](https://github.com/metomi/rose/pull/1504):
rose app-run, rose suite-run, rose task-run: the commands in `-v` mode now
report the loading of the run configuration, any optional keys, and/or CLI
defined `key=value` pairs.

--------------------------------------------------------------------------------

## 2015.01.0 (2015-01-07)

Rose release 23. This release works best with
[cylc-6.1.2](https://github.com/cylc/cylc/releases/tag/6.1.2).

### Noteworthy Changes

[#1496](https://github.com/metomi/rose/pull/1496):
rose_prune: new setting for pruning logs and log archives on the suite host.

[#1494](https://github.com/metomi/rose/pull/1494):
rose config-edit: allow choices to be edited in a choice widget.

[#1493](https://github.com/metomi/rose/pull/1493):
rosie go: fix `File -> New Suite`.

[#1486](https://github.com/metomi/rose/pull/1486):
rosie ls: send `all_revs=1` to the web service server instead of
`all_revs=True`.

--------------------------------------------------------------------------------

## Older Releases

[Rose 2014-XX](doc/changes-2014.md)

[Rose 2013-XX](doc/changes-2013.md)

Rose 2012-11 (2012-11-30) was Rose release 1.
