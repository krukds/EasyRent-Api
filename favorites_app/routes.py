from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from starlette import status

from db.models import FavoritesModel
from db.services.main_services import FavoritesService
from .schemes import FavoritesResponse, FavoritesPayload
from typing import List, Optional

router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"]
)

@router.get("", response_model=List[FavoritesResponse])
async def get_all_favorites(user_id: Optional[int] = Query(None)):
    query = select(FavoritesModel)

    if user_id is not None:
        query = query.where(FavoritesModel.user_id == user_id)

    favorites = await FavoritesService.execute(query)

    return [
        FavoritesResponse(
            id=fav.id,
            user_id=fav.user_id,
            listing_id=fav.listing_id
        )
        for fav in favorites
    ]


@router.post("", response_model=FavoritesResponse)
async def add_to_favorites(payload: FavoritesPayload):
    # 🔍 Перевіряємо, чи вже є така пара user_id + listing_id
    existing = await FavoritesService.select_one_by_filters(
        FavoritesModel.user_id == payload.user_id,
        FavoritesModel.listing_id == payload.listing_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This listing is already in favorites"
        )

    # ✅ Додаємо до обраного
    favorite = FavoritesModel(**payload.model_dump())
    saved = await FavoritesService.save(favorite)

    return FavoritesResponse(
        id=saved.id,
        user_id=saved.user_id,
        listing_id=saved.listing_id
    )


@router.delete("/{id}")
async def delete_favorite(id: int):
    favorite = await FavoritesService.select_one(FavoritesModel.id == id)
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    await FavoritesService.delete(id=id)
    return {"status": "ok", "message": "Favorite deleted"}

@router.delete("/by-user-and-listing")
async def delete_favorite_by_user_and_listing(user_id: int, listing_id: int):
    favorite = await FavoritesService.select_one_by_filters(
        FavoritesModel.user_id == user_id,
        FavoritesModel.listing_id == listing_id
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found for this user and listing")

    await FavoritesService.delete(user_id=user_id, listing_id=listing_id)
    return {"status": "ok", "message": "Favorite deleted"}