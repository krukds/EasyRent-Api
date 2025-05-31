from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime

from listing_app.schemes import ListingDetailResponse


class FavoritesPayload(BaseModel):
    listing_id: int

class FavoritesResponse(BaseModel):
    id: int
    user_id: int
    listing_id: int

class FavoriteListingResponse(BaseModel):
    favorite_id: int
    listing: ListingDetailResponse