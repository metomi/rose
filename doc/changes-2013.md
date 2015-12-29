# Rose Changes in 2013

Go to https://github.com/metomi/rose/milestones?state=closed
for a full listing of issues for each release.

See also:
* [Changes (current)](../CHANGES.md)

--------------------------------------------------------------------------------

## 2013-12 (2013-12-02)

This release of Rose works best with Cylc 5.4.2 or above.

### Highlighted Changes

[#1040](https://github.com/metomi/rose/pull/1040):
rose suite-run: check incompatible Cylc global config. In particular,
`rose suite-run` will now raise an exception if `[host][localhost]run directory`
and/or `[host][localhost]work directory` are not the defaults.

[#1026](https://github.com/metomi/rose/pull/1026),
[#1033](https://github.com/metomi/rose/pull/1033):
rose app-run, rose suite-run, rose config-edit, etc: support
optional source for file installation. E.g. In a `[file:path/to/file]` section,
a `source=(namelist:foo)` will allow `[namelist:foo]` to be missing or ignored.

[#1005](https://github.com/metomi/rose/pull/1005):
rose suite-run, rose suite-clean: the root directory of
`~/cylc-run/$SUITE/` is now configurable via site, user, or suite configuration.
On installation of a suite, `rose suite-run` will store the locations of the job
hosts in `~/cylc-run/$SUITE/log/rose-suite-run.locs`. The information can then
be used by `rose suite-clean` to determine what to remove. (N.B. Unfortunately,
this means that the new `rose suite-clean` may not correctly clean the suite
directories on job hosts created by an old version of `rose suite-run`.)

### Noteworthy Changes

[#1055](https://github.com/metomi/rose/pull/1055):
rose\_arch: fix `update-check=mtime+size` uniqueness problem for file
sources with identical modified times and sizes.

[#1053](https://github.com/metomi/rose/pull/1053):
rose config-edit: fix custom macro status bar reporting.

[#1049](https://github.com/metomi/rose/pull/1049):
rose host-select: run SSH commands with `-oConnectTimeout=T`,
and wait for all child processes to complete.

[#1046](https://github.com/metomi/rose/pull/1046):
rose config-edit: fix macro metadata setting for section.

[#1045](https://github.com/metomi/rose/pull/1045):
rosie id --to-web: fix hard coded Trac assumption. Note: requires a
change in the site configuration value `[rosie-id]prefix-web`. See example site
configuration file.

[#1039](https://github.com/metomi/rose/pull/1039):
rose config-edit: fix enable empty user-ignored section.

[#1037](https://github.com/metomi/rose/pull/1037):
rose config-edit: custom sub-panel widgets API documented.

[#1035](https://github.com/metomi/rose/pull/1035):
rose config-edit: fix orphaned warning for optional content sections.

[#1029](https://github.com/metomi/rose/pull/1029):
rose config-edit: fix file browser launch bug for unknown configuration.

[#1024](https://github.com/metomi/rose/pull/1024):
rose bush: job list mode: fixed `no_statuses` checkboxes returning nothing
bug.

[#1023](https://github.com/metomi/rose/pull/1023):
rose suite-gcontrol: raise exception on attempt to launch suite control
GUI on an unregistered Cylc suite.

[#1021](https://github.com/metomi/rose/pull/1021),
[#1031](https://github.com/metomi/rose/pull/1031):
rose bush: view file mode: some files are now prettified using
Google code prettify JS library.

[#1007](https://github.com/metomi/rose/pull/1007):
rose bush: now display Rose version that drives it.

[#1003](https://github.com/metomi/rose/pull/1003):
rose app-run, rose-suite-run, etc: file installation - a tilde `~`
in front a path pointing to a Subversion working copy did not get expanded.
This is now fixed.

[#999](https://github.com/metomi/rose/pull/999):
rose app-upgrade: apply trigger fixing after an upgrade.

--------------------------------------------------------------------------------

## 2013-11 (2013-11-14)

This release of Rose works with cylc 5.4.0 or above.

### Highlighted Changes

Changes that have significant impact on user experience.

[#993](https://github.com/metomi/rose/pull/993),
[#988](https://github.com/metomi/rose/pull/988),
[#980](https://github.com/metomi/rose/pull/980),
[#964](https://github.com/metomi/rose/pull/964),
[#857](https://github.com/metomi/rose/pull/857):
rose bush: a web service to browse user suite
logs. This replaces the old client side technology generated at suite run time
via `rose suite-run`, `rose suite-hook` and `rose suite-log`.
* Site/user configurable location of the Rose Bush web service.
* `rose bush` new command to start/stop an ad-hoc web service server.
* `rose suite-run` and `rose suite-hook`: modified to generate job log files DB
  for Rose Bush instead of files for the old client side suite log viewer.
* `rose suite-log`: modified to use Rose Bush web service by default.
* `rose suite-log --update`: the shorthand for this option is not `-U`.
* `rose suite-log --user=USER` or `-u USER` can now be used to view the suite
  log of an alternate user.

### Noteworthy Changes

Bug fixes, minor enhancements and documentation improvements:

[#996](https://github.com/metomi/rose/pull/996):
rose task-run `fcm_make` built-in app configuration: `args` can now be
used to specify more options and arguments to the `fcm make` command.

[#992](https://github.com/metomi/rose/pull/992):
Use the `gzip` command instead of Python's `gzip` library to write `*.gz`
files because the command is 10 times faster than Python's library. This
affects `rose suite-run`, `rose suite-log`, `rose_prune`, `rose_arch`.

[#982](https://github.com/metomi/rose/pull/982):
rose\_arch: add time diagnostics.

[#981](https://github.com/metomi/rose/pull/981):
rose config-edit: handle unregistered suite `gcylc` launch failure.

[#978](https://github.com/metomi/rose/pull/978):
rose metadata: different default metadata for different Rose
configuration files.

[#971](https://github.com/metomi/rose/pull/971):
rose macro: fix `fail-if` array variables that look like single float
values.

[#970](https://github.com/metomi/rose/pull/970):
rosie go: check suite is registered prior to running gui on it.

[#969](https://github.com/metomi/rose/pull/969),
[#966](https://github.com/metomi/rose/pull/966):
rose suite-run, etc: use `pgrep` as well as port files to
determine if a suite is still running or not.

[#968](https://github.com/metomi/rose/pull/968): rose stem: accept more schemes for Subversion URLs.

[#960](https://github.com/metomi/rose/pull/960):
rose\_arch: new `source-edit` setting to specify a command to transform
the content of the source file before sending it to the archive.

[#957](https://github.com/metomi/rose/pull/957):
rose config-edit: fix add latent mixed widget.

[#956](https://github.com/metomi/rose/pull/956):
rose config-dump: new `--no-pretty` option. Pretty print is now the
default.

[#949](https://github.com/metomi/rose/pull/949):
rose\_arch: allow use of file modified time and size instead of MD5
checksum to determine whether a source file is changed.

[#947](https://github.com/metomi/rose/pull/947):
rose suite-hook --mail: configurable email host

--------------------------------------------------------------------------------

## 2013-09 (2013-09-26)

This release of Rose works with cylc 5.3.0 or above.

### Highlighted Changes

Changes that have significant impact on user experience.

-None-

### Noteworthy Changes

Bug fixes, minor enhancements and documentation improvements:

[#938](https://github.com/metomi/rose/pull/938):
rosie go: improve filter removal.

[#937](https://github.com/metomi/rose/pull/937):
rose macro: diagnostic is now more similar to other Rose CLI commands.

[#936](https://github.com/metomi/rose/pull/936):
rosie go: default operator for query.

[#933](https://github.com/metomi/rose/pull/933):
rosa svn-pre-commit: document super users functionality in
configuration example.

[#932](https://github.com/metomi/rose/pull/932):
rose config-dump --pretty: new option to tell command to apply format
specific pretty printing.

[#931](https://github.com/metomi/rose/pull/931):
rose config-edit, rose-macro: reduce reporting of duplicated errors.

[#927](https://github.com/metomi/rose/pull/927):
rose app-run: fix default `[poll]delays=0`.

[#926](https://github.com/metomi/rose/pull/926):
rose mpi-launch: fix unbound `ROSE_LAUNCHER_BASE` on usage with a null
configuration.

[#925](https://github.com/metomi/rose/pull/925):
rose\_arch: fix incorrect behaviour if a source is a directory.

[#921](https://github.com/metomi/rose/pull/921):
rose host-select: new `--choice=N` option to choose a top from any of
the top `N` hosts.

[#919](https://github.com/metomi/rose/pull/919),
[#917](https://github.com/metomi/rose/pull/917),
[#897](https://github.com/metomi/rose/pull/897),
[#896](https://github.com/metomi/rose/pull/896),
[#894](https://github.com/metomi/rose/pull/894):
rose\_arch: improve diagnostics.

[#915](https://github.com/metomi/rose/pull/915):
rose suite-clean, rose suite-gcontrol, rose suite-stop: improve support
for determining the names of `rose-stem` suites.

[#913](https://github.com/metomi/rose/pull/913):
rose suite-run: use `pgrep` to check if suite is running or not.

[#912](https://github.com/metomi/rose/pull/912):
rose.popen: ensure that an `OSError` has the command name. This improves
diagnostics on command-not-found errors.

[#911](https://github.com/metomi/rose/pull/911):
rosa svn-post-commit: modify for Subversion 1.8.

[#908](https://github.com/metomi/rose/pull/908):
rose app-run: improve diagnostics for reference to ignored namelists.

[#902](https://github.com/metomi/rose/pull/902):
rose suite-log: fix `--archive '*'`.

[#901](https://github.com/metomi/rose/pull/901):
rose config-edit and rosie go: improve invalid colour diagnostics.

[#900](https://github.com/metomi/rose/pull/900):
rose config-edit: fix modal metadata dialog.

[#891](https://github.com/metomi/rose/pull/891):
rose suite-run: fix repeated jinja2 insertion when `rose suite-run` is
invoked from the installed suite directory.

[#889](https://github.com/metomi/rose/pull/889):
rose config: improve syntax error diagnostics.

[#888](https://github.com/metomi/rose/pull/888):
rose-app.conf, rose-suite.conf: A `SOURCE` in the `source=SOURCE ...`
declaration in a `[file:NAME]` section can now be a glob for matching files
names in the file system.

--------------------------------------------------------------------------------

## 2013-08 (2013-08-30)

This release of Rose works with cylc 5.3.0 or above.

### Highlighted Changes

Changes that have significant impact on user experience.

None in this release.

### Other Changes

Lots of bug fixes and enhancements, and documentation improvements.
The following are worth mentioning:

[#883](https://github.com/metomi/rose/pull/883):
rose\_arch: new built-in application: a generic solution to configure
site-specific archiving of suite files. (This built-in application should be
considered experimental at this release.)

[#878](https://github.com/metomi/rose/pull/878):
rosie: fix invalid prefix and local suite error crash bugs

[#868](https://github.com/metomi/rose/pull/868):
rose config-edit: added check on save toolbar and menu item.

[#864](https://github.com/metomi/rose/pull/864):
rose config-edit: added support for application configuration upgrade.

[#856](https://github.com/metomi/rose/pull/856):
rose config-edit: improved reporting of results from macros.

[#855](https://github.com/metomi/rose/pull/855):
rose macro: added command line trigger state validation.

[#851](https://github.com/metomi/rose/pull/851):
rose app-run: rose\_prune: modified to use the default shell to delete
files at the suite host. This should allow more powerful glob matching than
what is provided by the Python standard library.

[#850](https://github.com/metomi/rose/pull/850):
rose config-edit: add and document custom page for aligning variable
value elements.

[#849](https://github.com/metomi/rose/pull/849):
rose config-edit: added load all apps toolbar and menu item.

[#847](https://github.com/metomi/rose/pull/847):
rose suite-scan HOST: fixed.

[#846](https://github.com/metomi/rose/pull/846):
rose app-run, rose suite-run, rose task-run: fixed incorrect incremental
mode behaviour. When `mode=symlink` is removed from a target, the target should
be recreated, instead of being left to point to the old symbolic link.

[#845](https://github.com/metomi/rose/pull/845):
rose config-edit: support macro arguments.

--------------------------------------------------------------------------------

## 2013-07 (2013-07-31)

This release of Rose works with cylc 5.3.0 or above.

### Highlighted Changes

Changes that have significant impact on user experience.

[#823](https://github.com/metomi/rose/pull/823):
rosie create FROM-ID: suite copy is now done in a single changeset.
Previously, it was done in two changesets, one to create the suite, the other
to copy items from `FROM-ID`. The previous way can become unfriendly in merging
as Subversion adds `svn:mergeinfo` for each of the copied items from the
original suite.

Both `rosa svn-pre-commit` and `rosa svn-post-commit` have been modified to
handle this change. This version of `rosie create FROM-ID` will fail if the
`pre-commit` hook of the repository is still connected to the previous version
of `rosa svn-pre-commit`. An old version of `rosa svn-post-commit` will not
update the Rosie web service database correctly when this version of `rosie
create FROM-ID` is used to copy a suite.

[#799](https://github.com/metomi/rose/pull/799):
rose date: now supports letter options for both `--*-format=FORMAT` options.
* `--parse-format=FORMAT` can now be `-p FORMAT` (for `strptime`).
* `--format=FORMAT` is now a shorthand for `--print-format=FORMAT`.
  **It is no longer a shorthand for `--parse-format=FORMAT`.**
* `--print-format=FORMAT` can now be `-f FORMAT` (for `strftime`).

[#789](https://github.com/metomi/rose/pull/789):
rose\_prune: user interface refreshed. Functionalities now divided into 4
settings:
* `prune-remote-logs-at=cycle ...`
* `archive-logs-at=cycle ...`
* `prune-work-at=cycle[:globs] ...`
* `prune-datac-at=cycle[:globs] ...`

The 1st two functionalities call the underlying libraries of `rose
suite-log` to re-sync the remote job logs, prune them from the remote
hosts, (and archive the cycle job logs).

The last two functionalities are to prune items in the work directories
and the share cycle data directories. Globs can be specified for each
cycle so that only matched items in the relevant directories are
pruned.

### Other Changes

Lots of bug fixes and enhancements, and documentation improvements.
The following are worth mentioning:

[#840](https://github.com/metomi/rose/pull/840):
rose config-edit: improved metadata display for the UM STASH plugin widget.

[#839](https://github.com/metomi/rose/pull/839):
rose metadata: new `python_list` type for use with interfaces that support
Pythonic-format lists as input - e.g. Jinja2 via the rose-suite.conf file.

[#829](https://github.com/metomi/rose/pull/829):
rose host-select: add a new method to rank and set thresholds for hosts
by the amount of free memory.

[#827](https://github.com/metomi/rose/pull/827):
rose suite-hook --shutdown: add `--kill --now` as options to `cylc shutdown`.

[#824](https://github.com/metomi/rose/pull/824):
rose macro: add support for macro arguments.

[#815](https://github.com/metomi/rose/pull/815):
rose metadata: len function now available for fail-if, warn-if, etc.

[#811](https://github.com/metomi/rose/pull/811):
rose config-edit: rule checker will now display message on the status
bar if everything is OK.

[#809](https://github.com/metomi/rose/pull/809):
rose namelist-dump: allow and tidy zero-padded numeric inputs.

[#808](https://github.com/metomi/rose/pull/808):
rosie go: can now list the state of the suites in other user's
`$HOME/roses/` directory.

[#804](https://github.com/metomi/rose/pull/804):
rosie ls: new `--user=NAME` option to list the state of the suites in
other user's `$HOME/roses/` directory.

--------------------------------------------------------------------------------

## 2013-06 (2013-06-28)

This release of Rose works with cylc 5.3.0.

### Highlighted Changes

Changes that have significant impact on user experience.

[#769](https://github.com/metomi/rose/pull/769):
rose suite-run:
* Remove `--force` option. User should use `--reload` to install to a running
  suite.
* New option `--local-install-only` or `-l` to install suite locally only.
  With this option, it will not install the suite to remote job hosts.
* `--install-only` now implies `--no-gcontrol`.

[#761](https://github.com/metomi/rose/pull/761):
rose\_prune: new built-in application to housekeep a cycling suite.

[#739](https://github.com/metomi/rose/pull/739):
rose suite-log: replace `rose suite-log-view`. The old command is now an
alias of the new command with an improved interface. Support view and update
modes.
* In update mode, arguments can now be a `*` (for all task jobs), a cycle
  time or a task ID.
* Support a `--tidy-remote` option to remove job logs on remote hosts
  after their retrieval.
* Support a `--archive` option (and removed `--log-archive-threshold=CYCLE`) to
  switch on archive mode on the specified cycle times in the argument list.
* Switch off view mode by default in update mode, but can be turned on
  explicitly with an `--view`.
* *Admin Change*: The `[rose-suite-log-view]` section in site/user `rose.conf` is
  renamed `[rose-suite-log]`.

[#732](https://github.com/metomi/rose/pull/732):
rose config-edit: ability to load application configurations on demand
for large suites.

[#709](https://github.com/metomi/rose/pull/709):
rose config-edit: now has a status bar and a console to view errors
and information.

[#707](https://github.com/metomi/rose/pull/707):
rosie site/user configuration:
* *Admin Change*: A new site/user configuration setting
  `[rosie-id]prefix-ws.PREFIX=URL` is introduced to configure the web service URL
  of each `PREFIX`.
* The `[rosie-ws-client]ws-root-default=URL` site/user configuration setting is
  removed.
* The `--ws-root=URL` option is removed from `rosie lookup` and `rosie ls`.

[#668](https://github.com/metomi/rose/pull/668):
rose config-edit: support new configuration metadata `value-titles` to
define a list of titles to associate with a corresponding `values` setting.

[#666](https://github.com/metomi/rose/pull/666),
[#690](https://github.com/metomi/rose/pull/690):
rose task-env and rose task-run: the `--path=[NAME=]GLOB` option can
now be used in either command. Note, however, if `rose task-env` is used before
`rose task-run`, options shared between the 2 commands, (but not
`--path=[NAME=]GLOB`) options will be ignored by the subsequent `rose task-run`
command. This may some minor change in behaviour of some existing suites as
`PATH` would be modified by `rose task-env`.

[#661](https://github.com/metomi/rose/pull/661):
rose metadata-check: new command to validate configuration metadata.
Integrated into rose config-edit start-up checking.

### Other Changes

Lots of bug fixes and enhancements, and documentation improvements.
The following are worth mentioning:

[#758](https://github.com/metomi/rose/pull/758):
rosie go: home view now has `roses:/` displayed in the address bar for
the home view.

[#753](https://github.com/metomi/rose/pull/753):
rose documentation: added advice for delivery of training courses.

[#712](https://github.com/metomi/rose/pull/712):
rose config-edit: can show variable descriptions and help in-page.
Descriptions are shown by default. Customisable formatting.

[#707](https://github.com/metomi/rose/pull/707):
rosie site/user configuration: The `[rosie-browse]` section is now
`[rosie-go]`.

[#675](https://github.com/metomi/rose/pull/675):
rose config-edit: The quoted widget no longer messes with the quote
characters when a non-quote related error occurs.

[#672](https://github.com/metomi/rose/pull/672):
rose config-edit: titles and descriptions in the `Add` menu.

[#671](https://github.com/metomi/rose/pull/671):
rose suite-log-view: HTML view: fix delta time sort.

[#670](https://github.com/metomi/rose/pull/670):
rose config-edit: information on optional configuration. If a setting
can be modified in an optional configuration, the information will now be
shown with the setting's label.

[#665](https://github.com/metomi/rose/pull/665):
rose config-edit: fix ignore status logic.

[#663](https://github.com/metomi/rose/pull/663):
rose suite-hook and rose suite-log-view: more efficient logic.

[#659](https://github.com/metomi/rose/pull/659),
[#664](https://github.com/metomi/rose/pull/664):
rose suite-run site/user configuration: configure a list of
scannable hosts. This is useful when a set of hosts are no longer intended to be
used to run new suites but still have running suites on them.

[#652](https://github.com/metomi/rose/pull/652):
rosie go: can now navigate home view.

[#650](https://github.com/metomi/rose/pull/650):
rosie go: no longer crash when copying an empty suite.

[#649](https://github.com/metomi/rose/pull/649):
rose suite-shutdown: improve interface with `cylc shutdown`.

[#647](https://github.com/metomi/rose/pull/647):
rosie ls: now a query.

[#634](https://github.com/metomi/rose/pull/634):
rose config-edit: support latent ignored pages.

[#628](https://github.com/metomi/rose/pull/628):
rose mpi-launch: new `--file=FILE` option or `$PWD/rose-mpi-launch.rc`
to specify a command file to use with the MPI launcher.

--------------------------------------------------------------------------------

## 2013-05 (2013-05-15)

This release of Rose works with cylc 5.2.0.

### Highlighted Changes

Changes that have significant impact on user experience.

[#577](https://github.com/metomi/rose/pull/577):
rose suite-log-view: now uses `--name=SUITE-NAME` instead of an argument
to specify a suite.

[#559](https://github.com/metomi/rose/pull/559):
rose config-edit: added custom interface to display STASH configuration.

### Other Changes

Lots of bug fixes and enhancements, and documentation improvements.
The following are worth mentioning:

[#620](https://github.com/metomi/rose/pull/620):
rose suite-shutdown: added `--all` option to shutdown all of your
running rose suites.

[#621](https://github.com/metomi/rose/pull/621):
rose stem: will now log version control information for each source.

[#617](https://github.com/metomi/rose/pull/617):
rose suite-gcontrol: added `--all` option to launch the control
GUI for all your running suites.

[#605](https://github.com/metomi/rose/pull/605):
rose configuration files: added syntax highlight for Kate.

[#604](https://github.com/metomi/rose/pull/604):
rose date -c: new option, short for `rose date $ROSE_TASK_CYCLE_TIME`.

[#603](https://github.com/metomi/rose/pull/603),
[#641](https://github.com/metomi/rose/pull/641):
rose suite-log-view: new `--log-archive-threshold=CYCLE-TIME` option.
The option switches on job log archiving by specifying a cycle time threshold.
All job logs at this cycle time or older will be archived.

The HTML view has been modified to load the data of the jobs of selected
cycle times only. The default view will ignore cycles with job logs that have
been archived, but this can be modified via a multiple selection box and/or via
URL query.

[#595](https://github.com/metomi/rose/pull/595):
rosie lookup, rosie ls: now output with column headings.

[#571](https://github.com/metomi/rose/pull/571):
user guide: added a quick reference guide.

[#567](https://github.com/metomi/rose/pull/567):
rose suite-clean: new command to remove items created by suite runs.

[#546](https://github.com/metomi/rose/pull/546):
rose metadata: new macro option.

[#534](https://github.com/metomi/rose/pull/534):
rose\_ana built-in application: now support arguments.

[#475](https://github.com/metomi/rose/pull/475):
rose suite-hook, rose suite-log-view: support latest naming convention
of Cylc task ID. (Cylc 5.1.0)

[#467](https://github.com/metomi/rose/pull/467):
rose sgc: alias of `rose suite-gcontrol`.

User guide: added many new tutorials.

--------------------------------------------------------------------------------

## 2013-02 (2013-02-20)

This is the 3rd release of Rose.

### Highlighted Changes

Changes that have significant impact on user experience.

[#422](https://github.com/metomi/rose/pull/422):
rose suite-run: will now call `cylc validate --strict` by default.
Use the `--no-strict` option if this is not desirable.

### Other Changes

Lots of bug fixes and enhancements, and documentation improvements.
The following are worth mentioning:

[#454](https://github.com/metomi/rose/pull/454):
Optional configuration files are now supported by all types of Rose
configurations. The `opts=KEY ...` setting in the main configuration file of a
Rose configuration can now be used to select a list of optional configurations.

[#451](https://github.com/metomi/rose/pull/451):
rose config-edit: the description of a page is now displayed at its
header.

[#443](https://github.com/metomi/rose/pull/443):
rose config-edit: user can now reload metadata with a single menu command.

[#418](https://github.com/metomi/rose/pull/418):
rose suite-hook: support latest naming convention of Cylc task job log.
(Cylc 5.0.1 - 5.0.3.)

--------------------------------------------------------------------------------

## Rose 2013-01 (Released 2013-01-31)

This is the 2nd release of Rose. We hope you find it useful.

### Highlighted Changes

Changes that have significant impact on user experience.

[#244](https://github.com/metomi/rose/pull/244),
etc: Rose User Guide: Added S5 slide show enabled documentation chapters.
* Improved brief tour of the system.
* Chapters: Introduction, In Depth Topics, Suites
* Tutorials: Metadata, Suite Writing, Advanced (x9).

[#165](https://github.com/metomi/rose/pull/165),
[#242](https://github.com/metomi/rose/pull/242),
[#243](https://github.com/metomi/rose/pull/243):
rose suite-run: run modes and new log directory mechanism:
* Log directories no longer rotated.
* Introduce a run mode: `--run=reload|restart|run`.
  In reload and restart modes, the existing log directory is used.
  For the normal run mode, it creates a new log and carries out housekeeping.
* It creates a `log.DATETIME` directory (where `DATETIME` is the current date
  time in ISO8601 format), and creates a symbolic link log to point to it. If
  `--log-name=NAME` is specified, it creates another symbolic link `log.NAME`
  to point to it as well.
* Old `log.DATETIME` directories are normally archived into tar-gzip files. The
  `--no-log-archive` option switches off this behaviour. `log.DATETIME`
  directories with named `log.NAME` symbolic links will not be archived.
* If `--log-keep=DAYS` is specified, `log.DATETIME` directories with modified
  time older than the specified number of `DAYS` are removed.

[#404](https://github.com/metomi/rose/pull/404):
`rose task-run`'s *task utilities* are rebranded as `rose app-run`'s
*built-in applications*. This makes it logical to introduce a mode setting in
the `rose-app.conf` to specify a built-in application
(as opposed to running a command).
* `rose app-run`: `--app-mode=MODE` option is introduced to overwrite the `mode`
  setting. This would mainly be used internally by `rose task-run`.
  Users would normally use the `mode` setting to do this in the `rose-app.conf`.
* `rose task-run`: Removed both the `--no-auto-util` and `--util-key=KEY`
  options.  The `--app-mode=MODE` option supersedes the functionalities of both
  of these options. `--no-auto-util` is achieved by doing `--app-mode=command`.
* The `rose_install` task utility is pointless, so it is removed.
* New prerequisite polling functionality: The main command (or built-in
  application) will not start until all the prerequisites are met.

### Other Changes

There have been lots of minor bug fixes and enhancements for rose config-edit,
and lots of minor documentation improvements.

Changes that are worth mentioning:

[#396](https://github.com/metomi/rose/pull/396):
rose ana: command replaced by the `rose_ana` builtin application.

[#390](https://github.com/metomi/rose/pull/390):
rose config-edit: buttons to suite engine's gcontrol and log view.

[#388](https://github.com/metomi/rose/pull/388):
rose suite-run, rose app-run:
--opt-conf-key=KEY can now be specified via the `ROSE_SUITE_OPT_CONF_KEYS` and
`ROSE_APP_OPT_CONF_KEYS` environment variables

[#386](https://github.com/metomi/rose/pull/386):
rose suite-run, rose app-run: file install target names can now contain
environment variable substitution syntax.

[#375](https://github.com/metomi/rose/pull/375):
Rose configuration: add syntax highlight files for `gedit` and `vim`.

[#368](https://github.com/metomi/rose/pull/368):
rose suite-run: wait for `cylc run` to complete.

[#350](https://github.com/metomi/rose/pull/350):
rose suite-run: export Rose and suite engine versions to suite.

[#349](https://github.com/metomi/rose/pull/349):
rose env-cat: new command to substitute environment variables in input
files and print result.

[#340](https://github.com/metomi/rose/pull/340):
rose suite-run: tidy old symbolic links in `$HOME/.cylc/`.

[#329](https://github.com/metomi/rose/pull/329): rose suite-shutdown: new command.
* rose suite-gcontrol: use `--name=SUITE-NAME` to specify a suite name instead
of the last argument.

[#313](https://github.com/metomi/rose/pull/313):
rose config: added `--meta` and `--meta-key` options.

[#299](https://github.com/metomi/rose/pull/299):
rose task-run: the built-in `fcm_make(2)` task utilities can
now be configured using Rose application configurations.
* `fcm_make2*` task will automatically use `fcm_make*` task's application
  configuration.
* Support no directory change via the `use-pwd` option.
* Introduce `ROSE_TASK_MIRROR_TARGET`. Deprecate `MIRROR_TARGET`.
* Remove support for `ROSE_TASK_PRE_SCRIPT` - ask users to move to suite's pre
  command scripting.

[#284](https://github.com/metomi/rose/pull/284):
rose config-dump: new command to re-dump Rose configuration files in
in a directory into a common format.

[#282](https://github.com/metomi/rose/pull/282):
rose suite-log-view: Index view:
* Allow display of suite information.
* Added column for cycle time.
* Added data generation date-time.

[#273](https://github.com/metomi/rose/pull/273):
geditor setting: no longer use the environment variables EDITOR/VISUAL
to reduce the chance of opening a terminal based editor in a GUI environment.

[#261](https://github.com/metomi/rose/pull/261),
[#263](https://github.com/metomi/rose/pull/263):
rose config-edit: file `content` no longer supported.

[#248](https://github.com/metomi/rose/pull/248):
rose-suite-log-view: Log file view:
* Added link to toggle between HTML and text.
* Added link to view raw text.

[#238](https://github.com/metomi/rose/pull/238):
rose suite-log-view: New --full option to re-sync logs of remote tasks.

[#231](https://github.com/metomi/rose/pull/231):
rose date: New command.
