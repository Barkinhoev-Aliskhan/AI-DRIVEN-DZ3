from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("dashboard", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="WatchItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_price", models.FloatField(verbose_name="Целевая цена")),
                ("direction", models.CharField(choices=[("above", "Цена выше целевой"), ("below", "Цена ниже целевой")], max_length=10, verbose_name="Условие")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="watch_items", to="dashboard.share")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="watch_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Наблюдение", "verbose_name_plural": "Наблюдения"},
            constraints=[models.UniqueConstraint(fields=("user", "share"), name="unique_watch_item_per_user_share")],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField()),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
                ("watch_item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="tracker.watchitem")),
            ],
            options={"ordering": ("-created_at",), "verbose_name": "Уведомление", "verbose_name_plural": "Уведомления"},
        ),
        migrations.CreateModel(
            name="Portfolio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="Название")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="portfolios", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Портфель", "verbose_name_plural": "Портфели"},
            constraints=[models.UniqueConstraint(fields=("user", "name"), name="unique_portfolio_per_user")],
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("buy", "Покупка"), ("sell", "Продажа")], max_length=4)),
                ("quantity", models.PositiveIntegerField(verbose_name="Количество")),
                ("price", models.FloatField(verbose_name="Цена")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("portfolio", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="tracker.portfolio")),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="dashboard.share")),
            ],
            options={"ordering": ("created_at",), "verbose_name": "Операция", "verbose_name_plural": "Операции"},
        ),
        migrations.CreateModel(
            name="PriceHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price", models.FloatField()),
                ("recorded_at", models.DateTimeField(auto_now_add=True)),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="price_history", to="dashboard.share")),
            ],
            options={"ordering": ("recorded_at",), "verbose_name": "Историческая цена", "verbose_name_plural": "Исторические цены"},
        ),
        migrations.CreateModel(
            name="Strategy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("buy", "Покупка"), ("sell", "Продажа")], max_length=4, verbose_name="Действие")),
                ("trigger_price", models.FloatField(verbose_name="Триггерная цена")),
                ("quantity", models.PositiveIntegerField(verbose_name="Объём сделки")),
                ("trades_limit", models.PositiveIntegerField(default=10, verbose_name="Лимит сделок")),
                ("trades_done", models.PositiveIntegerField(default=0, verbose_name="Исполнено сделок")),
                ("position_qty", models.FloatField(default=0, verbose_name="Виртуальная позиция")),
                ("avg_price", models.FloatField(blank=True, null=True, verbose_name="Средняя цена позиции")),
                ("realized_pnl", models.FloatField(default=0, verbose_name="Реализованный P&L")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="strategies", to="dashboard.share")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="strategies", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",), "verbose_name": "Стратегия", "verbose_name_plural": "Стратегии"},
        ),
        migrations.CreateModel(
            name="StrategyLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=4)),
                ("price", models.FloatField()),
                ("quantity", models.PositiveIntegerField()),
                ("profit", models.FloatField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("strategy", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="logs", to="tracker.strategy")),
            ],
            options={"ordering": ("-created_at",), "verbose_name": "Запись журнала стратегий", "verbose_name_plural": "Записи журнала стратегий"},
        ),
        migrations.AddIndex(
            model_name="pricehistory",
            index=models.Index(fields=("share", "recorded_at"), name="pricehistory_share_recorded_idx"),
        ),
    ]
