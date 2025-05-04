from datetime import datetime
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Form, UploadFile, File
from sqlalchemy import select, update, insert, func
from sqlalchemy.orm import joinedload

from db.models import ListingModel, ListingTagListingModel, ReviewModel, ImageModel
from db.services.main_services import ListingService, ReviewService, UserService
from .schemes import ListingPayload, ListingResponse, ListingDetailResponse, UserShortResponse
from typing import List, Optional
from sqlalchemy.orm import joinedload


UPLOAD_DIR = Path("static/listing_photos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
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
    query = select(ListingModel).options(joinedload(ListingModel.images)).order_by(ListingModel.id)

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

    return [
        ListingResponse(
            id=l.id,
            name=l.name,
            description=l.description,
            price=l.price,
            city=l.city,
            street=l.street,
            building=l.building,
            flat=l.flat,
            floor=l.floor,
            all_floors=l.all_floors,
            rooms=l.rooms,
            bathrooms=l.bathrooms,
            square=l.square,
            communal=l.communal,
            created_at=l.created_at,
            owner_id=l.owner_id,
            heating_type_id=l.heating_type_id,
            listing_type_id=l.listing_type_id,
            listing_status_id=l.listing_status_id,
            latitude=l.latitude,
            longitude=l.longitude,
            images=[img.image_url for img in l.images] if l.images else []
        )
        for l in listings
    ]


@router.get("/{id}", response_model=ListingDetailResponse)
async def get_listing_by_id(id: int):
    query = (
        select(ListingModel)
        .options(
            joinedload(ListingModel.images),
            joinedload(ListingModel.listing_type),
            joinedload(ListingModel.heating_type),
            joinedload(ListingModel.listing_status),
            joinedload(ListingModel.tags),
            joinedload(ListingModel.owner),
            joinedload(ListingModel.images)
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
        tags=[tag.name for tag in listing.tags],
        latitude=listing.latitude,
        longitude=listing.longitude,
        images=[img.image_url for img in listing.images] if listing.images else []
    )


@router.post("", response_model=ListingDetailResponse)
async def create_listing(
    name: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    city: str = Form(...),
    street: str = Form(...),
    building: str = Form(...),
    flat: Optional[int] = Form(None),
    floor: int = Form(...),
    all_floors: int = Form(...),
    rooms: int = Form(...),
    bathrooms: Optional[int] = Form(None),
    square: int = Form(...),
    communal: int = Form(...),
    owner_id: int = Form(...),
    heating_type_id: int = Form(...),
    listing_type_id: int = Form(...),
    listing_status_id: int = Form(...),
    tag_ids: Optional[str] = Form(None),
    latitude_raw: Optional[str] = Form(None),
    longitude_raw: Optional[str] = Form(None),
    images: List[UploadFile] = File(...)
):
    if len(images) < 4:
        raise HTTPException(status_code=400, detail="At least 4 images are required.")

    # Парсимо координати з рядка у float
    try:
        latitude = float(latitude_raw) if latitude_raw else None
        longitude = float(longitude_raw) if longitude_raw else None
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid latitude or longitude format")

    # Парсимо список тегів
    parsed_tag_ids = [int(tag.strip()) for tag in tag_ids.split(",")] if tag_ids else []

    # Зберігаємо зображення у файлову систему
    filenames = []
    for img in images:
        file_path = UPLOAD_DIR / img.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(img.file, f)
        filenames.append(img.filename)

    # Зберігаємо оголошення та зображення в базу
    async with ListingService.session_maker() as session:
        listing = ListingModel(
            name=name,
            description=description,
            price=price,
            city=city,
            street=street,
            building=building,
            flat=flat,
            floor=floor,
            all_floors=all_floors,
            rooms=rooms,
            bathrooms=bathrooms,
            square=square,
            communal=communal,
            owner_id=owner_id,
            heating_type_id=heating_type_id,
            listing_type_id=listing_type_id,
            listing_status_id=listing_status_id,
            latitude=latitude,
            longitude=longitude,
            created_at=datetime.utcnow()
        )
        session.add(listing)
        await session.flush()

        for filename in filenames:
            session.add(ImageModel(listing_id=listing.id, image_url=filename))

        await session.commit()

    # Додаємо теги
    await ListingService.add_tags_to_listing(listing.id, parsed_tag_ids)

    # Завантажуємо повністю заповнений об'єкт
    async with ListingService.session_maker() as session:
        result = await session.execute(
            select(ListingModel)
            .options(
                joinedload(ListingModel.tags),
                joinedload(ListingModel.listing_type),
                joinedload(ListingModel.heating_type),
                joinedload(ListingModel.listing_status),
                joinedload(ListingModel.images),
                joinedload(ListingModel.owner),
            )
            .where(ListingModel.id == listing.id)
        )
        full_listing = result.unique().scalar_one()

        return ListingDetailResponse(
            **{
                key: value
                for key, value in full_listing.__dict__.items()
                if key not in {
                    "_sa_instance_state",
                    "tags", "listing_type", "heating_type", "listing_status", "images", "owner"
                }
            },
            tags=[tag.name for tag in full_listing.tags],
            listing_type=full_listing.listing_type.name if full_listing.listing_type else None,
            heating_type=full_listing.heating_type.name if full_listing.heating_type else None,
            listing_status=full_listing.listing_status.name if full_listing.listing_status else None,
            images=[img.image_url for img in full_listing.images],
            owner=UserShortResponse(
                id=full_listing.owner.id,
                email=full_listing.owner.email,
                first_name=full_listing.owner.first_name,
                last_name=full_listing.owner.last_name,
                phone=full_listing.owner.phone,
                photo_url=full_listing.owner.photo_url,
            ) if full_listing.owner else None
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
                joinedload(ListingModel.owner)
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
        tags=[tag.name for tag in updated_listing.tags],
        latitude=updated_listing.latitude,
        longitude=updated_listing.longitude
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