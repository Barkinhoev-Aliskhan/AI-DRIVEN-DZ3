from rest_framework import serializers

from dashboard.services import portfolio_service
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


class ShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share
        fields = (
            "id",
            "figi",
            "isin",
            "name",
            "ticker",
            "currency",
            "last_price",
            "is_trend_high",
            "updated_at",
        )


class WatchlistItemSerializer(serializers.ModelSerializer):
    share_detail = ShareSerializer(source="share", read_only=True)

    class Meta:
        model = WatchlistItem
        fields = ("id", "share", "share_detail", "created_at")

    def validate(self, attrs):
        request = self.context.get("request")
        share = attrs.get("share")
        if (
            request is not None
            and share is not None
            and WatchlistItem.objects.filter(user=request.user, share=share).exists()
        ):
            raise serializers.ValidationError(
                {"share": "Эта акция уже есть в вашем списке наблюдения."}
            )
        return attrs


class PriceAlertSerializer(serializers.ModelSerializer):
    share_detail = ShareSerializer(source="share", read_only=True)

    class Meta:
        model = PriceAlert
        fields = (
            "id",
            "share",
            "share_detail",
            "condition",
            "target_price",
            "is_active",
            "triggered_at",
            "created_at",
        )

    def validate_target_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Целевая цена должна быть больше нуля.")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "alert", "message", "is_read", "created_at")
        read_only_fields = ("alert", "message", "created_at")


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ("id", "name", "created_at")

    def validate_name(self, value):
        request = self.context.get("request")
        if (
            request is not None
            and Portfolio.objects.filter(user=request.user, name=value).exists()
        ):
            raise serializers.ValidationError("Портфель с таким названием уже существует.")
        return value


class PortfolioOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioOperation
        fields = ("id", "portfolio", "share", "action", "quantity", "price", "created_at")
        read_only_fields = ("created_at",)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Количество должно быть больше нуля.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Цена операции должна быть больше нуля.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        portfolio = attrs.get("portfolio")
        share = attrs.get("share")
        action_value = attrs.get("action")
        quantity = attrs.get("quantity")

        if request is not None and portfolio is not None and portfolio.user != request.user:
            raise serializers.ValidationError(
                {"portfolio": "Нельзя добавлять операции в чужой портфель."}
            )

        if action_value == PortfolioOperation.Action.SELL and portfolio and share:
            net = portfolio_service.get_net_quantity(portfolio, share)
            if quantity > net:
                raise serializers.ValidationError(
                    {
                        "quantity": (
                            f"Недостаточно акций {share.ticker} в портфеле: "
                            f"доступно {net}, продаётся {quantity}."
                        )
                    }
                )
        return attrs


class PriceHistorySerializer(serializers.ModelSerializer):
    share_ticker = serializers.CharField(source="share.ticker", read_only=True)

    class Meta:
        model = PriceHistory
        fields = ("id", "share", "share_ticker", "price", "recorded_at")


class StrategySerializer(serializers.ModelSerializer):
    share_detail = ShareSerializer(source="share", read_only=True)

    class Meta:
        model = Strategy
        fields = (
            "id",
            "user",
            "portfolio",
            "name",
            "share",
            "share_detail",
            "action",
            "trigger_condition",
            "trigger_price",
            "quantity",
            "is_active",
            "created_at",
        )
        read_only_fields = ("user", "is_active")

    def validate_trigger_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Пороговая цена должна быть больше нуля.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        portfolio = attrs.get("portfolio")
        if request is not None and portfolio is not None and portfolio.user != request.user:
            raise serializers.ValidationError(
                {"portfolio": "Нельзя привязать стратегию к чужому портфелю."}
            )
        return attrs


class StrategyTradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyTrade
        fields = ("id", "strategy", "share", "action", "price", "quantity", "executed_at")
