from datetime import datetime, timezone as dt_tz
from unittest import mock

from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from dashboard.admin import ShareAdmin
from dashboard.models import Share
from dashboard.serializers import ShareSerializer


def make_share(ticker="TEST", figi="F1", uid="U1", **kwargs):
    return Share.objects.create(
        figi=figi,
        isin="IS1",
        name=f"Corp {ticker}",
        ticker=ticker,
        currency="RUB",
        uid=uid,
        **kwargs,
    )


class ShareModelTests(TestCase):
    def test_str(self):
        share = make_share()
        self.assertEqual(str(share), f"{share.name} ({share.ticker})")

    def test_unique_figi(self):
        make_share(figi="F1", ticker="AAA", uid="UA")
        with self.assertRaises(IntegrityError):
            make_share(figi="F1", ticker="BBB", uid="UB")

    def test_unique_ticker(self):
        make_share(figi="F1", ticker="AAA", uid="UA")
        with self.assertRaises(IntegrityError):
            make_share(figi="F2", ticker="AAA", uid="UB")

    def test_unique_uid(self):
        make_share(figi="F1", ticker="AAA", uid="UA")
        with self.assertRaises(IntegrityError):
            make_share(figi="F2", ticker="BBB", uid="UA")

    def test_optional_fields_default_to_null(self):
        share = make_share()
        self.assertIsNone(share.last_price)
        self.assertIsNone(share.is_trend_high)
        self.assertIsNone(share.updated_at)

    def test_updated_at_set_on_save(self):
        share = make_share()
        share.refresh_from_db()
        self.assertIsNotNone(share.updated_at)

    def test_ordering_by_name(self):
        make_share(ticker="ZZZ", figi="F1", uid="U1", name="B Corp")
        make_share(ticker="AAA", figi="F2", uid="U2", name="A Corp")
        names = list(Share.objects.values_list("name", flat=True))
        self.assertEqual(names, ["A Corp", "B Corp"])


class ShareSerializerTests(TestCase):
    def test_fields(self):
        self.assertEqual(
            set(ShareSerializer.Meta.fields),
            {
                "id",
                "figi",
                "isin",
                "name",
                "ticker",
                "currency",
                "last_price",
                "is_trend_high",
                "updated_at",
            },
        )


class ShareAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.share = make_share(ticker="GAZP", figi="FGAZP", uid="UGAZP")

    def test_list_is_paginated(self):
        response = self.client.get("/api/v1/shares/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

    def test_filter_by_ticker(self):
        make_share(ticker="SBER", figi="FSBER", uid="USBER")
        response = self.client.get("/api/v1/shares/?ticker=SBER")
        self.assertEqual(
            [item["ticker"] for item in response.data["results"]], ["SBER"]
        )

    def test_filter_by_name(self):
        make_share(ticker="SBER", figi="FSBER", uid="USBER", name="Sberbank")
        response = self.client.get("/api/v1/shares/?name=Sberbank")
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_by_ticker(self):
        response = self.client.get("/api/v1/shares/?search=GAZP")
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_by_figi(self):
        response = self.client.get("/api/v1/shares/?search=FGAZP")
        self.assertEqual(len(response.data["results"]), 1)

    def test_ordering_by_name_desc(self):
        make_share(ticker="SBER", figi="FSBER", uid="USBER", name="Sberbank")
        response = self.client.get("/api/v1/shares/?ordering=-name")
        tickers = [item["ticker"] for item in response.data["results"]]
        self.assertEqual(tickers, ["SBER", "GAZP"])

    def test_create_share(self):
        payload = {
            "figi": "FNEW",
            "isin": "ISNEW",
            "name": "New Corp",
            "ticker": "NEW",
            "currency": "USD",
        }
        response = self.client.post("/api/v1/shares/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Share.objects.filter(ticker="NEW").exists())

    def test_update_share(self):
        response = self.client.patch(
            f"/api/v1/shares/{self.share.id}/",
            {"name": "Renamed Corp"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.share.refresh_from_db()
        self.assertEqual(self.share.name, "Renamed Corp")

    def test_delete_share(self):
        response = self.client.delete(f"/api/v1/shares/{self.share.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Share.objects.filter(id=self.share.id).exists())

    def test_uid_not_exposed_in_api(self):
        response = self.client.get("/api/v1/shares/")
        self.assertNotIn("uid", response.data["results"][0])


class UpdateLastPriceTaskTests(TestCase):
    def _run_task(self, price):
        received_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt_tz.utc)
        with mock.patch(
            "dashboard.tasks.get_last_data", return_value=[price, received_at]
        ):
            from dashboard.tasks import update_last_price

            update_last_price()

    def test_first_run_trend_is_unknown(self):
        share = make_share(last_price=None)
        self._run_task(100.0)
        share.refresh_from_db()
        self.assertEqual(share.last_price, 100.0)
        self.assertIsNone(share.is_trend_high)

    def test_price_growth_sets_true(self):
        share = make_share(last_price=100.0)
        self._run_task(110.0)
        share.refresh_from_db()
        self.assertTrue(share.is_trend_high)

    def test_price_fall_sets_false(self):
        share = make_share(last_price=100.0)
        self._run_task(90.0)
        share.refresh_from_db()
        self.assertFalse(share.is_trend_high)

    def test_network_error_keeps_record_intact(self):
        share = make_share(last_price=100.0)
        with mock.patch(
            "dashboard.tasks.get_last_data", side_effect=ConnectionError("fail")
        ):
            from dashboard.tasks import update_last_price

            update_last_price()
        share.refresh_from_db()
        self.assertEqual(share.last_price, 100.0)
        self.assertTrue(share.is_trend_high)


class ShareAdminTests(TestCase):
    def test_config(self):
        self.assertIn("updated_at", ShareAdmin.readonly_fields)
        self.assertIn(
            "ticker", ShareAdmin.list_display
        )
