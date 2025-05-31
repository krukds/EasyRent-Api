from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from starlette import status

from auth_app import get_current_active_user
from db.models import FavoritesModel, UserModel, ListingModel, ListingTagModel
from db.services.main_services import FavoritesService, ListingService, UserService
from listing_app.schemes import ListingDetailResponse, UserShortResponse
from .schemes import FavoritesResponse, FavoritesPayload, FavoriteListingResponse
from typing import List, Optional

router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"]
)


@router.get("", response_model=List[FavoriteListingResponse])
async def get_favorite_listings(user: UserModel = Depends(get_current_active_user)):
    # 1. Отримуємо всі обрані listing_id
    query = select(FavoritesModel).where(FavoritesModel.user_id == user.id)
    favorites = await FavoritesService.execute(query)

    if not favorites:
        return []

    # Створюємо мапу {listing_id: favorite_id}
    listing_id_to_favorite_id = {fav.listing_id: fav.id for fav in favorites}
    listing_ids = list(listing_id_to_favorite_id.keys())

    # 2. Отримуємо повні оголошення
    listing_query = (
        select(ListingModel)
        .where(ListingModel.id.in_(listing_ids))
        .options(
            joinedload(ListingModel.owner),
            joinedload(ListingModel.tags),
            joinedload(ListingModel.images),
            joinedload(ListingModel.city),
            joinedload(ListingModel.street),
            joinedload(ListingModel.listing_type),
            joinedload(ListingModel.heating_type),
            joinedload(ListingModel.listing_status),
        )
    )
    listings = await ListingService.execute(listing_query)

    results = []
    for l in listings:
        rating_data = await UserService.get_user_rating_stats(l.owner.id) if l.owner else {}

        listing_data = ListingDetailResponse(
            id=l.id,
            name=l.name,
            description=l.description,
            price=l.price,
            city_id=l.city_id,
            city_name=l.city.name_ukr,
            street_id=l.street_id,
            street_name_ukr=l.street.name_ukr,
            building=l.building,
            flat=l.flat,
            floor=l.floor,
            all_floors=l.all_floors,
            rooms=l.rooms,
            bathrooms=l.bathrooms,
            square=l.square,
            communal=l.communal,
            owner=UserShortResponse(
                id=l.owner.id,
                first_name=l.owner.first_name,
                last_name=l.owner.last_name,
                phone=l.owner.phone,
                email=l.owner.email,
                photo_url=l.owner.photo_url,
                average_rating=rating_data.get("average_rating", 0.0),
                reviews_count=rating_data.get("reviews_count", 0),
            ) if l.owner else None,
            listing_type=l.listing_type.name,
            heating_type=l.heating_type.name,
            listing_status=l.listing_status.name,
            created_at=l.created_at,
            tags=[tag.name for tag in l.tags],
            images=[img.image_url for img in l.images] if l.images else [],
            discard_reason=l.discard_reason,
        )

        results.append(FavoriteListingResponse(
            favorite_id=listing_id_to_favorite_id[l.id],
            listing=listing_data
        ))

    return results


@router.post("", response_model=FavoritesResponse)
async def add_to_favorites(
        payload: FavoritesPayload,
        user: UserModel = Depends(get_current_active_user)
):
    # 🔍 Перевіряємо, чи вже є така пара user_id + listing_id
    existing = await FavoritesService.select_one_by_filters(
        FavoritesModel.user_id == user.id,
        FavoritesModel.listing_id == payload.listing_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This listing is already in favorites"
        )

    # ✅ Додаємо до обраного
    favorite = FavoritesModel(user_id=user.id, **payload.model_dump())
    saved = await FavoritesService.save(favorite)

    return FavoritesResponse(
        id=saved.id,
        user_id=saved.user_id,
        listing_id=saved.listing_id
    )


@router.delete("/{id}")
async def delete_favorite(
        id: int,
        user: UserModel = Depends(get_current_active_user)
):
    favorite = await FavoritesService.select_one(FavoritesModel.id == id)
    if not favorite or favorite.user_id != user.id:
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