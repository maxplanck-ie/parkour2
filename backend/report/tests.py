from datetime import timedelta

from django.test import SimpleTestCase

from report.views import format_turnaround


class FormatTurnaroundTests(SimpleTestCase):
    def test_returns_hours_with_two_decimals(self):
        delta = timedelta(days=3, hours=4, minutes=30)
        self.assertEqual(format_turnaround(delta), 76.5)

    def test_returns_fractional_hours_when_shorter(self):
        delta = timedelta(hours=2, minutes=5)
        self.assertEqual(format_turnaround(delta), 2.08)

    def test_returns_none_when_delta_invalid(self):
        self.assertEqual(format_turnaround(None), None)
        self.assertEqual(format_turnaround(timedelta(hours=-1)), None)
