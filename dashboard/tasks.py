"""Фоновые задачи Celery."""

from tinkoff.invest import Client

from config.celery import app
from config.settings import TINKOFF_TOKEN, logger
from dashboard.models import Share
from dashboard.services.market_data import get_last_price, resolve_trend


@app.task
def update_last_price():
    """Обновляет последнюю цену и тренд для всех акций.

    Использует одно gRPC-соединение на весь пакет. При ошибке по одной
    акции остальные продолжают обновляться.
    """
    shares = list(Share.objects.all())
    if not shares:
        return

    with Client(TINKOFF_TOKEN) as client:
        for share in shares:
            try:
                price = get_last_price(client, share)
                trend = resolve_trend(share.last_price, price)
                share.last_price = price
                share.is_trend_high = trend
                share.save(update_fields=["last_price", "is_trend_high", "updated_at"])
            except Exception as e:
                logger.error(f"Failed to update share {share.id}: {e}")
