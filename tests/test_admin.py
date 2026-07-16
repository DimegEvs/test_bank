"""Тесты админских эндпоинтов."""

import pytest


@pytest.mark.asyncio
class TestAdmin:
    """Тесты эндпоинтов /api/admin."""

    # --- Users CRUD ---

    async def test_get_users_as_admin(self, admin_client):
        """Получение списка всех пользователей админом."""
        resp = await admin_client.get("/api/admin/users")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_users_as_user_forbidden(self, user_client):
        """Обычный пользователь не может получить список → 403."""
        resp = await user_client.get("/api/admin/users")
        assert resp.status_code == 403

    async def test_get_users_unauthorized(self, client):
        """Неаутентифицированный запрос → 401."""
        resp = await client.get("/api/admin/users")
        assert resp.status_code == 401

    async def test_create_user_as_admin(self, admin_client):
        """Админ создаёт нового пользователя."""
        resp = await admin_client.post(
            "/api/admin/users",
            json={
                "email": "created@test.com",
                "full_name": "Created",
                "password": "password123",
                "role": "user",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "created@test.com"
        assert data["role"] == "user"

    async def test_create_admin_as_admin(self, admin_client):
        """Админ создаёт другого админа."""
        resp = await admin_client.post(
            "/api/admin/users",
            json={
                "email": "admin2@test.com",
                "full_name": "Admin Two",
                "password": "password123",
                "role": "admin",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "admin"

    async def test_update_user_as_admin(self, admin_client, db_session):
        """Админ обновляет данные пользователя."""
        from tests.conftest import create_test_user

        user = await create_test_user(db_session, email="update@test.com")
        resp = await admin_client.put(
            f"/api/admin/users/{user.id}",
            json={
                "email": "updated@test.com",
                "full_name": "Updated Name",
                "role": "user",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "updated@test.com"
        assert resp.json()["full_name"] == "Updated Name"

    async def test_delete_user_as_admin(self, admin_client, db_session):
        """Админ удаляет пользователя."""
        from tests.conftest import create_test_user

        user = await create_test_user(db_session, email="delete@test.com")
        resp = await admin_client.delete(f"/api/admin/users/{user.id}")
        assert resp.status_code == 204

    # --- Accounts ---

    async def test_get_user_accounts_as_admin(self, admin_client, db_session):
        """Админ просматривает счета пользователя."""
        from tests.conftest import create_test_account, create_test_user

        user = await create_test_user(db_session, email="acc@test.com")
        await create_test_account(db_session, user_id=user.id, balance=500)
        resp = await admin_client.get(f"/api/admin/users/{user.id}/accounts")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["balance"] == "500.00"
