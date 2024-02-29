# Rose Changes

Go to https://github.com/metomi/rose/milestones?state=closed
for a full listing of issues for each release.

## 2019.01.9 (Upcoming)

### Fixes

[#2765](https://github.com/metomi/rose/pull/2765) - Fix bug in Rosie
Suite Discovery where certain content in `rose-suite.info` could cause
display issues.


## 2019.01.8 (2022-12-20)

### Fixes

[#2633](https://github.com/metomi/rose/pull/2633) - Fix problems with the
Cylc and Rose tutorials.


## 2019.01.7 (2022-04-13)

### Fixes

[#2488](https://github.com/metomi/rose/pull/2582) - Fix Python 2.6 bug
in [#2486](https://github.com/metomi/rose/pull/2486)


## 2019.01.6 (2022-03-29)

### Fixes

[#2485](https://github.com/metomi/rose/pull/2486) - Prevent Rose 2019
modifying Cylc 8 workflows.


## 2019.01.5 (2021-03-19)

Rose release 62. This maintenance release is expected to be used with:
* [cylc-flow-7.9.2](https://github.com/cylc/cylc-flow/releases/tag/7.9.2), or
* [cylc-flow-7.8.7](https://github.com/cylc/cylc-flow/releases/tag/7.8.7), and
* [fcm-2019.09.0](https://github.com/metomi/fcm/releases/tag/2019.09.0).

### Noteworthy Changes

[#2440](https://github.com/metomi/rose/pull/2440) Fix bug where incremental
fileinstall did not work if a file was installed previously, overwritten, then
returned to to the orginal source.



## 2019.01.4 (2020-12-11)

Rose release 61. This maintenance release is expected to be used with:
* [cylc-flow-7.9.2](https://github.com/cylc/cylc-flow/releases/tag/7.9.2), or
* [cylc-flow-7.8.7](https://github.com/cylc/cylc-flow/releases/tag/7.8.7), and
* [fcm-2019.09.0](https://github.com/metomi/fcm/releases/tag/2019.09.0).

### Noteworthy Changes

[#2417](https://github.com/metomi/rose/pull/2417) Fix bugs in the Rosie
pre/post-commit hook scripts.

[#2425](https://github.com/metomi/rose/pull/2425) Forewarn of any future
template variable incompatibility with Cylc8.
(see the
[discourse post](https://cylc.discourse.group/t/cylc8-rose-template-variables-jinja2-suite-rc/295)).


## 2019.01.3 (2020-04-22)

Rose release 60. This maintenance release is expected to be used with:
* [cylc-flow-7.8.5](https://github.com/cylc/cylc-flow/releases/tag/7.8.5)
* [fcm-2019.05.0](https://github.com/metomi/fcm/releases/tag/2019.05.0)

### Noteworthy Changes

[2399](https://github.com/metomi/rose/pull/2399)
Fix bug where `--host=localhost` gets ignored

#### Documentation Updates

[#2398](https://github.com/metomi/rose/pull/2398)
Remove forecast suite tutorial's absolute dependency on external data.

[#2392](https://github.com/metomi/rose/pull/2392)
A tutorial on how to use Message Triggers.


## 2019.01.2 (2019-06-12)

Rose release 59. This maintenance release is expected to be used with:
* [cylc-flow-7.8.3](https://github.com/cylc/cylc-flow/releases/tag/7.8.3), and
* [fcm-2019.05.0](https://github.com/metomi/fcm/releases/tag/2019.05.0).

### Noteworthy Changes

[#2343](https://github.com/metomi/rose/pull/2343):
rose.reporter: allow mojibake to pass through in diagnostic messages.

[#2338](https://github.com/metomi/rose/pull/2338):
rose app-run, rose task-run, rose suite-run: new suite variable dict for
templating insertion.

[#2330](https://github.com/metomi/rose/pull/2330):
rose app-run, rose task-run, rose suite-run: allow use of `--define=` on top
level special settings such as `opts` and `import` in configuration.


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


## Older Releases

[Rose 2017.XX](etc/changes-2017.md)

[Rose 2016.XX](etc/changes-2016.md)

[Rose 2015.XX](etc/changes-2015.md)

[Rose 2014-XX](etc/changes-2014.md)

[Rose 2013-XX](etc/changes-2013.md)

Rose 2012-11 (2012-11-30) was Rose release 1.
