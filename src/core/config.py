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
 
    # === Room settings ===
    ROOM_CODE_LENGTH: int
    MAX_PLAYERS_PER_ROOM: int
    MIN_PLAYERS_PER_ROOM: int
    DEFAULT_QUESTION_TIME: int
    ROOM_IDLE_TIMEOUT: int
    QUESTION_TIMEOUT_BUFFER: int
    
    # === Score calculation ===
    BASE_CORRECT_SCORE: int
    SPEED_BONUS_MAX: int
    WRONG_ANSWER_PENALTY: int
    
    # === JWT settings ===
    SECRET_KEY: SecretStr
    ALGORITHM: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'forbid'


settings = Settings()
