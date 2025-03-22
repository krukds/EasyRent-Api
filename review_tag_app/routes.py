from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from db.models import ReviewTagModel
from db.services.main_services import ReviewTagService
from .schemes import ReviewTagResponse
from typing import List

router = APIRouter(
    prefix="/review-tags",
    tags=["Review Tags"]
)

@router.get("", response_model=List[ReviewTagResponse])
async def get_all_review_tags():
    query = select(ReviewTagModel)
    tags = await ReviewTagService.execute(query)

    return [
        ReviewTagResponse(id=tag.id, name=tag.name)
        for tag in tags
    ]
