from django.db import models


class Share(models.Model):
    """Акция: идентификаторы инструмента, валюта, текущая цена и тренд."""

    figi = models.CharField(
        max_length=255,
        unique=True,
        help_text="Финансовый идентификатор инструмента (FIGI)",
    )
    isin = models.CharField(
        max_length=255,
        help_text="Международный идентификационный код ценной бумаги (ISIN)",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Наименование компании",
        help_text="Полное название компании-эмитента",
    )
    ticker = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Тикер",
        help_text="Биржевой тикер акции",
    )
    currency = models.CharField(
        max_length=20,
        verbose_name="Валюта",
        help_text="Валюта цены акции (например, RUB, USD)",
    )
    uid = models.CharField(
        max_length=255,
        unique=True,
        help_text="Уникальный идентификатор инструмента",
    )
    last_price = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Текущая цена",
        help_text="Последняя известная цена (заполняется фоновым обновлением)",
    )
    is_trend_high = models.BooleanField(
        blank=True,
        null=True,
        verbose_name="Растет цена",
        help_text="True — цена выросла относительно предыдущего значения, "
        "False — упала, None — сравнение невозможно",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        blank=True,
        null=True,
        verbose_name="Дата обновления",
    )

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.ticker})"
