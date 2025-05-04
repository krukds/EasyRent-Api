from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class TokenPayload(BaseModel):
    user_id: int
    expires_at: datetime


class LoginPayload(BaseModel):
    email: str
    password: str


class SignupPayload(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
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
    phone: str
    photo_url: Optional[str] = None
    role: int
    is_active: bool
    is_verified: bool
    average_rating: Optional[float] = None


class UserPayload(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    role: Optional[int] = None
