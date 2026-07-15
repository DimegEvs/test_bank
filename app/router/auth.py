from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Аутентификация по email/password и возврат JWT access-токена.

    Args:
        data (LoginRequest): Данные для входа (email, password).
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        TokenResponse: JWT-токен, тип токена и роль пользователя.

    Raises:
        HTTPException: 401 — если email или пароль неверны.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(
        subject=user.id, extra={"role": user.role.value}
    )
    return TokenResponse(access_token=token, role=user.role.value)
