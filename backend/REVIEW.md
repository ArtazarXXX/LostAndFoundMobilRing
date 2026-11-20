# Ревью бэкенда сервиса потерянных вещей

**Проект:** ИТ-Куб, итоговая работа
**Файлы:** `main.py`, `db.py`
**Технологии:** Python 3, FastAPI, SQLite

---

## Как читать этот документ

Каждая проблема описана по схеме:

- **Что не так** — суть проблемы простыми словами.
- **Почему это важно** — что сломается или что спросит комиссия.
- **Что делать** — пошаговая инструкция.
- **Было / Стало** — код «как сейчас» и «как должно быть».
- **На защите** (если применимо) — готовая формулировка для комиссии.

В конце — **итоговый чек-лист** и **общий пример «как мог бы выглядеть весь `main.py`»**.

---

## Раздел 1. Критические проблемы (нужно исправить обязательно)

### 1.1. SQL-инъекции во всех запросах

**Что не так.** Все SQL-запросы собираются через f-строки. Это значит, что данные пользователя (например, `url`) подставляются в текст запроса напрямую.

**Почему это важно.** Это самая известная веб-уязвимость в мире. Её обязательно проходят на любом курсе по веб-разработке, и **комиссия почти наверняка спросит**: «Защищён ли ваш сервис от SQL-инъекций?». Если ответить «нет» или «не знаю» — это серьёзный минус.

Пример атаки. Если злоумышленник передаст:

```
url = x'; DROP TABLE items; --
```

то твой код превратится в:

```sql
SELECT url, place, comment, status FROM items WHERE url = 'x'; DROP TABLE items; --'
```

И вся таблица `items` будет удалена.

**Что делать.** Использовать **параметризованные запросы**. Это значит, что вместо подстановки данных в строку, ты пишешь в SQL знаки `?`, а сами значения передаёшь отдельным аргументом. SQLite сам их безопасно подставит.

**Было:**
```python
cursor.execute(f"UPDATE items SET status = '{status}' WHERE url = '{url}'")

cursor.execute(
    f"INSERT INTO items (url, place, comment, status) "
    f"VALUES('{url}', '{place}', '{comment}', 'in applic')"
)

cursor.execute(f"SELECT url, place, comment, status FROM items WHERE url = '{url}'")
```

**Стало:**
```python
cursor.execute(
    "UPDATE items SET status = ? WHERE url = ?",
    (status, url),
)

cursor.execute(
    "INSERT INTO items (url, place, comment, status) VALUES (?, ?, ?, ?)",
    (url, place, comment, "in applic"),
)

cursor.execute(
    "SELECT url, place, comment, status FROM items WHERE url = ?",
    (url,),
)
```

Обрати внимание: если параметр **один**, кортеж всё равно нужен — `(url,)` с запятой. Без запятой это будет просто строка в скобках.

**На защите:** «Я использую параметризованные запросы — данные передаются в SQL через знак вопроса, а не подставляются в строку. Это защищает от SQL-инъекций.»

---

### 1.2. `return` внутри блока `finally`

**Что не так.** В каждом эндпоинте есть конструкция:

```python
try:
    cursor.execute(...)
finally:
    con.commit()
    con.close()
    return res
```

`return` стоит **внутри `finally`**, и из-за этого, если `cursor.execute(...)` упал с ошибкой, эта ошибка не вылетит наружу — её «съест» `return`. Клиент получит код 200 (успех) и пустой ответ, как будто всё хорошо.

**Почему это важно.** Если БД временно недоступна или запрос неправильный — пользователь увидит «успех» и не поймёт, что произошло. Отлаживать такие баги очень сложно.

**Что делать.** Вынести `return` за пределы `try/finally`. Логика должна быть:
1. Выполнить запрос.
2. Если упал — пробросить ошибку дальше.
3. Если всё хорошо — вернуть результат.

**Было:**
```python
@app.get("/admin/items/getall")
async def allitems():
    con = get_db_connection()
    cursor = con.cursor()
    res = {}
    try:
        cursor.execute("SELECT url, place, comment, status FROM items")
        SQLobject = cursor.fetchall()
        for i in SQLobject:
            if i["url"] not in res.keys():
                res[i["url"]] = [i["place"], i["comment"], i["status"]]
    finally:
        con.commit()
        con.close()
        return res
```

