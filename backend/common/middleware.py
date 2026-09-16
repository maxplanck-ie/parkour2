from django.conf import settings

from common.models import User


class DemoAutoLoginMiddleware:
    """Auto-authenticates every request as the demo fixture staff user.

    Only ever wired into MIDDLEWARE by config/settings/demo.py -- never
    imported by dev/prod/testing settings -- so this can't leak into a real
    deployment by accident.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Fetched fresh each request (not cached on the middleware instance):
        # the hourly reset_demo command truncates and reloads this row, so a
        # cached instance could otherwise go stale for the worker's lifetime.
        request.user = User.objects.get(email=settings.DEMO_STAFF_USER_EMAIL)
        return self.get_response(request)
