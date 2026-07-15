from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Account, Payment, User
from app.schemas import AccountOut, PaymentOut, UserOut

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
    from sqlalchemy import select

    result = await db.execute(
        select(Account).where(Account.user_id == current_user.id)
    )
    return result.scalars().all()


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
    from sqlalchemy import select

    result = await db.execute(
        select(Payment).where(Payment.user_id == current_user.id)
    )
    return result.scalars().all()
