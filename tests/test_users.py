"""Тесты пользовательских эндпоинтов."""

import pytest


@pytest.mark.asyncio
class TestUsers:
    """Тесты эндпоинтов /api/users."""

    async def test_get_me(self, user_client):
        """Получение профиля текущего пользователя."""
        resp = await user_client.get("/api/users/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@test.com"
        assert data["full_name"] == "Test User"
        assert data["role"] == "user"

    async def test_get_me_unauthorized(self, client):
        """Доступ без авторизации → 401."""
        resp = await client.get("/api/users/me")
        assert resp.status_code == 401

    async def test_get_my_accounts_empty(self, user_client):
        """Список счетов — пусто."""
        resp = await user_client.get("/api/users/me/accounts")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_account(self, user_client):
        """Создание счёта."""
        resp = await user_client.post("/api/users/me/accounts")
        assert resp.status_code == 201
        data = resp.json()
        assert data["balance"] == "0.00"
        assert "id" in data

    async def test_get_my_accounts_after_create(self, user_client):
        """Список счетов после создания."""
        await user_client.post("/api/users/me/accounts")
        resp = await user_client.get("/api/users/me/accounts")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_my_account_by_id(self, user_client):
        """Получение конкретного счёта по ID."""
        create_resp = await user_client.post("/api/users/me/accounts")
        account_id = create_resp.json()["id"]
        resp = await user_client.get(f"/api/users/me/accounts/{account_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == account_id

    async def test_get_my_account_not_found(self, user_client):
        """Несуществующий счёт → 404."""
        resp = await user_client.get("/api/users/me/accounts/999")
        assert resp.status_code == 404

    async def test_delete_my_account(self, user_client):
        """Удаление счёта."""
        create_resp = await user_client.post("/api/users/me/accounts")
        account_id = create_resp.json()["id"]
        resp = await user_client.delete(f"/api/users/me/accounts/{account_id}")
        assert resp.status_code == 204
        # Проверяем, что счёт удалён
        get_resp = await user_client.get(f"/api/users/me/accounts/{account_id}")
        assert get_resp.status_code == 404

    async def test_get_my_payments_empty(self, user_client):
        """Список платежей — пусто."""
        resp = await user_client.get("/api/users/me/payments")
        assert resp.status_code == 200
        assert resp.json() == []
