from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime


class ReviewTagResponse(BaseModel):
    id: int
    name: str