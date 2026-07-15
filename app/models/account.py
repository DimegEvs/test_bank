from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Account(Base):
    """Модель счёта пользователя.

    Attributes:
        id (int): Уникальный идентификатор счёта.
        user_id (int): Идентификатор владельца счёта.
        balance (Decimal): Баланс счёта (по умолчанию 0.00).
        created_at (datetime): Дата и время создания.
        user: Связь с моделью пользователя.
        payments: Список платежей по счёту.
    """
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="accounts")
    payments = relationship("Payment", back_populates="account")
