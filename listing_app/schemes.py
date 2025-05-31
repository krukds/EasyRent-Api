from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from listing_tag_app.schemes import ListingTagShort


UPLOAD_DIR = Path("static/listing_photos")
ACTIVE_STATUS_ID = 1
ARCHIVED_STATUS_ID = 2
MODERATION_STATUS_ID = 3
DISCARD_STATUS_ID = 4


class ListingPayload(BaseModel):
    name: str
    description: str
    price: int
    city_id: int
    street_id: int
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
    city_id: int
    city_name: str
    street_id: int
    street_name_ukr: str
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
    tags: List[ListingTagShort] = []


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
    city_id: int
    city_name: str
    street_id: int
    street_name_ukr: str
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



