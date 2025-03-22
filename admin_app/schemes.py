from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime


class AdminUserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    photo_url: Optional[str]
    is_active: bool
    role: int

    listing_count: int
    review_count: int
    average_rating: Optional[float]


class AdminReviewResponse(BaseModel):
    id: int
    user_id: int
    owner_id: int
    rating: float
    description: Optional[str]
    created_at: datetime
    review_status: Optional[str]
    tags: List[str]
    owner_first_name: Optional[str]
    owner_last_name: Optional[str]