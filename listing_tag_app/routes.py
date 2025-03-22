from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List

from db.models import ListingTagModel
from db.services.main_services import ListingTagService
from .schemes import ListingTagResponse

router = APIRouter(
    prefix="/listing-tags",
    tags=["Listing Tags"]
)

@router.get("", response_model=List[ListingTagResponse])
async def get_all_listing_tags_types():
    query = select(ListingTagModel)
    listing_tags = await ListingTagService.execute(query)

    return [
        ListingTagResponse(
            id=lt.id,
            name=lt.name,
            listing_tag_category_id=lt.listing_tag_category_id  # ✅ додали поле
        )
        for lt in listing_tags
    ]

