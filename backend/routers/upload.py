import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from auth import require_admin
from models import UploadResponse

router = APIRouter(tags=["upload"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 5 * 1024 * 1024


@router.post(
    "/upload",
    response_model=UploadResponse,
    dependencies=[Depends(require_admin)],
)
async def upload_photo(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Допустимы только jpg/png/webp")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Файл больше 5 МБ")

    name = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / name).write_bytes(data)

    # Возвращаем относительный путь — клиент (мобилка/админка) сам резолвит к base URL.
    # Так одна и та же запись в БД работает и для админки на 127.0.0.1, и для мобилки через 10.0.2.2.
    return UploadResponse(url=f"/uploads/{name}")