**Стало:**
```python
@app.get("/admin/items/getall")
def allitems():
    con = get_db_connection()
    try:
        rows = con.execute(
            "SELECT url, place, comment, status FROM items"
        ).fetchall()
    finally:
        con.close()

    return [
        {"url": r["url"], "place": r["place"],
         "comment": r["comment"], "status": r["status"]}
        for r in rows
    ]
```

---

### 1.3. `commit()` после `SELECT`

**Что не так.** После каждого `SELECT` вызывается `con.commit()`. `commit` нужен только тогда, когда в БД что-то **меняется** (`INSERT`, `UPDATE`, `DELETE`). После чтения данных коммитить нечего.

**Почему это важно.** Это не баг, но это явный признак того, что ученик не до конца понимает, что делает `commit`. На защите такой вопрос могут задать: «Зачем здесь commit?». Лучше убрать.

**Что делать.** Оставить `commit()` только в `create_items` и `restatus`. В `getall`, `getapplic`, `get_item`, `getaccept` — убрать.

---

### 1.4. Админские эндпоинты доступны кому угодно

**Что не так.** Эндпоинты `/admin/items/getall`, `/admin/items/getapplic`, `/admin/items/restatus` не требуют никакой авторизации. Любой человек, знающий адрес сервиса, может посмотреть все заявки и поменять их статусы.

В `db.py` создаётся таблица `admins` с логином и паролем — но она нигде не используется.

**Почему это важно.** Эндпоинт называется `/admin/...` — это явное обещание, что туда могут заходить только администраторы. Если защиты нет — комиссия об этом точно спросит.

**Что делать.** Самый простой вариант, которого хватит для школьного проекта:

1. Сделать эндпоинт `POST /admin/login`, который принимает логин и пароль, проверяет их в таблице `admins` и возвращает «токен» (это может быть просто случайная строка, например `secrets.token_hex(16)`).
2. Сохранить токен в памяти (в обычном `dict`) или в отдельной таблице `sessions`.
3. Сделать функцию-зависимость `check_admin`, которая читает заголовок `Authorization` и проверяет, что токен есть в списке.
4. Подключить эту зависимость ко всем `/admin/*` эндпоинтам.

**Пример простой реализации:**

```python
import secrets
from fastapi import Depends, Header, HTTPException

# Простое хранилище токенов в памяти
active_tokens: set[str] = set()

@app.post("/admin/login")
def login(username: str, password: str):
    con = get_db_connection()
    try:
        row = con.execute(
            "SELECT password FROM admins WHERE login = ?",
            (username,),
        ).fetchone()
    finally:
        con.close()

    if row is None or row["password"] != hash_password(password):
        raise HTTPException(status_code=401, detail="неверный логин или пароль")

    token = secrets.token_hex(16)
    active_tokens.add(token)
    return {"token": token}


def check_admin(authorization: str = Header(...)):
    # Заголовок приходит в виде "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0] != "Bearer" or parts[1] not in active_tokens:
        raise HTTPException(status_code=401, detail="нужна авторизация")


@app.get("/admin/items/getall", dependencies=[Depends(check_admin)])
def allitems():
    ...
```

Теперь, чтобы зайти на `/admin/items/getall`, фронт должен сначала вызвать `/admin/login`, получить токен и слать его в заголовке `Authorization: Bearer <token>`.

**На защите:** «У меня админ сначала логинится через `/admin/login`, получает токен, и без этого токена нельзя зайти на админские эндпоинты.»

---

### 1.5. Пароль админа в открытом виде

**Что не так.** В `db.py` закомментирована строка:

```python
# cursor.execute("INSERT INTO admins (logan, password) VALUES(?, ?)", ("admin", "123"))
```

Пароль `123` слабый и хранится в БД как есть. Если кто-то получит доступ к файлу `maindb.db` — пароль виден сразу.

**Почему это важно.** Хранить пароли в открытом виде — это нарушение базовых правил безопасности. На защите часто спрашивают: «А как у вас хранятся пароли?».

**Что делать.** Хешировать пароль перед сохранением. Хеш — это «отпечаток» пароля: из пароля можно получить хеш, а из хеша пароль восстановить нельзя. Когда пользователь логинится — мы хешируем введённый им пароль и сравниваем хеши.

Для школьного проекта достаточно `hashlib.sha256` из стандартной библиотеки:

