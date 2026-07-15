from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Payment(Base):
    """Модель платежа (пополнения счёта).

    Attributes:
        id (int): Уникальный идентификатор платежа.
        transaction_id (str): Уникальный идентификатор транзакции в сторонней системе.
        account_id (int): Идентификатор счёта.
        user_id (int): Идентификатор пользователя.
        amount (Decimal): Сумма пополнения.
        created_at (datetime): Дата и время создания.
        account: Связь с моделью счёта.
        user: Связь с моделью пользователя.
    """
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    account = relationship("Account", back_populates="payments")
    user = relationship("User", back_populates="payments")
