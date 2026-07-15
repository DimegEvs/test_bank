import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хеширует пароль открытым текстом с помощью bcrypt.

    Args:
        password (str): Пароль открытым текстом.

    Returns:
        str: bcrypt-хеш пароля.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль открытым текстом против bcrypt-хеша.

    Args:
        plain_password (str): Пароль открытым текстом.
        hashed_password (str): bcrypt-хеш для сравнения.

    Returns:
        bool: True, если пароль совпадает с хешем, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """Создаёт JWT access-токен.

    Args:
        subject (str | int): Субъект токена (обычно ID пользователя).
        extra (dict[str, Any] | None, optional): Дополнительные поля в payload.

    Returns:
        str: Закодированный JWT-токен.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Декодирует и проверяет JWT access-токен.

    Args:
        token (str): JWT-токен.

    Returns:
        dict[str, Any]: Payload токена.

    Raises:
        JWTError: Если токен невалиден или истёк.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def compute_signature(account_id: int, amount, transaction_id: str, user_id: int) -> str:
    """Вычисляет SHA256-подпись для платёжного вебхука.

    Подпись формируется как SHA256 от строки
    "{account_id}{amount}{transaction_id}{user_id}{secret_key}".

    Args:
        account_id (int): Идентификатор счёта пользователя.
        amount: Сумма пополнения.
        transaction_id (str): Уникальный идентификатор транзакции.
        user_id (int): Идентификатор пользователя.

    Returns:
        str: SHA256-хеш в виде шестнадцатеричной строки.
    """
    raw = f"{account_id}{amount}{transaction_id}{user_id}{settings.PAYMENT_SECRET_KEY}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_signature(received: str, expected: str) -> bool:
    """Сравнивает две подписи константным по времени методом.

    Args:
        received (str): Полученная подпись.
        expected (str): Ожидаемая подпись.

    Returns:
        bool: True, если подписи совпадают, иначе False.
    """
    return hmac.compare_digest(received, expected)
