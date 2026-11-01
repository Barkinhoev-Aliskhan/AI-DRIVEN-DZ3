"""Сервисный слой трекера — работа с БД. Чистая логика живёт в logic.py."""

from tracker.logic import apply_buy, apply_sell, should_execute, should_notify
from tracker.models import Notification, Strategy, StrategyLog


def notify_price_update(share, previous_price, new_price):
    """Проверяет активные наблюдения и создаёт уведомления без дублей (FR-22, FR-23)."""
    items = share.watch_items.filter(is_active=True).select_related("user")
    for item in items:
        if should_notify(previous_price, new_price, item.target_price, item.direction):
            Notification.objects.create(
                user=item.user,
                watch_item=item,
                message=(
                    f"{share.ticker} ({share.name}): цена {new_price:.2f} {share.currency} "
                    f"{'выше' if item.direction == 'above' else 'ниже'} целевого уровня "
                    f"{item.target_price:.2f}"
                ),
            )
            item.is_active = False
            item.save(update_fields=["is_active"])


def run_strategy(strategy, price):
    """Исполняет стратегию по текущей цене (FR-36..38). Возвращает True, если сделка исполнена."""
    if strategy.trades_done >= strategy.trades_limit:
        return False
    if not should_execute(strategy.action, strategy.trigger_price, price):
        return False
    if strategy.action == "sell" and strategy.position_qty <= 0:
        return False

    qty = strategy.quantity
    profit = None
    if strategy.action == "buy":
        strategy.position_qty, strategy.avg_price = apply_buy(
            strategy.position_qty, strategy.avg_price, qty, price
        )
    else:
        strategy.position_qty, profit = apply_sell(
            strategy.position_qty, strategy.avg_price, qty, price
        )
        strategy.realized_pnl += profit

    strategy.trades_done += 1
    strategy.save()
    StrategyLog.objects.create(
        strategy=strategy, action=strategy.action, price=price, quantity=qty, profit=profit
    )
    return True


def run_strategies(share, price):
    """Автосделки по всем активным стратегиям акции (FR-36)."""
    for strategy in share.strategies.filter(is_active=True):
        run_strategy(strategy, price)


def process_price_update(share, previous_price, new_price):
    """Единая точка вызова из фоновой задачи: мониторинг + стратегии."""
    notify_price_update(share, previous_price, new_price)
    run_strategies(share, new_price)
