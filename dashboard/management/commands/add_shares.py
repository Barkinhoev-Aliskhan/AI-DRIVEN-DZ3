from django.core.management.base import BaseCommand
from tinkoff.invest import Client

from config.settings import TINKOFF_TOKEN
from dashboard.models import Share


class Command(BaseCommand):
    help = "Добавляет акции из Tinkoff Invest API в БД (холодный старт)"

    def handle(self, *args, **options):
        created_count = 0
        with Client(TINKOFF_TOKEN) as client:
            response = client.instruments.shares()
            for share in response.instruments:
                _, was_created = Share.objects.get_or_create(
                    figi=share.figi,
                    defaults={
                        "name": share.name,
                        "isin": share.isin,
                        "ticker": share.ticker,
                        "currency": share.currency,
                        "uid": share.uid,
                    },
                )
                created_count += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(f"Загрузка завершена, новых акций: {created_count}")
        )
