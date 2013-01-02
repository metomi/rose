# Rose Changes

## Rose 2012-11+ (To be released 2013-Q1)

### Highlight Changes

Changes that has significant impact on user experience.

\#244: Tutorial: Added S5 slide show enabled documentation chapters.

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

### Other Changes

Changes that are worth mentioning.

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
