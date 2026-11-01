"""Построение графика цены акции."""

from datetime import timedelta

from plotly.graph_objs import Scatter
from plotly.offline import plot
from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now

from config.settings import TINKOFF_TOKEN, logger

from .market_data import quotation_to_float


def get_graph(share) -> str:
    """Возвращает HTML-фрагмент с графиком цены закрытия за 180 дней.

    При ошибке API возвращает пустую строку, не ломая страницу.
    """
    try:
        with Client(TINKOFF_TOKEN) as client:
            x_data, y_data = [], []
            for candle in client.get_all_candles(
                figi=share.figi,
                from_=now() - timedelta(days=180),
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
            ):
                x_data.append(candle.time.date())
                y_data.append(quotation_to_float(candle.close))
    except Exception as e:
        logger.error(f"Failed to build graph for share {share.id}: {e}")
        return ""

    return plot(
        [Scatter(x=x_data, y=y_data, mode="lines", name="close", opacity=0.8, marker_color="red")],
        output_type="div",
        include_plotlyjs=False,
    )
