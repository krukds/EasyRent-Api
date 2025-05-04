from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime

from auth_app.schemes import UserResponse


class ReviewPayload(BaseModel):
    user_id: int
    owner_id: int
    rating: condecimal(max_digits=2, decimal_places=1)  # Обмеження 0.0 - 5.0
    description: Optional[str] = None
    review_status_id: int
    tag_ids: List[int] = []

class OwnerResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    photo_url: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    owner_id: int
    rating: condecimal(max_digits=2, decimal_places=1)
    description: Optional[str] = None
    review_status_id: int
    created_at: datetime
    tags: List[str]
    owner: Optional[OwnerResponse] = None
    user: Optional[UserResponse] = None


class ReviewDetailResponse(ReviewResponse):
    review_status: str
