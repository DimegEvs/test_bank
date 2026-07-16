"""Тесты авторизации и регистрации."""

import pytest


@pytest.mark.asyncio
class TestAuth:
    """Тесты эндпоинтов /api/auth."""

    async def test_register_success(self, client):
        """Успешная регистрация нового пользователя."""
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "new@test.com",
                "full_name": "New User",
                "password": "password123",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@test.com"
        assert data["full_name"] == "New User"
        assert data["role"] == "user"
        assert "password" not in data
        # Cookie должна быть установлена
        assert "access_token" in resp.cookies

    async def test_register_duplicate_email(self, client, db_session):
        """Регистрация с уже существующим email → 409."""
        from tests.conftest import create_test_user

        await create_test_user(db_session, email="dup@test.com")
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "dup@test.com",
                "full_name": "Dup",
                "password": "password123",
            },
        )
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    async def test_register_short_password(self, client):
        """Пароль короче 6 символов → 422."""
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "short@test.com",
                "full_name": "Short",
                "password": "123",
            },
        )
        assert resp.status_code == 422

    async def test_login_success(self, client, db_session):
        """Успешный вход."""
        from tests.conftest import create_test_user

        await create_test_user(db_session, email="login@test.com", password="pass123")
        resp = await client.post(
            "/api/auth/login",
            json={"email": "login@test.com", "password": "pass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "user"
        assert "access_token" in resp.cookies

    async def test_login_wrong_password(self, client, db_session):
        """Неверный пароль → 401."""
        from tests.conftest import create_test_user

        await create_test_user(db_session, email="wrong@test.com", password="correct")
        resp = await client.post(
            "/api/auth/login",
            json={"email": "wrong@test.com", "password": "incorrect"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        """Несуществующий email → 401."""
        resp = await client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": "pass"},
        )
        assert resp.status_code == 401

    async def test_logout(self, user_client):
        """Выход удаляет cookie."""
        resp = await user_client.post("/api/auth/logout")
        assert resp.status_code == 200
        # Cookie должна быть удалена
        assert "access_token" not in resp.cookies or resp.cookies.get("access_token") == ""
