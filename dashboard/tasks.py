from tinkoff.invest import Client

from config.celery import app
from config.settings import TINKOFF_TOKEN, logger
from dashboard.models import Share
from dashboard.services.market_data import get_last_price, resolve_trend


def _save_history(share, price):
    """Сохраняет запись в историю цен (FR-31)."""
    try:
        from tracker.models import PriceHistory

        PriceHistory.objects.create(share=share, price=price)
    except Exception as e:
        logger.error(f"Failed to save price history for share {share.id}: {e}")


def _process_tracker(share, previous_price, new_price):
    """Запускает мониторинг и стратегии (FR-22, FR-36). Ленивый импорт."""
    try:
        from tracker.services import process_price_update

        process_price_update(share, previous_price, new_price)
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Tracker processing failed for share {share.id}: {e}")


@app.task
def update_last_price():
    """Обновляет последнюю цену и тренд для всех акций.

    Одно gRPC-соединение на весь пакет. При ошибке по одной акции остальные
    продолжают обновляться. После успешного обновления записывается история
    цен и запускаются мониторинг и стратегии.
    """
    shares = list(Share.objects.all())
    if not shares:
        return

    with Client(TINKOFF_TOKEN) as client:
        for share in shares:
            previous_price = share.last_price
            try:
                price = get_last_price(client, share)
                share.last_price = price
                share.is_trend_high = resolve_trend(previous_price, price)
                share.save(update_fields=["last_price", "is_trend_high", "updated_at"])
                _save_history(share, price)
                _process_tracker(share, previous_price, price)
            except Exception as e:
                logger.error(f"Failed to update share {share.id}: {e}")
