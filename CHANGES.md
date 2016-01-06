# Rose Changes

Go to https://github.com/metomi/rose/milestones?state=closed
for a full listing of issues for each release.

--------------------------------------------------------------------------------

## Next Release (2016-Q1?)

Rose release 35. This release will work best with
[cylc-6.7.4](https://github.com/cylc/cylc/releases/tag/6.7.4) and
[fcm-2015.12.0](https://github.com/metomi/fcm/releases/tag/2015.12.0),
or their successors.

### Noteworthy Changes

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
rose bush: cycles list and jobs list: display suite's `host:port` where
possible.

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
