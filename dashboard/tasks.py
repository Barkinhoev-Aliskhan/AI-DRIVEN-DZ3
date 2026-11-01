"""Регламентные задачи Celery."""

from dashboard.models import PriceHistory, Share
from dashboard.services import monitoring_service
from dashboard.services.market_data import get_last_data
from config.celery import app
from config.settings import logger


@app.task
def update_last_price():
    """Обновляет цены акций, пишет историю цен, проверяет алерты и стратегии."""
    for share in Share.objects.all():
        try:
            last_price, price_time = get_last_data(share)
        except Exception as error:
            logger.error(
                "Не удалось получить цену для %s: %s", share.ticker, error
            )
            continue

        previous_price = share.last_price
        is_trend_high = monitoring_service.compute_trend(previous_price, last_price)

        Share.objects.filter(id=share.id).update(
            last_price=last_price,
            is_trend_high=is_trend_high,
            updated_at=price_time,
        )

        PriceHistory.objects.create(share=share, price=last_price)

        try:
            monitoring_service.check_alerts_for_share(share, last_price)
            monitoring_service.run_strategies_for_share(share, last_price)
        except Exception as error:
            logger.error(
                "Ошибка обработки мониторинга для %s: %s", share.ticker, error
            )
