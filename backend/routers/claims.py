from fastapi import APIRouter, Depends, HTTPException

from auth import require_admin
from db import get_db_connection
from models import (
    Claim,
    ClaimCreate,
    ClaimStatusUpdate,
    MessageResponse,
    CLAIM_STATUSES,
)

router = APIRouter(tags=["claims"])


def _row_to_claim(row) -> Claim:
    return Claim(
        id=row["id"],
        item_id=row["item_id"],
        fio=row["fio"],
        group_name=row["group_name"],
        teacher=row["teacher"],
        status=row["status"],
        created_at=row["created_at"],
    )


@router.post("/users/claims", response_model=Claim)
def create_claim(payload: ClaimCreate):
    conn = get_db_connection()
    try:
        item = conn.execute(
            "SELECT id FROM items WHERE id = ?", (payload.item_id,)
        ).fetchone()
        if item is None:
            raise HTTPException(status_code=404, detail="Предмет не найден")
        cur = conn.execute(
            "INSERT INTO claims (item_id, fio, group_name, teacher) "
            "VALUES (?, ?, ?, ?)",
            (payload.item_id, payload.fio, payload.group_name, payload.teacher),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, item_id, fio, group_name, teacher, status, created_at "
            "FROM claims WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
    finally:
        conn.close()
    return _row_to_claim(row)


@router.get(
    "/admin/claims",
    response_model=list[Claim],
    dependencies=[Depends(require_admin)],
)
def admin_list_claims():
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT id, item_id, fio, group_name, teacher, status, created_at "
            "FROM claims ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_claim(r) for r in rows]


@router.put(
    "/admin/claims/{claim_id}/status",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
)
def admin_update_claim_status(claim_id: int, payload: ClaimStatusUpdate):
    if payload.status not in CLAIM_STATUSES:
        raise HTTPException(status_code=400, detail="Неверный статус")
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "UPDATE claims SET status = ? WHERE id = ?",
            (payload.status, claim_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
    finally:
        conn.close()
    return MessageResponse(message=f"Статус заявки изменён на {payload.status}")
