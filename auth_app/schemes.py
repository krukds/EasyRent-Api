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
    photo_url: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    photo_url: Optional[str] = None
    role: int
    is_active: bool
    is_verified: bool


class UserPayload(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str
    photo_url: Optional[str] = None
    role: int
