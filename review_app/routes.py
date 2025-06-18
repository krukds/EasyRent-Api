from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from starlette import status

from auth_app import get_current_active_user
from auth_app.schemes import UserResponse
from db.models import ReviewModel, ReviewStatusModel, ReviewTagModel, ReviewTagReviewModel, UserModel
from db.services import UserService
from db.services.main_services import ReviewService
from services.gpt_services import text_and_image_verification
from .schemes import ReviewPayload, ReviewResponse, ReviewDetailResponse, OwnerResponse
from typing import List, Optional

from .services import verify_review_description

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)


@router.get("", response_model=List[ReviewResponse])
async def get_all_reviews(
        user_id: Optional[int] = Query(None),
        owner_id: Optional[int] = Query(None)
):
    query = (
        select(ReviewModel)
            .options(
            joinedload(ReviewModel.tags),
            joinedload(ReviewModel.review_status),
            joinedload(ReviewModel.owner),
            joinedload(ReviewModel.user)
        )
    )

    if user_id is not None:
        query = query.where(ReviewModel.user_id == user_id)
    if owner_id is not None:
        query = query.where(ReviewModel.owner_id == owner_id)

    query = query.distinct()
    reviews = await ReviewService.execute(query)

    return [
        ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            owner_id=review.owner_id,
            rating=review.rating,
            description=review.description,
            review_status_id=review.review_status_id,
            created_at=review.created_at,
            review_status=review.review_status.name if review.review_status else None,
            tags=[tag.name for tag in review.tags],
            owner=OwnerResponse(
                id=review.owner.id,
                email=review.owner.email,
                first_name=review.owner.first_name,
                last_name=review.owner.last_name,
                phone=review.owner.phone,
                photo_url=review.owner.photo_url,
            ) if review.owner else None,
            user=UserResponse(
                id=review.user.id,
                email=review.user.email,
                password=review.user.password,
                first_name=review.user.first_name,
                last_name=review.user.last_name,
                phone=review.user.phone,
                photo_url=review.user.photo_url,
                role=review.user.role,
                is_active=review.user.is_active,
                is_verified=review.user.is_verified,
            ) if review.user else None
        )
        for review in reviews
    ]


@router.get("/{id}", response_model=ReviewResponse)
async def get_review_by_id(id: int):
    query = (
        select(ReviewModel)
            .options(
            joinedload(ReviewModel.tags),
            joinedload(ReviewModel.review_status)
        )
            .where(ReviewModel.id == id)
    )

    result = await ReviewService.execute(query)
    review = result[0] if result else None

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        owner_id=review.owner_id,
        rating=review.rating,
        description=review.description,
        review_status_id=review.review_status_id,
        created_at=review.created_at,
        review_status=review.review_status.name if review.review_status else None,
        tags=[tag.name for tag in review.tags]
    )


@router.post("", response_model=ReviewResponse)
async def create_review(
        payload: ReviewPayload,
        user: UserModel = Depends(get_current_active_user)
):
    if payload.user_id == payload.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot leave a review for yourself."
        )

    existing_review = await ReviewService.select_one_by_filters(
        ReviewModel.user_id == payload.user_id,
        ReviewModel.owner_id == payload.owner_id
    )

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review from this user to this owner already exists"
        )

    await verify_review_description(payload.description)

    async with ReviewService.session_maker() as session:
        review = ReviewModel(
            user_id=payload.user_id,
            owner_id=payload.owner_id,
            rating=payload.rating,
            description=payload.description,
            review_status_id=2,
        )
        session.add(review)
        await session.flush()
        await session.commit()

    await ReviewService.add_tags_to_review(review.id, payload.tag_ids)

    tag_count = await ReviewService.count_total_tags_for_owner(payload.owner_id)
    if tag_count > 5:
        await UserService.block_user(payload.owner_id)

    query = (
        select(ReviewModel)
            .options(joinedload(ReviewModel.tags))
            .where(ReviewModel.id == review.id)
    )
    result = await ReviewService.execute(query)
    review = result[0] if result else None

    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        owner_id=review.owner_id,
        rating=review.rating,
        description=review.description,
        review_status_id=review.review_status_id,
        created_at=review.created_at,
        tags=[tag.name for tag in review.tags]
    )


@router.put("/{id}", response_model=ReviewResponse)
async def update_review(
        id: int,
        payload: ReviewPayload,
        user: UserModel = Depends(get_current_active_user)
):
    review = await ReviewService.select_one(ReviewModel.id == id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    await verify_review_description(payload.description)

    for key, value in payload.model_dump().items():
        setattr(review, key, value)

    updated_review = await ReviewService.save(review)
    return updated_review


@router.delete("/{id}")
async def delete_review(
        id: int,
        user: UserModel = Depends(get_current_active_user)
):
    review = await ReviewService.select_one(ReviewModel.id == id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    await ReviewService.delete(id=id)
    return {"status": "ok"}
