from django.test import TestCase

from dashboard.models import Share
from dashboard.services.market_data import quotation_to_float, resolve_trend


class QuotationToFloatTests(TestCase):
    def test_units_and_nano(self):
        q = type("Q", (), {"units": 150, "nano": 500000000})()
        self.assertEqual(quotation_to_float(q), 150.5)

    def test_zero_nano(self):
        q = type("Q", (), {"units": 12, "nano": 0})()
        self.assertEqual(quotation_to_float(q), 12.0)


class ResolveTrendTests(TestCase):
    def test_no_previous_price(self):
        self.assertIsNone(resolve_trend(None, 100.0))

    def test_growing(self):
        self.assertIs(resolve_trend(99.0, 100.0), True)

    def test_falling(self):
        self.assertIs(resolve_trend(101.0, 100.0), False)

    def test_equal_is_growing(self):
        self.assertIs(resolve_trend(100.0, 100.0), True)


class ShareModelTest(TestCase):
    def test_str(self):
        share = Share(ticker="SBER", name="Сбербанк", figi="f1", uid="u1")
        self.assertEqual(str(share), "SBER (Сбербанк)")
