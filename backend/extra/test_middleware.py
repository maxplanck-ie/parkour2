from django.core.exceptions import TooManyFieldsSent
from django.test import RequestFactory, TestCase

from .middleware import ErrorMiddleware


class ErrorMiddlewareTest(TestCase):
    def setUp(self):
        self.middleware = ErrorMiddleware(get_response=lambda request: None)
        self.request = RequestFactory().post(
            "/admin/library_sample_shared/indextype/1/change/"
        )
        self.request.user = type("FakeUser", (), {"email": "test@example.com"})()

    def test_too_many_fields_sent_returns_friendly_400(self):
        response = self.middleware.process_exception(
            self.request, TooManyFieldsSent("Max number of fields exceeded")
        )

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"too many items", response.content)

    def test_other_exceptions_are_not_handled(self):
        response = self.middleware.process_exception(self.request, ValueError("boom"))

        self.assertIsNone(response)
