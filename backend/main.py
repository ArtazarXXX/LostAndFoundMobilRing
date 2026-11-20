from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from db import init_db
from routers import claims, items, upload

init_db()

app = FastAPI(title="ИТ-Куб: бюро находок")

app.include_router(items.router)
app.include_router(claims.router)
app.include_router(upload.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/admin-ui", StaticFiles(directory="admin", html=True), name="admin-ui")


@app.get("/")
def root():
    return RedirectResponse(url="/admin-ui/")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
