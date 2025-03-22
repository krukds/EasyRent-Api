from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime


class HeatingTypeResponse(BaseModel):
    id: int
    name: str