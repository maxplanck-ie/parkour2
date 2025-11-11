from django.apps import AppConfig


class RequestConfig(AppConfig):
    name = "request"

    def ready(self):
        # Import signal handlers
        from . import signals  # noqa: F401