```python
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# При создании админа:
con.execute(
    "INSERT INTO admins (login, password) VALUES (?, ?)",
    ("admin", hash_password("123")),
)

# При логине:
row = con.execute(
    "SELECT password FROM admins WHERE login = ?",
    (username,),
).fetchone()
if row and row["password"] == hash_password(entered_password):
    # пароль верный
    ...
```

**На защите:** «Пароли хранятся в виде хешей SHA-256. Если файл БД утечёт, восстановить из хеша исходный пароль нельзя.»

> **Бонус.** Если осталось время — посмотри библиотеку `bcrypt` (`pip install bcrypt`). Она надёжнее, потому что добавляет «соль» и работает медленно (это специально, чтобы перебор паролей был дольше). Но для школьного проекта `sha256` — нормальный вариант.

---

### 1.6. Опечатка `logan` вместо `login`

**Что не так.** В `db.py` поле в таблице `admins` называется `logan`. Это явная опечатка от `login`.

**Почему это важно.** Любой проверяющий это заметит сразу. Мелочь, но создаёт впечатление неаккуратности.

**Что делать.** Переименовать в `login`. Так как БД ещё не используется реальными пользователями — можно просто удалить старую `maindb.db` и создать заново. Или написать миграцию:

```python
con.execute("ALTER TABLE admins RENAME COLUMN logan TO login")
```

---

## Раздел 2. Логические недочёты

### 2.1. `if not SQLobject is None` — антипаттерн стиля

**Что не так.** В `get_item`:

```python
if not SQLobject is None:
    return {...}
else:
    return {...}
```

В Python принято писать `is not None`, а не `not ... is None`. Технически это работает одинаково, но читается хуже.

**Стало:**
```python
if SQLobject is not None:
    return {...}
else:
    return {...}
```

PEP 8 (стандарт оформления Python-кода) явно говорит про это. Любой проверяющий, который смотрел PEP 8, обратит внимание.

---

### 2.2. `if i["url"] not in res.keys()` — лишний `.keys()`

**Что не так.** Ты пишешь:

```python
if i["url"] not in res.keys():
```

В Python оператор `in` для словаря **по умолчанию** ищет среди ключей. Метод `.keys()` тут лишний.

**Было:**
```python
if i["url"] not in res.keys():
```

**Стало:**
```python
if i["url"] not in res:
```

Работает идентично, но короче и быстрее (без создания объекта `dict_keys`).

---

### 2.3. Длинная цепочка `or` для проверки статуса

**Что не так.** В `restatus`:

```python
if status == "in applic" or status == "accept" or status == "not accept" or status == "delete":
```

Это длинно и плохо читается. Если завтра добавишь новый статус — придётся искать все такие места.

**Что делать.** Создать множество допустимых значений и проверять через `in`:

**Было:**
```python
if status == "in applic" or status == "accept" or status == "not accept" or status == "delete":
    ...
```

**Стало:**
```python
ALLOWED_STATUSES = {"in applic", "accept", "not accept", "delete"}

if status in ALLOWED_STATUSES:
    ...
```

Ещё лучше — `Enum` (см. пункт 3.3).

---

### 2.4. `getapplic` фильтрует в Python вместо SQL

**Что не так.** В `getapplic`:

```python
cursor.execute("SELECT url, place, comment, status FROM items")  # вытаскиваем ВСЁ
SQLobject = cursor.fetchall()
for i in SQLobject:
    if i["status"] == "in applic" and ...:                      # фильтруем в Python
```

Сравни с `getaccept`, где фильтр уже в SQL:

```python
cursor.execute("SELECT ... FROM items WHERE status = 'accept'")
```

Так и должно быть везде.

**Почему это важно.** При маленькой БД разницы нет, но если заявок станет 10 000 — мы тащим из БД всё 10 000 строк, чтобы оставить только 50 «в рассмотрении». БД умеет фильтровать сама — это её работа.

На защите легко спросят: «Почему здесь фильтр в БД, а здесь в Python?». Лучше сделать одинаково.

**Стало:**
```python
@app.get("/admin/items/getapplic")
def applic():
    con = get_db_connection()
    try:
        rows = con.execute(
            "SELECT url, place, comment, status FROM items WHERE status = ?",
            ("in applic",),
        ).fetchall()
    finally:
        con.close()
    return [dict(r) for r in rows]
```

---

### 2.5. `restatus` не проверяет, что заявка существует

