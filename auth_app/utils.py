from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy import select, func

from auth_app.schemes import UserResponse
from config import config, password_crypt_context
from db import UserModel, SessionModel
from db.models import ReviewModel
from db.services import SessionService
from db.services.main_services import ReviewService
from utils import datetime_now


def hash_password(password: str) -> str:
    return password_crypt_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_crypt_context.verify(plain_password, hashed_password)


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


async def build_user_response(user: UserModel) -> UserResponse:
    # Підрахунок середнього рейтингу
    avg_rating_query = (
        select(func.avg(ReviewModel.rating))
            .where(ReviewModel.user_id == user.id)
    )
    result = await ReviewService.execute(avg_rating_query)
    average_rating = result[0] if result else None

    return UserResponse(
        **user.__dict__,
        average_rating=round(average_rating, 2) if average_rating else None
    )
