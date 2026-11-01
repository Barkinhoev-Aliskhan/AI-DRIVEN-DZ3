from django.conf import settings
from django.db import models

from dashboard.models import Share


class WatchItem(models.Model):
    """Элемент персонального мониторинга (FR-20)."""

    DIRECTION_ABOVE = "above"
    DIRECTION_BELOW = "below"
    DIRECTION_CHOICES = (
        (DIRECTION_ABOVE, "Цена выше целевой"),
        (DIRECTION_BELOW, "Цена ниже целевой"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watch_items"
    )
    share = models.ForeignKey(Share, on_delete=models.CASCADE, related_name="watch_items")
    target_price = models.FloatField(verbose_name="Целевая цена")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name="Условие")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "share"), name="unique_watch_item_per_user_share"
            )
        ]
        verbose_name = "Наблюдение"
        verbose_name_plural = "Наблюдения"

    def __str__(self):
        return f"{self.user} → {self.share.ticker} ({self.get_direction_display()} {self.target_price})"


class Notification(models.Model):
    """Уведомление о срабатывании наблюдения (FR-24)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    watch_item = models.ForeignKey(WatchItem, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return f"{self.user}: {self.message[:50]}"


class Portfolio(models.Model):
    """Виртуальный инвестиционный портфель (FR-25)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolios"
    )
    name = models.CharField(max_length=100, verbose_name="Название")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "name"), name="unique_portfolio_per_user")
        ]
        verbose_name = "Портфель"
        verbose_name_plural = "Портфели"

    def __str__(self):
        return f"{self.user}: {self.name}"


class Transaction(models.Model):
    """Операция покупки/продажи в портфеле (FR-26)."""

    BUY = "buy"
    SELL = "sell"
    ACTION_CHOICES = ((BUY, "Покупка"), (SELL, "Продажа"))

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="transactions")
    share = models.ForeignKey(Share, on_delete=models.CASCADE, related_name="transactions")
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.FloatField(verbose_name="Цена")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Операция"
        verbose_name_plural = "Операции"

    def __str__(self):
        return f"{self.get_action_display()} {self.quantity} x {self.share.ticker} @ {self.price}"


class PriceHistory(models.Model):
    """История изменения рыночных цен (FR-31)."""

    share = models.ForeignKey(Share, on_delete=models.CASCADE, related_name="price_history")
    price = models.FloatField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("recorded_at",)
        indexes = [
            models.Index(fields=("share", "recorded_at"), name="pricehistory_share_recorded_idx")
        ]
        verbose_name = "Историческая цена"
        verbose_name_plural = "Исторические цены"

    def __str__(self):
        return f"{self.share.ticker}: {self.price} @ {self.recorded_at}"


class Strategy(models.Model):
    """Симулятор стратегии: одно действие на стратегию (FR-35)."""

    ACTION_BUY = "buy"
    ACTION_SELL = "sell"
    ACTION_CHOICES = ((ACTION_BUY, "Покупка"), (ACTION_SELL, "Продажа"))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="strategies"
    )
    share = models.ForeignKey(Share, on_delete=models.CASCADE, related_name="strategies")
    action = models.CharField(max_length=4, choices=ACTION_CHOICES, verbose_name="Действие")
    trigger_price = models.FloatField(verbose_name="Триггерная цена")
    quantity = models.PositiveIntegerField(verbose_name="Объём сделки")
    trades_limit = models.PositiveIntegerField(default=10, verbose_name="Лимит сделок")
    trades_done = models.PositiveIntegerField(default=0, verbose_name="Исполнено сделок")
    position_qty = models.FloatField(default=0, verbose_name="Виртуальная позиция")
    avg_price = models.FloatField(blank=True, null=True, verbose_name="Средняя цена позиции")
    realized_pnl = models.FloatField(default=0, verbose_name="Реализованный P&L")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Стратегия"
        verbose_name_plural = "Стратегии"

    def __str__(self):
        return f"{self.user}: {self.get_action_display()} {self.share.ticker} @ {self.trigger_price}"


class StrategyLog(models.Model):
    """Журнал виртуальных операций стратегии (FR-37)."""

    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="logs")
    action = models.CharField(max_length=4)
    price = models.FloatField()
    quantity = models.PositiveIntegerField()
    profit = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Запись журнала стратегий"
        verbose_name_plural = "Записи журнала стратегий"

    def __str__(self):
        return f"{self.strategy}: {self.action} {self.quantity} @ {self.price}"
