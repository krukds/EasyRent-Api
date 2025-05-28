from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime


class ListingTagResponse(BaseModel):
    id: int
    name: str
    listing_tag_category_id: int

class ListingTagShort(BaseModel):
    id: int
    name: str

class ListingTagCategoryInfo(BaseModel):
    id: int
    name: str

class GroupedListingTagsResponse(BaseModel):
    category: ListingTagCategoryInfo
    tags: List[ListingTagShort]