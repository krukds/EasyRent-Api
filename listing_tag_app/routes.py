from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List

from db.models import ListingTagModel
from db.services.main_services import ListingTagService
from .schemes import ListingTagResponse, ListingTagCategoryInfo, ListingTagShort, GroupedListingTagsResponse

router = APIRouter(
    prefix="/listing-tags",
    tags=["Listing Tags"]
)

@router.get("", response_model=List[ListingTagResponse])
async def get_all_listing_tags():
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


@router.get("/grouped", response_model=List[GroupedListingTagsResponse])
async def get_grouped_listing_tags():
    query = (
        select(ListingTagModel)
        .options(joinedload(ListingTagModel.category))
        .order_by(ListingTagModel.listing_tag_category_id)
    )

    listing_tags = await ListingTagService.execute(query)

    grouped = {}
    for tag in listing_tags:
        category = tag.category
        if category.id not in grouped:
            grouped[category.id] = {
                "category": ListingTagCategoryInfo(id=category.id, name=category.name),
                "tags": []
            }
        grouped[category.id]["tags"].append(ListingTagShort(id=tag.id, name=tag.name))

    return list(grouped.values())


