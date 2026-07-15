from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account
from app.services.base import BaseService


class AccountService(BaseService[Account]):
    """Сервис для работы со счетами в базе данных."""

    model = Account

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: int) -> list[Account]:
        """Возвращает список счетов пользователя.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            user_id (int): Идентификатор пользователя.

        Returns:
            list[Account]: Список счетов пользователя.
        """
        result = await db.execute(
            select(Account).where(Account.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id_and_user(
        db: AsyncSession, account_id: int, user_id: int
    ) -> Account | None:
        """Возвращает счёт по идентификатору и владельцу.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            account_id (int): Идентификатор счёта.
            user_id (int): Идентификатор пользователя-владельца.

        Returns:
            Account | None: Найденный счёт или None.
        """
        result = await db.execute(
            select(Account).where(
                Account.id == account_id,
                Account.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        *,
        commit: bool = True,
        user_id: int,
        account_id: int | None = None,
        balance: int = 0,
    ) -> Account:
        """Создаёт новый счёт для пользователя.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            commit (bool, optional): Если True — фиксирует транзакцию (по умолчанию).
                Если False — только flush (для составных транзакций).
            user_id (int): Идентификатор пользователя-владельца.
            account_id (int | None, optional): Явный идентификатор счёта
                (если None, назначается БД).
            balance (int, optional): Начальный баланс (по умолчанию 0).

        Returns:
            Account: Созданный счёт.
        """
        return await super().create(
            db,
            commit=commit,
            id=account_id,
            user_id=user_id,
            balance=balance,
        )
