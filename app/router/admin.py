from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import Account, User, UserRole
from app.schemas import AccountOut, UserCreate, UserOut, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/api/admin", tags=["Admin"])

_admin = Depends(get_current_admin)


@router.get("/me", response_model=UserOut)
async def get_admin_me(current_admin: User = _admin):
    """Возвращает профиль текущего администратора.

    Args:
        current_admin (User): Текущий администратор из JWT.

    Returns:
        UserOut: Данные администратора (id, email, full_name, role).
    """
    return current_admin


@router.get("/users", response_model=list[UserOut])
async def list_users(
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает список всех пользователей.

    Args:
        current_admin (User): Текущий администратор из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        list[UserOut]: Список всех пользователей.
    """
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.get("/users/{user_id}/accounts", response_model=list[AccountOut])
async def get_user_accounts(
    user_id: int,
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает список счетов указанного пользователя с балансами.

    Args:
        user_id (int): Идентификатор пользователя.
        current_admin (User): Текущий администратор из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        list[AccountOut]: Список счетов пользователя.

    Raises:
        HTTPException: 404 — если пользователь не найден.
    """
    user_result = await db.execute(select(User).where(User.id == user_id))
    if user_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = await db.execute(
        select(Account).where(Account.user_id == user_id)
    )
    return result.scalars().all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Создаёт нового пользователя.

    Args:
        data (UserCreate): Данные для создания пользователя.
        current_admin (User): Текущий администратор из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        UserOut: Созданный пользователь.

    Raises:
        HTTPException: 409 — если email уже зарегистрирован.
    """
    user = User(
        email=data.email,
        full_name=data.full_name,
        password=hash_password(data.password),
        role=UserRole(data.role),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    await db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Обновляет данные существующего пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        data (UserUpdate): Поля для обновления.
        current_admin (User): Текущий администратор из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        UserOut: Обновлённый пользователь.

    Raises:
        HTTPException: 404 — если пользователь не найден.
        HTTPException: 409 — если email уже зарегистрирован.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if data.email is not None:
        user.email = data.email
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.password is not None:
        user.password = hash_password(data.password)
    if data.role is not None:
        user.role = UserRole(data.role)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Удаляет пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        current_admin (User): Текущий администратор из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Raises:
        HTTPException: 404 — если пользователь не найден.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    await db.delete(user)
    await db.commit()
