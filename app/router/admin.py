from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User
from app.schemas import AccountCreate, AccountOut, UserCreate, UserOut, UserUpdate
from app.services import AccountService, UserService

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
    return await UserService.list_all(db)


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
    user = await UserService.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return await AccountService.list_by_user(db, user_id)


@router.post("/users/{user_id}/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_user_account(
    user_id: int,
    data: AccountCreate,
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Создаёт новый счёт для указанного пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        data (AccountCreate): Данные для создания счёта (начальный баланс).
        current_admin (User): Текущий администратор из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        AccountOut: Созданный счёт.

    Raises:
        HTTPException: 404 — если пользователь не найден.
    """
    user = await UserService.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return await AccountService.create(
        db, user_id=user_id, balance=data.balance
    )


@router.get("/accounts/{account_id}", response_model=AccountOut)
async def get_account(
    account_id: int,
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает любой счёт по идентификатору.

    Args:
        account_id (int): Идентификатор счёта.
        current_admin (User): Текущий администратор из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        AccountOut: Данные счёта.

    Raises:
        HTTPException: 404 — если счёт не найден.
    """
    account = await AccountService.get_by_id(db, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Удаляет любой счёт по идентификатору.

    Args:
        account_id (int): Идентификатор счёта.
        current_admin (User): Текущий администратор из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Raises:
        HTTPException: 404 — если счёт не найден.
    """
    account = await AccountService.get_by_id(db, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    await AccountService.delete(db, account)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Создаёт нового пользователя.

    Сначала проверяет существование email, чтобы не расходовать
    sequence-значение id при неудачной попытке (PostgreSQL не откатывает sequence).

    Args:
        data (UserCreate): Данные для создания пользователя.
        current_admin (User): Текущий администратор из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        UserOut: Созданный пользователь.

    Raises:
        HTTPException: 409 — если email уже зарегистрирован.
    """
    existing = await UserService.get_by_email(db, data.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return await UserService.create(
        db,
        email=data.email,
        full_name=data.full_name,
        password=data.password,
        role=data.role,
    )


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_admin: User = _admin,
    db: AsyncSession = Depends(get_db),
):
    """Обновляет данные существующего пользователя.

    Если меняется email — сначала проверяет, не занят ли он другим пользователем,
    чтобы не расходовать sequence и не ловить IntegrityError.

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
    user = await UserService.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if data.email is not None and data.email != user.email:
        email_owner = await UserService.get_by_email(db, data.email)
        if email_owner is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    return await UserService.update(
        db,
        user,
        email=data.email,
        full_name=data.full_name,
        password=data.password,
        role=data.role,
    )


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
    user = await UserService.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    await UserService.delete(db, user)
