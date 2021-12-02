# Copyright (C) British Crown (Met Office) & Contributors.
# This file is part of Rose, a framework for meteorological suites.
#
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
"""The following options can be specified in:

* :rose:conf:`rose.conf[rose-ana]`
* :rose:conf:`rose_ana[ana:config]`

.. describe:: Options

    grepper-report-limit:
        A numerical value giving the maximum number of informational output
        lines to print for each comparison. This is intended for cases where
        for example a pattern-matching comparison is expected to match many
        thousands of occurrences in the given files; it may not be desirable
        to print the results of every comparison. After the given number of
        lines are printed a special message indicating that the rest of the
        output is truncated will be produced.
    skip-if-all-files-missing:
        Can be set to ``.true.`` or ``.false.``; if active, any comparison
        done on files by ``grepper`` will be skipped if all of those files
        are non-existent. In this case the task will return as "skipped"
        rather than passed/failed.

"""

import os
import re

from metomi.rose import TYPE_LOGICAL_VALUE_TRUE
from metomi.rose.apps.rose_ana import AnalysisTask


class SingleCommandStatus(AnalysisTask):
    """Run a shell command, passing or failing depending on the exit
    status of that command.

    Options:
        files (optional):
            A newline-separated list of filenames which may appear
            in the command.
        command:
            The command to run; if it contains Python style
            format specifiers these will be expanded using the list of
            files above (if provided).
        kgo_file:
            If the list of files above was provided gives the
            (0-based) index of the file holding the "kgo" or "control"
            output for use with the comparisons database (if active).
    """

    def run_analysis(self):
        """Main analysis routine called from rose_ana."""
        self.process_opt_files()
        self.process_opt_kgo()
        self.process_opt_command()
        self.process_opt_unhandled()
        self.get_config_opts()

        if self.check_for_skip():
            return

        self.run_command_and_check()
        self.update_kgo()

    def run_command_and_check(self):
        """Run the command and return based on the output."""
        # If the user has specified a KGO file, but it is missing, exit early
        if self.kgo is not None:
            kgo_file = self.files[self.kgo]
            if not os.path.exists(kgo_file):
                self.reporter(
                    "KGO File (file {0}) appears to be missing".format(
                        self.kgo + 1
                    ),
                    prefix="[FAIL] ",
                )
                # Note that by exiting early this task counts as failed
                return

        # The command may contain format substitution characters, which will
        # receive any filenames passed to the app.
        self.command = self.command.format(*self.files)
        returncode, stdout, stderr = self.run_command(self.command)
        if returncode == 0:
            self.reporter(stdout, prefix="[INFO] ")
            self.passed = True
        else:
            self.reporter("STDOUT:", prefix="[FAIL] ")
            self.reporter(stdout, prefix="[FAIL] ")
            self.reporter("STDERR:", prefix="[FAIL] ")
            self.reporter(stderr, prefix="[FAIL] ")

    def check_for_skip(self):
        """If the user's config options specified that the task should be
        ignored if all of its files were missing, set skipped attribute here.
        """
        if self.skip_if_missing and self.files:
            if not any(os.path.exists(fname) for fname in self.files):
                self.skipped = True
                self.reporter(
                    "All file arguments are missing, skipping task since "
                    "'skip-if-all-files-missing' is '{0}'".format(
                        TYPE_LOGICAL_VALUE_TRUE
                    )
                )
        return self.skipped

    def get_config_opts(self):
        """Process any configuration options."""
        report_limit = self.config.get("grepper-report-limit", None)
        self.max_report_lines = None
        if report_limit is not None and report_limit.isdigit():
            self.max_report_lines = int(report_limit)

        skip_missing = self.config.get("skip-if-all-files-missing", None)
        self.skip_if_missing = False
        if (
            skip_missing is not None
            and skip_missing == TYPE_LOGICAL_VALUE_TRUE
        ):
            self.skip_if_missing = True

    def process_opt_files(self):
        """Process the files option; a list of one or more filenames."""
        # Get the file list from the options dictionary
        files = self.options.pop("files", None)
        # Make sure it appears as a sensible list
        if files is None:
            files = []
        elif isinstance(files, str):
            files = [files]
        # Report the filenames (with paths)
        for ifile, fname in enumerate(files):
            self.reporter(
                "File {0}: {1}".format(
                    ifile + 1, os.path.abspath(files[ifile])
                )
            )
        self.files = files

    def process_opt_kgo(self):
        """
        Process the KGO option; an index indicating which file (if any) is
        the KGO (Known Good Output) - this may be needed later to assist in
        updating of test results.

        """
        # Get the kgo index from the options dictionary
        kgo = self.options.pop("kgo_file", None)
        # Parse the kgo index
        if kgo is not None:
            if kgo.strip() == "":
                kgo = None
            elif kgo.isdigit():
                kgo = int(kgo)
                if int(kgo) > len(self.files):
                    msg = "KGO index cannot be greater than number of files"
                    raise ValueError(msg)
                self.reporter("KGO is file {0}".format(kgo + 1))
            else:
                msg = (
                    "KGO index not recognised; should be either a digit or "
                    "left blank"
                )
                raise ValueError(msg)
        self.kgo = kgo

    def process_opt_command(self):
        """
        Process the command option; this is the (shell) command that will
        be run for this task.

        """
        # Get the command from the options
        self.command = self.options.pop("command", None)
        if self.command is not None:
            self.reporter("Command: {0}".format(self.command))
        else:
            msg = "Command not specified"
            raise ValueError(msg)

    def run_command(self, command):
        """Simple command runner; returns output error and return code."""
        retcode, stdout, stderr = self.popen.run(command, shell=True)
        return retcode, stdout, stderr

    def read_file(self, filename):
        """Return the content of a given file as a list of lines."""
        with open(filename, "r") as ifile:
            output = ifile.read().splitlines()
        return output

    def update_kgo(self):
        """
        Update the KGO database with the status of any files marked by the
        kgo_file option (i.e. whether they have passed/failed the test.

        """
        if self.kgo is not None and self.kgo_db is not None:
            # Identify the KGO file from its index
            kgo_file = self.files[self.kgo]
            # Now find the other file/s (this is presently designed to expect
            # there to be 1 KGO and 1 non-KGO file
            for ifile, suite_file in enumerate(self.files):
                if ifile == self.kgo:
                    continue
                self.kgo_db.enter_comparison(
                    self.options["full_task_name"],
                    os.path.abspath(kgo_file),
                    os.path.abspath(suite_file),
                    ["FAIL", " OK "][self.passed],
                    "Compared using grepper",
                )


