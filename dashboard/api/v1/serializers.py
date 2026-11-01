"""Совместимость со старыми путями импорта сериализаторов."""

from dashboard.serializers import (  # noqa: F401
    NotificationSerializer,
    PortfolioOperationSerializer,
    PortfolioSerializer,
    PriceAlertSerializer,
    PriceHistorySerializer,
    ShareSerializer,
    StrategySerializer,
    StrategyTradeSerializer,
    WatchlistItemSerializer,
)
