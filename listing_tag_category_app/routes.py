from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from db.models import ListingTagCategoryModel
from db.services.main_services import ListingTagCategoryService
from .schemes import ListingTagCategoryResponse
from typing import List

router = APIRouter(
    prefix="/listing-tag-categories",
    tags=["Listing Tag Categories"]
)

@router.get("", response_model=List[ListingTagCategoryResponse])
async def get_all_listing_tag_categories():
    query = select(ListingTagCategoryModel)
    listing_types = await ListingTagCategoryService.execute(query)

    return [
        ListingTagCategoryResponse(id=lt.id, name=lt.name)
        for lt in listing_types
    ]
