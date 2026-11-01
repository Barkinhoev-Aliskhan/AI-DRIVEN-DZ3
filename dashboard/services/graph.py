"""Построение графиков цены акции."""

from datetime import timedelta

from plotly.graph_objs import Scatter
from plotly.offline import plot
from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now

from config.settings import TINKOFF_TOKEN, logger


def _render(traces) -> str:
    """Единый рендер: скрипт plotly подключается с CDN."""
    return plot(traces, output_type="div", include_plotlyjs="cdn")


def _fetch_candles(client, figi, days=180):
    x_data, y_data = [], []
    for candle in client.get_all_candles(
        figi=figi,
        from_=now() - timedelta(days=days),
        interval=CandleInterval.CANDLE_INTERVAL_DAY,
    ):
        x_data.append(candle.time.date())
        y_data.append(candle.close.units + candle.close.nano / 1_000_000_000)
    return x_data, y_data


def get_graph(share) -> str:
    """HTML-фрагмент с графиком цены закрытия за 180 дней; при ошибке — пустая строка."""
    try:
        with Client(TINKOFF_TOKEN) as client:
            x_data, y_data = _fetch_candles(client, share.figi)
    except Exception as e:
        logger.error(f"Failed to build graph for share {share.id}: {e}")
        return ""

    if not x_data:
        return ""
    return _render(
        [Scatter(x=x_data, y=y_data, mode="lines", name="close", opacity=0.8, marker_color="red")]
    )


def get_history_graph(history) -> str:
    """График по накопленной истории цен из БД (FR-34)."""
    x_data = [h.recorded_at for h in history]
    y_data = [h.price for h in history]
    if not x_data:
        return ""
    return _render(
        [Scatter(x=x_data, y=y_data, mode="lines", name="price", opacity=0.8, marker_color="blue")]
    )
