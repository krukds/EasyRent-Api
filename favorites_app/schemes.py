from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime

class FavoritesPayload(BaseModel):
    user_id: int
    listing_id: int

class FavoritesResponse(BaseModel):
    id: int
    user_id: int
    listing_id: int