**Что не так.** Если передать несуществующий `url`, `UPDATE` ничего не сделает, но клиент получит ответ «статус изменён».

```python
cursor.execute("UPDATE items SET status = ? WHERE url = ?", (status, url))
# даже если ничего не обновилось, мы возвращаем "статус изменён"
return {"message": f"статус изменён на {status}"}
```

**Что делать.** Проверить `cursor.rowcount` — это количество строк, которые `UPDATE` затронул.

**Стало:**
```python
cursor.execute("UPDATE items SET status = ? WHERE url = ?", (status, url))
con.commit()

if cursor.rowcount == 0:
    raise HTTPException(status_code=404, detail="заявка не найдена")

return {"message": f"статус изменён на {status}"}
```

---

### 2.6. Отсутствие правильных HTTP-кодов

**Что не так.** Когда заявки нет, эндпоинт возвращает:

```python
return {"message": "нет такой заявки"}
```

Но HTTP-код при этом — **200 OK**. То есть с точки зрения протокола всё хорошо, и фронт обязан смотреть в тело ответа, чтобы понять, что что-то не так.

**Почему это важно.** Существует общепринятый стандарт: **404 Not Found** означает «не найдено», **400 Bad Request** — «неверные данные», **401 Unauthorized** — «нужна авторизация», **500 Internal Server Error** — «что-то сломалось на сервере». Возвращать «нет такой заявки» с кодом 200 — то же самое, что говорить «всё хорошо, но плохо».

**Что делать.** Использовать `HTTPException` из FastAPI:

**Было:**
```python
@app.get("/users/items/getitem/{url}")
async def get_item(url: str):
    ...
    if not SQLobject is None:
        return {...}
    else:
        return {"message": "нет такой заявки"}
```

**Стало:**
```python
from fastapi import HTTPException

@app.get("/users/items/getitem/{url}")
def get_item(url: str):
    con = get_db_connection()
    try:
        row = con.execute(
            "SELECT url, place, comment, status FROM items WHERE url = ?",
            (url,),
        ).fetchone()
    finally:
        con.close()

    if row is None:
        raise HTTPException(status_code=404, detail="заявка не найдена")

    return dict(row)
```

То же самое — для `restatus` при невалидном статусе (использовать код 400 вместо 200).

---

### 2.7. Ответ в виде словаря с `url` как ключом

**Что не так.** Везде в `getall`, `getapplic`, `getaccept`:

```python
res[i["url"]] = [i["place"], i["comment"], i["status"]]
```

То есть ответ выглядит так:

```json
{
  "https://example.com/img1.jpg": ["it_cube", "забытый рюкзак", "in applic"],
  "https://example.com/img2.jpg": ["coridor", "ключи", "accept"]
}
```

Здесь два недостатка:

1. Если в БД две записи с одинаковым `url` — вторая молча затрёт первую в ответе.
2. Список `[place, comment, status]` без имён полей — фронт обязан помнить порядок. Завтра добавишь поле `created_at` — фронт начнёт показывать его вместо `status`, и никто это не заметит.

**Что делать.** Возвращать **массив объектов** с именованными полями.

**Было:**
```python
res = {}
for i in SQLobject:
    if i["url"] not in res.keys():
        res[i["url"]] = [i["place"], i["comment"], i["status"]]
return res
```

**Стало:**
```python
return [
    {
        "url": r["url"],
        "place": r["place"],
        "comment": r["comment"],
        "status": r["status"],
    }
    for r in rows
]
```

Ответ станет таким:

```json
[
  {"url": "...", "place": "it_cube", "comment": "забытый рюкзак", "status": "in applic"},
  {"url": "...", "place": "coridor", "comment": "ключи", "status": "accept"}
]
```

С таким форматом фронту работать гораздо удобнее — это стандартный JSON-массив.

---

## Раздел 3. Архитектурные улучшения (это плюсы для защиты)

### 3.1. Pydantic-модели для входа и выхода

**Что не так.** Сейчас параметры передаются как простые типы:

```python
@app.post("/users/items/create")
async def create_items(url: str, place: str, comment: str):
```

FastAPI считает их **query-параметрами**, то есть они идут в URL: `POST /users/items/create?url=...&place=...&comment=...`. Для длинного `comment` с пробелами и спецсимволами это неудобно.

**Что делать.** Использовать **Pydantic-модели** — это рекомендованный способ во FastAPI.

