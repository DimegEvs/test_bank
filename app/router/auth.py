from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.security import create_access_token, verify_password
from app.services import UserService

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    """Устанавливает access-токен в http-only cookie.

    Args:
        response (Response): Объект ответа FastAPI.
        token (str): JWT access-токен.
    """
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового пользователя. Роль всегда "user".

    После регистрации автоматически устанавливает cookie с JWT-токеном.

    Args:
        data (RegisterRequest): Данные для регистрации (email, full_name, password).
        response (Response): Объект ответа для установки cookie.
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

    user = await UserService.create(
        db,
        email=data.email,
        full_name=data.full_name,
        password=data.password,
        role="user",
    )

    token = create_access_token(subject=user.id, extra={"role": user.role.value})
    _set_auth_cookie(response, token)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Аутентификация по email/password и установка JWT в cookie.

    Args:
        data (LoginRequest): Данные для входа (email, password).
        response (Response): Объект ответа для установки cookie.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        TokenResponse: JWT-токен, тип токена и роль пользователя.

    Raises:
        HTTPException: 401 — если email или пароль неверны.
    """
    user = await UserService.get_by_email(db, data.email)

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(
        subject=user.id, extra={"role": user.role.value}
    )
    _set_auth_cookie(response, token)

    return TokenResponse(access_token=token, role=user.role.value)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    """Выход из системы — удаляет cookie с access-токеном.

    Args:
        response (Response): Объект ответа для удаления cookie.

    Returns:
        dict: Сообщение об успешном выходе.
    """
    response.delete_cookie(key=settings.COOKIE_NAME)
    return {"detail": "Successfully logged out"}
