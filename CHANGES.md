# Rose Changes

Go to https://github.com/metomi/rose/milestones?state=closed
for a full listing of issues for each release.

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
