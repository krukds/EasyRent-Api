import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from passlib.context import CryptContext


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASS: SecretStr

    JWT_SECRET_KEY: SecretStr
    JWT_REFRESH_SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"

    ORGANISATION_ID: str
    API_KEY: SecretStr
    VERIFICATION_ASSISTANT_ID: str
    MODERATOR_ASSISTANT_ID: str
    OWNERSHIP_VERIFICATION_ASSISTANT_ID: str

    EMAIL_SMTP_SERVER: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_LOGIN: str
    EMAIL_PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()
password_crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

os.environ['TESSDATA_PREFIX'] = r'D:\Tesseract\Tesseract-OCR'
