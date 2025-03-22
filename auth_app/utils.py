from datetime import datetime, timedelta, timezone

from jose import jwt

from config import config
from db import UserModel, SessionModel
from db.services import SessionService
from utils import datetime_now


def create_access_token(user_id: int, expires_at: datetime = None) -> str:
    if expires_at is None:
        expires_at = generate_access_token_expires_at()
    to_encode = {
        "expires_at": int(expires_at.timestamp()),  # JWT зберігає як unix timestamp
        "user_id": str(user_id)
    }
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY.get_secret_value(), config.ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: int, expires_at: datetime = None) -> str:
    if expires_at is None:
        expires_at = generate_refresh_token_expires_at()

    to_encode = {
        "expires_at": int(expires_at.timestamp()),
        "user_id": str(user_id)
    }
    encoded_jwt = jwt.encode(to_encode, config.JWT_REFRESH_SECRET_KEY.get_secret_value(), config.ALGORITHM)
    return encoded_jwt


def generate_access_token_expires_at() -> datetime:
    # Повертаємо дату з timezone → UTC
    return datetime.now(timezone.utc) + timedelta(days=1)


def generate_refresh_token_expires_at() -> datetime:
    # Повертаємо теж datetime з timezone
    return datetime.now(timezone.utc) + timedelta(days=7)


async def create_user_session(user_id: int) -> SessionModel:
    access_token_expires_at = generate_access_token_expires_at()
    session = SessionModel(
        user_id=user_id,
        access_token=create_access_token(user_id, access_token_expires_at),
        expires_at=access_token_expires_at  # ✅ Тепер це timezone-aware datetime
    )
    await SessionService.save(session)
    return session
