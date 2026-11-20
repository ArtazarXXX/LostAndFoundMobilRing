import os
import random
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from auth import require_admin
from db import get_db_connection
from models import (
    ChatMessage,
    ChatMessageCreate,
    Item,
    ItemCreate,
    ItemStatusUpdate,
    MessageResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
    ITEM_STATUSES,
)

router = APIRouter(tags=["items"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 5 * 1024 * 1024


def _row_to_item(row) -> Item:
    # Safely extract keys in case of older SQLite rows
    keys = row.keys() if hasattr(row, "keys") else []
    return Item(
        id=row["id"],
        url=row["url"],
        place=row["place"],
        comment=row["comment"],
        status=row["status"],
        type=row["type"] if "type" in keys else "found",
        category=row["category"] if "category" in keys else "other",
        created_at=row["created_at"] if "created_at" in keys else "",
        return_code=row["return_code"] if "return_code" in keys else "1234",
        author=row["author"] if "author" in keys else "Дежурный",
    )


@router.get("/users/items/getaccept", response_model=list[Item])
def list_accepted(
    item_type: Optional[str] = Query(None, alias="type"),
    category: Optional[str] = Query(None),
):
    conn = get_db_connection()
    try:
        query = "SELECT * FROM items WHERE status IN ('accept', 'returned')"
        params = []
        if item_type:
            query += " AND type = ?"
            params.append(item_type)
        if category and category != "all":
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY id DESC"
        rows = conn.execute(query, tuple(params)).fetchall()
    finally:
        conn.close()
    return [_row_to_item(r) for r in rows]


@router.get("/users/items/getitem/{item_id}", response_model=Item)
def get_item(item_id: int):
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM items WHERE id = ?",
            (item_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    return _row_to_item(row)


@router.post("/users/items", response_model=Item)
async def user_submit_item(
    photo: UploadFile = File(...),
    place: str = Form(..., min_length=1, max_length=200),
    comment: str = Form(..., min_length=1, max_length=1000),
    type: str = Form("found"),
    category: str = Form("other"),
    author: str = Form("Максим Кабанов"),
):
    ext = os.path.splitext(photo.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Допустимы только jpg/png/webp")

    data = await photo.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Файл больше 5 МБ")

    name = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / name).write_bytes(data)
    url = f"/uploads/{name}"

    # Generate 4-digit code for safe handover
    return_code = f"{random.randint(1000, 9999)}"

    conn = get_db_connection()
    try:
        cur = conn.execute(
            "INSERT INTO items (url, place, comment, status, type, category, return_code, author) "
            "VALUES (?, ?, ?, 'accept', ?, ?, ?, ?)",
            (url, place, comment, type, category, return_code, author),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM items WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
    finally:
        conn.close()
    return _row_to_item(row)


@router.get("/users/items/{item_id}/messages", response_model=list[ChatMessage])
def get_item_messages(item_id: int):
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT id, item_id, sender_name, text, created_at FROM messages "
            "WHERE item_id = ? ORDER BY id ASC",
            (item_id,),
        ).fetchall()
    finally:
        conn.close()
    return [
        ChatMessage(
            id=r["id"],
            item_id=r["item_id"],
            sender_name=r["sender_name"],
            text=r["text"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post("/users/items/{item_id}/messages", response_model=ChatMessage)
def post_item_message(item_id: int, payload: ChatMessageCreate):
    conn = get_db_connection()
    try:
        # Check item exists
        item = conn.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
        if item is None:
            raise HTTPException(status_code=404, detail="Предмет не найден")

        cur = conn.execute(
            "INSERT INTO messages (item_id, sender_name, text) VALUES (?, ?, ?)",
            (item_id, payload.sender_name, payload.text),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, item_id, sender_name, text, created_at FROM messages WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
    finally:
        conn.close()

    return ChatMessage(
        id=row["id"],
        item_id=row["item_id"],
        sender_name=row["sender_name"],
        text=row["text"],
        created_at=row["created_at"],
    )


@router.post("/users/items/{item_id}/verify_code", response_model=VerifyCodeResponse)
def verify_return_code(item_id: int, payload: VerifyCodeRequest):
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT id, return_code, status FROM items WHERE id = ?",
            (item_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Предмет не найден")

        expected = str(row["return_code"]).strip()
        actual = str(payload.code).strip()

        if expected != actual:
            return VerifyCodeResponse(
                success=False,
                message="Неверный проверочный код. Уточните код у владельца.",
                status=row["status"],
            )

        # Mark as returned
        conn.execute(
            "UPDATE items SET status = 'returned' WHERE id = ?",
            (item_id,),
        )
        # Add a system message in chat
        conn.execute(
            "INSERT INTO messages (item_id, sender_name, text) VALUES (?, ?, ?)",
            (item_id, "Система", "🎉 Вещь успешно передана законному владельцу! Возврат подтверждён проверочным кодом."),
        )
        conn.commit()
    finally:
        conn.close()

    return VerifyCodeResponse(
        success=True,
        message="Код подтверждён! Статус вещи изменён на 'Возвращено'.",
        status="returned",
    )


@router.get(
    "/admin/items/getall",
    response_model=list[Item],
    dependencies=[Depends(require_admin)],
)
def admin_list_all():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    finally:
        conn.close()
    return [_row_to_item(r) for r in rows]


@router.get(
    "/admin/items/getapplic",
    response_model=list[Item],
    dependencies=[Depends(require_admin)],
)
def admin_list_pending():
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM items WHERE status = 'in_applic' ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_item(r) for r in rows]


@router.post(
    "/admin/items",
    response_model=Item,
    dependencies=[Depends(require_admin)],
)
def admin_create_item(payload: ItemCreate):
    return_code = f"{random.randint(1000, 9999)}"
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "INSERT INTO items (url, place, comment, status, type, category, return_code) "
            "VALUES (?, ?, ?, 'accept', ?, ?, ?)",
            (payload.url, payload.place, payload.comment, payload.type, payload.category, return_code),
        )
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute("SELECT * FROM items WHERE id = ?", (new_id,)).fetchone()
    finally:
        conn.close()
    return _row_to_item(row)


@router.put(
    "/admin/items/{item_id}/status",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
)
def admin_update_status(item_id: int, payload: ItemStatusUpdate):
    if payload.status not in ITEM_STATUSES:
        raise HTTPException(status_code=400, detail="Неверный статус")
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "UPDATE items SET status = ? WHERE id = ?",
            (payload.status, item_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Предмет не найден")
    finally:
        conn.close()
    return MessageResponse(message=f"Статус изменён на {payload.status}")

