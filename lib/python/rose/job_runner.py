# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
#-----------------------------------------------------------------------------
"""A multiprocessing runner of jobs with dependencies."""

from multiprocessing import Pool
from rose.reporter import Event
from rose.resource import ResourceLocator
from time import sleep


class JobEvent(Event):
    """Event raised when a job completes."""
    def __init__(self, job):
        Event.__init__(self, job)
        if job.event_level is not None:
            self.level = job.event_level

    def __str__(self):
        return str(self.args[0])


class JobManager(object):
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

    def get_job(self):
        """Return the next job that requires processing."""
        while self.ready_jobs:
            job = self.ready_jobs.pop()
            for dep_key, dep_job in job.pending_for.items():
                if dep_job.state == dep_job.ST_DONE:
                    job.pending_for.pop(dep_key)
                    if dep_job.needed_by.has_key(job.name):
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
        """Return pending jobs if there are no ready/working ones."""
        if not self.has_jobs:
            jobs = []
            for job in self.jobs.values():
                if job.pending_for:
                    jobs.append(job)
            return jobs

    def has_jobs(self):
        """Return True if there are ready jobs or working jobs."""
        return (bool(self.ready_jobs) or bool(self.working_jobs))

    def has_ready_jobs(self):
        """Return True if there are ready jobs."""
        return bool(self.ready_jobs)

    def put_job(self, job_proxy):
        """Tell the manager that a job has completed."""
        job = self.working_jobs.pop(job_proxy.name)
        job.update(job_proxy)
        job.state = job.ST_DONE
        for up_key, up_job in job.needed_by.items():
            job.needed_by.pop(up_key)
            up_job.pending_for.pop(job.name)
            if not up_job.pending_for:
                self.ready_jobs.append(up_job)
                up_job.state = up_job.ST_READY
        return job


class JobProxy(object):
    """Represent the state of the job."""

    ST_DONE = "ST_DONE"
    #ST_FAILED = "ST_FAILED"
    ST_PENDING = "ST_PENDING"
    ST_READY = "ST_READY"
    ST_WORKING = "ST_WORKING"

    def __init__(self, context, pending_for=None, event_level=None):
        """
        Initiate a new instance.

        context: The real context of this job, which must be serialisable.
                 The context will be processed by the job processor.
                 The context should have a context.name attribute with a str
                 value and a context.update(other) method that updates itself
                 with the value of "other".
        pending_for: A dict to map job (context) names and JobProxy objects
                     that are required by this job.
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

    def __str__(self):
        return str(self.context)

    def update(self, other):
        """Update self.contextwith the values of "other.context"."""
        self.context.update(other.context)


class JobRunner(object):
    """Runs JobProxy objects with pool of workers."""

    NPROC = 6
    POLL_DELAY = 0.05

    def __init__(self, job_processor, nproc=None):
        """
        Initialise a job runner.

        job_processor: the processor of a job. Must implement a process_job()
        and a post_process_job() methods. See the run() method for detail.

        nproc: maximum number of processes in the pool. If None or not
        specified, use self.NPROC.

        """
        self.job_processor = job_processor
        conf = ResourceLocator.default().get_conf()
        if nproc is None:
            nproc = self.NPROC
        self.nproc = nproc

    def run(self, job_manager, *args):
        """
        Start the job runner with an instance of JobManager.

        Poll self.job_manager for ready jobs.
        
        Put ready jobs in a worker pool, which calls
            self.job_processor.process_job(job_proxy, *args)

        When a job is completed, calls
            self.job_processor.post_process_job(job_proxy, *args)

        """
        nproc = self.nproc
        if nproc > len(job_manager.jobs):
            nproc = len(job_manager.jobs)
        pool = Pool(processes=nproc)

        results = {}
        while job_manager.has_jobs():
            # Process results, if any is ready
            for name, result in results.items():
                if result.ready():
                    results.pop(name)
                    job_proxy, args_of_events = result.get()
                    for args_of_event in args_of_events:
                        self.job_processor.handle_event(*args_of_event)
                    job = job_manager.put_job(job_proxy)
                    self.job_processor.post_process_job(job, *args)
                    self.job_processor.handle_event(JobEvent(job))
            # Add some more jobs into the worker pool, as they are ready
            while job_manager.has_ready_jobs():
                job = job_manager.get_job()
                if job is None:
                    break
                job_run_args = [self.job_processor, job] + list(args)
                result = pool.apply_async(_job_run, job_run_args)
                results[job.name] = result
            if results:
                sleep(self.POLL_DELAY)

        dead_jobs = job_manager.get_dead_jobs()
        if dead_jobs:
            raise JobRunnerNotCompletedError(dead_jobs)

    __call__ = run


def _job_run(job_processor, job_proxy, *args):
    """Helper for JobRunner."""
    event_handler = JobRunnerWorkerEventHandler()
    job_processor.set_event_handler(event_handler)
    try:
        job_processor.process_job(job_proxy, *args)
    except Exception as e:
        #import traceback
        #traceback.print_exc(e)
        raise e
    finally:
        job_processor.set_event_handler(None)
    return (job_proxy, event_handler.events)


class JobRunnerWorkerEventHandler(object):
    """Temporary event handler in a function run by a pool worker process.

    Events are collected in the self.events which is a list of tuples
    representing the arguments the report method in an instance of
    rose.reporter.Reporter.

    """
    def __init__(self):
        self.events = []

    def __call__(self, message, kind=None, level=None, prefix=None,
                 clip=None):
        self.events.append((message, kind, level, prefix, clip))


class JobRunnerNotCompletedError(Exception):
    """Error raised when there are no ready/working jobs but pending ones."""
    def __str__(self):
        ret = ""
        for job in self.args:
            ret += "[DEAD TASK] %s\n" % str(job)
        return ret
