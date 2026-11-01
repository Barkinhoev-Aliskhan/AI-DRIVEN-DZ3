from django.conf import settings
from django.db import models


class Share(models.Model):
    """Акция (исходная сущность приложения)."""

    figi = models.CharField(max_length=255, unique=True)
    isin = models.CharField(max_length=255)
    name = models.CharField(max_length=255, verbose_name="Наименование компании")
    ticker = models.CharField(max_length=10, unique=True, verbose_name="Тикер")
    currency = models.CharField(max_length=20, verbose_name="Валюта")
    uid = models.CharField(max_length=255, unique=True)
    last_price = models.FloatField(blank=True, null=True, verbose_name="Текущая цена")
    is_trend_high = models.BooleanField(
        blank=True, null=True, verbose_name="Растет цена"
    )
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.ticker})"


class WatchlistItem(models.Model):
    """Акция в персональном списке наблюдения пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watchlist_items",
        verbose_name="Пользователь",
    )
    share = models.ForeignKey(
        Share,
        on_delete=models.CASCADE,
        related_name="watchers",
        verbose_name="Акция",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Акция в списке наблюдения"
        verbose_name_plural = "Акции в списках наблюдения"
        unique_together = ("user", "share")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} watches {self.share.ticker}"


class PriceAlert(models.Model):
    """Уведомление о достижении акцией целевого уровня цены.

    После первого срабатывания деактивируется (is_active=False) — это
    гарантирует отсутствие повторных уведомлений об одном и том же событии.
    """

    class Condition(models.TextChoices):
        ABOVE = "above", "Цена выше цели"
        BELOW = "below", "Цена ниже цели"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name="Пользователь",
    )
    share = models.ForeignKey(
        Share,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name="Акция",
    )
    condition = models.CharField(
        max_length=10, choices=Condition.choices, verbose_name="Условие"
    )
    target_price = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="Целевая цена"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    triggered_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Время срабатывания"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Целевое уведомление"
        verbose_name_plural = "Целевые уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.share.ticker} {self.condition} {self.target_price}"


class Notification(models.Model):
    """Уведомление пользователя о сработавшем целевом уровне."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Пользователь",
    )
    alert = models.ForeignKey(
        PriceAlert,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Уведомление",
    )
    message = models.CharField(max_length=500, verbose_name="Текст уведомления")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление пользователя"
        verbose_name_plural = "Уведомления пользователей"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user}: {self.message[:50]}"


class Portfolio(models.Model):
    """Виртуальный инвестиционный портфель пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portfolios",
        verbose_name="Пользователь",
    )
    name = models.CharField(max_length=100, verbose_name="Название портфеля")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Портфель"
        verbose_name_plural = "Портфели"
        unique_together = ("user", "name")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.name}"


class PortfolioOperation(models.Model):
    """Виртуальная операция покупки/продажи акции в портфеле."""

    class Action(models.TextChoices):
        BUY = "buy", "Покупка"
        SELL = "sell", "Продажа"

    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="operations",
        verbose_name="Портфель",
    )
    share = models.ForeignKey(
        Share,
        on_delete=models.CASCADE,
        related_name="portfolio_operations",
        verbose_name="Акция",
    )
    action = models.CharField(max_length=10, choices=Action.choices, verbose_name="Тип операции")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="Цена операции"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Операция портфеля"
        verbose_name_plural = "Операции портфелей"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.quantity} {self.share.ticker} @ {self.price}"


class PriceHistory(models.Model):
    """Точка истории рыночной цены акции."""

    share = models.ForeignKey(
        Share,
        on_delete=models.CASCADE,
        related_name="price_history",
        verbose_name="Акция",
    )
    price = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="Цена"
    )
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name="Время фиксации")

    class Meta:
        verbose_name = "Историческая цена"
        verbose_name_plural = "История цен"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["share", "recorded_at"], name="dashboard_pricehist_idx"),
        ]

    def __str__(self):
        return f"{self.share.ticker}: {self.price} @ {self.recorded_at}"


class Strategy(models.Model):
    """Симуляционная стратегия покупки/продажи акции по условию цены.

    Стратегия одноразовая: после первого срабатывания деактивируется,
    чтобы по одному условию не создавались дублирующие виртуальные сделки.
    """

    class Action(models.TextChoices):
        BUY = "buy", "Покупка"
        SELL = "sell", "Продажа"

    class TriggerCondition(models.TextChoices):
        ABOVE = "above", "Цена выше порога"
        BELOW = "below", "Цена ниже порога"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="strategies",
        verbose_name="Пользователь",
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="strategies",
        verbose_name="Привязанный портфель",
    )
    name = models.CharField(max_length=100, verbose_name="Название стратегии")
    share = models.ForeignKey(
        Share,
        on_delete=models.CASCADE,
        related_name="strategies",
        verbose_name="Акция",
    )
    action = models.CharField(max_length=10, choices=Action.choices, verbose_name="Действие")
    trigger_condition = models.CharField(
        max_length=10, choices=TriggerCondition.choices, verbose_name="Условие срабатывания"
    )
    trigger_price = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="Пороговая цена"
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество акций")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Инвестиционная стратегия"
        verbose_name_plural = "Инвестиционные стратегии"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.action} {self.share.ticker} {self.trigger_condition} {self.trigger_price}"


class StrategyTrade(models.Model):
    """Журнал виртуальных сделок, исполненных стратегией."""

    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name="trades",
        verbose_name="Стратегия",
    )
    share = models.ForeignKey(
        Share,
        on_delete=models.CASCADE,
        related_name="strategy_trades",
        verbose_name="Акция",
    )
    action = models.CharField(max_length=10, choices=Strategy.Action.choices, verbose_name="Действие")
    price = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="Цена сделки"
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    executed_at = models.DateTimeField(auto_now_add=True, verbose_name="Время сделки")

    class Meta:
        verbose_name = "Сделка стратегии"
        verbose_name_plural = "Сделки стратегий"
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.strategy.name}: {self.action} {self.quantity} {self.share.ticker} @ {self.price}"
