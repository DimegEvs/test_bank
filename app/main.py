from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.router import admin_router, auth_router, users_router, webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения: запуск и завершение.

    Args:
        app (FastAPI): Экземпляр приложения FastAPI.

    Yields:
        None: Контекст активного приложения.
    """
    print("Starting application...")
    yield
    print("Shutting down application...")


app = FastAPI(
    title="Test Bank API",
    description="REST API for user accounts and payment processing",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(webhook_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка работоспособности приложения.

    Returns:
        dict: Статус приложения.
    """
    return {"status": "ok"}


# UI — отдача статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/ui", tags=["UI"])
async def ui():
    """Отдаёт главную страницу веб-интерфейса.

    Returns:
        FileResponse: HTML-файл index.html.
    """
    return FileResponse("static/index.html")
