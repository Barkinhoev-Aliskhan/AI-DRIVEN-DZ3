from config.celery import app
from config.settings import logger
from dashboard.models import Share
from dashboard.services.market_data import get_last_data


@app.task
def update_last_price():
    """Обновляет last_price и is_trend_high для всех акций.

    Дефекты исходной версии, исправленные здесь:
    1) сравнение с None (первый запуск) падало с TypeError, после чего
       флаг безусловно ставился в True — теперь при отсутствии старой цены
       флаг остаётся None (тренд неизвестен);
    2) при ошибке получения цены запись больше не трогается вообще,
       а не перезаписывается ложным значением флага.
    """
    for share in Share.objects.all():
        try:
            last_price, _received_at = get_last_data(share)
        except Exception as e:  # noqa: BLE001 — сеть/API могут дать любую ошибку
            logger.error(f"Не удалось получить цену для {share.ticker}: {e}")
            continue

        old_price = share.last_price
        if old_price is None:
            is_trend_high = None
        else:
            is_trend_high = last_price > old_price

        Share.objects.filter(id=share.id).update(
            last_price=last_price, is_trend_high=is_trend_high
        )
