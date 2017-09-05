# Rose Changes

Go to https://github.com/metomi/rose/milestones?state=closed
for a full listing of issues for each release.

--------------------------------------------------------------------------------

## 2017.09.0 (2017-09-05)

Rose release 51. This release is expected to be used with:
* [cylc-7.5.0](https://github.com/cylc/cylc/releases/tag/7.5.0), and
* [fcm-2017.02.0](https://github.com/metomi/fcm/releases/tag/2017.02.0).

### Noteworthy Changes

[#2106](https://github.com/metomi/rose/pull/2106):
rose app-upgrade: fix CLI help.

[#2104](https://github.com/metomi/rose/pull/2104):
isodatetime: bundled library updated to 2017.08.0 release.

[#2099](https://github.com/metomi/rose/pull/2099):
rose_ana: grepper now prints to STDOUT on failure.

[#2096](https://github.com/metomi/rose/pull/2096):
rose suite-run: timestamp for log directory on a remote job host should now
match that of the suite host.

[#2094](https://github.com/metomi/rose/pull/2094):
rose macro: improve feedback for invalid input.

[#2090](https://github.com/metomi/rose/pull/2090):
Rose Bush: improve suite search logic - always drill down at least a level from
the root at `~/cylc-run/`.

[#2089](https://github.com/metomi/rose/pull/2089):
Rose Bush: add links to `.txt` and `.html` files in suite's `log/` directory.

--------------------------------------------------------------------------------

## 2017.05.0 (2017-05-17)

Rose release 50. This release is expected to be used with:
* [cylc-7.3.0](https://github.com/cylc/cylc/releases/tag/7.3.0) or
  [cylc-7.4.0](https://github.com/cylc/cylc/releases/tag/7.4.0), and
* [fcm-2017.02.0](https://github.com/metomi/fcm/releases/tag/2017.02.0).

### Noteworthy Changes

[#2073](https://github.com/metomi/rose/pull/2073):
rose_ana: allow grepper classes to treat missing KGO files as failed tasks.

[#2071](https://github.com/metomi/rose/pull/2071):
rose config-edit: support new `element-titles` metadata setting to allow users
to put headings above columns in arrays.

[#2070](https://github.com/metomi/rose/pull/2070):
rose suite-run: when installing a suite on a remote job host, it can now call
itself on the remote host without invoking a login shell.
* New `[rose-suite-run]remote-no-login-shell` setting in the site/user
  `rose.conf` to switch off/on usage of a remote login shell.
* The old `[rose-home-at]` section in the site/user `rose.conf` file has been
  replaced by the new `[rose-suite-run]remote-rose-bin` setting. The new
  setting can be used to specify the path to the `rose` executable on different
  hosts.
* See `${ROSE_HOME}/etc/rose.conf.example` in your distribution for detail.

[#2067](https://github.com/metomi/rose/pull/2067):
rose mpi-launch: fix usage of `ROSE_LAUNCHER_ULIMIT_OPTS=-a`.

[#2064](https://github.com/metomi/rose/pull/2064):
rose_ana improvements:
* `AnalysisTask` object now has a skipped attribute rather than just passed -
  if skipped is `True`, rose_ana will report on it differently as well as not
  considering it a failure overall
* Overall summary line right at the end of the output which gives total counts
  of passed, failed and skipped tests.

[#2063](https://github.com/metomi/rose/pull/2063):
rose config-edit: fix display of unnecessary scrollbars in dialogs.

[#2061](https://github.com/metomi/rose/pull/2061):
rose config-edit: remove errors associated with a variable before removing the
variable itself. This fixes the previously incorrect behaviour where the panel
would continue to show an error after removing the variable.

[#2046](https://github.com/metomi/rose/pull/2046):
New API docs for `rose.config` and `rose.macro`.

--------------------------------------------------------------------------------

## 2017.02.0 (2017-02-28)

Rose release 49. **This release is expected to be used with
[cylc-7.2.0](https://github.com/cylc/cylc/releases/tag/7.2.0) and
[fcm-2017.02.0](https://github.com/metomi/fcm/releases/tag/2017.02.0) or
compatible.**

### Noteworthy Changes

[#2057](https://github.com/metomi/rose/pull/2057):
isodatetime: bundled library updated to 2017.02.1 release.

[#2052](https://github.com/metomi/rose/pull/2052):
rose macro: fix issue when applying macros to `rose-suite.info` in the presence
of optional configurations intended for `rose-suite.conf`.

[#2050](https://github.com/metomi/rose/pull/2050):
rose suite-clean: `--only=` now supports Bash extended globs (extglob).

[#2049](https://github.com/metomi/rose/pull/2049):
rose bush: job entry: disable links to any zero-size files in the drop down box
for sequence job logs.

[#2048](https://github.com/metomi/rose/pull/2048):
rose bush: taskjobs: added a button for unchecking all task status filters.

[#2047](https://github.com/metomi/rose/pull/2047):
rose_ana: fix some issues with writing to the KGO database.

--------------------------------------------------------------------------------

## 2017.01.0 (2017-01-26)

Rose release 48. **This release is expected to be used with
[cylc-7.1.0](https://github.com/cylc/cylc/releases/tag/7.1.0) and
[fcm-2016.12.0](https://github.com/metomi/fcm/releases/tag/2016.12.0).**

### Noteworthy Changes

[#2043](https://github.com/metomi/rose/pull/2043):
rose macro: default macros will now apply to `rose-suite.info` as well.

[#2039](https://github.com/metomi/rose/pull/2039):
rose app-upgrade: improve diagnostics on removal of settings.

[#2036](https://github.com/metomi/rose/pull/2036):
rose config-edit: fix namespaces stealing sort-keys from option sections.

[#2034](https://github.com/metomi/rose/pull/2034):
rose config-edit: prevent radio buttons from filling full page width.

[#2033](https://github.com/metomi/rose/pull/2033):
Rose Bush: task jobs list: turn off auto-complete for sequence log forms.

[#2032](https://github.com/metomi/rose/pull/2032):
rose_prune: improve logic to prune items only from job hosts of relevant
cycles.

[#2031](https://github.com/metomi/rose/pull/2031):
rose suite-clean: improve logic for cleaning up parent directories.
For suites under sub-directory hierarchy, clean all the way to the root where
possible.

[#2030](https://github.com/metomi/rose/pull/2030):
Rose Bush: suites list:
* Fix links to suites with `/` characters in their names.
* Follow symbolic links in `~user/cylc-run/` when looking for suites.

--------------------------------------------------------------------------------

## 2016.12.0 (2016-12-22)

Rose release 47. **This release is expected to be used with
[cylc-7.0.0](https://github.com/cylc/cylc/releases/tag/7.0.0) and
[fcm-2016.12.0](https://github.com/metomi/fcm/releases/tag/2016.12.0).**

### Noteworthy Changes

[#2027](https://github.com/metomi/rose/pull/2027):
rose config-edit: use multi-line text widget for multi-line values.

[#2025](https://github.com/metomi/rose/pull/2025):
rose app-run/task-run: new environment variable `ROSE_APP_COMMAND_KEY`,
equivalent to the `--command-key` option.

[#2023](https://github.com/metomi/rose/pull/2023)
Rose training course docs: update to parameterization for simple cases.

[#2021](https://github.com/metomi/rose/pull/2021):
Rose Bush and rose suite-* utilities: modify to work best with cylc 7,
following the change in the location of service files in cylc 7 suites.
(See [cylc/cylc#2067](https://github.com/cylc/cylc/pull/2067).)

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

## Older Releases

[Rose 2015.XX](doc/changes-2015.md)

[Rose 2014-XX](doc/changes-2014.md)

[Rose 2013-XX](doc/changes-2013.md)

Rose 2012-11 (2012-11-30) was Rose release 1.
