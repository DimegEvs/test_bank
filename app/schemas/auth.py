"""Схемы аутентификации: вход, регистрация, токен."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Схема запроса для входа (авторизации).

    Attributes:
        email (EmailStr): Email пользователя.
        password (str): Пароль открытым текстом.
    """
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Схема запроса для регистрации нового пользователя.

    Attributes:
        email (EmailStr): Email пользователя.
        full_name (str): Полное имя (1-255 символов).
        password (str): Пароль (6-128 символов).
    """
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    """Схема ответа с JWT-токеном.

    Attributes:
        access_token (str): JWT access-токен.
        token_type (str): Тип токена (Cookie).
        role (str): Роль пользователя (user или admin).
    """
    access_token: str
    token_type: str = 'Cookie'
    role: str
1