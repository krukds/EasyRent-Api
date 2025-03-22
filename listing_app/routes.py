from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, update, insert, func
from sqlalchemy.orm import joinedload

from db.models import ListingModel, ListingTagListingModel, ReviewModel
from db.services.main_services import ListingService, ReviewService, UserService
from .schemes import ListingPayload, ListingResponse, ListingDetailResponse, UserShortResponse
from typing import List, Optional

router = APIRouter(
    prefix="/listing",
    tags=["Listings"]
)

@router.get("", response_model=List[ListingResponse])
async def get_all_listings(
    city: Optional[str] = Query(None),
    street: Optional[str] = Query(None),
    building: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    rooms: Optional[int] = Query(None),
    bathrooms: Optional[int] = Query(None),
    min_floor: Optional[int] = Query(None),
    max_floor: Optional[int] = Query(None),
    min_all_floors: Optional[int] = Query(None),
    max_all_floors: Optional[int] = Query(None),
    min_square: Optional[int] = Query(None),
    max_square: Optional[int] = Query(None),
    min_communal: Optional[int] = Query(None),
    max_communal: Optional[int] = Query(None),
    owner_id: Optional[int] = Query(None),
    heating_type_id: Optional[int] = Query(None),
    listing_type_id: Optional[int] = Query(None),
    status_id: Optional[int] = Query(None)
):
    query = select(ListingModel)

    if city:
        query = query.where(ListingModel.city.ilike(f"%{city}%"))
    if street:
        query = query.where(ListingModel.street.ilike(f"%{street}%"))
    if building:
        query = query.where(ListingModel.building.ilike(f"%{building}%"))

    if min_price is not None:
        query = query.where(ListingModel.price >= min_price)
    if max_price is not None:
        query = query.where(ListingModel.price <= max_price)

    if rooms is not None:
        query = query.where(ListingModel.rooms == rooms)
    if bathrooms is not None:
        query = query.where(ListingModel.bathrooms == bathrooms)

    if min_floor is not None:
        query = query.where(ListingModel.floor >= min_floor)
    if max_floor is not None:
        query = query.where(ListingModel.floor <= max_floor)

    if min_all_floors is not None:
        query = query.where(ListingModel.all_floors >= min_all_floors)
    if max_all_floors is not None:
        query = query.where(ListingModel.all_floors <= max_all_floors)

    if min_square is not None:
        query = query.where(ListingModel.square >= min_square)
    if max_square is not None:
        query = query.where(ListingModel.square <= max_square)

    if min_communal is not None:
        query = query.where(ListingModel.communal >= min_communal)
    if max_communal is not None:
        query = query.where(ListingModel.communal <= max_communal)

    if owner_id is not None:
        query = query.where(ListingModel.owner_id == owner_id)
    if heating_type_id is not None:
        query = query.where(ListingModel.heating_type_id == heating_type_id)
    if listing_type_id is not None:
        query = query.where(ListingModel.listing_type_id == listing_type_id)
    if status_id is not None:
        query = query.where(ListingModel.listing_status_id == status_id)

    listings = await ListingService.execute(query)
    return listings


from sqlalchemy.orm import joinedload

@router.get("/{id}", response_model=ListingDetailResponse)
async def get_listing_by_id(id: int):
    query = (
        select(ListingModel)
        .options(
            joinedload(ListingModel.listing_type),
            joinedload(ListingModel.heating_type),
            joinedload(ListingModel.listing_status),
            joinedload(ListingModel.tags),
            joinedload(ListingModel.owner),  # ✅ додано
        )
        .where(ListingModel.id == id)
    )

    result = await ListingService.execute(query)
    listing = result[0] if result else None

    rating_data = await UserService.get_user_rating_stats(listing.owner.id)

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    return ListingDetailResponse(
        id=listing.id,
        name=listing.name,
        description=listing.description,
        price=listing.price,
        city=listing.city,
        street=listing.street,
        building=listing.building,
        flat=listing.flat,
        floor=listing.floor,
        all_floors=listing.all_floors,
        rooms=listing.rooms,
        bathrooms=listing.bathrooms,
        square=listing.square,
        communal=listing.communal,
        owner=UserShortResponse(
            id=listing.owner.id,
            email=listing.owner.email,
            first_name=listing.owner.first_name,
            last_name=listing.owner.last_name,
            phone=listing.owner.phone,
            photo_url=listing.owner.photo_url,
            average_rating=rating_data["average_rating"],
            reviews_count=rating_data["reviews_count"],
        ) if listing.owner else None,
        created_at=listing.created_at,
        listing_type=listing.listing_type.name if listing.listing_type else None,
        heating_type=listing.heating_type.name if listing.heating_type else None,
        listing_status=listing.listing_status.name if listing.listing_status else None,
        tags=[tag.name for tag in listing.tags]
    )


