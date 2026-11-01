# investing — трекер акций (отрефакторенная версия)

Проект: aidd-topic-03-homework. REST API по акциям с фоновым обновлением цен
из Tinkoff Invest API (Celery) и админкой Django.

## Быстрый старт

```bash
# 1. Инфраструктура (PostgreSQL + Redis)
docker-compose -f docker-compose.yml up -d

# 2. Зависимости
pip install -r requirements.txt

# 3. Секреты (опционально, есть dev-значения по умолчанию)
export TINKOFF_TOKEN="твой_токен"
export SECRET_KEY="случайная_строка"
export DJANGO_DEBUG="True"

# 4. Миграции и суперпользователь
python manage.py migrate
python manage.py createsuperuser

# 5. Первоначальная загрузка списка акций
python manage.py add_shares

# 6. Запуск (в трёх терминалах)
python manage.py runserver
celery -A config beat
celery -A config worker -l info
# Windows: celery -A config worker -l info -P eventlet
```

## Проверка работоспособности

- API: `http://127.0.0.1:8000/api/v1/shares/` — JSON с пагинацией (count/next/previous/results)
- Фильтр: `?ticker=SBER`, `?name=Sberbank`
- Поиск: `?search=GAZP` (работает по name, ticker, figi, isin)
- Сортировка: `?ordering=-name`
- Админка: `/admin/dashboard/share/`
- Тесты: `python manage.py test dashboard`

## Что изменено (см. audit-report.md)

1. Секреты (SECRET_KEY, токен, креды БД) вынесены в переменные окружения с dev-фолбэками.
2. Beat-расписание исправлено: 10 секунд -> 5 минут (соответствует README и имени задачи).
3. Исправлена логика тренда в dashboard/tasks.py: при отсутствии старой цены
   флаг становится None (раньше из-за TypeError молча ставился True);
   при ошибке сети запись не перезаписывается.
4. Расширен поиск в API: name, ticker (полнотекстово), figi, isin — как в админке.
5. Дублирование убрано: ShareFilter вынесен в filters.py, сериализатор —
   в dashboard/serializers.py (совместимость сохранена через dashboard/api/v1/).
6. Добавлены __str__, ordering, help_text у модели; updated_at только для чтения в админке.
7. Добавлены автотесты (25 кейсов): модель, API, задача обновления цен, админка.

## Восстановленные файлы (сверь с оригиналом!)

Эти файлы не были доступны, восстановлены по интерфейсу использования —
если оригинал отличается, подставь его (интерфейсы сохранены):

- `dashboard/services/market_data.py` — функция get_last_data(share) -> [цена, время]
- `dashboard/urls.py` — маршрутизация /api/v1/
- `user/urls.py` — маршруты приложения user

## Требования для работы

- PostgreSQL (docker-compose), Redis (docker-compose)
- Токен Tinkoff Invest API с правом чтения рыночных данных
