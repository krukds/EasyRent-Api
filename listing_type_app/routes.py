from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from db.models import ListingTypeModel
from db.services.main_services import ListingTypeService
from .schemes import ListingTypeResponse
from typing import List

router = APIRouter(
    prefix="/listing-types",
    tags=["Listing Types"]
)

@router.get("", response_model=List[ListingTypeResponse])
async def get_all_listing_types():
    query = select(ListingTypeModel)
    listing_types = await ListingTypeService.execute(query)

    return [
        ListingTypeResponse(id=ht.id, name=ht.name)
        for ht in listing_types
    ]
