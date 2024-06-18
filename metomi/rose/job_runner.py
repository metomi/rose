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

    ASYNC_SLEEP_TIME = 0.1

    def __init__(self, job_processor, nproc=None):
        """
        Initialise a job runner.

        job_processor: the processor of a job. Must implement a process_job()
        and a post_process_job() methods. See the run() method for detail.

        nproc: maximum number of processes in the pool. If None or not
        specified, use self.NPROC.

        """
        self.job_processor = job_processor

    async def run(
        self,
        job_manager,
        conf_tree,
        loc_dao,
        work_dir,
        concurrency=6,
    ):
        """Start the job runner with an instance of JobManager.

        Args:
            job_manager (JobManager):
                A JobManager object used to handle the list of jobs to be done
            conf_tree:
                The Rose configuration tree containing the definitions of the
                things to do.
            loc_dao:
                Location database to record what has been done.
            work_dir:
                Work directory.
            concurrency:
                The maximum number of jobs to run concurrently.

        """
        await self._run(
            job_manager, conf_tree, loc_dao, work_dir, concurrency=concurrency
        )
        dead_jobs = job_manager.get_dead_jobs()
        if dead_jobs:
            raise JobRunnerNotCompletedError(dead_jobs)

    async def _run(
        self,
        job_manager,
        conf_tree,
        loc_dao,
        work_dir,
        concurrency=6,
    ):
        running = []
        args = (conf_tree, loc_dao, work_dir)
        await asyncio.gather(
            self._run_jobs(running, job_manager, args, concurrency),
            self._post_process_jobs(running, job_manager, args),
        )

    async def _run_jobs(self, running, job_manager, args, concurrency):
        """Run pending jobs subject to the concurrency limit.

        This coroutine exits when there are no more jobs left to run.

        Args:
            running:
                Jobs will be added to this list when run.
            job_manager:
                A JobManager object used to handle the list of jobs to be done
            args:
                Arguments to pass through to jobs / post-processing.
            concurrency:
                The maximum number of jobs to run concurrently.

        """
        while job_manager.has_jobs():
            while len(running) < concurrency:
                # run jobs
                job = job_manager.get_job()
                if job is None:
                    # we've run out of jobs for now
                    break
                task = asyncio.create_task(
                    self.job_processor.process_job(job, *args)
                )
                task.job = job
                running.append(task)
            # we've hit the concurrency limit => wait
            await asyncio.sleep(self.ASYNC_SLEEP_TIME)

    async def _post_process_jobs(self, running, job_manager, args):
        """Post process completed jobs.

        This coroutine exits when there are not more jobs left to run / post
        process.

        Args:
            running:
                Jobs will be added to this list when run.
            job_manager:
                A JobManager object used to handle the list of jobs to be done
            args:
                Arguments to pass through to jobs / post-processing.

        """
        while running or job_manager.has_jobs():
            if not running:
                # wait for more tasks to be queued
                await asyncio.sleep(self.ASYNC_SLEEP_TIME)
                continue
            done, _running = await asyncio.wait(
                running,
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                running.remove(task)
                job = task.job
                job.exc = task.exception()
                job_manager.put_job(job)
                if not job.exc:
                    self.job_processor.post_process_job(job, *args)
                    self.job_processor.handle_event(JobEvent(job))
                else:
                    self.job_processor.handle_event(job.exc)

    __call__ = run


class JobRunnerNotCompletedError(Exception):
    """Error raised when there are no ready/working jobs but pending ones."""

    def __str__(self):
        ret = ""
        for job in self.args[0]:
            ret += "%s\n" % str(job.context)
        return ret
