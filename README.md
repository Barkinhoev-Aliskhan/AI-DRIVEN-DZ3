# Investing Dashboard

Дашборд акций на Django + Tinkoff Invest API.

## Запуск

```bash
docker-compose up -d                      # PostgreSQL + Redis

python3 -m venv venv
source venv/bin/activate                  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                      # впиши TINKOFF_TOKEN

python manage.py migrate
python manage.py add_shares               # первичная загрузка акций
python manage.py runserver                # http://127.0.0.1:8000
```

В отдельных терминалах (после активации venv):

```bash
celery -A config worker -l info
celery -A config beat -l info
```

## Проверка

```bash
python manage.py check
python manage.py test dashboard
```
