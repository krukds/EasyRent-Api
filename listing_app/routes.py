import shutil
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Form, UploadFile, File, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from auth_app import get_current_active_user
from db.models import ListingModel, ImageModel, ListingTagModel, UserModel
from db.services.main_services import ListingService, UserService
from listing_tag_app.schemes import ListingTagShort
from .schemes import ListingPayload, ListingResponse, ListingDetailResponse, UserShortResponse, UPLOAD_DIR, \
    ACTIVE_STATUS_ID, ARCHIVED_STATUS_ID, MODERATION_STATUS_ID

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
router = APIRouter(
    prefix="/listing",
    tags=["Listings"]
)

@router.get("", response_model=List[ListingResponse])
async def get_all_listings(
    city_id: Optional[int] = Query(None),
    street_id: Optional[int] = Query(None),
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
    status_id: Optional[int] = Query(None),
    tag_ids: Optional[str] = Query(None),
    sort_by: str = Query("price_desc")
):
    if tag_ids is not None:
        tag_ids = list(map(int, tag_ids.split(",")))
    query = (
        select(ListingModel)
        .options(
            joinedload(ListingModel.images),
            joinedload(ListingModel.street),
            joinedload(ListingModel.city),
            joinedload(ListingModel.tags)
        )
    )

    if sort_by == "price_desc":
        query = query.order_by(ListingModel.price.desc())
    elif sort_by == "price_asc":
        query = query.order_by(ListingModel.price.asc())
    else:
        query = query.order_by(ListingModel.id.desc())

    if city_id:
        query = query.where(ListingModel.city_id == city_id)
    if street_id:
        query = query.where(ListingModel.street_id == street_id)
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
    if tag_ids:
        query = query.where(ListingModel.tags.any(ListingTagModel.id.in_(tag_ids)))

    listings = await ListingService.execute(query)

    return [
        ListingResponse(
            id=l.id,
            name=l.name,
            description=l.description,
            price=l.price,
            city_id=l.city_id,
            city_name=l.city.name_ukr if l.city else "",
            street_id=l.street_id,
            street_name_ukr=l.street.name_ukr if l.street else "",
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
            images=[img.image_url for img in l.images] if l.images else [],
            discard_reason=l.discard_reason,
            tags=[
                ListingTagShort(id=tag.id, name=tag.name)
                for tag in l.tags
            ] if l.tags else []
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
            joinedload(ListingModel.street),
            joinedload(ListingModel.city),
        )
        .where(ListingModel.id == id)
    )

    result = await ListingService.execute(query)
    listing = result[0] if result else None

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Якщо owner є — отримаємо рейтинг, інакше None
    rating_data = (
        await UserService.get_user_rating_stats(listing.owner.id)
        if listing.owner else {"average_rating": 0.0, "reviews_count": 0}
    )

    return ListingDetailResponse(
        id=listing.id,
        name=listing.name,
        description=listing.description,
        price=listing.price,
        city_id=listing.city_id,
        city_name=listing.city.name_ukr if listing.city else "",
        street_id=listing.street_id,
        street_name_ukr=listing.street.name_ukr if listing.street else "",
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
        images=[img.image_url for img in listing.images] if listing.images else [],
        discard_reason=listing.discard_reason,
    )


@router.post("")
async def create_listing(
        name: str = Form(...),
        description: str = Form(...),
        price: int = Form(...),
        city_id: int = Form(...),
        street_id: int = Form(...),
        building: str = Form(...),
        flat: Optional[int] = Form(None),
        floor: int = Form(...),
        all_floors: int = Form(...),
        rooms: int = Form(...),
        bathrooms: Optional[int] = Form(None),
        square: int = Form(...),
        communal: int = Form(...),
        # owner_id: int = Form(...),
        heating_type_id: int = Form(...),
        listing_type_id: int = Form(...),
        # listing_status_id: int = Form(...),
        tag_ids: Optional[str] = Form(None),
        images: List[UploadFile] = File(...),
        document_ownership: UploadFile = File(...),
        user: UserModel = Depends(get_current_active_user)

):
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Ви повинні бути верифікованими")

    if len(images) < 5:
        raise HTTPException(status_code=400, detail="Повинно бути щонайменше 5 фотографій")

    document_ownership_path = UPLOAD_DIR / f"{time.time()}-{document_ownership.filename}"
    with open(document_ownership_path, "wb") as f:
        shutil.copyfileobj(document_ownership.file, f)
    
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
            city_id=city_id,
            street_id=street_id,
            building=building,
            flat=flat,
            floor=floor,
            all_floors=all_floors,
            rooms=rooms,
            bathrooms=bathrooms,
            square=square,
            communal=communal,
            owner_id=user.id,
            heating_type_id=heating_type_id,
            listing_type_id=listing_type_id,
            listing_status_id=MODERATION_STATUS_ID,
            created_at=datetime.utcnow(),
            discard_reason=None,
            document_ownership_path=str(document_ownership_path)
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
        print(full_listing.__dict__)
        return {"status": True}


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
        listing.listing_status_id = MODERATION_STATUS_ID

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
    )



@router.delete("/{id}")
async def delete_listing(id: int):
    listing = await ListingService.select_one(ListingModel.id == id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    await ListingService.delete(id=id)
    return {"status": "ok"}


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
    archived_listing_id = result[0] if result else None

    if archived_listing_id is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    return {
        "status": "ok",
        "message": "Listing archived successfully",
        "listing_id": archived_listing_id
    }

@router.put("/{id}/activate")
async def activate_listing(id: int):
    query = (
        update(ListingModel)
        .where(ListingModel.id == id)
        .values(listing_status_id=ACTIVE_STATUS_ID)
        .returning(ListingModel.id)
    )
    print(f"Executing: UPDATE listing SET listing_status_id = {ACTIVE_STATUS_ID} WHERE id = {id}")

    result = await ListingService.execute(query, commit=True)
    activated_listing_id = result[0] if result else None

    if activated_listing_id is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    return {
        "status": "ok",
        "message": "Listing activated successfully",
        "listing_id": activated_listing_id
    }



@router.patch("/{id}/reason")
async def update_discard_reason(id: int, reason: str = Form(...)):
    query = (
        update(ListingModel)
        .where(ListingModel.id == id)
        .values(discard_reason=reason)
        .returning(ListingModel.id)
    )
    result = await ListingService.execute(query, commit=True)
    if not result.first():
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"status": "ok", "message": "Reason updated"}
