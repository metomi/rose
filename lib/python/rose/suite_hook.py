# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
#-------------------------------------------------------------------------------

"""Hook functionalities for a suite task."""

from email.mime.text import MIMEText
import os
import pwd
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener
from rose.reporter import Reporter
from rose.suite_engine_proc import SuiteEngineProcessor
from rose.suite_log_view import SuiteLogViewGenerator
from smtplib import SMTP

class RoseSuiteHook(object):

    """Hook functionalities for a suite task."""

    def __init__(self, event_handler=None, popen=None, suite_engine_proc=None):
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        self.popen = popen
        if suite_engine_proc is None:
            suite_engine_proc = SuiteEngineProcessor.get_processor(
                    event_handler=event_handler, popen=popen)
        self.suite_engine_proc = suite_engine_proc
        self.suite_log_view_generator = SuiteLogViewGenerator(
                event_handler=event_handler,
                suite_engine_proc=suite_engine_proc)

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler if it is callabale."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def run(self, suite, task, hook_event, hook_message=None,
            should_mail=False, mail_cc_list=None, should_shutdown=False):
        """
        Invoke the hook for a suite task.

        1. If the task runs remotely, retrieve its log from the remote host.
        2. Generate the suite log view.
        3. If "should_mail", send an email notification to the current user,
           and those in the "mail_cc_list".
        4. If "should_shutdown", shut down the suite.

        """
        task_log_dir, r_task_log_dir = self.suite_engine_proc.get_log_dirs(
                suite, task)

        # Retrieve log
        if task and r_task_log_dir:
            cmd = self.popen.get_cmd(
                    "rsync", r_task_log_dir + "/" + task + "*", task_log_dir)
            self.popen(*cmd)

        # Generate suite log view
        suite_log_dir = os.path.dirname(task_log_dir)
        self.suite_log_view_generator(suite_log_dir)

        # Send email notification if required
        if should_mail:
            text = ""
            if task:
                text += "Task: %s\n" % task
            if hook_message:
                text += "Message: %s\n" % hook_message
            text += "See: file://%s/index.html\n" % (suite_log_dir)
            msg = MIMEText(text)
            user = pwd.getpwuid(os.getuid()).pw_name
            msg["From"] = user
            msg["To"] = user
            if mail_cc_list:
                msg["Cc"] = ", ".join(mail_cc_list)
            else:
                mail_cc_list = []
            msg["Subject"] = "[%s] %s" % (hook_event, suite)
            smtp = SMTP('localhost')
            smtp.sendmail(user, [user] + mail_cc_list, msg.as_string())
            smtp.quit()

        # Shut down if required
        if should_shutdown:
            self.suite_engine_proc.shutdown(suite)

    __call__ = run
        

def main():
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("mail_cc", "mail", "shutdown")
    opts, args = opt_parser.parse_args()
    for key in ["mail_cc"]:
        values = []
        if getattr(opts, key):
            for value in getattr(opts, key):
                values.extend(value.split(","))
        setattr(opts, key, values)
    report = Reporter(opts.verbosity - opts.quietness)
    popen = RosePopener(event_handler=report)
    suite_engine_proc = SuiteEngineProcessor.get_processor(
            event_handler=report, popen=popen)
    args = suite_engine_proc.process_suite_hook_args(*args, **vars(opts))
    hook = RoseSuiteHook(event_handler=report,
                         popen=popen,
                         suite_engine_proc=suite_engine_proc)
    hook(*args,
         should_mail=opts.mail,
         mail_cc_list=opts.mail_cc,
         should_shutdown=opts.shutdown)


if __name__ == "__main__":
    main()
