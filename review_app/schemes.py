from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime


class ReviewPayload(BaseModel):
    user_id: int
    owner_id: int
    rating: condecimal(max_digits=2, decimal_places=1)  # Обмеження 0.0 - 5.0
    description: Optional[str] = None
    review_status_id: int
    tag_ids: List[int] = []


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    owner_id: int
    rating: condecimal(max_digits=2, decimal_places=1)
    description: Optional[str] = None
    review_status_id: int
    created_at: datetime
    tags: List[str]


class ReviewDetailResponse(ReviewResponse):
    review_status: str