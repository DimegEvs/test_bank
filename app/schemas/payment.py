"""Схемы платежей: вывод и вебхук."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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
