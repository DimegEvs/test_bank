from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.router import admin_router, auth_router, users_router, webhook_router

templates = Jinja2Templates(directory="templates")


app = FastAPI(
    title="Test Bank API",
    description="REST API for user accounts and payment processing",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(webhook_router)


# UI — отдача через Jinja2 templates
@app.get("/", tags=["UI"])
async def ui(request: Request):
    """Отдаёт главную страницу веб-интерфейса.

    Args:
        request (Request): Объект запроса FastAPI.

    Returns:
        TemplateResponse: HTML-шаблон index.html.
    """
    return templates.TemplateResponse("index.html", {"request": request})
