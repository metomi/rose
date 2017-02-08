#!/usr/bin/env python
import os
import sqlite3

# Get the path to the database
suite_dir = os.environ["ROSE_SUITE_DIR"]
db_filename = os.path.join(suite_dir, "log", "rose-ana-comparisons.db")

# Connect to it
conn = sqlite3.connect(db_filename)

# Print out the task entries
res = conn.execute("SELECT task_name, completed FROM tasks")
for itask, task in enumerate(res.fetchall()):
    print ("{0} | {1} | {2}".format(itask + 1, *task))

# Print out the comparison entries
res = conn.execute("SELECT comp_task, kgo_file, suite_file, "
                   "status, comparison FROM comparisons")
for icomparison, comparison in enumerate(res.fetchall()):
    print ("{0} | ".format(icomparison + 1) + " | ".join(comparison))


