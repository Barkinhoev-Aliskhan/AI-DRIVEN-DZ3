# Investing — трекер акций с персональной аналитикой

Приложение на Django + DRF: каталог акций (Tinkoff Invest API), фоновое
обновление цен (Celery + Redis) и новые персональные функции:

1. **Персональный мониторинг акций** — списки наблюдения (`/api/v1/watchlist/`),
   целевые уровни цены (`/api/v1/alerts/`), уведомления (`/api/v1/notifications/`).
   Уведомления срабатывают один раз — дублирование исключено.
2. **Виртуальный инвестиционный портфель** — `/api/v1/portfolios/`,
   операции `/api/v1/portfolio-operations/`, сводка стоимости и P&L:
   `GET /api/v1/portfolios/{id}/summary/`.
3. **История изменения цен** — автоматически пишется задачей Celery в
   `PriceHistory`; просмотр `/api/v1/price-history/?share=...&date_from=...&date_to=...`,
   статистика `/api/v1/price-history/stats/`, график `/api/v1/price-history/chart/`.
4. **Симулятор стратегий** — `/api/v1/strategies/` (одноразовые правила
   buy/sell по цене), журнал сделок `/api/v1/strategy-trades/`, оценка
   эффективности: `GET /api/v1/strategies/{id}/effectiveness/`.

## Запуск

```bash
docker-compose -f docker-compose.yml up -d   # PostgreSQL + Redis
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py add_shares                  # загрузка акций из Tinkoff
python manage.py runserver
celery -A config beat                        # планировщик
celery -A config worker -l info              # воркер
```

Для Windows-воркера: `pip install eventlet cryptography` и
`celery -A config worker -l info -P eventlet`.

Переменные окружения (вместо правки settings.py):
`TINKOFF_TOKEN`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DB_HOST/DB_NAME/DB_USER/DB_PASSWORD/DB_PORT`, `CELERY_BROKER_URL`.

## Аутентификация API

Персональные эндпоинты требуют аутентификации (сессии Django):
войдите в админку или получите сессию через стандартный `django.contrib.auth`;
для простоты можно включить `rest_framework.authtoken`.

## Тесты

```bash
python manage.py test dashboard
```

## Что проверено при подготовке сборки

Статическая проверка: синтаксис всех модулей, согласованность импортов,
соответствие миграций моделям, целостность роутинга. Запуск в реальном
окружении (PostgreSQL + Redis + воркер) — на стороне пользователя по
чек-листу выше.
