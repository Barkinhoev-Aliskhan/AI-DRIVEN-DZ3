"""REST API приложения.

Публичные данные рынка (список акций, история цен) доступны без
аутентификации; персональные сущности (списки наблюдения, алерты,
уведомления, портфели, стратегии) требуют аутентификации и изолируются
по владельцу.
"""

import json

from django_filters import rest_framework as filters
from plotly import graph_objects as go
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from dashboard.models import (
    Notification,
    Portfolio,
    PortfolioOperation,
    PriceAlert,
    PriceHistory,
    Share,
    Strategy,
    StrategyTrade,
    WatchlistItem,
)
from dashboard.services import monitoring_service, portfolio_service
from dashboard.filters import ShareFilter
from dashboard.serializers import (
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


class ShareViewSet(viewsets.ModelViewSet):
    """CRUD акций с фильтрацией, поиском и сортировкой."""

    serializer_class = ShareSerializer
    queryset = Share.objects.all()
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend, SearchFilter)
    filterset_class = ShareFilter
    ordering_fields = ["name", "ticker", "updated_at"]
    search_fields = ["figi", "isin", "name", "ticker"]


class WatchlistItemViewSet(viewsets.ModelViewSet):
    """Персональный список наблюдения за акциями."""

    serializer_class = WatchlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            WatchlistItem.objects.filter(user=self.request.user)
            .select_related("share")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PriceAlertViewSet(viewsets.ModelViewSet):
    """Целевые уровни цены с автоматическими уведомлениями."""

    serializer_class = PriceAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            PriceAlert.objects.filter(user=self.request.user)
            .select_related("share")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Уведомления пользователя: просмотр, отметка о прочтении, удаление."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related(
            "alert__share"
        )


class PortfolioViewSet(viewsets.ModelViewSet):
    """Виртуальные инвестиционные портфели пользователя."""

    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """Текущая стоимость, прибыль и убытки портфеля."""
        portfolio = self.get_object()
        return Response(portfolio_service.build_portfolio_summary(portfolio))


class PortfolioOperationViewSet(viewsets.ModelViewSet):
    """История виртуальных операций покупки/продажи акций."""

    serializer_class = PortfolioOperationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            PortfolioOperation.objects.filter(portfolio__user=self.request.user)
            .select_related("portfolio", "share")
            .order_by("-created_at")
        )


class PriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """История изменения цен акций за выбранные периоды."""

    serializer_class = PriceHistorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = PriceHistory.objects.select_related("share").order_by("-recorded_at")
        params = self.request.query_params
        share_id = params.get("share")
        if share_id:
            queryset = queryset.filter(share_id=share_id)
        date_from = params.get("date_from")
        if date_from:
            queryset = queryset.filter(recorded_at__gte=date_from)
        date_to = params.get("date_to")
        if date_to:
            queryset = queryset.filter(recorded_at__lte=date_to)
        return queryset

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Абсолютное и процентное изменение цены за период."""
        queryset = list(self.get_queryset())
        if not queryset:
            return Response({"detail": "Нет данных за выбранный период."})
        first_point = queryset[-1]
        last_point = queryset[0]
        first_price = first_point.price
        last_price = last_point.price
        absolute_change = last_price - first_price
        if first_price:
            percent_change = absolute_change / first_price * 100
        else:
            percent_change = None
        return Response(
            {
                "share_id": first_point.share_id,
                "ticker": first_point.share.ticker,
                "points_count": len(queryset),
                "first_recorded_at": first_point.recorded_at,
                "first_price": first_price,
                "last_recorded_at": last_point.recorded_at,
                "last_price": last_price,
                "absolute_change": absolute_change,
                "percent_change": percent_change,
            }
        )

    @action(detail=False, methods=["get"])
    def chart(self, request):
        """Данные для графика изменения цены (JSON, plotly)."""
        queryset = self.get_queryset().order_by("recorded_at")
        points = list(queryset)
        if not points:
            return Response({"data": []})
        figure = go.Figure(
            data=go.Scatter(
                x=[point.recorded_at for point in points],
                y=[float(point.price) for point in points],
                mode="lines+markers",
                name=points[0].share.ticker,
            )
        )
        figure.update_layout(
            title=f"Изменение цены {points[0].share.ticker}",
            xaxis_title="Время",
            yaxis_title="Цена",
        )
        return Response(json.loads(figure.to_json()))


class StrategyViewSet(viewsets.ModelViewSet):
    """Симуляционные стратегии покупки/продажи акций."""

    serializer_class = StrategySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Strategy.objects.filter(user=self.request.user)
            .select_related("share", "portfolio")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def effectiveness(self, request, pk=None):
        """Оценка эффективности стратегии по журналу сделок."""
        strategy = self.get_object()
        return Response(monitoring_service.strategy_effectiveness(strategy))


class StrategyTradeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Журнал виртуальных сделок стратегий пользователя."""

    serializer_class = StrategyTradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            StrategyTrade.objects.filter(strategy__user=self.request.user)
            .select_related("strategy", "share")
            .order_by("-executed_at")
        )
