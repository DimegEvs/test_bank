"""Схемы счетов: вывод и создание."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


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
