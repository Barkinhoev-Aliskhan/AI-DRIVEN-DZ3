"""Расчёты виртуального портфеля: позиции, средняя цена, P&L."""

from decimal import Decimal

from django.core.exceptions import ValidationError

from dashboard.models import PortfolioOperation

BUY = PortfolioOperation.Action.BUY
SELL = PortfolioOperation.Action.SELL


def get_net_quantity(portfolio, share):
    """Чистая позиция (количество) по акции в портфеле."""
    operations = PortfolioOperation.objects.filter(portfolio=portfolio, share=share)
    net = 0
    for operation in operations:
        if operation.action == BUY:
            net += operation.quantity
        else:
            net -= operation.quantity
    return net


def build_portfolio_summary(portfolio):
    """Возвращает сводку портфеля по позициям с методологией средней цены.

    Логика:
      - покупка: увеличивает позицию, пересчитывает среднюю цену как
        полная стоимость закупки / суммарное количество;
      - продажа: фиксирует реализованный P&L относительно текущей
        средней цены и уменьшает позицию (средняя цена не меняется).
    """
    operations = (
        PortfolioOperation.objects.filter(portfolio=portfolio)
        .select_related("share")
        .order_by("created_at", "id")
    )

    positions = {}
    for operation in operations:
        key = operation.share_id
        position = positions.setdefault(
            key,
            {
                "share": operation.share,
                "quantity": 0,
                "avg_price": Decimal("0"),
                "total_cost": Decimal("0"),
                "realized_pnl": Decimal("0"),
            },
        )
        if operation.action == BUY:
            new_quantity = position["quantity"] + operation.quantity
            position["total_cost"] += operation.price * operation.quantity
            position["avg_price"] = position["total_cost"] / new_quantity
            position["quantity"] = new_quantity
        else:
            sellable = min(operation.quantity, position["quantity"])
            position["realized_pnl"] += (operation.price - position["avg_price"]) * sellable
            position["total_cost"] -= position["avg_price"] * sellable
            position["quantity"] -= sellable

    items = []
    total_value = Decimal("0")
    total_unrealized = Decimal("0")
    total_realized = Decimal("0")
    has_unknown_price = False

    for position in positions.values():
        share = position["share"]
        last_price = share.last_price
        realized = position["realized_pnl"]
        total_realized += realized

        if position["quantity"] > 0:
            if last_price is None:
                has_unknown_price = True
                market_value = None
                unrealized = None
            else:
                last_decimal = Decimal(str(last_price))
                market_value = last_decimal * position["quantity"]
                unrealized = (last_decimal - position["avg_price"]) * position["quantity"]
                total_value += market_value
                if unrealized is not None:
                    total_unrealized += unrealized
        else:
            market_value = None
            unrealized = None

        items.append(
            {
                "share_id": share.id,
                "ticker": share.ticker,
                "quantity": position["quantity"],
                "avg_price": position["avg_price"],
                "last_price": last_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized,
                "realized_pnl": realized,
            }
        )

    return {
        "positions": items,
        "totals": {
            "market_value": total_value,
            "unrealized_pnl": total_unrealized,
            "realized_pnl": total_realized,
            "has_unknown_price": has_unknown_price,
        },
    }


def validate_operation(portfolio, share, action, quantity):
    """Бизнес-правило: нельзя продать больше, чем есть в портфеле."""
    if action == SELL:
        net = get_net_quantity(portfolio, share)
        if quantity > net:
            raise ValidationError(
                f"Недостаточно акций {share.ticker} в портфеле: "
                f"доступно {net}, продаётся {quantity}."
            )
