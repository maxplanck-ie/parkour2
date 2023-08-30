import logging


class ErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("django.request")

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        request.META["USER"] = request.user.email
