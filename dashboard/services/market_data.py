"""Получение рыночных данных из Tinkoff Invest API.

ВНИМАНИЕ: этот модуль восстановлен по косвенным признакам (вызов get_last_data(share)
из dashboard/tasks.py возвращает [последняя_цена, время]). Сверь с оригинальным файлом
из репозитория и при расхождениях подставь свою реализацию — интерфейс сохранён.
"""

from tinkoff.invest import Client

from config.settings import TINKOFF_TOKEN


def get_last_data(share):
    """Возвращает [последняя цена (float), время котировки] по FIGI акции."""
    with Client(TINKOFF_TOKEN) as client:
        response = client.market_data.get_last_prices(figi=[share.figi])
        if not response.last_prices:
            raise ValueError(f"Нет данных о последней цене для {share.ticker}")
        last_price_item = response.last_prices[0]
        price = last_price_item.price.units + last_price_item.price.nano / 1e9
        return [price, last_price_item.time]
