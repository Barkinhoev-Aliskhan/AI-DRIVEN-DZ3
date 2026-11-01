"""Тесты приложения: исходная функциональность и новые возможности."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from dashboard.models import (
    Notification,
    Portfolio,
    PortfolioOperation,
    PriceAlert,
    PriceHistory,
    Share,
    Strategy,
    StrategyTrade,
    WatchlistItem,
)
from dashboard.services import monitoring_service, portfolio_service

User = get_user_model()


def create_share(**overrides):
    defaults = dict(
        figi="FIGI-TEST-1",
        isin="ISIN-TEST-1",
        name="Test Corp",
        ticker="TEST",
        currency="RUB",
        uid="UID-TEST-1",
        last_price=100.0,
    )
    defaults.update(overrides)
    return Share.objects.create(**defaults)


class ShareModelTests(TestCase):
    def test_unique_figi(self):
        from django.db import IntegrityError

        create_share()
        with self.assertRaises(IntegrityError):
            create_share(figi="FIGI-TEST-1", ticker="OTHER", uid="UID-OTHER")

    def test_updated_at_auto_refresh(self):
        share = create_share()
        before = share.updated_at
        share.name = "Renamed Corp"
        share.save()
        share.refresh_from_db()
        self.assertIsNotNone(share.updated_at)
        if before is not None:
            self.assertGreaterEqual(share.updated_at, before)

    def test_optional_price_fields(self):
        share = create_share(last_price=None, is_trend_high=None)
        self.assertIsNone(share.last_price)
        self.assertIsNone(share.is_trend_high)


class ShareAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.share = create_share()

    def test_list_with_pagination(self):
        response = self.client.get("/api/v1/shares/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)

    def test_search_by_ticker(self):
        response = self.client.get("/api/v1/shares/?search=TEST")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_ticker(self):
        response = self.client.get("/api/v1/shares/?ticker=TEST")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_ordering_by_name_desc(self):
        response = self.client.get("/api/v1/shares/?ordering=-name")
        self.assertEqual(response.status_code, 200)


class WatchlistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass-12345")
        self.other = User.objects.create_user("bob", password="pass-12345")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.share = create_share()

    def test_create_watchlist_item(self):
        response = self.client.post(
            "/api/v1/watchlist/", {"share": self.share.id}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WatchlistItem.objects.count(), 1)
        self.assertEqual(WatchlistItem.objects.first().user, self.user)

    def test_duplicate_watchlist_item_rejected(self):
        self.client.post("/api/v1/watchlist/", {"share": self.share.id}, format="json")
        response = self.client.post(
            "/api/v1/watchlist/", {"share": self.share.id}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_isolation_between_users(self):
        WatchlistItem.objects.create(user=self.other, share=self.share)
        response = self.client.get("/api/v1/watchlist/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

    def test_requires_authentication(self):
        anonymous = APIClient()
        response = anonymous.get("/api/v1/watchlist/")
        self.assertEqual(response.status_code, 403)


class PriceAlertTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass-12345")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.share = create_share()

    def test_create_alert_and_validation(self):
        response = self.client.post(
            "/api/v1/alerts/",
            {
                "share": self.share.id,
                "condition": "above",
                "target_price": "150.0000",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        bad = self.client.post(
            "/api/v1/alerts/",
            {"share": self.share.id, "condition": "above", "target_price": "-5"},
            format="json",
        )
        self.assertEqual(bad.status_code, 400)

    def test_alert_triggers_once_and_notifies(self):
        alert = PriceAlert.objects.create(
            user=self.user,
            share=self.share,
            condition=PriceAlert.Condition.ABOVE,
            target_price=Decimal("90"),
        )
        triggered = monitoring_service.check_alerts_for_share(self.share, 95.0)
        self.assertEqual(triggered, 1)
        alert.refresh_from_db()
        self.assertFalse(alert.is_active)
        self.assertIsNotNone(alert.triggered_at)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)

        # Повторный вызов по тому же событию не создаёт дубликат уведомления.
        triggered_again = monitoring_service.check_alerts_for_share(self.share, 96.0)
        self.assertEqual(triggered_again, 0)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)

    def test_below_condition_triggers(self):
        PriceAlert.objects.create(
            user=self.user,
            share=self.share,
            condition=PriceAlert.Condition.BELOW,
            target_price=Decimal("50"),
        )
        triggered = monitoring_service.check_alerts_for_share(self.share, 45.0)
        self.assertEqual(triggered, 1)

    def test_notification_isolation(self):
        other = User.objects.create_user("bob", password="pass-12345")
        PriceAlert.objects.create(
            user=other,
            share=self.share,
            condition=PriceAlert.Condition.ABOVE,
            target_price=Decimal("90"),
        )
        monitoring_service.check_alerts_for_share(self.share, 95.0)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 0)
        self.assertEqual(Notification.objects.filter(user=other).count(), 1)


class PortfolioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass-12345")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.share = create_share()

    def test_buy_and_summary(self):
        portfolio = Portfolio.objects.create(user=self.user, name="Main")
        PortfolioOperation.objects.create(
            portfolio=portfolio,
            share=self.share,
            action=PortfolioOperation.Action.BUY,
            quantity=10,
            price=Decimal("100"),
        )
        PortfolioOperation.objects.create(
            portfolio=portfolio,
            share=self.share,
            action=PortfolioOperation.Action.BUY,
            quantity=10,
            price=Decimal("120"),
        )
        summary = portfolio_service.build_portfolio_summary(portfolio)
        position = summary["positions"][0]
        self.assertEqual(position["quantity"], 20)
        self.assertEqual(position["avg_price"], Decimal("110"))
        self.assertEqual(position["realized_pnl"], Decimal("0"))

    def test_sell_validation_blocks_oversell(self):
        portfolio = Portfolio.objects.create(user=self.user, name="Main")
        response = self.client.post(
            "/api/v1/portfolio-operations/",
            {
                "portfolio": portfolio.id,
                "share": self.share.id,
                "action": "sell",
                "quantity": 5,
                "price": "100",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_sell_vs_average_price(self):
        portfolio = Portfolio.objects.create(user=self.user, name="Main")
        PortfolioOperation.objects.create(
            portfolio=portfolio,
            share=self.share,
            action=PortfolioOperation.Action.BUY,
            quantity=10,
            price=Decimal("100"),
        )
        PortfolioOperation.objects.create(
            portfolio=portfolio,
            share=self.share,
            action=PortfolioOperation.Action.SELL,
            quantity=4,
            price=Decimal("150"),
        )
        summary = portfolio_service.build_portfolio_summary(portfolio)
        position = summary["positions"][0]
        self.assertEqual(position["quantity"], 6)
        self.assertEqual(position["realized_pnl"], Decimal("200"))
        self.assertEqual(position["avg_price"], Decimal("100"))

    def test_operation_history(self):
        portfolio = Portfolio.objects.create(user=self.user, name="Main")
        PortfolioOperation.objects.create(
            portfolio=portfolio,
            share=self.share,
            action=PortfolioOperation.Action.BUY,
            quantity=1,
            price=Decimal("100"),
        )
        response = self.client.get("/api/v1/portfolio-operations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_cannot_operate_foreign_portfolio(self):
        other = User.objects.create_user("bob", password="pass-12345")
        foreign = Portfolio.objects.create(user=other, name="Foreign")
        response = self.client.post(
            "/api/v1/portfolio-operations/",
            {
                "portfolio": foreign.id,
                "share": self.share.id,
                "action": "buy",
                "quantity": 1,
                "price": "100",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class PriceHistoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.share = create_share()

    def _add_point(self, price, offset_seconds=0):
        from django.utils import timezone
        from datetime import timedelta

        record = PriceHistory.objects.create(share=self.share, price=Decimal(str(price)))
        if offset_seconds:
            PriceHistory.objects.filter(pk=record.pk).update(
                recorded_at=timezone.now() + timedelta(seconds=offset_seconds)
            )
        return record

    def test_history_saved_and_listed(self):
        self._add_point(100)
        self._add_point(110)
        response = self.client.get(f"/api/v1/price-history/?share={self.share.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_stats_absolute_and_percent_change(self):
        self._add_point(100, offset_seconds=-600)
        self._add_point(125, offset_seconds=0)
        response = self.client.get(
            f"/api/v1/price-history/stats/?share={self.share.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data["absolute_change"]), Decimal("25"))
        self.assertAlmostEqual(
            float(response.data["percent_change"]), 25.0, places=4
        )

    def test_chart_endpoint(self):
        self._add_point(100)
        response = self.client.get(f"/api/v1/price-history/chart/?share={self.share.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)


class StrategyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass-12345")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.share = create_share()

    def test_strategy_executes_once(self):
        strategy = Strategy.objects.create(
            user=self.user,
            name="Buy low",
            share=self.share,
            action=Strategy.Action.BUY,
            trigger_condition=Strategy.TriggerCondition.BELOW,
            trigger_price=Decimal("90"),
            quantity=5,
        )
        executed = monitoring_service.run_strategies_for_share(self.share, 85.0)
        self.assertEqual(executed, 1)
        strategy.refresh_from_db()
        self.assertFalse(strategy.is_active)
        self.assertEqual(StrategyTrade.objects.count(), 1)

        executed_again = monitoring_service.run_strategies_for_share(self.share, 80.0)
        self.assertEqual(executed_again, 0)
        self.assertEqual(StrategyTrade.objects.count(), 1)

    def test_strategy_creates_portfolio_operation(self):
        portfolio = Portfolio.objects.create(user=self.user, name="Auto")
        Strategy.objects.create(
            user=self.user,
            portfolio=portfolio,
            name="Buy low",
            share=self.share,
            action=Strategy.Action.BUY,
            trigger_condition=Strategy.TriggerCondition.BELOW,
            trigger_price=Decimal("90"),
            quantity=5,
        )
        monitoring_service.run_strategies_for_share(self.share, 85.0)
        self.assertEqual(
            PortfolioOperation.objects.filter(portfolio=portfolio).count(), 1
        )

    def test_effectiveness(self):
        strategy = Strategy.objects.create(
            user=self.user,
            name="Roundtrip",
            share=self.share,
            action=Strategy.Action.BUY,
            trigger_condition=Strategy.TriggerCondition.BELOW,
            trigger_price=Decimal("90"),
            quantity=10,
        )
        monitoring_service.run_strategies_for_share(self.share, 80.0)
        strategy.is_active = True
        strategy.save(update_fields=["is_active"])
        monitoring_service.run_strategies_for_share(self.share, 100.0)

        result = monitoring_service.strategy_effectiveness(strategy)
        self.assertEqual(result["buy_quantity"], 10)
        self.assertEqual(result["sell_quantity"], 10)
        self.assertEqual(result["realized_pnl"], Decimal("200"))

    def test_trade_journal_isolated(self):
        other = User.objects.create_user("bob", password="pass-12345")
        Strategy.objects.create(
            user=other,
            name="Bob strat",
            share=self.share,
            action=Strategy.Action.BUY,
            trigger_condition=Strategy.TriggerCondition.BELOW,
            trigger_price=Decimal("90"),
            quantity=1,
        )
        monitoring_service.run_strategies_for_share(self.share, 80.0)
        response = self.client.get("/api/v1/strategy-trades/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)
