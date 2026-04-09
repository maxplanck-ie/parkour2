import logging
import tempfile
from unittest.mock import patch

from common.logger import CustomAdminEmailHandler


def _record(message):
    return logging.LogRecord(
        name="django.request",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


class TestCustomAdminEmailHandler:
    def test_suppresses_identical_errors_within_window(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_file = f"{tmp_dir}/email_dedup_state.json"
            CustomAdminEmailHandler.reset_state(state_file)
            handler = CustomAdminEmailHandler(
                include_html=False,
                dedup_window_seconds=180,
                summary_email_every_seconds=0,
                state_file_path=state_file,
            )
            rec = _record("boom")

            with (
                patch("common.logger.time.time", side_effect=[1.0, 2.0, 3.0, 190.0]),
                patch("common.logger.mail.mail_admins") as mail_admins,
            ):
                handler.emit(rec)
                handler.emit(rec)
                handler.emit(rec)
                handler.emit(rec)

        expected_calls = 3
        assert mail_admins.call_count == expected_calls  # noqa: S101
        summary_subject = mail_admins.call_args_list[1].args[0]
        assert (  # noqa: S101
            "Suppressed 2 duplicate backend error email(s)" in summary_subject
        )

    def test_flushes_summary_when_error_changes(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_file = f"{tmp_dir}/email_dedup_state.json"
            CustomAdminEmailHandler.reset_state(state_file)
            handler = CustomAdminEmailHandler(
                include_html=False,
                dedup_window_seconds=180,
                summary_email_every_seconds=0,
                state_file_path=state_file,
            )

            with (
                patch("common.logger.time.time", side_effect=[1.0, 2.0, 3.0]),
                patch("common.logger.mail.mail_admins") as mail_admins,
            ):
                handler.emit(_record("boom"))
                handler.emit(_record("boom"))
                handler.emit(_record("different boom"))

        expected_calls = 3
        assert mail_admins.call_count == expected_calls  # noqa: S101
        summary_subject = mail_admins.call_args_list[1].args[0]
        assert (  # noqa: S101
            "Suppressed 1 duplicate backend error email(s)" in summary_subject
        )

    def test_suppresses_duplicates_across_handler_instances(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_file = f"{tmp_dir}/email_dedup_state.json"
            CustomAdminEmailHandler.reset_state(state_file)

            handler_a = CustomAdminEmailHandler(
                include_html=False,
                dedup_window_seconds=180,
                summary_email_every_seconds=0,
                state_file_path=state_file,
            )
            handler_b = CustomAdminEmailHandler(
                include_html=False,
                dedup_window_seconds=180,
                summary_email_every_seconds=0,
                state_file_path=state_file,
            )

            with (
                patch("common.logger.time.time", side_effect=[1.0, 2.0]),
                patch("common.logger.mail.mail_admins") as mail_admins,
            ):
                handler_a.emit(_record("boom"))
                handler_b.emit(_record("boom"))

            expected_calls = 1
            assert mail_admins.call_count == expected_calls  # noqa: S101
