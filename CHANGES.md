# Rose Changes

Go to https://github.com/metomi/rose/milestones?state=closed
for a full listing of issues for each release.

<!-- The topmost release date is automatically updated by GitHub Actions. When
creating a new release entry be sure to copy & paste the span tag with the
`actions:bind` attribute, which is used by a regex to find the text to be
updated. Only the first match gets replaced, so it's fine to leave the old
ones in. -->

--------------------------------------------------------------------------------

## 2.2.0 (<span actions:bind='release-date'>Upcoming</span>)

### Breaking Changes

[2736](https://github.com/metomi/rose/pull/2736)
Rose now ignores `PYTHONPATH` to make it more robust to task environments
which set this value. If you want to add to the Rose environment itself,
e.g. to write a rose-ana test, use `ROSE_PYTHONPATH`.

## 2.1.0 (<span actions:bind='release-date'>Released 2023-07-21</span>)

### Fixes

[#2699](https://github.com/metomi/rose/pull/2699) -
Fix an issue where the incremental mode in Rose Bunch was ignored when rerun
as a task in a Cylc workflow. This change also ensure that incremental mode
ignores the previous output in the event that the task is re-run as part of a
later flow

[#2700](https://github.com/metomi/rose/pull/2700) -
Fix rosie password caching.

--------------------------------------------------------------------------------

## 2.0.4 (<span actions:bind='release-date'>Released 2023-04-27</span>)

### Fixes

[#2684](https://github.com/metomi/rose/pull/2684) -
Fix an issue where file installation could fail due to high concurrency.

--------------------------------------------------------------------------------

## 2.0.3 (<span actions:bind='release-date'>Released 2023-02-13</span>)

### Fixes

[#2666](https://github.com/metomi/rose/pull/2666) -
Fix issues with `rose date` when run in integer cycling Cylc workflows.

[#2670](https://github.com/metomi/rose/pull/2670) - Rose Macro made to
follow Python 2 type comparison rules.


--------------------------------------------------------------------------------

## 2.0.2 (<span actions:bind='release-date'>Released 2022-11-08</span>)

### Fixes

[#2608](https://github.com/metomi/rose/pull/2608) - Fix problems with the
tutorials.

--------------------------------------------------------------------------------

## 2.0.1 (<span actions:bind='release-date'>Released 2022-09-14</span>)

### Fixes

[#2612](https://github.com/metomi/rose/pull/2612) - Allows the pre
remote install checks to use any Python version >= 2.7.

--------------------------------------------------------------------------------

## 2.0.0 (<span actions:bind='release-date'>Released 2022-07-28</span>)

For use with Cylc, see [Cylc-Rose](https://github.com/cylc/cylc-rose).

Minor internal changes since 2.0rc3.

--------------------------------------------------------------------------------

## 2.0rc3 (<span actions:bind='release-date'>Released 2022-05-20</span>)

### Fixes

[#2574](https://github.com/metomi/rose/pull/2574) -
fix bug in rose mpi-launch that caused it to fail if the configured command
contained spaces.

--------------------------------------------------------------------------------

## 2.0rc2 (<span actions:bind='release-date'>Released 2022-03-24</span>)

### Enhancements

[#2555](https://github.com/metomi/rose/pull/2555) - `rose host-select` now
passes through `$CYLC_ENV_NAME` and the user's login env vars.

### Fixes

[#2557](https://github.com/metomi/rose/pull/2557) -
[FCM Make](https://github.com/metomi/fcm) now works
correctly with remote tasks and tasks which have their platform or host defined
as a subshell.

[#2548](https://github.com/metomi/rose/pull/2548) - Added back the
`rose-conf.vim` syntax highlighting file for ViM that was accidentally removed.

--------------------------------------------------------------------------------

## 2.0rc1 (<span actions:bind='release-date'>Released 2022-02-17</span>)

[#2510](https://github.com/metomi/rose/pull/2510) -
Re-enable Rosie ID to work with Cylc 8 Version control recording
infrastructure.

[#2514](https://github.com/metomi/rose/pull/2514) -
Remove `rosa rpmbuild` tool.

[#2519](https://github.com/metomi/rose/pull/2519) -
Updated the Rose documentation to describe using
`cylc validate; cylc install; cylc play` instead of `rose suite-run`.

[#2522](https://github.com/metomi/rose/pull/2522) -
Removed the Rsync implied by the `prune-remote-logs-at` option of
Rose prune.

[#2528](https://github.com/metomi/rose/pull/2528) -
Rose Date only emits a warning if running in interactive mode.


-------------------------------------------------------------------------------

## 2.0b3 (<span actions:bind='release-date'>Released 2021-11-10</span>)

For use with Cylc see [Cylc-Rose](https://github.com/cylc/cylc-rose).

### Noteworthy Changes

[#2493](https://github.com/metomi/rose/pull/2493) -
Disable the `rosie disco` web service pending a fix to the tornado version
conflict with cylc-uiserver, see https://github.com/metomi/rose/pull/2493

--------------------------------------------------------------------------------

## 2.0b2 (<span actions:bind='release-date'>Released 2021-07-28</span>)

Rose release 61. This is a __beta pre-release__.

For use with Cylc see [Cylc-Rose](https://github.com/cylc/cylc-rose).

--------------------------------------------------------------------------------

## 2.0b1 (2021-03-26)

Rose release 60. This is a __beta pre-release__.

For use with Cylc see [Cylc-Rose](https://github.com/cylc/cylc-rose).

### Noteworthy Changes

* All old GTK-based GUIs removed (no new alternative implemented yet)
* Suite control commands have been removed:
  * `rose suite-run` is now `cylc install`.
  * `rose suite-restart` is now `cylc play`
  * `rose suite-clean` is now `cylc clean`
* Full list of retired commands (run them on the command line to see their
  replacements):
  * `rose config-edit`
  * `rose edit`
  * `rose sgc`
  * `rose slv`
  * `rose suite-clean`
  * `rose suite-cmp-vc`
  * `rose suite-gcontrol`
  * `rose suite-hook`
  * `rose suite-init`
  * `rose suite-log-view`
  * `rose suite-log`
  * `rose suite-restart`
  * `rose suite-run`
  * `rose suite-scan`
  * `rose suite-shutdown`
  * `rose suite-stop`
  * `rose task-hook`
* `rose host-select` updated to use `psutil`.
* Allow `fcm_make` to work with hierarchical workflow registrations.

### Missing Interfaces

The ability to tell where a Cylc task has or will run has not yet been
re-implemented which can effect remote functionality of `fcm_make` and
`rose_prune` - [#2445](https://github.com/metomi/rose/issues/2445).

--------------------------------------------------------------------------------

## 2.0a1 (2019-09-19)

Rose release 59. This is an __alpha preview__ release. It is expected that it
will be used with:
* [cylc-flow-8.0a1](https://github.com/cylc/cylc-flow/releases/tag/7.8.2), and
* [fcm-2019.05.0](https://github.com/metomi/fcm/releases/tag/2019.05.0).

It is able to run most existing Rose Suites and has been ported to Python3.

**but**
* It is not production-ready yet.
* There are no GUI programs available.

### Noteworthy Changes

**This is the first Python3 version of Rose**

[#2446](https://github.com/metomi/rose/pull/2446): Host select: change implementation to psutil for portability.

[#2288](https://github.com/metomi/rose/pull/2288):
Rosie & Rosa: migrate to Python 3(.6-.7) & Tornado

[#2317](https://github.com/metomi/rose/pull/2317):
Python3 Conversion of Rose Suite Run

[#2366](https://github.com/metomi/rose/pull/2366):
Rose and Rosie: Future versions of Rose will be deployed to PyPI and installed
via Conda.

--------------------------------------------------------------------------------

## 2019.01.1 (2019-05-03)

Rose release 58. This maintenance release is expected to be used with:
* [cylc-flow-7.8.2](https://github.com/cylc/cylc-flow/releases/tag/7.8.2), and
* [fcm-2019.05.0](https://github.com/metomi/fcm/releases/tag/2019.05.0).

### Noteworthy Changes

[#2328](https://github.com/metomi/rose/pull/2328):
rose_ana: speed up by running in multiple threads.

[#2296](https://github.com/metomi/rose/pull/2296):
rose config-edit: fix element removal on array-like types.

[#2290](https://github.com/metomi/rose/pull/2290):
rose suite-run: fix connection to suite that has just been started.

[#2289](https://github.com/metomi/rose/pull/2289):
rose config-edit: fix int spin box manual edit.

--------------------------------------------------------------------------------

## 2019.01.0 (2019-01-25)

Rose release 57. This release is expected to be used with:
* [cylc-7.8.1](https://github.com/cylc/cylc/releases/tag/7.8.1), and
* [fcm-2017.10.0](https://github.com/metomi/fcm/releases/tag/2017.10.0).

### Highlighted Changes

[#2265](https://github.com/metomi/rose/pull/2265):
rose_bunch: new `argument-mode` setting allows the use of `izip`,
`izip_longest` or `product` logic as described in Python's
[itertools](https://docs.python.org/3/library/itertools.html) for building the
commands with different combinations of arguments.

### Noteworthy Changes

[#2279](https://github.com/metomi/rose/pull/2279):
rose suite-run: report debug statements only when requested.

[#2277](https://github.com/metomi/rose/pull/2277):
rose suite-shutdown: fix traceback.

[#2276](https://github.com/metomi/rose/pull/2276):
rosie: discovery service clients: fix `import gi.repository.Secret` traceback.

[#2275](https://github.com/metomi/rose/pull/2275):
rose_ana: grepper: fix overzealous informational message about KGO.

[#2266](https://github.com/metomi/rose/pull/2266),
[#2269](https://github.com/metomi/rose/pull/2269),
[#2273](https://github.com/metomi/rose/pull/2273),
[#2274](https://github.com/metomi/rose/pull/2274),
[#2280](https://github.com/metomi/rose/pull/2280):
Misc doc fixes.

[#2230](https://github.com/metomi/rose/pull/2230):
Report test coverage.

--------------------------------------------------------------------------------

## 2018.11.0 (2018-11-28)

Rose release 56. This release is expected to be used with:
* [cylc-7.8.0](https://github.com/cylc/cylc/releases/tag/7.8.0), and
* [fcm-2017.10.0](https://github.com/metomi/fcm/releases/tag/2017.10.0).

### Noteworthy Changes

[#2256](https://github.com/metomi/rose/pull/2256):
rose_arch: now fails gracefully if run under `rose app-run` as opposed to run
under `rose task-run`.

[#2254](https://github.com/metomi/rose/pull/2254):
rosie go: fix authentication caching issue on Gnome Shell desktops.

[#2239](https://github.com/metomi/rose/pull/2239):
Rose-Cylc realignment part 1:
* The `--host=HOST` option for most Rose-wrapped-Cylc commands should now be
  redundant.
* Rose will now use the suite contact file to determine whether a suite is
  running or not.
* rose suite-gcontrol --all: will now launch `cylc gscan` (instead of launching
  many `cylc gui` which can cause a machine to run out of resource if the user
  is running a large number of suites).
* rose suite-scan: will now invoke `cylc scan` directly.
* On launching a suite, `rose suite-run` will now write (Rose) automatic and
  custom environment variables to head of `suite.rc`.
* New `ROSE_SITE` environment/jinja2 suite variable + `site=SITE` setting -
  useful for site portable suites.

[#2237](https://github.com/metomi/rose/pull/2237):
rose_ana: fix grepper path functions.

[#2234](https://github.com/metomi/rose/pull/2234):
Use same logic as Cylc to to identify host names of current host.

[#2218](https://github.com/metomi/rose/pull/2218):
rose_bunch: `command-format` setting is now optional.

[#2217](https://github.com/metomi/rose/pull/2217):
rose-suite.conf: adds support for EmPy suite variables `[empy:suite.rc]`,
compliments [cylc/cylc#2734](https://github.com/cylc/cylc/pull/2734).

[#2207](https://github.com/metomi/rose/pull/2207):
Rose Configuration Metadata: improve handling of environment variable
substitution in quoted string types.

### Other Changes

Rose Bush is being rebranded *Cylc Review* under the Cylc project. We have not
yet removed Rose Bush logic from the Rose project, but it will no longer be
maintained. We encourage sites and users to migrate to *Cylc Review* soon.

Lots of improvements and fixes to documentation.

Launch programs with `python2` instead of `python`.

--------------------------------------------------------------------------------

## 2018.06.0 (2018-06-27)

Rose release 55. This release is expected to be used with:
* [cylc-7.7.2](https://github.com/cylc/cylc/releases/tag/7.7.2), and
* [fcm-2017.10.0](https://github.com/metomi/fcm/releases/tag/2017.10.0).

### Noteworthy Changes

[#2201](https://github.com/metomi/rose/pull/2201),
[#2200](https://github.com/metomi/rose/pull/2200),
[#2199](https://github.com/metomi/rose/pull/2199),
[#2196](https://github.com/metomi/rose/pull/2196),
[#2195](https://github.com/metomi/rose/pull/2195),
[#2193](https://github.com/metomi/rose/pull/2193),
[#2191](https://github.com/metomi/rose/pull/2191),
[#2190](https://github.com/metomi/rose/pull/2190):
Rose User Guide: misc fixes and improvements.

[#2194](https://github.com/metomi/rose/pull/2194):
rose suite-run: improve handling of `root-dir` settings on remote machine.

--------------------------------------------------------------------------------

## 2018.05.0 (2018-05-22)

Rose release 54. This release is expected to be used with:
* [cylc-7.7.0](https://github.com/cylc/cylc/releases/tag/7.7.0), and
* [fcm-2017.10.0](https://github.com/metomi/fcm/releases/tag/2017.10.0).

### Noteworthy Changes

[#2184](https://github.com/metomi/rose/pull/2184):
Rose User Guide: overhaul.
* New Cylc and Rose tutorial.
* New API reference.
* New style.

[#2171](https://github.com/metomi/rose/pull/2171):
rosie discovery clients now support Gnome libsecret for password caching.

[#2167](https://github.com/metomi/rose/pull/2167):
Rose Bush: file view: further limit on what can be served within a suite
directory.

[#2163](https://github.com/metomi/rose/pull/2163):
rose suite-run: new option `--validate-suite-only` to validate suite only
without installing the suite.

[#2151](https://github.com/metomi/rose/pull/2151):
Rose Bush: suites list, cycles list, task jobs list, and broadcast lists pages
now refresh automatically every 2 minutes.

--------------------------------------------------------------------------------

## 2018.02.0 (2018-02-07)

Rose release 53. This release is expected to be used with:
* [cylc-7.6.0](https://github.com/cylc/cylc/releases/tag/7.6.0), and
* [fcm-2017.10.0](https://github.com/metomi/fcm/releases/tag/2017.10.0).

### Noteworthy Changes

[#2146](https://github.com/metomi/rose/pull/2146):
Rose Bush: fix links for viewing files in suites with `/` in their names.

[#2145](https://github.com/metomi/rose/pull/2145):
rose suite-clean, rose suite-run, rose-suite-restart, etc: improve diagnostic
message when the commands detect that the suite may still be running. The
commands now include information of the location of the contact file and
relevant information from within.

[#2141](https://github.com/metomi/rose/pull/2141):
rose metadata-check: allow check to pass for GTK widgets if there is no display
in the environment.

[#2140](https://github.com/metomi/rose/pull/2140):
rose macro: fix behaviour with transfomer macro with custom argument where it
would die on an optional configuration that did not have the custom argument.

[#2139](https://github.com/metomi/rose/pull/2139):
rosa svn-pre-commit: now prevent users from adding a file at the branch level.

[#2138](https://github.com/metomi/rose/pull/2138):
rose_arch: prevents users from specifying a target as compulsory as well as
optional, e.g. `[arch:foo]` and `[arch:(foo)]`.

[#2137](https://github.com/metomi/rose/pull/2137):
rose config-edit: fix traceback opening page menu for `rose-suite.conf`.

[#2127](https://github.com/metomi/rose/pull/2127):
Rose Bush: file view: Prevent files being served outside of suite directory.

[#2124](https://github.com/metomi/rose/pull/2124):
rose config-edit: STASH panel: fix update of the expanded selection in the
event that re-orddering of rows are required when a table is modified.

[#2123](https://github.com/metomi/rose/pull/2123):
Rose installation no longer depends on the external `simplejson` library.
It now uses `json` in Python's standard library.

[#2122](https://github.com/metomi/rose/pull/2122):
Rose Bush:
* When a line number is specified in the URL the line will be highlighted on
  page load.
* Selecting a line no longer requires a content reload.
* Highlighting of logger level information (i.e. INFO, DEBUG, ...) is now
  restored (broken by the new logging system).

[#2120](https://github.com/metomi/rose/pull/2120):
rose suite-cmp-vc: new command to compare version control system information of
suite source between latest install and now.

--------------------------------------------------------------------------------

## Older Releases

[Rose 2017.XX](etc/changes-2017.md)

[Rose 2016.XX](etc/changes-2016.md)

[Rose 2015.XX](etc/changes-2015.md)

[Rose 2014-XX](etc/changes-2014.md)

[Rose 2013-XX](etc/changes-2013.md)

Rose 2012-11 (2012-11-30) was Rose release 1.
