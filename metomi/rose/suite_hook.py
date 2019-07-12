# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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

"""Hook functionalities for a suite."""

from email.mime.text import MIMEText
import os
import pwd
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopener
from metomi.rose.reporter import Reporter
from metomi.rose.resource import ResourceLocator
from metomi.rose.suite_engine_proc import SuiteEngineProcessor
from smtplib import SMTP, SMTPException
import socket


class RoseSuiteHook(object):

    """Hook functionalities for a suite."""

    def __init__(self, event_handler=None, popen=None, suite_engine_proc=None):
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        self.popen = popen
        if suite_engine_proc is None:
            suite_engine_proc = SuiteEngineProcessor.get_processor(
                event_handler=event_handler, popen=popen)
        self.suite_engine_proc = suite_engine_proc

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler if it is callabale."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def run(self, suite_name, task_id, hook_event, hook_message=None,
            should_mail=False, mail_cc_list=None, should_shutdown=False,
            should_retrieve_job_logs=False):
        """
        Invoke the hook for a suite.

        1. For a task hook, if the task runs remotely, retrieve its log from
           the remote host.
        2. If "should_mail", send an email notification to the current user,
           and those in the "mail_cc_list".
        3. If "should_shutdown", shut down the suite.

        """
        # Retrieve log and populate job logs database
        task_ids = []
        if task_id and should_retrieve_job_logs:
            task_ids = [task_id]
            self.suite_engine_proc.job_logs_pull_remote(suite_name, task_ids)

        # Send email notification if required
        email_exc = None
        if should_mail:
            text = ""
            if task_id:
                text += "Task: %s\n" % task_id
            if hook_message:
                text += "Message: %s\n" % hook_message
            url = self.suite_engine_proc.get_suite_log_url(None, suite_name)
            text += "See: %s\n" % (url)
            user = pwd.getpwuid(os.getuid()).pw_name
            conf = ResourceLocator.default().get_conf()
            host = conf.get_value(["rose-suite-hook", "email-host"],
                                  default="localhost")
            msg = MIMEText(text)
            msg["From"] = user + "@" + host
            msg["To"] = msg["From"]
            if mail_cc_list:
                mail_cc_addresses = []
                for mail_cc_address in mail_cc_list:
                    if "@" not in mail_cc_address:
                        mail_cc_address += "@" + host
                    mail_cc_addresses.append(mail_cc_address)
                msg["Cc"] = ", ".join(mail_cc_addresses)
                mail_cc_list = mail_cc_addresses
            else:
                mail_cc_list = []
            msg["Subject"] = "[%s] %s" % (hook_event, suite_name)
            smtp_host = conf.get_value(["rose-suite-hook", "smtp-host"],
                                       default="localhost")
            try:
                smtp = SMTP(smtp_host)
                smtp.sendmail(
                    msg["From"], [msg["To"]] + mail_cc_list, msg.as_string())
                smtp.quit()
            except (socket.error, SMTPException) as email_exc:
                pass

        # Shut down if required
        if should_shutdown:
            self.suite_engine_proc.shutdown(suite_name, args=["--kill"])

        if email_exc is not None:
            raise

    __call__ = run


def main():
    """Implement "rose suite-hook" command."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options(
        "mail_cc", "mail", "retrieve_job_logs", "shutdown")
    opts, args = opt_parser.parse_args()
    for key in ["mail_cc"]:
        values = []
        if getattr(opts, key):
            for value in getattr(opts, key):
                values.extend(value.split(","))
        setattr(opts, key, values)
    report = Reporter(opts.verbosity - opts.quietness - 1)  # Reduced default
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
         should_shutdown=opts.shutdown,
         should_retrieve_job_logs=opts.retrieve_job_logs)


if __name__ == "__main__":
    main()
