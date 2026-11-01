"""Чистая бизнес-логика трекера — без Django, покрывается юнит-тестами."""


def should_notify(previous_price, new_price, target_price, direction):
    """Решает, пересекли ли цену целевой уровень (FR-23, без дублей).

    Уведомление только при пересечении: цена была с одной стороны уровня,
    стала с другой. Если предыдущей цены нет — событие не фиксируется.
    """
    if previous_price is None or new_price is None:
        return False
    if direction == "above":
        return previous_price < target_price <= new_price
    if direction == "below":
        return previous_price > target_price >= new_price
    return False


def price_change(first_price, last_price):
    """Абсолютное и процентное изменение (FR-33). Процент None при нулевой цене."""
    absolute = last_price - first_price
    if first_price == 0:
        percent = None
    else:
        percent = absolute / first_price * 100
    return {"absolute": absolute, "percent": percent}


def should_execute(action, trigger_price, price):
    """Условие сделки стратегии (FR-36): покупка — цена <= триггера, продажа — >=."""
    if action == "buy":
        return price <= trigger_price
    if action == "sell":
        return price >= trigger_price
    return False


def apply_buy(position_qty, avg_price, qty, price):
    """Покупка: взвешенная средняя цена (FR-28). Возвращает (qty, avg)."""
    total = position_qty + qty
    new_avg = ((avg_price or 0.0) * position_qty + price * qty) / total
    return total, new_avg


def apply_sell(position_qty, avg_price, qty, price):
    """Продажа: реализованный P&L (FR-28). Возвращает (qty, profit). Продажа не превышает остаток."""
    sell_qty = min(qty, position_qty)
    profit = (price - avg_price) * sell_qty if position_qty > 0 else 0.0
    return position_qty - sell_qty, profit


def calculate_position(transactions):
    """Позиции {share_id: (qty, avg)} и реализованный P&L из журнала операций (FR-28..30).

    Позиции всегда пересчитываются на лету — денормализация исключена.
    """
    positions = {}
    realized = 0.0
    for t in transactions:
        qty, avg = positions.get(t.share_id, (0.0, 0.0))
        if t.quantity > 0:
            qty, avg = apply_buy(qty, avg, t.quantity, t.price)
        else:
            qty, profit = apply_sell(qty, avg, -t.quantity, t.price)
            realized += profit
        positions[t.share_id] = (qty, avg)
    return positions, realized
