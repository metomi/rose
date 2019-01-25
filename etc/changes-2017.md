# Rose Changes in 2017

Go to https://github.com/metomi/rose/milestones?state=closed
for a full listing of issues for each release.

See also:
* [Changes (current)](../CHANGES.md)

--------------------------------------------------------------------------------

## 2017.10.0 (2017-10-03)

Rose release 52. This release is expected to be used with:
* [cylc-7.5.0](https://github.com/cylc/cylc/releases/tag/7.5.0), and
* [fcm-2017.10.0](https://github.com/metomi/fcm/releases/tag/2017.10.0).

### Noteworthy Changes

[#2117](https://github.com/metomi/rose/pull/2117):
Rose Metadata mini language: support `len(this(N))` syntax.

[#2114](https://github.com/metomi/rose/pull/2114):
rose_ana: import errors for external plugins are now pushed to the task level
so a plugin import error will no longer bring down everything else.

[#2109](https://github.com/metomi/rose/pull/2109):
rose suite-run, rose suite-restart, rose suite-clean, etc: now use the cylc-7.X
contact file as an indicator that a suite is still alive. This should allow
the commands to be faster, with reduced network calls.

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

