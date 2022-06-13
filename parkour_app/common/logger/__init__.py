from django.core import mail
from django.utils.log import AdminEmailHandler
from django.views.debug import ExceptionReporter, get_exception_reporter_filter

import traceback


class CustomAdminEmailHandler(AdminEmailHandler):
    def __init__(self, include_html=True):
        AdminEmailHandler.__init__(self)
        self.include_html = include_html

    def emit(self, record):
        try:
            request = record.request
            subject = '%s %s (IP %s) | %s' % (
                record.levelname,
                record.status_code,
                (request.META.get('REMOTE_ADDR')),
                record.getMessage(),
            )
            reporter_filter = get_exception_reporter_filter(request)
            request_repr = reporter_filter.get_request_repr(request)

        except Exception:
            subject = '%s: %s' % (record.levelname, record.getMessage())
            request = None
            request_repr = 'Request repr() is unavailable'

        subject = self.format_subject(subject)

        if record.exc_info:
            exc_info = record.exc_info
            stack_trace = '\n'.join(
                traceback.format_exception(*record.exc_info)
            )
        else:
            exc_info = (None, record.getMessage(), None)
            stack_trace = 'No stack trace is available'

        message = '%s\n\n%s' % (stack_trace, request_repr)
        reporter = ExceptionReporter(request, is_email=True, *exc_info)
        html_message = self.include_html and reporter.get_traceback_html() or \
            None

        mail.mail_admins(
            subject,
            message,
            fail_silently=True,
            html_message=html_message
        )
