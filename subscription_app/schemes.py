from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SubscriptionPayload(BaseModel):
    user_id: int
    listing_type_id: Optional[int] = None
    heating_type_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    rooms: Optional[int] = None
    bathrooms: Optional[int] = None
    min_floors: Optional[int] = None
    max_floors: Optional[int] = None
    min_all_floors: Optional[int] = None
    max_all_floors: Optional[int] = None
    min_square: Optional[float] = None
    max_square: Optional[float] = None
    city: Optional[str] = None
    tag_ids: List[int] = []

class SubscriptionResponse(SubscriptionPayload):
    id: int
    created_at: datetime

class SubscriptionDetailResponse(BaseModel):
    id: int
    user_id: int
    listing_type_id: Optional[int] = None
    heating_type_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    rooms: Optional[int] = None
    bathrooms: Optional[int] = None
    min_floors: Optional[int] = None
    max_floors: Optional[int] = None
    min_all_floors: Optional[int] = None
    max_all_floors: Optional[int] = None
    min_square: Optional[float] = None
    max_square: Optional[float] = None
    city: Optional[str] = None
    listing_type: Optional[str] = None
    heating_type: Optional[str] = None
    created_at: datetime
    tags: List[str] = []
