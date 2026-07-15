import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import WebhookRequest
from app.services import AccountService, PaymentService, UserService

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

    # 2. Проверка идемпотентности — если транзакция уже обработана, возвращаем 200
    if await PaymentService.get_by_transaction_id(db, data.transaction_id) is not None:
        return {"status": "already_processed"}

    # 3. Проверка существования пользователя
    user = await UserService.get_by_id(db, data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 4. Проверка / создание счёта
    account = await AccountService.get_by_id_and_user(
        db, data.account_id, data.user_id
    )

    if account is None:
        # Проверяем, не принадлежит ли account_id другому пользователю
        existing_account = await AccountService.get_by_id(db, data.account_id)
        if existing_account is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account belongs to another user",
            )
        # Создаём новый счёт для пользователя (без commit — фиксируется вместе с платежом)
        account = await AccountService.create(
            db, commit=False, user_id=data.user_id, account_id=data.account_id
        )

    # 5. Сохранение платежа и начисление суммы на баланс
    result = await PaymentService.create_and_credit(
        db,
        account=account,
        transaction_id=data.transaction_id,
        user_id=data.user_id,
        amount=data.amount,
    )

    if result == "already_processed":
        return {"status": "already_processed"}

    return {"status": "processed", "account_id": account.id, "new_balance": str(account.balance)}