class SingleCommandPattern(SingleCommandStatus):
    """Run a single command and then pass/fail depending on the presence of a
    particular expression in that command's standard output.

    Options:
        files (optional):
            Same as previous task. command - same as previous task.
        kgo_file:
            Same as previous task.
        pattern:
            The regular expression to search for in the stdout from the
            command.

    """

    def run_analysis(self):
        """Main analysis routine called from rose_ana."""
        # Note that this is identical to the above class, only it has the
        # additional pattern option; so call back to the parent class
        self.process_opt_pattern()
        super(SingleCommandPattern, self).run_analysis()

    def process_opt_pattern(self):
        """
        Process the pattern option; a regular expression which will be
        checked against the command output.

        """
        # Get the pattern from the options dictionary
        self.pattern = self.options.pop("pattern", None)
        if self.pattern is not None:
            self.reporter("Pattern: {0}".format(self.pattern))
        else:
            msg = "Must specify a pattern"
            raise ValueError(msg)

    def run_command_and_check(self):
        """
        Run the command and check for the presence of the pattern in its
        standard output.

        """
        # If the user has specified a KGO file, but it is missing, exit early
        if self.kgo is not None:
            kgo_file = self.files[self.kgo]
            if not os.path.exists(kgo_file):
                self.reporter(
                    "KGO File (file {0}) appears to be missing".format(
                        self.kgo + 1
                    ),
                    prefix="[FAIL] ",
                )
                # Note that by exiting early this task counts as failed
                return

        # The command may contain format substitution characters, which will
        # receive any filenames passed to the app.
        self.command = self.command.format(*self.files)
        returncode, stdout, stderr = self.run_command(self.command)

        search = re.search(self.pattern, stdout)
        if search:
            self.passed = True


