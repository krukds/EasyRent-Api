from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime


class ListingTagResponse(BaseModel):
    id: int
    name: str
    listing_tag_category_id: int