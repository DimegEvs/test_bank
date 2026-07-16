"""Тесты платёжного вебхука."""

import hashlib

import pytest

from app.config import settings


def _make_signature(account_id: int, amount, transaction_id: str, user_id: int) -> str:
    """Вычисляет подпись так же, как бэкенд."""
    raw = f"{account_id}{amount}{transaction_id}{user_id}{settings.PAYMENT_SECRET_KEY}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@pytest.mark.asyncio
class TestWebhook:
    """Тесты эндпоинта /api/webhook/payment."""

    async def test_valid_webhook_creates_account_and_credits(self, client, db_session):
        """Валидный вебхук: создаёт счёт и зачисляет сумму."""
        from tests.conftest import create_test_user

        user = await create_test_user(db_session, email="wh@test.com")
        tx_id = "tx-001"
        amount = 100.50

        sig = _make_signature(account_id=1, amount=amount, transaction_id=tx_id, user_id=user.id)

        resp = await client.post(
            "/api/webhook/payment",
            json={
                "transaction_id": tx_id,
                "user_id": user.id,
                "account_id": 1,
                "amount": amount,
                "signature": sig,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processed"
        assert data["account_id"] == 1
        assert float(data["new_balance"]) == 100.50

    async def test_invalid_signature(self, client, db_session):
        """Неверная подпись → 400."""
        from tests.conftest import create_test_user

        user = await create_test_user(db_session, email="wh2@test.com")
        resp = await client.post(
            "/api/webhook/payment",
            json={
                "transaction_id": "tx-002",
                "user_id": user.id,
                "account_id": 1,
                "amount": 100,
                "signature": "invalid_signature",
            },
        )
        assert resp.status_code == 400

    async def test_idempotency(self, client, db_session):
        """Повторный вебхук с тем же transaction_id → already_processed."""
        from tests.conftest import create_test_user

        user = await create_test_user(db_session, email="wh3@test.com")
        tx_id = "tx-003"
        amount = 200

        sig = _make_signature(account_id=1, amount=amount, transaction_id=tx_id, user_id=user.id)

        # Первый запрос
        resp1 = await client.post(
            "/api/webhook/payment",
            json={
                "transaction_id": tx_id,
                "user_id": user.id,
                "account_id": 1,
                "amount": amount,
                "signature": sig,
            },
        )
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "processed"

        # Повторный запрос
        resp2 = await client.post(
            "/api/webhook/payment",
            json={
                "transaction_id": tx_id,
                "user_id": user.id,
                "account_id": 1,
                "amount": amount,
                "signature": sig,
            },
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "already_processed"

    async def test_webhook_credits_existing_account(self, client, db_session):
        """Вебхук на существующий счёт — сумма добавляется к балансу."""
        from tests.conftest import create_test_account, create_test_user

        user = await create_test_user(db_session, email="wh4@test.com")
        account = await create_test_account(
            db_session, user_id=user.id, balance=50, account_id=1
        )
        tx_id = "tx-004"
        amount = 100

        sig = _make_signature(account_id=1, amount=amount, transaction_id=tx_id, user_id=user.id)

        resp = await client.post(
            "/api/webhook/payment",
            json={
                "transaction_id": tx_id,
                "user_id": user.id,
                "account_id": 1,
                "amount": amount,
                "signature": sig,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "processed"
        assert float(resp.json()["new_balance"]) == 150.0

    async def test_webhook_user_not_found(self, client):
        """Несуществующий пользователь → 404."""
        tx_id = "tx-005"
        sig = _make_signature(account_id=1, amount=100, transaction_id=tx_id, user_id=999)
        resp = await client.post(
            "/api/webhook/payment",
            json={
                "transaction_id": tx_id,
                "user_id": 999,
                "account_id": 1,
                "amount": 100,
                "signature": sig,
            },
        )
        assert resp.status_code == 404

    async def test_webhook_account_belongs_to_another_user(self, client, db_session):
        """Счёт принадлежит другому пользователю → 409."""
        from tests.conftest import create_test_account, create_test_user

        owner = await create_test_user(db_session, email="owner@test.com")
        other = await create_test_user(
            db_session, email="other@test.com", password="otherpass"
        )
        await create_test_account(
            db_session, user_id=owner.id, account_id=1
        )

        tx_id = "tx-006"
        sig = _make_signature(account_id=1, amount=100, transaction_id=tx_id, user_id=other.id)

        resp = await client.post(
            "/api/webhook/payment",
            json={
                "transaction_id": tx_id,
                "user_id": other.id,
                "account_id": 1,
                "amount": 100,
                "signature": sig,
            },
        )
        assert resp.status_code == 409

    async def test_webhook_multiple_payments_accumulate(self, client, db_session):
        """Несколько вебхуков на один счёт — баланс накапливается."""
        from tests.conftest import create_test_user

        user = await create_test_user(db_session, email="wh5@test.com")

        for i in range(3):
            tx_id = f"tx-batch-{i}"
            amount = 50
            sig = _make_signature(
                account_id=1, amount=amount, transaction_id=tx_id, user_id=user.id
            )
            resp = await client.post(
                "/api/webhook/payment",
                json={
                    "transaction_id": tx_id,
                    "user_id": user.id,
                    "account_id": 1,
                    "amount": amount,
                    "signature": sig,
                },
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "processed"

        
        assert float(resp.json()["new_balance"]) == 150.0