@router.post("", response_model=ListingDetailResponse)
async def create_listing(payload: ListingPayload):
    async with ListingService.session_maker() as session:
        # Створення нового обʼєкта
        listing = ListingModel(**payload.model_dump(exclude={"tag_ids"}))
        session.add(listing)
        await session.flush()
        await session.commit()

        # Додаємо теги (у новій сесії, але це окей)
        await ListingService.add_tags_to_listing(listing.id, payload.tag_ids)

        # Повторно витягуємо обʼєкт разом із тегами (новий select!)
        query = (
            select(ListingModel)
            .options(
                joinedload(ListingModel.tags),
                joinedload(ListingModel.listing_type),
                joinedload(ListingModel.heating_type),
                joinedload(ListingModel.listing_status),
            )
            .where(ListingModel.id == listing.id)
        )
        result = await session.execute(query)
        listing_with_tags = result.unique().scalar_one()

        return ListingDetailResponse(
            **{
                key: value
                for key, value in listing_with_tags.__dict__.items()
                if key not in {
                    "tags", "_sa_instance_state",
                    "listing_type", "heating_type", "listing_status"
                }
            },
            listing_type=listing_with_tags.listing_type.name if listing_with_tags.listing_type else None,
            heating_type=listing_with_tags.heating_type.name if listing_with_tags.heating_type else None,
            listing_status=listing_with_tags.listing_status.name if listing_with_tags.listing_status else None,
            tags=[tag.name for tag in listing_with_tags.tags]
        )



@router.put("/{id}", response_model=ListingDetailResponse)
async def update_listing(id: int, payload: ListingPayload):
    async with ListingService.session_maker() as session:
        query = (
            select(ListingModel)
            .options(
                joinedload(ListingModel.tags),
                joinedload(ListingModel.listing_type),
                joinedload(ListingModel.heating_type),
                joinedload(ListingModel.listing_status),
            )
            .where(ListingModel.id == id)
        )
        result = await session.execute(query)
        listing = result.unique().scalar_one_or_none()

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Оновлюємо поля (крім tag_ids)
        for key, value in payload.model_dump(exclude={"tag_ids"}).items():
            setattr(listing, key, value)

        await session.commit()

    # Оновлюємо теги (в окремій сесії)
    await ListingService.update_tags_for_listing(id, payload.tag_ids)

    # Повторно отримуємо з усіма зв'язками
    async with ListingService.session_maker() as session:
        query = (
            select(ListingModel)
            .options(
                joinedload(ListingModel.tags),
                joinedload(ListingModel.listing_type),
                joinedload(ListingModel.heating_type),
                joinedload(ListingModel.listing_status),
            )
            .where(ListingModel.id == id)
        )
        result = await session.execute(query)
        updated_listing = result.unique().scalar_one()

    return ListingDetailResponse(
        **{
            key: value
            for key, value in updated_listing.__dict__.items()
            if key not in {
                "tags", "_sa_instance_state",
                "listing_type", "heating_type", "listing_status"
            }
        },
        listing_type=updated_listing.listing_type.name if updated_listing.listing_type else None,
        heating_type=updated_listing.heating_type.name if updated_listing.heating_type else None,
        listing_status=updated_listing.listing_status.name if updated_listing.listing_status else None,
        tags=[tag.name for tag in updated_listing.tags]
    )



@router.delete("/{id}")
async def delete_listing(id: int):
    listing = await ListingService.select_one(ListingModel.id == id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    await ListingService.delete(id=id)
    return {"status": "ok"}


ARCHIVED_STATUS_ID = 2



@router.put("/{id}/archive")
async def archive_listing(id: int):
    query = (
        update(ListingModel)
        .where(ListingModel.id == id)
        .values(listing_status_id=ARCHIVED_STATUS_ID)
        .returning(ListingModel.id)
    )
    print(f"Executing: UPDATE listing SET listing_status_id = {ARCHIVED_STATUS_ID} WHERE id = {id}")

    result = await ListingService.execute(query, commit=True)
    archived_listing_id = result.first()

    if archived_listing_id is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    return {
        "status": "ok",
        "message": "Listing archived successfully",
        "listing_id": archived_listing_id
    }