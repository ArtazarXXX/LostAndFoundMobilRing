import sqlite3
import random
import bcrypt

DB_NAME = "maindb.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        place TEXT NOT NULL,
        comment TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'in_applic',
        type TEXT NOT NULL DEFAULT 'found',
        category TEXT NOT NULL DEFAULT 'other',
        created_at TEXT NOT NULL DEFAULT '',
        return_code TEXT NOT NULL DEFAULT '1234'
    )""")

    # Migration: add columns if table already existed without them
    cur.execute("PRAGMA table_info(items)")
    existing_cols = {col["name"] for col in cur.fetchall()}
    if "type" not in existing_cols:
        cur.execute("ALTER TABLE items ADD COLUMN type TEXT NOT NULL DEFAULT 'found'")
    if "category" not in existing_cols:
        cur.execute("ALTER TABLE items ADD COLUMN category TEXT NOT NULL DEFAULT 'other'")
    if "created_at" not in existing_cols:
        cur.execute("ALTER TABLE items ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
    if "return_code" not in existing_cols:
        cur.execute("ALTER TABLE items ADD COLUMN return_code TEXT NOT NULL DEFAULT '1234'")
    if "author" not in existing_cols:
        cur.execute("ALTER TABLE items ADD COLUMN author TEXT NOT NULL DEFAULT 'Дежурный'")

    cur.execute("""CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        fio TEXT NOT NULL,
        group_name TEXT NOT NULL,
        teacher TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        sender_name TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
    )""")

    cur.execute("SELECT COUNT(*) AS n FROM admins")
    if cur.fetchone()["n"] == 0:
        pw_hash = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
        cur.execute("INSERT INTO admins (login, password_hash) VALUES (?, ?)",
                    ("admin", pw_hash))

    # Clean re-seed to guarantee 100% matched images and realistic items
    cur.execute("DELETE FROM claims")
    cur.execute("DELETE FROM messages")
    cur.execute("DELETE FROM items")
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('items', 'claims', 'messages')")
    except Exception:
        pass
    sample = [
        # 1. Headphones (matches 7d641929fae34015868fd3dd36af62e0.jpg)
        ("/uploads/7d641929fae34015868fd3dd36af62e0.jpg",
         "Кабинет графического дизайна", "Полноразмерные наушники на деревянном столе. Забыты после лекции по медиа.",
         "accept", "found", "tech", "Сегодня, 13:40", "6412", "Анастасия Александровна"),

        # 2. Red Kanken Backpack (matches a3aec1dfbf654edea68da33c89881d87.jpg)
        ("/uploads/a3aec1dfbf654edea68da33c89881d87.jpg",
         "Раздевалка", "Найден красный рюкзак Fjallraven Kanken на скамейке в раздевалке.",
         "accept", "found", "clothes", "Сегодня, 12:15", "4821", "Дежурный по гардеробу"),

        # 3. iPhone 13 (matches b03bef2df0fb413b9988261d795e22e7.jpg) - Автор: Максим Кабанов!
        ("/uploads/b03bef2df0fb413b9988261d795e22e7.jpg",
         "Кабинет мобильной разработки", "Тёмно-синий iPhone 13, лежал на парте 2 ряда у окна после урока.",
         "accept", "found", "tech", "Сегодня, 11:30", "7392", "Максим Кабанов"),

        # 4. Keys with blue fob (matches 19fa2b01e10549a08b592cc4d2dbec9c.jpg)
        ("/uploads/19fa2b01e10549a08b592cc4d2dbec9c.jpg",
         "Коридор 1 этажа", "Связка из трёх ключей (Punto, Sami) с синим брелоком домофона.",
         "accept", "found", "keys", "Вчера, 16:20", "9021", "Дмитрий Семенов"),

        # 5. Student Card (matches card.jpg)
        ("/uploads/card.jpg",
         "Коридор 1 этажа", "Пластиковый пропуск учащегося с синей шейной лентой. Оставлен на турникете.",
         "accept", "found", "cards", "Сегодня, 08:30", "3185", "Пост охраны"),

        # 6. Colorful umbrella (matches dc34568a822844ec821f45ca6581b575.jpg)
        ("/uploads/dc34568a822844ec821f45ca6581b575.jpg",
         "Раздевалка", "Складной чёрный зонт с ярким геометрическим абстрактным рисунком.",
         "accept", "found", "other", "Вчера, 17:50", "1940", "Администратор"),

        # 7. Pencil case (matches pencil_case.jpg)
        ("/uploads/pencil_case.jpg",
         "Кабинет 5", "Синий тканевый пенал с цветными карандашами и ручками на 3 парте.",
         "accept", "found", "other", "Вчера, 15:10", "5812", "Екатерина Смирнова"),

        # 8. Sneakers - Автор: Максим Кабанов (matches c746dcad0c8b451f8dbda6c374baa947.jpg)
        ("/uploads/c746dcad0c8b451f8dbda6c374baa947.jpg",
         "Раздевалка", "Потерял сменную обувь: серые кроссовки Adidas Spezial (Moscow) с полосками, 42 размер.",
         "accept", "lost", "clothes", "Сегодня, 10:45", "5192", "Максим Кабанов"),

        # 9. MacBook - Автор: Максим Кабанов (matches seed_images/6.jpg)
        ("file:///android_asset/seed_images/6.jpg",
         "Кабинет 10", "Забыл серебристый ноутбук Apple MacBook на столике у окна.",
         "accept", "lost", "tech", "Сегодня, 09:15", "8824", "Максим Кабанов"),

        # 10. Colorful Backpack (matches a3bcc5d1c1464057b990308d8718e7c6.jpg)
        ("/uploads/a3bcc5d1c1464057b990308d8718e7c6.jpg",
         "Кабинет 3", "Потерян разноцветный школьный рюкзак с нашивкой (зелёный верх, фиолетовый карман).",
         "accept", "lost", "clothes", "Вчера, 13:20", "4310", "Алиса Морозова"),

        # 11. Black headphones (matches seed_images/2.jpg)
        ("file:///android_asset/seed_images/2.jpg",
         "Кабинет 11", "Потеряны чёрные накладные проводные наушники после репетиции.",
         "accept", "lost", "tech", "16 ноя, 18:30", "2751", "Кирилл В."),

        # 12. Returned green bottle (matches seed_images/3.jpg)
        ("file:///android_asset/seed_images/3.jpg",
         "Кабинет робототехники", "Матовая зелёная термобутылка для воды. Успешно возвращена владельцу!",
         "returned", "found", "other", "15 ноя, 14:00", "2048", "Преподаватель Сергей"),

        # 13. Returned pass card - Автор: Максим Кабанов (matches card.jpg)
        ("/uploads/card.jpg",
         "Учительская", "Терял электронный пропуск с лентой. Вещь благополучно возвращена!",
         "returned", "lost", "cards", "14 ноя, 08:20", "9910", "Максим Кабанов"),
    ]
    cur.executemany(
        "INSERT INTO items (url, place, comment, status, type, category, created_at, return_code, author) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        sample,
    )

    # Seed sample messages for item 1
    cur.execute("DELETE FROM messages")
    cur.execute(
        "INSERT INTO messages (item_id, sender_name, text) VALUES (?, ?, ?)",
        (1, "Максим Кабанов", "Здравствуйте! Это мои наушники, забыл после урока.")
    )
    cur.execute(
        "INSERT INTO messages (item_id, sender_name, text) VALUES (?, ?, ?)",
        (1, "Анастасия Александровна", "Привет, Максим! Наушники у меня в учительской. Заходи на перемене!")
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("DB initialized.")

