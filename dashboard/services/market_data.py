"""Работа с рыночными данными Tinkoff Invest API."""

from tinkoff.invest import Client

from config.settings import TINKOFF_TOKEN, logger


def quotation_to_float(quotation) -> float:
    """Переводит Quotation (units + nano) в float."""
    return quotation.units + quotation.nano / 1_000_000_000


def resolve_trend(previous_price, new_price):
    """Определяет направление изменения цены.

    Возвращает None, если предыдущей цены нет (тренд неизвестен),
    иначе True (цена не упала) или False (цена упала).
    """
    if previous_price is None:
        return None
    return new_price >= previous_price


def get_last_price(client, share) -> float:
    """Получает последнюю цену акции через переданного клиента."""
    resp = client.market_data.get_last_prices(figi=[share.figi])
    price = resp.last_prices.pop()
    logger.info(f"Get last data for share with id {share.id}")
    return quotation_to_float(price.price)


def get_last_data(share):
    """Совместимая обёртка: открывает клиента и возвращает [цена, время]."""
    with Client(TINKOFF_TOKEN) as client:
        resp = client.market_data.get_last_prices(figi=[share.figi])
        item = resp.last_prices.pop()
        logger.info(f"Get last data for share with id {share.id}")
        return [quotation_to_float(item.price), item.time]
