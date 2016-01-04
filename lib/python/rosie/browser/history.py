# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
#
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

import ast
import os

import rosie.browser


class HistoryManager():

    """Class for managing the search history."""

    def __init__(self, hist_path=None, hist_length=rosie.browser.SIZE_HISTORY):
        self.archive = []
        self.session_log = []
        if hist_path is not None:
            self.hist_path = os.path.expanduser(hist_path)
        else:
            self.hist_path = os.path.expanduser(rosie.browser.HISTORY_LOCATION)
        self.set_hist_length(hist_length)
        self.hist_io = HistoryIO(self.hist_path, self.timescale)
        self.load_history()

    def clean_log(self, log):
        """ method to clean a history log so only the most recent instance of a
        history item is kept.
        """
        if len(log) <= 1:
            return log
        else:
            i = 0
            while i < (len(log) - 1):
                j = (len(log) - 1)
                while j > i:
                    if str(log[j]) == str(log[i]):
                        log.pop(j)
                    j -= 1
                i += 1

            return log

    def clear_session_log(self):
        """Clear the search history log for the current session."""
        self.session_log = []
        self.current_search = 0

    def clear_archive(self):
        """Clear the search history archive."""
        self.archive = []

    def clear_history(self):
        """Clear all search history"""
        self.session_log = []
        self.archive = []

    def set_hist_length(self, time):
        """Set the number of history items to store."""
        self.timescale = time

    def print_archive(self):
        """Print the history archive."""
        for l in self.archive:
            print str(l)

    def print_session(self):
        """Print the session history."""
        for l in self.session_log:
            print str(l)

    def load_history(self):
        """Load in the archived search history."""
        self.archive = self.hist_io.load_history()
        self.archive = self.clean_log(self.archive)

    def get_last(self):
        """Get the last history item to be recorded."""
        if len(self.session_log) > 1:
            return self.session_log[1]
        else:
            return False

    def get_latest(self):
        """Get the most recent history item recorded."""
        if len(self.session_log) > 0:
            return self.session_log[0]
        else:
            return False

    def get_previous(self):
        """Return the history item prior to the one currently being examined.
        """
        if len(self.session_log) > 1:
            if self.current_search < (len(self.session_log) - 1):
                self.current_search += 1
                return [self.session_log[self.current_search],
                        self.current_search < (len(self.session_log) - 1)]
            else:
                return None, False
        else:
            return None, False

    def get_next(self):
        """Return the history item after the one currently being examined."""
        if self.current_search > 0:
            self.current_search -= 1
            return [self.session_log[self.current_search],
                    self.current_search != 0]
        else:
            return None, False

    def get_n_searches(self):
        """Return the number of history items for this session."""
        return len(self.session_log)

    def get_archive(self):
        """Return the archive of history items."""
        return self.archive

    def get_clean_session_log(self):
        """Return the non-home entries from the session log"""
        session = []
        for record in self.session_log:
            if record.h_type != "home":
                session.append(record)
        return session

    def record_search(self, search_type, description, hist_search):
        """Record a history item."""
        record = HistoryItem(search_type, description, hist_search)
        self.current_search = 0
        if len(self.session_log) == 0:
            self.session_log.insert(0, record)
            return True
        else:
            if str(record) != str(self.session_log[0]):
                self.session_log.insert(0, record)
                return True
            else:
                return False

    def store_history(self):
        """Save the combined session history and archive."""
        complete_hist = self.get_clean_session_log() + self.archive
        complete_hist = self.clean_log(complete_hist)
        hist_out = [complete_hist[i] for i in range(min(self.timescale,
                                                    len(complete_hist)))]
        self.hist_io.write_history(hist_out)


class HistoryIO():

    """Convenience class for managing the reading and writing of history
    items.
    """

    def __init__(self, hist_path=rosie.browser.HISTORY_LOCATION,
                 hist_length=rosie.browser.SIZE_HISTORY):
        self.hist_path = hist_path
        self.timescale = hist_length
        path = hist_path.split("/")
        path.pop(-1)
        folder = ""
        for f in range(len(path) - 1):
            folder = folder + path[f] + "/"
        folder = folder + path[-1]
        if not os.path.isdir(folder):
            os.mkdir(folder)

    def load_history(self):
        """Read in the search history."""
        history = []
        if os.path.exists(self.hist_path):

            f = open(self.hist_path, 'r+')
            archive = f.readlines()
            f.close()

            for i, h in enumerate(archive):

                entry = h
                entry = entry.split(",")
                entry[-1] = entry[-1].replace("\n", "")

                end = None

                if entry[-1] == "True":
                    entry[-1] = True
                elif entry[-1] == "False":
                    entry[-1] = False
                else:
                    entry[-1] = False

                details = ""

                for i in range(1, len(entry) - 1):
                    details = details + str(entry[i])
                    if i < (len(entry) - 2):
                        details = details + ","

                history.append(HistoryItem(entry[0], details, entry[-1]))

        else:
            f = open(self.hist_path, 'w')
            f.close()

        return history

    def write_history(self, archive=False):
        """Write out the search history."""
        if archive:
            f = open(self.hist_path, 'w')
            for i, h in enumerate(archive):
                if i < self.timescale and h.h_type != "home":
                    f.write(str(h) + '\n')
                else:
                    break
            f.close()


class HistoryItem():

    """Class for recording search history items."""

    def __init__(self, h_type="", details="", search_history=False):
        self.h_type = h_type
        self.details = ast.literal_eval(details)
        self.search_history = search_history

    def __str__(self):
        """Define string format."""
        return (self.h_type + "," + repr(self.details) + ","
                + ("False", "True")[self.search_history])

    def get_out_string(self):
        """Return the output string."""
        return str(self)