```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    url: str
    place: str
    comment: str

class ItemOut(BaseModel):
    url: str
    place: str
    comment: str
    status: str


@app.post("/users/items/create", response_model=ItemOut)
def create_items(item: ItemCreate):
    con = get_db_connection()
    try:
        con.execute(
            "INSERT INTO items (url, place, comment, status) VALUES (?, ?, ?, ?)",
            (item.url, item.place, item.comment, "in applic"),
        )
        con.commit()
    finally:
        con.close()

    return ItemOut(
        url=item.url,
        place=item.place,
        comment=item.comment,
        status="in applic",
    )
```

Теперь:
- данные передаются в **теле** запроса (JSON), а не в URL;
- FastAPI автоматически проверяет, что все поля присутствуют и правильного типа;
- в `/docs` появляется красивая автодокументация;
- ответ тоже становится строго описанным.

**На защите:** «Использую Pydantic-модели — встроенный механизм валидации FastAPI. Если клиент пришлёт неправильные данные, он получит ошибку 422 с описанием, что не так.»

---

### 3.2. Валидация полей через Pydantic

Если уже используешь Pydantic — можно сразу добавить ограничения:

```python
from pydantic import BaseModel, Field, HttpUrl

class ItemCreate(BaseModel):
    url: HttpUrl                              # должно быть валидным URL
    place: str = Field(min_length=1, max_length=100)
    comment: str = Field(max_length=1000)
```

Если кто-то отправит пустое `place` — FastAPI вернёт ошибку 422 ещё до того, как код дойдёт до БД.

---

### 3.3. `Enum` для статусов

**Что не так.** Магические строки `"in applic"`, `"accept"`, `"not accept"`, `"delete"` рассыпаны по коду. Если опечатаешься в одном месте — баг, который никто не поймает.

**Что делать.** Завести `Enum`:

```python
from enum import Enum

class ItemStatus(str, Enum):
    PENDING = "in applic"
    ACCEPTED = "accept"
    REJECTED = "not accept"
    DELETED = "delete"
```

И тогда:

```python
@app.put("/admin/items/restatus")
def restatus(url: str, status: ItemStatus):
    # FastAPI сам отвалидирует, что status — один из четырёх допустимых
    con = get_db_connection()
    try:
        cursor = con.execute(
            "UPDATE items SET status = ? WHERE url = ?",
            (status.value, url),
        )
        con.commit()
    finally:
        con.close()

    if cursor.rowcount == 0:
        raise HTTPException(404, "заявка не найдена")
    return {"message": f"статус изменён на {status.value}"}
```

При создании заявки:

```python
con.execute(
    "INSERT INTO items (url, place, comment, status) VALUES (?, ?, ?, ?)",
    (item.url, item.place, item.comment, ItemStatus.PENDING.value),
)
```

Теперь магических строк нет, и опечатка приведёт к ошибке Python ещё до запуска.

> **Совет.** Назвать `"in applic"` лучше как `"pending"` (в рассмотрении). Запись `"in applic"` выглядит как обрезанное `"in application"` — непонятно. Но если БД уже работает с этим значением, оставь как есть, чтобы не ломать данные.

---

### 3.4. Использовать `with` для соединения с БД

**Что не так.** В каждой функции одно и то же:

```python
con = get_db_connection()
cursor = con.cursor()
try:
    ...
finally:
    con.close()
```

Это можно сократить, потому что `sqlite3.Connection` поддерживает контекстный менеджер.

**Стало:**
```python
with get_db_connection() as con:
    rows = con.execute(
        "SELECT url, place, comment, status FROM items"
    ).fetchall()

return [dict(r) for r in rows]
```

`with` сам сделает `commit` (если не было ошибки) или `rollback` (если была), и закроет соединение.

> **Важно.** Контекстный менеджер `sqlite3.Connection` коммитит изменения, но **не закрывает соединение** автоматически — для этого нужен либо `con.close()` после `with`, либо обернуть в `contextlib.closing`. Для школьного проекта проще оставить явный `try / finally / close()`.

---

### 3.5. Объединить похожие эндпоинты

**Что не так.** `getall`, `getapplic`, `getaccept` — это одна и та же функция с разным фильтром по статусу.

**Что делать.** Можно сделать один эндпоинт с опциональным параметром:

