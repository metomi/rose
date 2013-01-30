# Rose Changes

## Rose 2012-01 (To be released 2013-01)

### Highlight Changes

Changes that have significant impact on user experience.

\#244: Rose User Guide: Added S5 slide show enabled documentation chapters.
* Improved brief tour of the system.
* Chapters: Introduction, In Depth Topics, Suites
* Tutorials: Metadata, Suite Writing, Advanced (x9).

\#165, #243: rose suite-run: run modes and new log directory mechanism:
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
* `rose task-run`: Removed both the `--no-auto-util` and `--util-key=KEY` options.
  The `--app-mode=MODE` option supersedes the functionalities of both of these
  options. `--no-auto-util` is achieved by doing `--app-mode=command`.
* The `rose_install` task utility is pointless, so it is removed.
* New prerequisite polling functionality: The main command (or built-in
  application) will not start until all the prerequisites are met.

### Other Changes

Changes that are worth mentioning.

\#398: rosie go: disable the suite delete functionality if current user does not own the suite.

\#396: rose ana: command replaced by the `rose_ana` builtin application.

\#393: rosie go, rosie ls: recover from checked out deleted suites.

\#392: rose config-edit, rosie go: improve splash screen.

\#390: rose config-edit: buttons to suite engine's gcontrol and log view.

\#388: rose suite-run, rose app-run:
--opt-conf-key=KEY can now be specified via the `ROSE_SUITE_OPT_CONF_KEYS` and `ROSE_APP_OPT_CONF_KEYS`
environment variables

\#386: rose suite-run, rose app-run:
file install target names can now contain environment variable substitution syntax.

\#378: rose config-edit: fix trigger for null-value missing parent.

\#377: HTML documents: add syntax highlighting.

\#375: Rose configuration: add syntax highlight files for `gedit` and `vim`.

\#370: rose suite-run, rose suite-gcontrol: send `cylc gui` output to `/dev/null`.

\#368: rose suite-run: wait for `cylc run` to complete.

\#363: installation guide: more instruction on running `rosie.ws` under `mod_wsgi`.

\#362: installation guide: more instruction on the roles of different hosts.

\#361: rose config-edit: a single value setting can now be fixed on mismatch with metadata.

\#350: rose suite-run: export Rose and suite engine versions to suite.

\#349: rose env-cat: new command to substitute environment variables in input files and print result.

\#342: rosa svn-post-commit: fix branch creation DB update.

\#340: rose suite-run: tidy old symbolic links in `$HOME/.cylc/`.

\#329: rose suite-shutdown: new command.
* rose suite-gcontrol: use `--name=SUITE-NAME` to specify a suite name instead of the last argument.

\#325: rose config-edit: fix section ignore problem.

\#313: rose config: added `--meta` and `--meta-key` options.

\#299: rose task-run: the built-in `fcm_make(2)` task utilities can
now be configured using Rose application configurations.
* `fcm_make2*` task will automatically use `fcm_make*` task's application configuration.
* Support no directory change via the `use-pwd` option.
* Introduce `ROSE_TASK_MIRROR_TARGET`. Deprecate `MIRROR_TARGET`.
* Remove support for `ROSE_TASK_PRE_SCRIPT` - ask users to move to suite's pre command scripting.

\#297: rose mpi-launch: added standard verbosity options.
* Hard coded support for the various MPI launchers are removed.
* Default MPI launchers and their options are now configurable in the site/user configuration.

\#298: rose suite-run: fix failure if `svn` not installed.
Also support generating version files for suites in a `git` repository.

\#285: rose suite-run: simplify `ssh` commands with `bash --login`.

\#284: rose config-dump: new command to re-dump Rose configuration files in
in a directory into a common format.

\#283: rose config-edit: `fail-if` errors should disappear when the settings
are fixed.

\#282: rose suite-log-view: Index view:
* Allow display of suite information.
* Added column for cycle time.
* Added data generation date-time.

\#281: rosie delete: fix traceback.

\#273: geditor setting: no longer use the environment variables EDITOR/VISUAL
to reduce the chance of opening a terminal based editor in a GUI environment.

\#271: rose metadata-gen: Removes some extraneous `duplicate` metadata.

\#261, #263: rose config-edit: file `content` no longer supported.

\#257: rosie app-upgrade: fix various bugs.

\#253: rose config-edit: fix modifier latent variables.

\#252: rosie lookup: fix non-terminal display problem.

\#249: rose config-edit: Fix duplicate errors.

\#248: rose-suite-log-view: Log file view:
* Added link to toggle between HTML and text.
* Added link to view raw text.

\#242: rose suite-run: New --restart option to launch `cylc restart` instead of
`cylc run`.

\#241: rosie create: Allow alternate prefix for special metadata suite.

\#239: rose config-edit, rose-macro: Added auto fixer functionality.

\#238: rose suite-log-view: New --full option to re-sync logs of remote tasks.

\#237: rosie go: Fixed start up error.

\#236: rosie create: Fixed copy bug.

\#235: Improved demo suite.

\#233: rose config-edit: Better *ignored* errors and latent variable triggering.

\#232: Installation Guide: Improved wording.

\#231: rose date: New command.

\#228: Reference Guide: Configuration: Remove deprecated syntax.

\#227: rose: Improved CLI help and version display.

## Rose 2012-11 (2012-11-30)

This is the 1st release of Rose. Enjoy!