class FilePattern(SingleCommandPattern):
    """Check for occurrences of a particular expression or value within the
    contents of two or more files.

    Options:
        files (optional):
            Same as previous tasks.
        kgo_file:
            Same as previous tasks.
        pattern:
            The regular expression to search for in the files. The
            expression should include one or more capture groups; each
            of these will be compared between the files any time the
            pattern occurs.
        tolerance (optional):
            By default the above comparisons will be compared exactly,
            but if this argument is specified they will be converted to
            float values and compared according to the given tolerance.
            If this tolerance ends in % it will be interpreted as a
            relative tolerance (otherwise absolute).

    """

    def run_analysis(self):
        """Main analysis routine called from rose_ana."""
        self.process_opt_files()
        self.process_opt_kgo()
        self.process_opt_pattern()
        self.process_opt_tolerance()
        self.process_opt_unhandled()
        self.get_config_opts()

        if self.check_for_skip():
            return

        # If the user has specified a KGO file, but it is missing, exit early
        if self.kgo is not None:
            kgo_file = self.files[self.kgo]
            if not os.path.exists(kgo_file):
                self.reporter(
                    "KGO File (file {0}) appears to be missing".format(
                        self.kgo + 1
                    ),
                    prefix="[FAIL] ",
                )
                # Note that by exiting early this task counts as failed
                return

        # Generate the groupings - the pattern can match multiple times
        matched_groups = self.search_for_matches()

        # Check that the number of matchings found is equal in all files
        group_lens = [len(groups) for groups in matched_groups.values()]
        for igroup, group_len in enumerate(group_lens[1:]):
            if group_len != group_lens[0]:
                msg = (
                    "File ({0}) matches pattern {1} times, but File ({2}) "
                    "matches it {3} times, cannot test"
                )
                raise ValueError(
                    msg.format(
                        self.files[0],
                        group_lens[0],
                        self.files[igroup + 1],
                        group_len,
                    )
                )

        # Compare the result of each matching
        passed = [True] * len(self.files)
        comparison_total = 0
        failure_total = 0
        for igroup in range(group_lens[0]):
            ref_group = matched_groups[self.files[0]][igroup]
            for ifile, fname in enumerate(self.files[1:]):
                group = matched_groups[fname][igroup]
                for imatch, (match1, match2) in enumerate(
                    zip(ref_group, group)
                ):
                    # If a tolerance was given, the matches must be numbers
                    failed = False
                    comparison_total += 1
                    if self.tolerance is not None:
                        try:
                            match1 = float(match1)
                            match2 = float(match2)
                        except ValueError:
                            msg = (
                                "Cannot do tolerance comparison, groups "
                                "matched by pattern are not reals"
                            )
                            raise ValueError(msg)
                        if self.relative_tol:
                            lower = match2 * (1.0 - 0.01 * self.tolerance)
                            upper = match2 * (1.0 + 0.01 * self.tolerance)
                        else:
                            lower = match2 - self.tolerance
                            upper = match2 + self.tolerance
                        if not lower <= match1 <= upper:
                            failed = True
                    elif match1 != match2:
                        failed = True

                    # Update the state of the current file if it failed above
                    if failed:
                        passed[ifile + 1] = False
                        failure_total += 1

                    # Now move on to report the output of the comparison (if
                    # the user's config limits the amount of output skip this)
                    if (
                        self.max_report_lines is not None
                        and comparison_total > self.max_report_lines
                    ):
                        continue

                    if failed:
                        msg = (
                            "Mismatch in group {0} of pattern for "
                            "occurrence {1} in files"
                        )
                        prefix = "[FAIL] "
                        self.reporter(
                            msg.format(imatch + 1, igroup + 1), prefix=prefix
                        )
                        msg = "File {0}: {1}"
                        self.reporter(msg.format(1, match1), prefix=prefix)
                        self.reporter(
                            msg.format(ifile + 2, match2), prefix=prefix
                        )

                    else:
                        msg = (
                            "Group {0} of pattern for occurrence {1} in "
                            "files matches"
                        )
                        self.reporter(
                            msg.format(imatch + 1, igroup + 1),
                            level=self.reporter.V,
                        )
                        if self.tolerance is None:
                            msg = "Value: {0}"
                            self.reporter(
                                msg.format(match1), level=self.reporter.V
                            )
                        else:
                            msg = "File {0}: {1}"
                            self.reporter(
                                msg.format(1, match1), level=self.reporter.V
                            )
                            self.reporter(
                                msg.format(ifile + 2, match2),
                                level=self.reporter.V,
                            )

        # If not all comparisons were printed, note it here
        if (
            self.max_report_lines is not None
            and comparison_total > self.max_report_lines
        ):
            self.reporter("... Some output omitted due to limit ...")

        msg = "Performed {0} comparison{1}, with {2} failure{3}"
        self.reporter(
            msg.format(
                comparison_total,
                {1: ""}.get(comparison_total, "s"),
                failure_total,
                {1: ""}.get(failure_total, "s"),
            )
        )

        # If everything passed - the task did too
        self.passed = all(passed)
        self.update_kgo()

    def process_opt_tolerance(self):
        """
        Process the tolerance option; a value given either an absolute or
        relative tolerance which a numeric value must lie within.

        """
        # Get the tolerance from the options dictionary
        tolerance = self.options.pop("tolerance", None)
        # Convert the tolerance
        self.relative_tol = False
        if tolerance is not None:
            # Determine what type of tolerance it is and set the flag
            if tolerance.endswith("%"):
                self.relative_tol = True
                tolerance = float(tolerance.strip("%"))
                self.reporter("Relative (%) tolerance: {0}".format(tolerance))
            else:
                tolerance = float(tolerance)
                self.reporter("Absolute tolerance: {0}".format(tolerance))
        self.tolerance = tolerance

    def search_for_matches(self):
        """
        Search the contents of the files for the patterns; returning a
        dictionary whose keys are the file-names and whose values are
        lists of the groupings (one for each occurrence)

        """
        matched_groups = {}
        for fname in self.files:
            matched_groups[fname] = []
            for line in self.read_file(fname):
                search = re.search(self.pattern, line)
                if search:
                    matched_groups[fname].append(search.groups())
        return matched_groups


