from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import AccountOut, PaymentOut, UserOut
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
