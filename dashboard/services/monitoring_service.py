"""Проверка целевых уровней (алертов) и исполнение стратегий."""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from dashboard.models import (
    Notification,
    PortfolioOperation,
    PriceAlert,
    Strategy,
    StrategyTrade,
)


def compute_trend(previous_price, new_price):
    """Определяет признак роста цены.

    Возвращает None, если предыдущей цены ещё нет (первый замер) —
    флаг тренда в этом случае считается недостоверным.
    """
    if previous_price is None:
        return None
    return new_price > previous_price


def condition_met(condition, price, target):
    """Проверяет условие "цена выше/ниже цели"."""
    price = Decimal(str(price))
    if condition == PriceAlert.Condition.ABOVE:
        return price >= target
    return price <= target


def check_alerts_for_share(share, price):
    """Обходит активные алерты акции и создаёт уведомления о срабатываниях.

    Исключает дублирование: алерт деактивируется при первом срабатывании,
    поэтому повторный вызов по тому же событию уведомление не создаёт.
    """
    triggered = 0
    active_alerts = PriceAlert.objects.filter(share=share, is_active=True).select_related("user")
    for alert in active_alerts:
        if not condition_met(alert.condition, price, alert.target_price):
            continue
        with transaction.atomic():
            updated = PriceAlert.objects.filter(pk=alert.pk, is_active=True).update(
                is_active=False, triggered_at=timezone.now()
            )
            if not updated:
                # Алерт уже деактивирован параллельной задачей — пропускаем.
                continue
            direction = "выше" if alert.condition == PriceAlert.Condition.ABOVE else "ниже"
            Notification.objects.create(
                user=alert.user,
                alert=alert,
                message=(
                    f"Активировано уведомление: {share.ticker} {direction} цели "
                    f"{alert.target_price} (текущая цена {price})."
                ),
            )
            triggered += 1
    return triggered


def run_strategies_for_share(share, price):
    """Исполняет активные стратегии по акции при выполнении их условий.

    Стратегия одноразовая: после срабатывания деактивируется, чтобы
    по одному условию не создавались дублирующие виртуальные сделки.
    Если стратегия привязана к портфелю, дополнительно создаётся
    виртуальная операция покупки/продажи.
    """
    executed = 0
    active_strategies = Strategy.objects.filter(share=share, is_active=True).select_related("user")
    for strategy in active_strategies:
        if not condition_met(strategy.trigger_condition, price, strategy.trigger_price):
            continue
        with transaction.atomic():
            updated = Strategy.objects.filter(pk=strategy.pk, is_active=True).update(
                is_active=False
            )
            if not updated:
                continue
            StrategyTrade.objects.create(
                strategy=strategy,
                share=share,
                action=strategy.action,
                price=Decimal(str(price)),
                quantity=strategy.quantity,
            )
            if strategy.portfolio is not None:
                PortfolioOperation.objects.create(
                    portfolio=strategy.portfolio,
                    share=share,
                    action=strategy.action,
                    quantity=strategy.quantity,
                    price=Decimal(str(price)),
                )
            executed += 1
    return executed


def strategy_effectiveness(strategy):
    """Оценивает эффективность стратегии по её журналу сделок.

    Средняя цена закупки пересчитывается только по покупкам; продажи
    фиксируют реализованный P&L относительно текущей средней цены.
    """
    trades = list(strategy.trades.order_by("executed_at", "id"))

    buy_quantity = 0
    buy_cost = Decimal("0")
    avg_buy_price = Decimal("0")
    sell_quantity = 0
    sell_proceeds = Decimal("0")
    realized_pnl = Decimal("0")

    for trade in trades:
        if trade.action == Strategy.Action.BUY:
            buy_quantity += trade.quantity
            buy_cost += trade.price * trade.quantity
            avg_buy_price = buy_cost / buy_quantity if buy_quantity else Decimal("0")
        else:
            sellable = min(trade.quantity, buy_quantity - sell_quantity)
            sell_quantity += sellable
            sell_proceeds += trade.price * sellable
            realized_pnl += (trade.price - avg_buy_price) * sellable

    open_quantity = buy_quantity - sell_quantity
    return {
        "trades_count": len(trades),
        "buy_quantity": buy_quantity,
        "buy_cost": buy_cost,
        "avg_buy_price": avg_buy_price,
        "sell_quantity": sell_quantity,
        "sell_proceeds": sell_proceeds,
        "realized_pnl": realized_pnl,
        "open_quantity": open_quantity,
        "open_cost_basis": avg_buy_price * open_quantity,
    }
