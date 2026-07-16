"""Схемы пользователей: вывод, создание, обновление."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    """Схема ответа с данными пользователя.

    Attributes:
        id (int): Идентификатор пользователя.
        email (EmailStr): Email пользователя.
        full_name (str): Полное имя пользователя.
        role (str): Роль пользователя.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str


class UserCreate(BaseModel):
    """Схема запроса для создания пользователя.

    Attributes:
        email (EmailStr): Email пользователя.
        full_name (str): Полное имя (1-255 символов).
        password (str): Пароль (6-128 символов).
        role (str): Роль (user или admin, по умолчанию user).
    """
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="user", pattern="^(user|admin)$")


class UserUpdate(BaseModel):
    """Схема запроса для обновления пользователя.

    Все поля опциональны — обновляются только переданные.

    Attributes:
        email (EmailStr | None): Новый email.
        full_name (str | None): Новое полное имя.
        password (str | None): Новый пароль.
        role (str | None): Новая роль.
    """
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    role: str | None = Field(default=None, pattern="^(user|admin)$")
