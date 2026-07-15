from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import AccountCreate, AccountOut, PaymentOut, UserOut
from app.services import AccountService, PaymentService

router = APIRouter(prefix="/api/users", tags=["Users"])

# Реэкспорт зависимости для корректной интроспекции FastAPI
_current_user = Depends(get_current_user)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = _current_user):
    """Возвращает профиль текущего аутентифицированного пользователя.

    Args:
        current_user (User): Текущий пользователь из JWT.

    Returns:
        UserOut: Данные пользователя (id, email, full_name, role).
    """
    return current_user


@router.get("/me/accounts", response_model=list[AccountOut])
async def get_my_accounts(
    current_user: User = _current_user,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает список всех счетов текущего пользователя с балансами.

    Args:
        current_user (User): Текущий пользователь из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        list[AccountOut]: Список счетов пользователя.
    """
    return await AccountService.list_by_user(db, current_user.id)


@router.post("/me/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_my_account(
    current_user: User = _current_user,
    db: AsyncSession = Depends(get_db),
):
    """Создаёт новый счёт для текущего пользователя с нулевым балансом.

    Args:
        current_user (User): Текущий пользователь из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        AccountOut: Созданный счёт.
    """
    return await AccountService.create(db, user_id=current_user.id)


@router.get("/me/accounts/{account_id}", response_model=AccountOut)
async def get_my_account(
    account_id: int,
    current_user: User = _current_user,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает конкретный счёт текущего пользователя по идентификатору.

    Args:
        account_id (int): Идентификатор счёта.
        current_user (User): Текущий пользователь из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        AccountOut: Данные счёта.

    Raises:
        HTTPException: 404 — если счёт не найден или принадлежит другому пользователю.
    """
    account = await AccountService.get_by_id_and_user(db, account_id, current_user.id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


@router.delete("/me/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    account_id: int,
    current_user: User = _current_user,
    db: AsyncSession = Depends(get_db),
):
    """Удаляет счёт текущего пользователя.

    Args:
        account_id (int): Идентификатор счёта.
        current_user (User): Текущий пользователь из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Raises:
        HTTPException: 404 — если счёт не найден или принадлежит другому пользователю.
    """
    account = await AccountService.get_by_id_and_user(db, account_id, current_user.id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    await AccountService.delete(db, account)


@router.get("/me/payments", response_model=list[PaymentOut])
async def get_my_payments(
    current_user: User = _current_user,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает список всех платежей текущего пользователя.

    Args:
        current_user (User): Текущий пользователь из JWT.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        list[PaymentOut]: Список платежей пользователя.
    """
    return await PaymentService.list_by_user(db, current_user.id)
