from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения / файла .env.

    Attributes:
        DATABASE_URL (str): URL подключения к БД (async).
        DATABASE_URL_SYNC (str): URL подключения к БД (sync, для Alembic).
        JWT_SECRET_KEY (str): Секретный ключ для подписи JWT-токенов.
        JWT_ALGORITHM (str): Алгоритм подписи JWT (по умолчанию HS256).
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Время жизни access-токена в минутах.
        PAYMENT_SECRET_KEY (str): Секретный ключ для проверки подписи вебхука.
        COOKIE_NAME (str): Имя cookie для хранения access-токена.
        COOKIE_SECURE (bool): Флаг Secure (только HTTPS в продакшене).
        COOKIE_SAMESITE (str): Политика SameSite для cookie.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    PAYMENT_SECRET_KEY: str

    COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"


settings = Settings()
