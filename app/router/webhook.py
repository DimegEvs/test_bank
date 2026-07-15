import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Account, Payment, User
from app.schemas import WebhookRequest

router = APIRouter(prefix="/api/webhook", tags=["Webhook"])


def _compute_signature(account_id: int, amount, transaction_id: str, user_id: int) -> str:
    """Вычисляет SHA256-подпись для платёжного вебхука.

    Подпись = SHA256("{account_id}{amount}{transaction_id}{user_id}{secret_key}").

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


@router.post("/payment", status_code=status.HTTP_200_OK)
async def process_payment_webhook(
    data: WebhookRequest,
    db: AsyncSession = Depends(get_db),
):
    """Обрабатывает вебхук от сторонней платёжной системы.

    Шаги обработки:
        1. Проверка подписи объекта.
        2. Проверка идемпотентности по transaction_id.
        3. Проверка существования пользователя.
        4. Проверка / создание счёта пользователя.
        5. Сохранение платежа и начисление суммы на баланс (одна транзакция).

    Args:
        data (WebhookRequest): Данные вебхука (transaction_id, account_id,
            user_id, amount, signature).
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        dict: Статус обработки и (при успехе) новый баланс счёта.

    Raises:
        HTTPException: 400 — если подпись невалидна.
        HTTPException: 404 — если пользователь не найден.
        HTTPException: 409 — если счёт принадлежит другому пользователю.
    """
    # 1. Проверка подписи
    expected_sig = _compute_signature(
        data.account_id, data.amount, data.transaction_id, data.user_id
    )
    if not hmac.compare_digest(data.signature, expected_sig):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    existing = await db.execute(
        select(Payment).where(Payment.transaction_id == data.transaction_id)
    )
    if existing.scalar_one_or_none() is not None:
        return {"status": "already_processed"}

    # 3. Проверка существования пользователя
    user_result = await db.execute(select(User).where(User.id == data.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 4. Проверка / создание счёта
    account_result = await db.execute(
        select(Account).where(
            Account.id == data.account_id,
            Account.user_id == data.user_id,
        )
    )
    account = account_result.scalar_one_or_none()

    if account is None:
        # Проверяем, не принадлежит ли account_id другому пользователю
        account_by_id = await db.execute(
            select(Account).where(Account.id == data.account_id)
        )
        if account_by_id.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account belongs to another user",
            )
        # Создаём новый счёт для пользователя
        account = Account(
            id=data.account_id,
            user_id=data.user_id,
            balance=0,
        )
        db.add(account)
        await db.flush()

    # 5. Сохранение платежа и начисление суммы на баланс
    payment = Payment(
        transaction_id=data.transaction_id,
        account_id=account.id,
        user_id=data.user_id,
        amount=data.amount,
    )
    db.add(payment)
    account.balance += data.amount

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # Состояние гонки: другой запрос уже вставил тот же transaction_id
        return {"status": "already_processed"}

    return {"status": "processed", "account_id": account.id, "new_balance": str(account.balance)}
