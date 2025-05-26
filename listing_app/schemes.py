from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class ListingPayload(BaseModel):
    name: str
    description: str
    price: int
    city: str
    street: str
    building: str
    flat: Optional[int] = None
    floor: int
    all_floors: int
    rooms: int
    bathrooms: Optional[int] = None
    square: int
    communal: int
    owner_id: int
    heating_type_id: int
    listing_type_id: int
    listing_status_id: int
    tag_ids: List[int] = []
    images: List[str]
    discard_reason: Optional[str] = None


class ListingResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int
    city: str
    street: str
    building: str
    flat: Optional[int] = None
    floor: int
    all_floors: int
    rooms: int
    bathrooms: Optional[int] = None
    square: int
    communal: int
    owner_id: int
    heating_type_id: int
    listing_type_id: int
    listing_status_id: int
    created_at: datetime
    images: list[str] = []
    discard_reason: Optional[str] = None


class UserShortResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    photo_url: Optional[str] = None
    average_rating: Optional[float] = None
    reviews_count: Optional[int] = None


class ListingDetailResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int
    city: str
    street: str
    building: str
    flat: Optional[int]
    floor: int
    all_floors: int
    rooms: int
    bathrooms: Optional[int]
    square: int
    communal: int
    owner: Optional[UserShortResponse]
    listing_type: str
    heating_type: str
    listing_status: str
    created_at: datetime
    tags: List[str] = []
    images: list[str] = []
    discard_reason: Optional[str] = None






