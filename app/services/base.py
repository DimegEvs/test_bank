from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    """Базовый сервис с универсальными CRUD-операциями и управлением транзакциями.

    Наследники должны задать атрибут класса ``model`` — ORM-модель.

    Методы записи (``create``, ``update``, ``delete``) принимают параметр
    ``commit``. По умолчанию ``commit=True`` — метод сам фиксирует транзакцию.
    Если ``commit=False`` — выполняется только ``flush`` (изменения видны
    в текущей сессии, но не зафиксированы в БД). Это позволяет объединять
    несколько операций в одну атомарную транзакцию: все методы вызываются
    с ``commit=False``, а финальный — с ``commit=True``.
    """

    model: type[ModelType]

    # ------------------------------------------------------------------ read

    @classmethod
    async def get_by_id(
        cls, db: AsyncSession, obj_id: int
    ) -> ModelType | None:
        """Возвращает объект по идентификатору.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            obj_id (int): Идентификатор объекта.

        Returns:
            ModelType | None: Найденный объект или None.
        """
        result = await db.execute(select(cls.model).where(cls.model.id == obj_id))
        return result.scalar_one_or_none()

    @classmethod
    async def list_all(cls, db: AsyncSession) -> Sequence[ModelType]:
        """Возвращает список всех объектов, отсортированных по id.

        Args:
            db (AsyncSession): Асинхронная сессия БД.

        Returns:
            Sequence[ModelType]: Список всех объектов.
        """
        result = await db.execute(select(cls.model).order_by(cls.model.id))
        return result.scalars().all()

    # ----------------------------------------------------------------- write

    @classmethod
    async def create(
        cls, db: AsyncSession, *, commit: bool = True, **kwargs: Any
    ) -> ModelType:
        """Создаёт новый объект.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            commit (bool, optional): Если True — фиксирует транзакцию (по умолчанию).
                Если False — только flush (для составных транзакций).
            **kwargs: Поля объекта.

        Returns:
            ModelType: Созданный объект.
        """
        obj = cls.model(**kwargs)
        db.add(obj)
        await db.flush()
        if commit:
            await db.commit()
            await db.refresh(obj)
        return obj

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        obj: ModelType,
        *,
        commit: bool = True,
        **kwargs: Any,
    ) -> ModelType:
        """Обновляет поля объекта. None-значения игнорируются.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            obj (ModelType): Объект для обновления.
            commit (bool, optional): Если True — фиксирует транзакцию (по умолчанию).
                Если False — только flush (для составных транзакций).
            **kwargs: Поля для обновления.

        Returns:
            ModelType: Обновлённый объект.
        """
        for key, value in kwargs.items():
            if value is not None:
                setattr(obj, key, value)
        await db.flush()
        if commit:
            await db.commit()
            await db.refresh(obj)
        return obj

    @classmethod
    async def delete(
        cls, db: AsyncSession, obj: ModelType, *, commit: bool = True
    ) -> None:
        """Удаляет объект.

        Args:
            db (AsyncSession): Асинхронная сессия БД.
            obj (ModelType): Объект для удаления.
            commit (bool, optional): Если True — фиксирует транзакцию (по умолчанию).
                Если False — только flush (для составных транзакций).
        """
        await db.delete(obj)
        await db.flush()
        if commit:
            await db.commit()
