from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime


class ListingTagCategoryResponse(BaseModel):
    id: int
    name: str