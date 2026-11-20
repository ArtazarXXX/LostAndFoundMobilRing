import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from db import get_db_connection

security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT password_hash FROM admins WHERE login = ?",
            (credentials.username,),
        ).fetchone()
    finally:
        conn.close()

    if row is None or not bcrypt.checkpw(
        credentials.password.encode(), row["password_hash"].encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
