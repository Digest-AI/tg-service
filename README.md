# Tg Service

## Описание

Telegram-бот сервис для платформы Digest.ai. Отвечает за привязку Telegram-аккаунта к профилю пользователя на сайте, отправку уведомлений о событиях и управление подпиской.

---

## Реализованные фичи

### Бот

- `/start` — приветствие и генерация кода привязки (6 символов, TTL 10 минут). Если аккаунт уже привязан — показывает статус
- `/premium` — выбор и покупка Premium-подписки через Telegram Stars (1, 3, 12 месяцев)
- `/help` — справка и контакт поддержки
- Callback `new_code` — генерация нового кода (старый удаляется из БД)
- Callback `start_link` — повторный запуск флоу привязки

### Middleware

- `CheckLinkedMiddleware` — блокирует любые сообщения от непривязанных пользователей (кроме `/start`, `/help`, `/premium`)

### Модели (SQLite)

**User**

| Поле | Тип | Описание |
|---|---|---|
| `id` | BigAutoField | Первичный ключ |
| `public_id` | CharField | ID пользователя из основного сервиса (unique) |
| `username` | CharField | Telegram username (unique) |
| `telegram_id` | CharField | Числовой Telegram ID (unique) |

**VerificationCode**

| Поле | Тип | Описание |
|---|---|---|
| `id` | BigAutoField | Первичный ключ |
| `code` | CharField(6) | Код привязки (unique) |
| `username` | CharField | Telegram username пользователя |
| `telegram_id` | CharField | Числовой Telegram ID пользователя |
| `expires_at` | DateTimeField | Время истечения (TTL 10 минут) |

> Код удаляется из БД сразу после использования. На каждого пользователя хранится не более одной записи.

### REST API

**Для frontend**

| Метод | URL | Описание |
|---|---|---|
| `GET` | `/api/users/` | Список пользователей |
| `POST` | `/api/users/` | Создать пользователя |
| `GET` | `/api/users/{id}/` | Получить пользователя |
| `PATCH` | `/api/users/{id}/` | Обновить пользователя |
| `DELETE` | `/api/users/{id}/` | Удалить пользователя |
| `POST` | `/api/verification-codes/verify/` | Верифицировать код привязки |

Пример верификации кода:
```bash
curl -X POST http://localhost:8160/api/verification-codes/verify/ \
  -H "Content-Type: application/json" \
  -d '{"code": "B5EMNP", "publicId": "user-uuid-from-main-service"}'
```

**Для recommendations-service**

| Метод | URL | Описание |
|---|---|---|
| `POST` | `/api/recommendations/` | Отправить рекомендацию пользователю в Telegram |

Пример отправки рекомендации:
```bash
curl -X POST http://localhost:8160/api/recommendations/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user",
    "title": "Конференция по AI в Москве",
    "date": "15 мая 2026",
    "description": "Ведущие эксперты обсудят тренды AI в бизнесе.",
    "url": "https://digest.ai/events/1"
  }'
```

### Проверка привязки аккаунта

```bash
python manage.py shell -c "
from api.models import User
telegram_id = 'ВАШ_TELEGRAM_ID'
user = User.objects.filter(telegram_id=telegram_id).first()
if user:
    print(f'Привязан: username={user.username}, public_id={user.public_id}')
else:
    print('Аккаунт не привязан')
"
```

### Тестирование уведомлений

```bash
# Уведомление-рекомендация
python manage.py sendnotification <TELEGRAM_ID> --type recommendation

# Напоминание о событии
python manage.py sendnotification <TELEGRAM_ID> --type reminder
```

---

## Как запустить локально

Убедитесь что у вас установлен Python и pip.

В папке проекта:

1. `python -m venv .venv`
2. `.venv\Scripts\activate` (Windows), `source .venv/bin/activate` (Mac)
3. `pip install -r r.txt`
4. `python manage.py migrate`
5. `python manage.py runserver`

Сервер запустится на localhost:8160

Для запуска бота:

6. Заполнить `.env` (скопировать `.env.example` если есть, или создать вручную)
7. `python main.py`

---

## Переменные окружения (.env)

| Переменная | Описание |
|---|---|
| `SECRET_KEY` | Django secret key |
| `ENVIRONMENT` | `development` или `production` |
| `HOST` | Хост сервера |
| `ALLOWED_HOSTS` | Разрешённые хосты через запятую |
| `CORS_ALLOWED_ORIGINS` | Разрешённые origins через запятую |
| `SERVICE_ID` | Идентификатор сервиса (`tg-service`) |
| `SERVICE_SECRET` | Секрет для межсервисной аутентификации |
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather |
