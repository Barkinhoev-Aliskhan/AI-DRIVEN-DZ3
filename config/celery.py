import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# Регулярное обновление цен: раз в 5 минут (согласовано с README).
app.conf.beat_schedule = {
    "update-prices-every-5-min": {
        "task": "dashboard.tasks.update_last_price",
        "schedule": 300.0,
    },
}
