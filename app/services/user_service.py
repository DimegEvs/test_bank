from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.security import hash_password
from app.services.base import BaseService


class UserService(BaseService[User]):
    """Сервис для работы с пользователями в базе данных."""

    model = User

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """Возвращает пользователя по email.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            email (str): Email пользователя.

        Returns:
            User | None: Найденный пользователь или None.
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        *,
        commit: bool = True,
        email: str,
        full_name: str,
        password: str,
        role: str = "user",
    ) -> User:
        """Создаёт нового пользователя. Пароль хешируется автоматически.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            commit (bool, optional): Если True — фиксирует транзакцию (по умолчанию).
                Если False — только flush (для составных транзакций).
            email (str): Email пользователя.
            full_name (str): Полное имя пользователя.
            password (str): Пароль открытым текстом (будет хеширован).
            role (str, optional): Роль пользователя (по умолчанию "user").

        Returns:
            User: Созданный пользователь.

        Raises:
            IntegrityError: Если email уже зарегистрирован.
        """
        return await super().create(
            db,
            commit=commit,
            email=email,
            full_name=full_name,
            password=hash_password(password),
            role=UserRole(role),
        )

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        user: User,
        *,
        commit: bool = True,
        email: str | None = None,
        full_name: str | None = None,
        password: str | None = None,
        role: str | None = None,
    ) -> User:
        """Обновляет поля пользователя. Пароль хешируется автоматически.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            user (User): Объект пользователя для обновления.
            commit (bool, optional): Если True — фиксирует транзакцию (по умолчанию).
                Если False — только flush (для составных транзакций).
            email (str | None, optional): Новый email.
            full_name (str | None, optional): Новое полное имя.
            password (str | None, optional): Новый пароль (будет хеширован).
            role (str | None, optional): Новая роль.

        Returns:
            User: Обновлённый пользователь.

        Raises:
            IntegrityError: Если новый email уже зарегистрирован.
        """
        fields: dict = {}
        if email is not None:
            fields["email"] = email
        if full_name is not None:
            fields["full_name"] = full_name
        if password is not None:
            fields["password"] = hash_password(password)
        if role is not None:
            fields["role"] = UserRole(role)

        return await super().update(db, user, commit=commit, **fields)
