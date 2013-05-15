# Rose Changes

Go to https://github.com/metomi/rose/issues/milestones?state=closed
for a full listing of issues for each release.

--------------------------------------------------------------------------------

## 2013-05 (2013-05-15)

This release of Rose works with cylc 5.2.0.

### Highlight Changes

Changes that have significant impact on user experience.

\#577: rose suite-log-view: now uses `--name=SUITE-NAME` instead of an argument
to specify a suite.

\#559: rose config-edit: added custom interface to display STASH configuration.

### Other Changes

Lots of bug fixes and enhancements, and documentation improvements.
The following are worth mentioning:

\#620: rose suite-shutdown: added `--all` option to shutdown all of your
running rose suites.

\#621: rose stem: will now log version control information for each source.

\#617: rose suite-gcontrol: added `--all` option to launch the control
GUI for all your running suites.

\#605: rose configuration files: added syntax highlight for Kate.

\#604: rose date -c: new option, short for `rose date $ROSE_TASK_CYCLE_TIME`.

\#603, #641: rose suite-log-view: new `--log-archive-threshold=CYCLE-TIME` option.
The option switches on job log archiving by specifying a cycle time threshold.
All job logs at this cycle time or older will be archived.

The HTML view has been modified to load the data of the jobs of selected
cycle times only. The default view will ignore cycles with job logs that have
been archived, but this can be modified via a multiple selection box and/or via
URL query.

\#595: rosie lookup, rosie ls: now output with column headings.

\#571: user guide: added a quick reference guide.

\#567: rose suite-clean: new command to remove items created by suite runs.

\#546: rose metadata: new macro option.

\#534: rose_ana built-in application: now support arguments.

\#475: rose suite-hook, rose suite-log-view: support latest naming convention
of Cylc task ID. (Cylc 5.1.0)

\#467: rose sgc: alias of `rose suite-gcontrol`.

User guide: added many new tutorials.

--------------------------------------------------------------------------------

## 2013-02 (2013-02-20)

This is the 3rd release of Rose.

### Highlight Changes

Changes that have significant impact on user experience.

\#422: rose suite-run: will now call `cylc validate --strict` by default.
Use the `--no-strict` option if this is not desirable.

### Other Changes

Lots of bug fixes and enhancements, and documentation improvements.
The following are worth mentioning:

\#454: Optional configuration files are now supported by all types of Rose
configurations. The `opts=KEY ...` setting in the main configuration file of a
Rose configuration can now be used to select a list of optional configurations.

\#451: rose config-edit: the description of a page is now displayed at its
header.

\#443: rose config-edit: user can now reload metadata with a single menu command.

\#418: rose suite-hook: support latest naming convention of Cylc task job log.
(Cylc 5.0.1 - 5.0.3.)

--------------------------------------------------------------------------------

## Rose 2013-01 (Released 2013-01-31)

This is the 2nd release of Rose. We hope you find it useful.

### Highlight Changes

Changes that have significant impact on user experience.

\#244, etc: Rose User Guide: Added S5 slide show enabled documentation chapters.
* Improved brief tour of the system.
* Chapters: Introduction, In Depth Topics, Suites
* Tutorials: Metadata, Suite Writing, Advanced (x9).

\#165, #242, #243: rose suite-run: run modes and new log directory mechanism:
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

\#404: `rose task-run`'s *task utilities* are rebranded as `rose app-run`'s
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

\#396: rose ana: command replaced by the `rose_ana` builtin application.

\#390: rose config-edit: buttons to suite engine's gcontrol and log view.

\#388: rose suite-run, rose app-run:
--opt-conf-key=KEY can now be specified via the `ROSE_SUITE_OPT_CONF_KEYS` and
`ROSE_APP_OPT_CONF_KEYS` environment variables

\#386: rose suite-run, rose app-run:
file install target names can now contain environment variable substitution
syntax.

\#375: Rose configuration: add syntax highlight files for `gedit` and `vim`.

\#368: rose suite-run: wait for `cylc run` to complete.

\#350: rose suite-run: export Rose and suite engine versions to suite.

\#349: rose env-cat: new command to substitute environment variables in input
files and print result.

\#340: rose suite-run: tidy old symbolic links in `$HOME/.cylc/`.

\#329: rose suite-shutdown: new command.
* rose suite-gcontrol: use `--name=SUITE-NAME` to specify a suite name instead
of the last argument.

\#313: rose config: added `--meta` and `--meta-key` options.

\#299: rose task-run: the built-in `fcm_make(2)` task utilities can
now be configured using Rose application configurations.
* `fcm_make2*` task will automatically use `fcm_make*` task's application
  configuration.
* Support no directory change via the `use-pwd` option.
* Introduce `ROSE_TASK_MIRROR_TARGET`. Deprecate `MIRROR_TARGET`.
* Remove support for `ROSE_TASK_PRE_SCRIPT` - ask users to move to suite's pre
  command scripting.

\#284: rose config-dump: new command to re-dump Rose configuration files in
in a directory into a common format.

\#282: rose suite-log-view: Index view:
* Allow display of suite information.
* Added column for cycle time.
* Added data generation date-time.

\#273: geditor setting: no longer use the environment variables EDITOR/VISUAL
to reduce the chance of opening a terminal based editor in a GUI environment.

\#261, #263: rose config-edit: file `content` no longer supported.

\#248: rose-suite-log-view: Log file view:
* Added link to toggle between HTML and text.
* Added link to view raw text.

\#238: rose suite-log-view: New --full option to re-sync logs of remote tasks.

\#231: rose date: New command.

--------------------------------------------------------------------------------

## Rose 2012-11 (Released 2012-11-30)

This is the 1st release of Rose. Enjoy!
