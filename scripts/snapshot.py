#!/usr/bin/env python3
"""
Снимок состояния бэка в assets мобилки.

Что делает:
  1. Тянет /users/items/getaccept с локального бэка.
  2. Для каждой вещи скачивает фото (любой URL: и внешние https, и /uploads/...).
  3. Сохраняет фото в mobile/app/src/main/assets/seed_images/<id>.<ext>.
  4. Переписывает item.url на 'file:///android_asset/seed_images/<id>.<ext>'.
  5. Записывает результат в mobile/app/src/main/assets/seed_items.json.

После этого ./gradlew assembleDebug — и APK содержит актуальный snapshot.
На стороннем устройстве без сети мобилка покажет именно эти вещи.

Запуск:
  python3 scripts/snapshot.py
  python3 scripts/snapshot.py --base http://192.168.1.10:8000  # бэк на другом хосте
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "mobile" / "app" / "src" / "main" / "assets"
IMAGES_DIR = ASSETS_DIR / "seed_images"
SEED_JSON = ASSETS_DIR / "seed_items.json"

DEFAULT_BASE = "http://127.0.0.1:8000"
HEADERS = {"User-Agent": "itcube-snapshot/1.0"}


def fetch_json(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def absolute(base: str, url: str) -> str:
    if url.startswith("/"):
        return base.rstrip("/") + url
    return url


def guess_ext(url: str, data: bytes) -> str:
    path = urllib.parse.urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".jpg"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE,
                        help="базовый URL бэка")
    args = parser.parse_args()

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    # Чистим старые картинки, чтобы не таскать мусор
    for old in IMAGES_DIR.glob("*"):
        old.unlink()

    items_url = args.base.rstrip("/") + "/users/items/getaccept"
    print(f"[+] fetch {items_url}")
    try:
        items = fetch_json(items_url)
    except Exception as e:
        print(f"[!] не смог получить список: {e}", file=sys.stderr)
        return 1

    print(f"[+] получено {len(items)} вещей")

    snapshot = []
    for it in items:
        item_id = it["id"]
        photo_url = absolute(args.base, it["url"])
        try:
            data = fetch_bytes(photo_url)
            ext = guess_ext(photo_url, data)
            out = IMAGES_DIR / f"{item_id}{ext}"
            out.write_bytes(data)
            local_url = f"file:///android_asset/seed_images/{item_id}{ext}"
            print(f"    #{item_id:>2}  ok ({len(data) // 1024} KiB)  -> {out.name}")
        except Exception as e:
            print(f"    #{item_id:>2}  фото не скачалось ({e}); кладу с оригинальным URL")
            local_url = it["url"]

        snapshot.append({
            "id": item_id,
            "url": local_url,
            "place": it["place"],
            "comment": it["comment"],
            "status": it["status"],
        })

    SEED_JSON.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[+] записано в {SEED_JSON.relative_to(ROOT)}")
    print("[i] теперь: cd mobile && ./gradlew assembleDebug")
    return 0


if __name__ == "__main__":
    sys.exit(main())
