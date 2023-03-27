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
"""A multiprocessing runner of jobs with dependencies."""

import asyncio
from metomi.rose.reporter import Event


class JobEvent(Event):
    """Event raised when a job completes."""

    def __init__(self, job):
        Event.__init__(self, job)
        if job.event_level is not None:
            self.level = job.event_level

    def __str__(self):
        return str(self.args[0])


class JobManager:
    """Manage a set of JobProxy objects and their states."""

    def __init__(self, jobs, names=None):
        """Initiate a job manager.

        jobs: A dict of all available jobs (job.name, job).
        names: A list of keys in jobs to process.
               If not set or empty, process all jobs.

        """
        self.jobs = jobs
        self.ready_jobs = []
        if not names:
            names = jobs.keys()
        for name in names:
            self.ready_jobs.append(self.jobs[name])
        self.working_jobs = {}
        self.dead_jobs = []

    def get_job(self):
        """Return the next job that requires processing."""
        while self.ready_jobs:
            job = self.ready_jobs.pop()
            for dep_key, dep_job in list(job.pending_for.items()):
                if dep_job.state == dep_job.ST_DONE:
                    job.pending_for.pop(dep_key)
                    if job.name in dep_job.needed_by:
                        dep_job.needed_by.pop(job.name)
                else:
                    dep_job.needed_by[job.name] = job
                    if dep_job.state is None:
                        dep_job.state = dep_job.ST_READY
                        self.ready_jobs.append(dep_job)
            if job.pending_for:
                job.state = job.ST_PENDING
            else:
                self.working_jobs[job.name] = job
                job.state = job.ST_WORKING
                return job

    def get_dead_jobs(self):
        """Return failed/pending jobs when there are no ready/working ones."""
        jobs = self.dead_jobs
        if not self.has_jobs:
            for job in self.jobs.values():
                if job.pending_for:
                    jobs.append(job)
        return jobs

    def has_jobs(self):
        """Return True if there are ready jobs or working jobs."""
        return bool(self.ready_jobs) or bool(self.working_jobs)

    def has_ready_jobs(self):
        """Return True if there are ready jobs."""
        return bool(self.ready_jobs)

    def put_job(self, job_proxy):
        """Tell the manager that a job has completed."""
        job = self.working_jobs.pop(job_proxy.name)
        job.update(job_proxy)
        if job_proxy.exc is None:
            job.state = job.ST_DONE
            for up_key, up_job in list(job.needed_by.items()):
                job.needed_by.pop(up_key)
                up_job.pending_for.pop(job.name)
                if not up_job.pending_for:
                    self.ready_jobs.append(up_job)
                    up_job.state = up_job.ST_READY
        else:
            self.dead_jobs.append(job)
        return job


class JobProxy:
    """Represent the state of the job."""

    ST_DONE = "ST_DONE"
    ST_PENDING = "ST_PENDING"
    ST_READY = "ST_READY"
    ST_WORKING = "ST_WORKING"

    def __init__(self, context, event_level=None):
        """
        Initiate a new instance.

        context: The real context of this job, which must be serialisable.
                 The context will be processed by the job processor.
                 The context should have a context.name attribute with a str
                 value and a context.update(other) method that updates itself
                 with the value of "other".
        event_level: The job runner may raise an event when this job completes.
                     This tell the event handler only to report this event if
                     the current verbosity is higher than this level.

        """
        self.context = context
        self.name = context.name
        self.pending_for = {}
        self.event_level = event_level
        self.needed_by = {}
        self.state = self.ST_READY
        self.exc = None

    def __str__(self):
        return str(self.context)

    def update(self, other):
        """Update self.contextwith the values of "other.context"."""
        self.context.update(other.context)


class JobRunner:
    """Runs JobProxy objects with pool of workers."""

    def __init__(self, job_processor, nproc=None):
        """
        Initialise a job runner.

        job_processor: the processor of a job. Must implement a process_job()
        and a post_process_job() methods. See the run() method for detail.

        nproc: maximum number of processes in the pool. If None or not
        specified, use self.NPROC.

        """
        self.job_processor = job_processor

    def run(self, job_manager, *args):
        """
        Start the job runner with an instance of JobManager.

        Args:
            job_manager (JobManager):
                A JobManager object used to handle the list of jobs to be done

        Outline:
                 +------------------+
            +---->  job_manager.    +------------>  FINISH
            |    |  has_jobs ?      |   No
            |    +------------------+
            |        |Yes
            |    +---v--------------+
            |    |Post-process any  |
            |    |finished jobs     |
            |    +---+--------------+
            |        |
            |    +---v--------------------------------+
            |    |   Check for ready jobs             |
            |    |   Add ready jobs to "awaiting"     |
            |    +---+-------------------------^------+
            |        |                         |
            |    +---v---------------+         |
            +----+ Are there any jobs|         |
            No   | in "awaiting"?    |         |
                 +-------------------+         |
                     |Yes                      |
                 +-------------------+         |
                 | Add jobs to event |         |
                 | loop - wait until |         |
                 | asyncio returns   |         |
                 | first result.     +---------+
                 +-------------------+

        """
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self.job_processor.handle_event)
        results = {}

        while job_manager.has_jobs():
            # Post-process all finished jobs and handle exceptions.
            for job_proxy, result in list(results.items()):
                results.pop(job_proxy)
                job_proxy.exc = result.exception()
                job_manager.put_job(job_proxy)
                if not job_proxy.exc:
                    self.job_processor.post_process_job(job_proxy, *args)
                    self.job_processor.handle_event(JobEvent(job_proxy))
                else:
                    self.job_processor.handle_event(job_proxy.exc)

            awaiting = set()

            def get_ready_jobs():
                """Get list of jobs with satisfied dependencies"""
                while job_manager.has_ready_jobs():
                    job = job_manager.get_job()
                    if job is None:
                        break
                    task = loop.create_task(
                        self.job_processor.process_job(job, *args)
                    )
                    task.job = job
                    awaiting.add(task)

            get_ready_jobs()
            while awaiting:
                # Submit all tasks in awaiting to event loop, then wait until
                # one of them completes, at which point check whether any more
                # jobs have become ready and submit those.
                just_completed, awaiting = loop.run_until_complete(
                    asyncio.wait(awaiting, return_when=asyncio.FIRST_COMPLETED)
                )
                results.update({task.job: task for task in just_completed})
                get_ready_jobs()

        dead_jobs = job_manager.get_dead_jobs()
        if dead_jobs:
            raise JobRunnerNotCompletedError(dead_jobs)

    __call__ = run


class JobRunnerNotCompletedError(Exception):
    """Error raised when there are no ready/working jobs but pending ones."""

    def __str__(self):
        ret = ""
        for job in self.args[0]:
            ret += "%s\n" % str(job.context)
        return ret
