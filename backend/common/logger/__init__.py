import contextlib
import hashlib
import json
import os
import threading
import time
import traceback

from django.core import mail
from django.utils.log import AdminEmailHandler
from django.views.debug import ExceptionReporter, get_exception_reporter_filter


class CustomAdminEmailHandler(AdminEmailHandler):
    _state_lock = threading.Lock()
    _last_signature = None
    _last_subject = ""
    _last_message = ""
    _last_primary_sent_at = 0.0
    _last_summary_sent_at = 0.0
    _suppressed_duplicates = 0

    def __init__(
        self,
        include_html=True,
        dedup_window_seconds=180,
        summary_email_every_seconds=60,
        state_file_path=None,
        **kwargs,
    ):
        super().__init__(include_html=include_html, **kwargs)
        self.dedup_window_seconds = max(0, int(dedup_window_seconds))
        self.summary_email_every_seconds = max(0, int(summary_email_every_seconds))
        self.state_file_path = state_file_path

    @classmethod
    def reset_state(cls, state_file_path=None):
        with cls._state_lock:
            cls._last_signature = None
            cls._last_subject = ""
            cls._last_message = ""
            cls._last_primary_sent_at = 0.0
            cls._last_summary_sent_at = 0.0
            cls._suppressed_duplicates = 0

        if state_file_path:
            with contextlib.suppress(OSError):
                os.remove(state_file_path)

    @staticmethod
    def _default_state():
        return {
            "last_signature": None,
            "last_subject": "",
            "last_message": "",
            "last_primary_sent_at": 0.0,
            "last_summary_sent_at": 0.0,
            "suppressed_duplicates": 0,
        }

    @staticmethod
    def _signature(subject, message):
        value = f"{subject}\0{message}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @contextlib.contextmanager
    def _locked_shared_state(self):
        import fcntl

        defaults = self._default_state()
        state_dir = os.path.dirname(self.state_file_path)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)

        with open(self.state_file_path, "a+", encoding="utf-8") as state_file:
            fcntl.flock(state_file.fileno(), fcntl.LOCK_EX)

            state_file.seek(0)
            raw = state_file.read().strip()

            with contextlib.suppress(json.JSONDecodeError):
                if raw:
                    defaults.update(json.loads(raw))

            yield defaults

            state_file.seek(0)
            state_file.truncate(0)
            state_file.write(json.dumps(defaults))
            state_file.flush()
            os.fsync(state_file.fileno())

            fcntl.flock(state_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _summary_payload(state, now):
        suppressed = state["suppressed_duplicates"]
        if suppressed <= 0:
            return None

        return {
            "suppressed": suppressed,
            "since_first": max(1, int(now - state["last_primary_sent_at"])),
            "last_subject": state["last_subject"],
            "last_message": state["last_message"],
        }

    def _emit_summary(self, payload):
        if not payload:
            return

        summary_subject = self.format_subject(
            "Suppressed "
            f"{payload['suppressed']} duplicate backend error email(s) in {payload['since_first']}s",
        )
        summary_message = (
            "Duplicate backend errors were suppressed to reduce email noise.\n\n"
            f"Suppressed duplicates: {payload['suppressed']}\n"
            f"Window so far: {payload['since_first']} seconds\n"
            f"Most recent subject: {payload['last_subject']}\n\n"
            "Most recent message:\n"
            f"{payload['last_message']}"
        )
        mail.mail_admins(summary_subject, summary_message, fail_silently=True)

    def _build_email_content(self, record):
        html_message = None

        try:
            request = record.request
            subject = "{} {} (IP {}) | {}".format(
                record.levelname,
                record.status_code,
                (request.META.get("REMOTE_ADDR")),
                record.getMessage(),
            )
            reporter_filter = get_exception_reporter_filter(request)
            request_repr = reporter_filter.get_request_repr(request)

        except Exception:
            subject = f"{record.levelname}: {record.getMessage()}"
            request = None
            request_repr = "Request repr() is unavailable"

        subject = self.format_subject(subject)

        if record.exc_info:
            exc_info = record.exc_info
            stack_trace = "\n".join(traceback.format_exception(*record.exc_info))
        else:
            exc_info = (None, record.getMessage(), None)
            stack_trace = "No stack trace is available"

        message = f"{stack_trace}\n\n{request_repr}"
        reporter = ExceptionReporter(request, is_email=True, *exc_info)
        if self.include_html:
            html_message = reporter.get_traceback_html()

        return subject, message, html_message

    def emit(self, record):
        subject, message, html_message = self._build_email_content(record)
        signature = self._signature(subject, message)
        now = time.time()

        should_send_primary = False
        summary_payload = None

        try:
            if not self.state_file_path:
                raise OSError("Shared dedup state file path is not configured")

            with self._locked_shared_state() as state:
                same_as_previous = signature == state["last_signature"]
                within_window = (
                    now - state["last_primary_sent_at"] <= self.dedup_window_seconds
                )

                if same_as_previous and within_window and self.dedup_window_seconds > 0:
                    state["suppressed_duplicates"] += 1
                    state["last_subject"] = subject
                    state["last_message"] = message

                    if (
                        self.summary_email_every_seconds > 0
                        and now - state["last_summary_sent_at"]
                        >= self.summary_email_every_seconds
                    ):
                        summary_payload = self._summary_payload(state, now)
                        state["suppressed_duplicates"] = 0
                        state["last_summary_sent_at"] = now
                else:
                    summary_payload = self._summary_payload(state, now)
                    if summary_payload:
                        state["suppressed_duplicates"] = 0
                        state["last_summary_sent_at"] = now

                    state["last_signature"] = signature
                    state["last_subject"] = subject
                    state["last_message"] = message
                    state["last_primary_sent_at"] = now
                    should_send_primary = True
        except OSError:
            # Fallback to per-process state only if shared state file is unavailable.
            with self.__class__._state_lock:
                same_as_previous = signature == self.__class__._last_signature
                within_window = (
                    now - self.__class__._last_primary_sent_at
                    <= self.dedup_window_seconds
                )

                if same_as_previous and within_window and self.dedup_window_seconds > 0:
                    self.__class__._suppressed_duplicates += 1
                    self.__class__._last_subject = subject
                    self.__class__._last_message = message

                    if (
                        self.summary_email_every_seconds > 0
                        and now - self.__class__._last_summary_sent_at
                        >= self.summary_email_every_seconds
                    ):
                        summary_payload = {
                            "suppressed": self.__class__._suppressed_duplicates,
                            "since_first": max(
                                1,
                                int(now - self.__class__._last_primary_sent_at),
                            ),
                            "last_subject": self.__class__._last_subject,
                            "last_message": self.__class__._last_message,
                        }
                        self.__class__._suppressed_duplicates = 0
                        self.__class__._last_summary_sent_at = now
                else:
                    if self.__class__._suppressed_duplicates > 0:
                        summary_payload = {
                            "suppressed": self.__class__._suppressed_duplicates,
                            "since_first": max(
                                1,
                                int(now - self.__class__._last_primary_sent_at),
                            ),
                            "last_subject": self.__class__._last_subject,
                            "last_message": self.__class__._last_message,
                        }
                        self.__class__._suppressed_duplicates = 0
                        self.__class__._last_summary_sent_at = now

                    self.__class__._last_signature = signature
                    self.__class__._last_subject = subject
                    self.__class__._last_message = message
                    self.__class__._last_primary_sent_at = now
                    should_send_primary = True

        if summary_payload:
            self._emit_summary(summary_payload)

        if should_send_primary:
            mail.mail_admins(
                subject,
                message,
                fail_silently=True,
                html_message=html_message,
            )
