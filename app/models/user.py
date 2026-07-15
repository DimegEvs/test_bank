from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(PyEnum):
    """Роль пользователя в системе.

    Attributes:
        user: Обычный пользователь.
        admin: Администратор.
    """
    user = "user"
    admin = "admin"


class User(Base):
    """Модель пользователя системы.

    Attributes:
        id (int): Уникальный идентификатор.
        email (str): Email пользователя (уникальный).
        full_name (str): Полное имя пользователя.
        password (str): bcrypt-хеш пароля.
        role (UserRole): Роль пользователя (user или admin).
        created_at (datetime): Дата и время создания.
        accounts: Список счетов пользователя.
        payments: Список платежей пользователя.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        default=UserRole.user,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
