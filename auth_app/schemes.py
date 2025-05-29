from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class TokenPayload(BaseModel):
    user_id: int
    expires_at: datetime


class LoginPayload(BaseModel):
    email: str
    password: str


class SignupPayload(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    patronymic: str
    phone: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    password: str
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    phone: str
    photo_url: Optional[str] = None
    passport_path: Optional[str] = None
    role: int
    is_active: bool
    is_verified: bool
    average_rating: Optional[float] = None
    reviews_count: Optional[int] = None


class UserPayload(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    patronymic: Optional[str] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    passport_path: Optional[str] = None
    role: Optional[int] = None
