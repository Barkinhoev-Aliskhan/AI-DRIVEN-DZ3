from django.contrib import admin

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


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("figi", "isin", "name", "ticker", "currency")
    search_fields = ("figi", "isin", "name", "ticker")
    fields = (
        "figi",
        "isin",
        "name",
        "ticker",
        "currency",
        "uid",
        "last_price",
        "is_trend_high",
    )
    readonly_fields = ("updated_at",)


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "share", "created_at")
    search_fields = ("user__username", "share__ticker")


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "share", "condition", "target_price", "is_active", "triggered_at")
    search_fields = ("user__username", "share__ticker")
    list_filter = ("condition", "is_active")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    search_fields = ("user__username", "message")
    list_filter = ("is_read",)


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "created_at")
    search_fields = ("user__username", "name")


@admin.register(PortfolioOperation)
class PortfolioOperationAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "share", "action", "quantity", "price", "created_at")
    search_fields = ("portfolio__user__username", "share__ticker")
    list_filter = ("action",)


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("share", "price", "recorded_at")
    search_fields = ("share__ticker",)


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "name",
        "share",
        "action",
        "trigger_condition",
        "trigger_price",
        "quantity",
        "is_active",
    )
    search_fields = ("user__username", "name", "share__ticker")
    list_filter = ("action", "trigger_condition", "is_active")


@admin.register(StrategyTrade)
class StrategyTradeAdmin(admin.ModelAdmin):
    list_display = ("strategy", "share", "action", "price", "quantity", "executed_at")
    search_fields = ("strategy__name", "share__ticker")
    list_filter = ("action",)
