from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List

from db.models import ListingStatusModel
from db.services.main_services import ListingStatusService
from .schemes import ListingStatusResponse

router = APIRouter(
    prefix="/listing-statuses",
    tags=["Listing Statuses"]
)

@router.get("", response_model=List[ListingStatusResponse])
async def get_all_listing_statuses_types():
    query = select(ListingStatusModel)
    listing_statuses = await ListingStatusService.execute(query)

    return [
        ListingStatusResponse(
            id=ls.id,
            name=ls.name,
            listing_status_id=ls.id,
        )
        for ls in listing_statuses
    ]

