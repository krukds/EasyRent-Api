from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from admin_app.schemes import AdminUserResponse, AdminReviewResponse
from auth_app.deps import get_admin_user
from db.services.main_services import UserService, ReviewService
from db.models import UserModel, ListingModel, ReviewModel

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/block-user/{user_id}")
async def block_user(user_id: int, admin: UserModel = Depends(get_admin_user)):
    user = await UserService.select_one(UserModel.id == user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await UserService.save(user)
    return {"status": "ok", "message": f"User {user_id} blocked"}


@router.post("/unblock-user/{user_id}")
async def unblock_user(user_id: int, admin: UserModel = Depends(get_admin_user)):
    user = await UserService.select_one(UserModel.id == user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    await UserService.save(user)
    return {"status": "ok", "message": f"User {user_id} unblocked"}


@router.delete("/review/{review_id}")
async def delete_review(review_id: int, admin: UserModel = Depends(get_admin_user)):
    deleted = await ReviewService.delete(id=review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"status": "ok", "message": f"Review {review_id} deleted"}


@router.get("/users", response_model=List[AdminUserResponse])
async def get_users_for_admin(
    id: Optional[int] = Query(None),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    _: UserModel = Depends(get_admin_user)  # Перевірка, що адмін
):
    query = select(UserModel)

    if id:
        query = query.where(UserModel.id == id)
    if first_name:
        query = query.where(UserModel.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.where(UserModel.last_name.ilike(f"%{last_name}%"))

    users = await UserService.execute(query)

    responses = []
    for user in users:
        # 🔁 Отримуємо рейтинг і кількість відгуків
        rating_stats = await UserService.get_user_rating_stats(user.id)

        # 🔢 Підрахунок кількості оголошень
        listing_count_q = select(func.count()).select_from(ListingModel).where(ListingModel.owner_id == user.id)
        listing_count_result = await UserService.execute(listing_count_q)
        listing_count = listing_count_result[0] if listing_count_result else 0

        responses.append(AdminUserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            photo_url=user.photo_url,
            is_active=user.is_active,
            role=user.role,
            listing_count=listing_count,
            review_count=rating_stats["reviews_count"],
            average_rating=rating_stats["average_rating"]
        ))

    return responses



@router.get("/reviews", response_model=List[AdminReviewResponse])
async def get_reviews_for_admin(
    owner_id: Optional[int] = Query(None),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    _: UserModel = Depends(get_admin_user)
):
    query = (
        select(ReviewModel)
        .join(ReviewModel.owner)
        .options(
            joinedload(ReviewModel.owner),
            joinedload(ReviewModel.tags),
            joinedload(ReviewModel.review_status)
        )
    )

    if owner_id:
        query = query.where(ReviewModel.owner_id == owner_id)
    if first_name:
        query = query.where(UserModel.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.where(UserModel.last_name.ilike(f"%{last_name}%"))

    result = await ReviewService.execute(query)
    reviews = result or []

    return [
        AdminReviewResponse(
            id=r.id,
            user_id=r.user_id,
            owner_id=r.owner_id,
            rating=r.rating,
            description=r.description,
            created_at=r.created_at,
            review_status=r.review_status.name if r.review_status else None,
            tags=[t.name for t in r.tags],
            owner_first_name=r.owner.first_name if r.owner else None,
            owner_last_name=r.owner.last_name if r.owner else None
        )
        for r in reviews
    ]
