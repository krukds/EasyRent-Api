from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime


class ListingStatusResponse(BaseModel):
    id: int
    name: str
    listing_status_id: int