class FileCommandPattern(FilePattern):
    """Check for occurrences of a particular expression or value in the
    standard output from a command applied to two or more files.

    Options:
        files (optional):
            Same as previous tasks.
        kgo_file:
            Same as previous tasks.
        pattern:
            Same as previous tasks.
        tolerance (optional):
            Same as previous tasks.
        command:
            The command to run; it should contain a Python style format
            specifier to be expanded using the list of files above.

    """

    def run_analysis(self):
        """Main analysis routine called from rose_ana."""
        # Note that this is identical to the above class, only it has the
        # additional command option; so call back to the parent class
        self.process_opt_command()
        super(FileCommandPattern, self).run_analysis()

    def search_for_matches(self):
        """
        Run the command on each file then search its output for the pattern;
        returning a dictionary whose keys are the file-names and whose values
        are lists of the groupings (one for each occurrence).

        """
        matched_groups = {}
        for fname in self.files:
            matched_groups[fname] = []
            command = self.command.format(fname)
            returncode, stdout, stderr = self.run_command(command)
            if returncode == 0:
                for line in stdout.split("\n"):
                    search = re.search(self.pattern, line)
                    if search:
                        matched_groups[fname].append(search.groups())
            else:
                msg = "Command failed, stderr: {0}"
                raise ValueError(msg.format(stderr))

        return matched_groups
