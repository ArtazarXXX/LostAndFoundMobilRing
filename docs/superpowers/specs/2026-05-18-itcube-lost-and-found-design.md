# ИТ-Куб: приложение поиска пропавших вещей — дизайн

**Дата:** 2026-05-18
**Статус:** утверждён, готов к плану реализации

## Цель

Мобильное Android-приложение для учеников ИТ-Куба, в котором можно посмотреть список найденных в Кубе вещей и заявить "это моя вещь". Админка — отдельный веб-фронтенд (вне этой спеки). Приложение должно работать в оффлайн-режиме с предзагруженными данными для демонстрации.

## Текущее состояние

В репозитории три папки:

- `Loss/` — Android-проект с 4 layout-экранами (add, item, form, form2) и пустыми Java-классами. Шрифты Fredoka/JetBrainsMono, основной цвет `#9FCFEC`.
- `Loss 2/` — Android-проект с прототипом главной (поиск + баннеры), почти ничего нет.
- `mobileback-main/` — FastAPI + SQLite (`maindb.db`) с эндпоинтами для предметов и заглушкой админов. SQL-инъекции через f-strings, авторизация не реализована, таблицы заявок на возврат нет.

## Архитектурное решение

База — `Loss/` (переименуем в `mobile/`). `Loss 2/` удаляется, идея поиска переносится в главный экран. Бэкенд — `mobileback-main/` (переименуем в `backend/`), переписывается с разбиением на модули.

### Мобилка

- **Платформа:** Android, Java, minSdk 24, существующая стилистика (Fredoka/JetBrainsMono, `#9FCFEC`).
- **Сетевой слой:** Retrofit + Gson + OkHttp logging, Glide для фото.
- **Экраны:**
  - `MainActivity` — список одобренных вещей (RecyclerView) + поле поиска (фильтр по `place` и `comment`).
  - `ItemActivity` — детали вещи + кнопка "это моя вещь".
  - `ClaimFormActivity` — форма (ФИО, группа, преподаватель) и отправка.
- **Пакеты:** `data/api`, `data/model`, `data/repository`, `ui/main`, `ui/item`, `ui/claim`.
- **Оффлайн-режим:** при `IOException` или таймауте 2с репозиторий читает `assets/seed_items.json` (6-8 примеров) и фото-плейсхолдеры из `res/drawable/`. В оффлайне форма заявки показывает тост "демо-режим, заявка не отправлена" и не отправляет на бэкенд. В UI баннер "Демо-режим (без сети)".
- **AddActivity удаляется** — добавление вещей это задача веб-админки.
- **Form2Activity удаляется** — одна форма достаточна.

### Бэкенд

- **Платформа:** FastAPI + SQLite, Python.
- **Структура:** `app/main.py`, `app/routers/items.py`, `app/routers/auth.py`, `app/routers/claims.py`, `app/routers/upload.py`, `app/models.py`, `app/db.py`.
- **Безопасность:** все SQL-запросы параметризованные (`?` плейсхолдеры), пароли админов через bcrypt, HTTP Basic auth на `/admin/*` через `Depends`.
- **Схема БД:**
  - `admins (id, login, password_hash)` — расширение существующей таблицы.
  - `items (id, url, place, comment, status)` — без изменений; статусы `in_applic / accept / not_accept / delete`.
  - `claims (id, item_id, fio, group_name, teacher, status, created_at)` — новая таблица; статусы `pending / done / rejected`.
- **Эндпоинты:**
  - `POST /upload` — multipart, сохраняет в `uploads/<uuid>.<ext>`, возвращает публичный URL. Только для админа.
  - `GET /users/items/getaccept` — публично, как сейчас.
  - `GET /users/items/getitem/{id}` — публично (URL → id, чтобы не плодить путаниц).
  - `POST /users/claims` — публично, создаёт заявку.
  - `GET /admin/items/getall`, `GET /admin/items/getapplic`, `PUT /admin/items/restatus` — auth, как сейчас, на параметризованных SQL.
  - `GET /admin/claims`, `PUT /admin/claims/{id}/status` — auth, для веб-админки.
- **Хранилище фото:** локальная папка `uploads/`, отдача через `StaticFiles` по `/uploads/*`.
- **Seed-данные:** один админ `admin/admin` для разработки (bcrypt), несколько тестовых предметов.

## Поток данных (основной сценарий)

1. Ученик открывает приложение → `MainActivity` показывает список из `GET /users/items/getaccept`. Фото грузятся по URL из бэкенда.
2. Если сеть недоступна → fallback к фикстурам, баннер "Демо-режим".
3. Тап на вещь → `ItemActivity` с деталями.
4. Тап "это моя вещь" → `ClaimFormActivity`.
5. Заполнил форму → `POST /users/claims` с `item_id`. Успех → тост + возврат на главную. В оффлайне → демо-тост без отправки.

## Этапы реализации

0. **Чистка:** удалить `Loss 2/`, переименовать `Loss/` → `mobile/`, `mobileback-main/` → `backend/`.
1. **Бэкенд: рефакторинг** — разбить main.py на модули, параметризованный SQL, bcrypt-хеши, HTTP Basic auth на `/admin/*`.
2. **Бэкенд: claims + upload** — миграция БД, `POST /upload`, `POST /users/claims`, админские эндпоинты для заявок, `StaticFiles`, ручной прогон через curl.
3. **Мобилка: каркас** — удалить `AddActivity` и `Form2Activity`, зависимости (Retrofit, Gson, Glide, RecyclerView), permissions, базовый URL в BuildConfig, структура пакетов.
4. **Мобилка: главная** — `MainActivity` со списком, поиском, загрузкой фото.
5. **Мобилка: детали + форма заявки** — `ItemActivity` (EditText → TextView для описания) и `ClaimFormActivity` (переименованный `form_activity`).
6. **Оффлайн-режим** — `assets/seed_items.json`, фото-плейсхолдеры, fallback в репозитории, демо-баннер.
7. **Финальный прогон** — сценарии в эмуляторе с бэкендом и без, README с инструкцией.

## Out of scope

- Веб-админка (отдельный фронтенд, отдельный спек).
- Регистрация и авторизация учеников.
- Push-уведомления о статусе заявки.
- Production-хранилище фото (S3/CDN) — позже, когда уйдём от локального демо.
- Полноценная миграционная система (Alembic) — для текущего объёма достаточно ручных `CREATE TABLE IF NOT EXISTS`.
