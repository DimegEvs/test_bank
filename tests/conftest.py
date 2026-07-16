"""Конфигурация pytest: тестовая БД, fixtures."""

from collections.abc import AsyncGenerator

import psycopg2
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import get_db
from app.main import app
from app.models import Account, Base, User, UserRole
from app.security import hash_password

# ---------------------------------------------------------------------------
# Тестовая БД
# ---------------------------------------------------------------------------

TEST_DB_NAME = "test_bank_test"
TEST_DATABASE_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/" + TEST_DB_NAME


def _ensure_test_database():
    """Создаёт тестовую БД, если она не существует."""
    sync_url = settings.DATABASE_URL_SYNC.replace("+psycopg2", "").rsplit("/", 1)[0] + "/postgres"
    conn = psycopg2.connect(sync_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
    if cur.fetchone() is None:
        cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    cur.close()
    conn.close()


def _drop_test_database():
    """Удаляет тестовую БД."""
    sync_url = settings.DATABASE_URL_SYNC.replace("+psycopg2", "").rsplit("/", 1)[0] + "/postgres"
    conn = psycopg2.connect(sync_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cur.close()
    conn.close()


_ensure_test_database()


test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """Заменитель get_db для тестов — каждый вызов получает свежее подключение."""
    async with test_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Создание / удаление таблиц
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def setup_tables():
    """Создаёт таблицы перед тестом, удаляет после."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Подмена зависимости
# ---------------------------------------------------------------------------

app.dependency_overrides[get_db] = get_test_db


# ---------------------------------------------------------------------------
# Клиенты
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    """Неаутентифицированный HTTP-клиент."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def user_client():
    """HTTP-клиент, аутентифицированный как тестовый пользователь."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with test_session_factory() as session:
            user = User(
                email="user@test.com",
                full_name="Test User",
                password=hash_password("userpass"),
                role=UserRole.user,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        resp = await ac.post(
            "/api/auth/login",
            json={"email": "user@test.com", "password": "userpass"},
        )
        assert resp.status_code == 200
        yield ac


@pytest_asyncio.fixture
async def admin_client():
    """HTTP-клиент, аутентифицированный как тестовый администратор."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with test_session_factory() as session:
            admin = User(
                email="admin@test.com",
                full_name="Test Admin",
                password=hash_password("adminpass"),
                role=UserRole.admin,
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)

        resp = await ac.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "adminpass"},
        )
        assert resp.status_code == 200
        yield ac


# ---------------------------------------------------------------------------
# Утилиты для тестов
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session():
    """Прямой доступ к тестовой сессии БД (для подготовки данных).

    С NullPool каждая сессия получает своё подключение, поэтому
    открытая сессия не конфликтует с API-вызовами через клиент.
    """
    async with test_session_factory() as session:
        yield session


async def create_test_user(
    session: AsyncSession,
    email: str = "user@test.com",
    password: str = "userpass",
    full_name: str = "Test User",
    role: UserRole = UserRole.user,
) -> User:
    """Создаёт пользователя напрямую в БД."""
    user = User(
        email=email,
        full_name=full_name,
        password=hash_password(password),
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_test_account(
    session: AsyncSession,
    user_id: int,
    balance: int = 0,
    account_id: int | None = None,
) -> Account:
    """Создаёт счёт напрямую в БД."""
    account = Account(
        id=account_id,
        user_id=user_id,
        balance=balance,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account