```python
@app.get("/admin/items")
def list_items(status: ItemStatus | None = None):
    con = get_db_connection()
    try:
        if status is None:
            rows = con.execute(
                "SELECT url, place, comment, status FROM items"
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT url, place, comment, status FROM items WHERE status = ?",
                (status.value,),
            ).fetchall()
    finally:
        con.close()
    return [dict(r) for r in rows]
```

Теперь один эндпоинт работает за всех:
- `GET /admin/items` — все;
- `GET /admin/items?status=in%20applic` — на рассмотрении;
- `GET /admin/items?status=accept` — одобренные.

**Это не обязательно**, но если хочется добавить «глубину» проекту — это хороший повод поговорить на защите про принцип DRY (Don't Repeat Yourself — не повторяйся).

---

### 3.6. `db.py` исполняет SQL прямо при импорте

**Что не так.** В `db.py`:

```python
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS admins (...)")
...
conn.close()
```

Эти строки выполняются **в момент импорта** файла. Это значит, что любой `from db import ...` лезет в файловую систему. Плюс глобальные `conn` и `cursor` после `close()` остаются «битыми».

**Что делать.** Завернуть инициализацию в функцию:

```python
import sqlite3

DB_NAME = "maindb.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            password TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            place TEXT,
            comment TEXT,
            status TEXT
        )""")


if __name__ == "__main__":
    init_db()
    print("База инициализирована")
```

И в `main.py` один раз вызвать `init_db()` при запуске.

Заодно я добавил `UNIQUE` к `login` и `url` — это даст БД самой следить, чтобы не было дубликатов.

---

### 3.7. Проверить импорт `from proga.db import ...`

**Что не так.** В `main.py` написано:

```python
from proga.db import get_db_connection
```

Но в репозитории нет папки `proga/`. Скорее всего, локально у тебя структура такая:

```
proga/
├── main.py
└── db.py
```

а в репозитории файлы лежат уже без папки. Если проверяющий скачает код и попробует запустить — получит `ModuleNotFoundError`.

**Что делать.** Привести в порядок: либо добавить папку `proga/` с пустым `__init__.py` (чтобы это был «настоящий» Python-пакет), либо изменить импорт на:

```python
from db import get_db_connection
```

Проверь так: открой терминал в корне проекта и запусти:

```
python main.py
```

Если запускается без ошибок — значит импорт правильный.

---

## Раздел 4. Косметика (мелочи, но добавят балл)

### 4.1. Имена переменных

В Python принято использовать `snake_case` (слова через нижнее подчёркивание). У тебя:

| Сейчас      | Лучше          | Почему                      |
|-------------|----------------|-----------------------------|
| `SQLobject` | `rows`         | snake_case + понятнее       |
| `con`       | `conn`         | стандартное сокращение      |
| `applic`    | `pending_items`| понятнее, что возвращает    |
| `restatus`  | `update_status`| глагол + объект             |
| `allitems`  | `list_items`   | стандартное название «листинга» |

### 4.2. Описание API

Сейчас в `main.py` описание API в виде комментария-строки:

```python
'''
/admin/items/getall - возвращает все данные о предметах
...
'''
```

Лучше передать описание в FastAPI — тогда оно появится в `/docs`:

```python
app = FastAPI(
    title="Сервис потерянных вещей ИТ-Куб",
    description="API для подачи и обработки заявок о найденных вещах",
    version="1.0.0",
)
```

И к каждому эндпоинту можно добавить описание:

```python
@app.post(
    "/users/items/create",
    summary="Создать заявку",
    description="Создаёт новую заявку со статусом «на рассмотрении»",
)
def create_items(item: ItemCreate):
    ...
```

В автодокументации FastAPI (`http://127.0.0.1:8000/docs`) это всё красиво отобразится.

### 4.3. `requirements.txt`

**Обязательно** добавь файл `requirements.txt` в корень проекта:

```
fastapi
uvicorn
pydantic
```

Без него проверяющий не сможет установить зависимости одной командой `pip install -r requirements.txt`.

Если используешь конкретные версии — лучше зафиксировать:

```
fastapi==0.115.0
uvicorn==0.32.0
pydantic==2.9.0
```

Точные версии посмотри командой:

```
pip show fastapi uvicorn pydantic
```

### 4.4. Файл БД в репозитории

В репозитории лежит файл `maindb.db`. В реальных проектах файлы БД не хранят в git (там может быть личная информация пользователей, и при каждом запуске БД меняется).

Создай файл `.gitignore` с содержимым:

```
maindb.db
__pycache__/
*.pyc
.venv/
.idea/
.vscode/
```

Для защиты можно отдельно положить «демо-базу» с тестовыми данными в файл `maindb.example.db` или дать SQL-скрипт для создания тестовых записей.

### 4.5. Параметры запуска uvicorn

**Было:**
```python
if __name__ == "__main__":
    uvicorn.run(app)
```

**Стало:**
```python
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

Понятнее: видно, на каком хосте и порту запустится сервер.

---

## Раздел 5. Итоговый чек-лист

Распечатай и пройдись по пунктам перед защитой.

### Обязательно

- [ ] Все f-string SQL заменены на параметризованные запросы (`?` + кортеж)
- [ ] `return` вынесен из `finally`
- [ ] `commit()` убран после `SELECT`
- [ ] Опечатка `logan` → `login`
- [ ] `if not X is None` → `if X is not None`
- [ ] `not in res.keys()` → `not in res`
- [ ] `getapplic` фильтрует в SQL
- [ ] `restatus` проверяет `cursor.rowcount`
- [ ] `get_item` возвращает 404 при отсутствии заявки
- [ ] `restatus` возвращает 400 при невалидном статусе
- [ ] Добавлен `requirements.txt`
- [ ] Импорт `from proga.db` работает (или поправлен на `from db`)
- [ ] Файл `maindb.db` убран из git, добавлен `.gitignore`

### Очень желательно (даст плюсы на защите)

- [ ] Pydantic-модели `ItemCreate`, `ItemOut`
- [ ] `Enum ItemStatus` для статусов
- [ ] Простая авторизация админа: `POST /admin/login` + токен в заголовке
- [ ] Хеширование пароля (`hashlib.sha256`)
- [ ] Объединение `getall` / `getapplic` / `getaccept` в один эндпоинт с фильтром
- [ ] Описание API через `FastAPI(title=..., description=...)`
- [ ] `init_db()` вместо side-effect при импорте
- [ ] `UNIQUE` на `items.url` и `admins.login`

### По желанию (если осталось время)

- [ ] Использование `bcrypt` вместо `sha256`
- [ ] Логирование (модуль `logging`)
- [ ] Простые тесты на `pytest` + `TestClient`
- [ ] Пагинация (`limit`, `offset`)

---

## Раздел 6. Готовые формулировки для защиты

| Вопрос комиссии | Что отвечать |
|---|---|
| Защищён ли сервис от SQL-инъекций? | «Да, я использую параметризованные запросы — данные подставляются через знак вопроса, а не в текст SQL.» |
| Как у вас хранятся пароли? | «В виде хешей SHA-256. По хешу пароль восстановить нельзя — это защищает от утечки БД.» |
| Как защищена админка? | «Админ логинится через `POST /admin/login`, получает токен, и без него `/admin/*` эндпоинты возвращают 401.» |
| Что будет, если клиент пришлёт неправильные данные? | «Pydantic автоматически проверит типы и обязательные поля, FastAPI вернёт ошибку 422 с описанием.» |
| Зачем `Enum` для статусов? | «Чтобы не было опечаток в магических строках — все допустимые значения в одном месте.» |
| Что вернёт сервис, если заявки нет? | «HTTP 404 с понятным описанием — клиент по коду сразу понимает, что ресурс не найден.» |
| Зачем вообще FastAPI? | «Это современный фреймворк для API на Python. Поддерживает асинхронность, автоматическую валидацию через Pydantic и сам генерирует документацию в `/docs`.» |

---

## Раздел 7. Большой пример «как мог бы выглядеть весь `main.py`»

Это **рекомендованный** вариант — собрано всё, что обсуждалось выше. Можешь использовать как образец.

```python
import hashlib
import secrets
import sqlite3
from enum import Enum

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from db import get_db_connection, init_db


# ======= модели =======

class ItemStatus(str, Enum):
    PENDING = "in applic"
    ACCEPTED = "accept"
    REJECTED = "not accept"
    DELETED = "delete"


class ItemCreate(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    place: str = Field(min_length=1, max_length=100)
    comment: str = Field(max_length=1000)


class ItemOut(BaseModel):
    url: str
    place: str
    comment: str
    status: ItemStatus


class LoginRequest(BaseModel):
    username: str
    password: str


# ======= вспомогательные функции =======

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


active_tokens: set[str] = set()


def check_admin(authorization: str = Header(...)):
    parts = authorization.split()
    if len(parts) != 2 or parts[0] != "Bearer" or parts[1] not in active_tokens:
        raise HTTPException(status_code=401, detail="нужна авторизация")


# ======= приложение =======

app = FastAPI(
    title="Сервис потерянных вещей ИТ-Куб",
    description="API для подачи и обработки заявок о найденных вещах",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup():
    init_db()


# ======= авторизация =======

@app.post("/admin/login")
def login(payload: LoginRequest):
    con = get_db_connection()
    try:
        row = con.execute(
            "SELECT password FROM admins WHERE login = ?",
            (payload.username,),
        ).fetchone()
    finally:
        con.close()

    if row is None or row["password"] != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="неверный логин или пароль")

    token = secrets.token_hex(16)
    active_tokens.add(token)
    return {"token": token}


# ======= админские эндпоинты =======

@app.get(
    "/admin/items",
    response_model=list[ItemOut],
    dependencies=[Depends(check_admin)],
    summary="Список заявок (опционально с фильтром по статусу)",
)
def list_items(status: ItemStatus | None = None):
    con = get_db_connection()
    try:
        if status is None:
            rows = con.execute(
                "SELECT url, place, comment, status FROM items"
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT url, place, comment, status FROM items WHERE status = ?",
                (status.value,),
            ).fetchall()
    finally:
        con.close()
    return [dict(r) for r in rows]


@app.put(
    "/admin/items/restatus",
    dependencies=[Depends(check_admin)],
    summary="Изменить статус заявки",
)
def update_status(url: str, status: ItemStatus):
    con = get_db_connection()
    try:
        cursor = con.execute(
            "UPDATE items SET status = ? WHERE url = ?",
            (status.value, url),
        )
        con.commit()
    finally:
        con.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="заявка не найдена")
    return {"message": f"статус изменён на {status.value}"}


# ======= пользовательские эндпоинты =======

@app.post(
    "/users/items/create",
    response_model=ItemOut,
    status_code=201,
    summary="Создать заявку",
)
def create_item(item: ItemCreate):
    con = get_db_connection()
    try:
        try:
            con.execute(
                "INSERT INTO items (url, place, comment, status) VALUES (?, ?, ?, ?)",
                (item.url, item.place, item.comment, ItemStatus.PENDING.value),
            )
            con.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="заявка с таким url уже существует")
    finally:
        con.close()

    return ItemOut(
        url=item.url,
        place=item.place,
        comment=item.comment,
        status=ItemStatus.PENDING,
    )


@app.get(
    "/users/items/getitem/{url:path}",
    response_model=ItemOut,
    summary="Получить заявку по url",
)
def get_item(url: str):
    con = get_db_connection()
    try:
        row = con.execute(
            "SELECT url, place, comment, status FROM items WHERE url = ?",
            (url,),
        ).fetchone()
    finally:
        con.close()

    if row is None:
        raise HTTPException(status_code=404, detail="заявка не найдена")
    return dict(row)


@app.get(
    "/users/items/getaccept",
    response_model=list[ItemOut],
    summary="Список одобренных заявок",
)
def get_accepted():
    con = get_db_connection()
    try:
        rows = con.execute(
            "SELECT url, place, comment, status FROM items WHERE status = ?",
            (ItemStatus.ACCEPTED.value,),
        ).fetchall()
    finally:
        con.close()
    return [dict(r) for r in rows]


# ======= точка входа =======

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

И обновлённый `db.py`:

```python
import sqlite3

DB_NAME = "maindb.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            password TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            place TEXT,
            comment TEXT,
            status TEXT
        )""")


if __name__ == "__main__":
    init_db()
    print("База инициализирована")
```

---

## Что почитать

Если интересно, после защиты можно посмотреть глубже:

- **FastAPI tutorial** — официальный, очень подробный: <https://fastapi.tiangolo.com/tutorial/>
- **PEP 8** — стандарт оформления Python-кода: <https://peps.python.org/pep-0008/>
- **OWASP Top 10** — список самых частых веб-уязвимостей: <https://owasp.org/www-project-top-ten/>
- **bcrypt** — нормальная библиотека для хеширования паролей.
- **SQLAlchemy** — следующий шаг после ручных SQL-запросов.

Удачной защиты!
