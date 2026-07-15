from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User, UserRole
from app.security import decode_access_token


async def get_current_user(
    access_token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Определяет текущего аутентифицированного пользователя из cookie с JWT.

    Args:
        access_token (str | None): JWT-токен из cookie.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        User: Текущий аутентифицированный пользователь.

    Raises:
        HTTPException: 401 — если токен отсутствует, невалиден или пользователь не найден.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    if access_token is None:
        raise credentials_exception

    try:
        payload = decode_access_token(access_token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверяет, что текущий пользователь имеет роль администратора.

    Args:
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        User: Текущий пользователь с ролью admin.

    Raises:
        HTTPException: 403 — если пользователь не является администратором.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
