from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account, Payment
from app.services.base import BaseService


class PaymentService(BaseService[Payment]):
    """Сервис для работы с платежами в базе данных."""

    model = Payment

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: int) -> list[Payment]:
        """Возвращает список платежей пользователя.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            user_id (int): Идентификатор пользователя.

        Returns:
            list[Payment]: Список платежей пользователя.
        """
        result = await db.execute(
            select(Payment).where(Payment.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_transaction_id(
        db: AsyncSession, transaction_id: str
    ) -> Payment | None:
        """Возвращает платёж по уникальному идентификатору транзакции.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            transaction_id (str): Уникальный идентификатор транзакции.

        Returns:
            Payment | None: Найденный платёж или None.
        """
        result = await db.execute(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def create_and_credit(
        cls,
        db: AsyncSession,
        account: Account,
        transaction_id: str,
        user_id: int,
        amount: Decimal,
        *,
        commit: bool = True,
    ) -> Literal["processed", "already_processed"]:
        """Сохраняет платёж и начисляет сумму на баланс счёта.

        Выполняется как одна атомарная операция: если ``commit=True``,
        фиксирует всю текущую транзакцию сессии (включая изменения,
        сделанные другими сервисами с ``commit=False``).

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            account (Account): Счёт для начисления.
            transaction_id (str): Уникальный идентификатор транзакции.
            user_id (int): Идентификатор пользователя.
            amount (Decimal): Сумма пополнения.
            commit (bool, optional): Если True — фиксирует транзакцию (по умолчанию).

        Returns:
            Literal["processed", "already_processed"]: Статус операции.
                "processed" — платёж сохранён, баланс обновлён.
                "already_processed" — транзакция уже существует (состояние гонки).
        """
        payment = Payment(
            transaction_id=transaction_id,
            account_id=account.id,
            user_id=user_id,
            amount=amount,
        )
        db.add(payment)
        account.balance += amount
        await db.flush()

        if not commit:
            return "processed"

        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            return "already_processed"

        return "processed"
