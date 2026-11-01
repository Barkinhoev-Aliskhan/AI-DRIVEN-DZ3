"""Получение рыночных данных через Tinkoff Invest API.

ВНИМАНИЕ: этот модуль восстановлен по интерфейсу вызова из исходного
проекта (get_last_data(share) -> [цена, время]). Перед сдачей сверьте
его с вашим оригиналом dashboard/services/market_data.py.
"""

from django.utils import timezone
from tinkoff.invest import Client

from config.settings import TINKOFF_TOKEN


def _quotation_to_float(quotation):
    """Переводит Quotation (units + nano) в float."""
    return float(quotation.units) + quotation.nano / 1e9


def get_last_data(share):
    """Возвращает [последняя цена, время фиксации] для акции по её FIGI.

    Бросает исключение, если данных по инструменту нет.
    """
    with Client(TINKOFF_TOKEN) as client:
        response = client.market_data.get_last_prices(figi=[share.figi])

    if not response.last_prices:
        raise ValueError(f"Нет данных о цене для FIGI {share.figi}")

    item = response.last_prices[0]
    return [_quotation_to_float(item.price), timezone.now()]
