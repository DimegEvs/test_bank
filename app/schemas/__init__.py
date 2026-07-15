from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
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
        token_type (str): Тип токена (bearer).
        role (str): Роль пользователя (user или admin).
    """
    access_token: str
    token_type: str = 'Bearer'
    role: str


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------
class AccountOut(BaseModel):
    """Схема ответа с данными счёта.

    Attributes:
        id (int): Идентификатор счёта.
        user_id (int): Идентификатор владельца.
        balance (Decimal): Баланс счёта.
        created_at (datetime): Дата и время создания.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    balance: Decimal
    created_at: datetime


class AccountCreate(BaseModel):
    """Схема запроса для создания счёта.

    Attributes:
        balance (Decimal): Начальный баланс (по умолчанию 0.00, только для admin).
    """
    balance: Decimal = Field(default=Decimal("0.00"), ge=0)


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------
class PaymentOut(BaseModel):
    """Схема ответа с данными платежа.

    Attributes:
        id (int): Идентификатор платежа.
        transaction_id (str): Уникальный идентификатор транзакции.
        account_id (int): Идентификатор счёта.
        user_id (int): Идентификатор пользователя.
        amount (Decimal): Сумма пополнения.
        created_at (datetime): Дата и время создания.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    account_id: int
    user_id: int
    amount: Decimal
    created_at: datetime


class WebhookRequest(BaseModel):
    """Схема запроса вебхука от сторонней платёжной системы.

    Attributes:
        transaction_id (str): Уникальный идентификатор транзакции.
        user_id (int): Идентификатор пользователя.
        account_id (int): Идентификатор счёта.
        amount (Decimal): Сумма пополнения.
        signature (str): SHA256-подпись объекта.
    """
    transaction_id: str
    user_id: int
    account_id: int
    amount: Decimal
    signature: str
