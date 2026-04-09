"""Compatibility wrapper for the external mail dedup extension."""

from django_error_mail_dedup.handlers import DedupAdminEmailHandler


class CustomAdminEmailHandler(DedupAdminEmailHandler):
    """Backwards-compatible alias for legacy import path."""
