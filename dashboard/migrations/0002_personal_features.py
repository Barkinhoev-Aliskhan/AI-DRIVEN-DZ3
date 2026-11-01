from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WatchlistItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="watchers", to="dashboard.share", verbose_name="Акция")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="watchlist_items", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Акция в списке наблюдения",
                "verbose_name_plural": "Акции в списках наблюдения",
                "ordering": ["-created_at"],
                "unique_together": {("user", "share")},
            },
        ),
        migrations.CreateModel(
            name="Portfolio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("name", models.CharField(max_length=100, verbose_name="Название портфеля")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="portfolios", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Портфель",
                "verbose_name_plural": "Портфели",
                "ordering": ["-created_at"],
                "unique_together": {("user", "name")},
            },
        ),
        migrations.CreateModel(
            name="PriceAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("condition", models.CharField(choices=[("above", "Цена выше цели"), ("below", "Цена ниже цели")], max_length=10, verbose_name="Условие")),
                ("target_price", models.DecimalField(decimal_places=4, max_digits=12, verbose_name="Целевая цена")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
                ("triggered_at", models.DateTimeField(blank=True, null=True, verbose_name="Время срабатывания")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alerts", to="dashboard.share", verbose_name="Акция")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alerts", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Целевое уведомление",
                "verbose_name_plural": "Целевые уведомления",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.CharField(max_length=500, verbose_name="Текст уведомления")),
                ("is_read", models.BooleanField(default=False, verbose_name="Прочитано")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("alert", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="dashboard.pricealert", verbose_name="Уведомление")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Уведомление пользователя",
                "verbose_name_plural": "Уведомления пользователей",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PortfolioOperation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("buy", "Покупка"), ("sell", "Продажа")], max_length=10, verbose_name="Тип операции")),
                ("quantity", models.PositiveIntegerField(verbose_name="Количество")),
                ("price", models.DecimalField(decimal_places=4, max_digits=12, verbose_name="Цена операции")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("portfolio", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="operations", to="dashboard.portfolio", verbose_name="Портфель")),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="portfolio_operations", to="dashboard.share", verbose_name="Акция")),
            ],
            options={
                "verbose_name": "Операция портфеля",
                "verbose_name_plural": "Операции портфелей",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PriceHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price", models.DecimalField(decimal_places=4, max_digits=12, verbose_name="Цена")),
                ("recorded_at", models.DateTimeField(auto_now_add=True, verbose_name="Время фиксации")),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="price_history", to="dashboard.share", verbose_name="Акция")),
            ],
            options={
                "verbose_name": "Историческая цена",
                "verbose_name_plural": "История цен",
                "ordering": ["-recorded_at"],
            },
        ),
        migrations.CreateModel(
            name="Strategy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("name", models.CharField(max_length=100, verbose_name="Название стратегии")),
                ("action", models.CharField(choices=[("buy", "Покупка"), ("sell", "Продажа")], max_length=10, verbose_name="Действие")),
                ("trigger_condition", models.CharField(choices=[("above", "Цена выше порога"), ("below", "Цена ниже порога")], max_length=10, verbose_name="Условие срабатывания")),
                ("trigger_price", models.DecimalField(decimal_places=4, max_digits=12, verbose_name="Пороговая цена")),
                ("quantity", models.PositiveIntegerField(verbose_name="Количество акций")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("portfolio", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="strategies", to="dashboard.portfolio", verbose_name="Привязанный портфель")),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="strategies", to="dashboard.share", verbose_name="Акция")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="strategies", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Инвестиционная стратегия",
                "verbose_name_plural": "Инвестиционные стратегии",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="StrategyTrade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("buy", "Покупка"), ("sell", "Продажа")], max_length=10, verbose_name="Действие")),
                ("price", models.DecimalField(decimal_places=4, max_digits=12, verbose_name="Цена сделки")),
                ("quantity", models.PositiveIntegerField(verbose_name="Количество")),
                ("executed_at", models.DateTimeField(auto_now_add=True, verbose_name="Время сделки")),
                ("share", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="strategy_trades", to="dashboard.share", verbose_name="Акция")),
                ("strategy", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="trades", to="dashboard.strategy", verbose_name="Стратегия")),
            ],
            options={
                "verbose_name": "Сделка стратегии",
                "verbose_name_plural": "Сделки стратегий",
                "ordering": ["-executed_at"],
            },
        ),
        migrations.AddIndex(
            model_name="pricehistory",
            index=models.Index(fields=["share", "recorded_at"], name="dashboard_pricehist_idx"),
        ),
    ]
