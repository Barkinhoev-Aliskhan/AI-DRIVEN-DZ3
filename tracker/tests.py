from django.test import TestCase

from tracker.logic import (
    apply_buy,
    apply_sell,
    calculate_position,
    price_change,
    should_execute,
    should_notify,
)


class ShouldNotifyTests(TestCase):
    """FR-23: уведомление только при пересечении уровня."""

    def test_crossing_up_notifies(self):
        self.assertTrue(should_notify(89.0, 91.0, 90.0, "above"))

    def test_no_crossing_no_notify(self):
        self.assertFalse(should_notify(95.0, 96.0, 90.0, "above"))

    def test_exact_level_notifies(self):
        self.assertTrue(should_notify(89.9, 90.0, 90.0, "above"))

    def test_first_price_no_notify(self):
        self.assertFalse(should_notify(None, 100.0, 90.0, "above"))

    def test_below_direction(self):
        self.assertTrue(should_notify(101.0, 99.0, 100.0, "below"))
        self.assertFalse(should_notify(99.0, 98.0, 100.0, "below"))


class PriceChangeTests(TestCase):
    """FR-33: абсолютное и процентное изменение."""

    def test_positive_change(self):
        result = price_change(100.0, 110.0)
        self.assertAlmostEqual(result["absolute"], 10.0)
        self.assertAlmostEqual(result["percent"], 10.0)

    def test_negative_change(self):
        result = price_change(100.0, 90.0)
        self.assertAlmostEqual(result["absolute"], -10.0)
        self.assertAlmostEqual(result["percent"], -10.0)

    def test_zero_first_price(self):
        result = price_change(0.0, 50.0)
        self.assertAlmostEqual(result["absolute"], 50.0)
        self.assertIsNone(result["percent"])


class ApplyBuySellTests(TestCase):
    """FR-28: взвешенная средняя и реализованный P&L."""

    def test_weighted_average(self):
        qty, avg = apply_buy(0.0, 0.0, 10, 100.0)
        qty, avg = apply_buy(qty, avg, 10, 110.0)
        self.assertEqual(qty, 20)
        self.assertAlmostEqual(avg, 105.0)

    def test_sell_profit(self):
        qty, profit = apply_sell(20, 105.0, 5, 120.0)
        self.assertEqual(qty, 15)
        self.assertAlmostEqual(profit, 75.0)

    def test_sell_more_than_owned(self):
        qty, profit = apply_sell(3, 100.0, 10, 110.0)
        self.assertEqual(qty, 0)
        self.assertAlmostEqual(profit, 30.0)

    def test_sell_from_empty_position(self):
        qty, profit = apply_sell(0, 0.0, 5, 110.0)
        self.assertEqual(qty, 0)
        self.assertAlmostEqual(profit, 0.0)


class CalculatePositionTests(TestCase):
    """FR-28..30: позиции пересчитываются из журнала."""

    def _tx(self, share_id, quantity, price):
        return type("Tx", (), {"share_id": share_id, "quantity": quantity, "price": price})()

    def test_positions_and_realized(self):
        transactions = [
            self._tx(1, 10, 100.0),
            self._tx(1, 10, 110.0),
            self._tx(1, -5, 120.0),
            self._tx(2, 4, 50.0),
        ]
        positions, realized = calculate_position(transactions)
        self.assertEqual(positions[1], (15.0, 105.0))
        self.assertEqual(positions[2], (4.0, 50.0))
        self.assertAlmostEqual(realized, 75.0)

    def test_deletion_recomputed(self):
        """FR-30: после удаления операции позиции пересчитываются из остатка журнала."""
        all_txs = [self._tx(1, 10, 100.0), self._tx(1, 10, 110.0)]
        positions, _ = calculate_position(all_txs)
        self.assertEqual(positions[1], (20.0, 105.0))
        remaining = all_txs[:1]  # удалили вторую операцию
        positions, _ = calculate_position(remaining)
        self.assertEqual(positions[1], (10.0, 100.0))


class ShouldExecuteTests(TestCase):
    """FR-36: условия сделок стратегий."""

    def test_buy_triggered(self):
        self.assertTrue(should_execute("buy", 100.0, 99.0))

    def test_buy_not_triggered(self):
        self.assertFalse(should_execute("buy", 100.0, 101.0))

    def test_sell_triggered(self):
        self.assertTrue(should_execute("sell", 120.0, 121.0))

    def test_sell_not_triggered(self):
        self.assertFalse(should_execute("sell", 120.0, 119.0))
