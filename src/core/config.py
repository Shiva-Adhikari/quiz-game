# Standard library imports
from pydantic import EmailStr, SecretStr

# Third-party imports
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # === Database ===
    DATABASE_URL: SecretStr

    # === Security ===
    SECRET_KEY: SecretStr

    # === Server Configuration ===
    HOST: SecretStr
    PORT: int

    # === Debug ===
    DEBUG: bool

    # === OTP ===
    OTP_EXPIRE: int

    # === Email ===
    SENDER_EMAIL: EmailStr
    SENDER_PASSWORD: SecretStr
    EMAIL_HOST: SecretStr
    EMAIL_PORT: int

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'forbid'


settings = Settings()
