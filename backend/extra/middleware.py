import logging

from django.core.exceptions import TooManyFieldsSent
from django.http import HttpResponseBadRequest


class ErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("django.request")

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        request.META["USER"] = request.user.email

        if isinstance(exception, TooManyFieldsSent):
            return HttpResponseBadRequest(
                "This request selected too many items at once (e.g. "
                '"select all" on a large list, or assigning a large number '
                "of indices to an Index Type). Please split it into smaller "
                "batches and try again, or contact an administrator if this "
                "keeps happening."
            )
