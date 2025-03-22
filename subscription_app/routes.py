from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, insert
from sqlalchemy.orm import joinedload

from db.models import SubscriptionModel, ListingTagSubscriptionModel
from db.services.main_services import SubscriptionService
from .schemes import SubscriptionDetailResponse, SubscriptionResponse, SubscriptionPayload
from typing import List, Optional

router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"]
)


@router.get("", response_model=List[SubscriptionDetailResponse])
async def get_all_subscriptions(user_id: Optional[int] = Query(None)):
    query = (
        select(SubscriptionModel)
        .options(
            joinedload(SubscriptionModel.listing_type),
            joinedload(SubscriptionModel.heating_type),
            joinedload(SubscriptionModel.tags)
        )
    )

    if user_id is not None:
        query = query.where(SubscriptionModel.user_id == user_id)

    subscriptions = await SubscriptionService.execute(query)

    return [
        SubscriptionDetailResponse(
            id=sub.id,
            user_id=sub.user_id,
            listing_type_id=sub.listing_type_id,
            heating_type_id=sub.heating_type_id,
            min_price=sub.min_price,
            max_price=sub.max_price,
            rooms=sub.rooms,
            bathrooms=sub.bathrooms,
            min_floors=sub.min_floors,
            max_floors=sub.max_floors,
            min_all_floors=sub.min_all_floors,
            max_all_floors=sub.max_all_floors,
            min_square=sub.min_square,
            max_square=sub.max_square,
            city=sub.city,
            min_communal=sub.min_communal,
            max_communal=sub.max_communal,
            created_at=sub.created_at,
            listing_type=sub.listing_type.name if sub.listing_type else None,
            heating_type=sub.heating_type.name if sub.heating_type else None,
            tags=[tag.name for tag in sub.tags]
        )
        for sub in subscriptions
    ]

@router.post("", response_model=SubscriptionResponse)
async def create_subscription(payload: SubscriptionPayload):
    async with SubscriptionService.session_maker() as session:
        # створюємо об'єкт
        subscription = SubscriptionModel(
            **payload.model_dump(exclude={"tag_ids"})
        )
        session.add(subscription)
        await session.flush()  # отримуємо subscription.id

        # додаємо теги
        if payload.tag_ids:
            insert_values = [
                {"subscription_id": subscription.id, "listing_tag_id": tag_id}
                for tag_id in payload.tag_ids
            ]
            await session.execute(insert(ListingTagSubscriptionModel).values(insert_values))

        await session.commit()

    return SubscriptionResponse(
                **{
                    key: value
                    for key, value in subscription.__dict__.items()
                    if key != "_sa_instance_state"
                },
                tag_ids=payload.tag_ids
            )


@router.put("/{user_id}", response_model=SubscriptionResponse)
async def update_subscription(user_id: int, payload: SubscriptionPayload):
    sub = await SubscriptionService.select_one(SubscriptionModel.user_id == user_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    for key, value in payload.model_dump().items():
        setattr(sub, key, value)
    updated = await SubscriptionService.save(sub)
    return updated


@router.delete("/{user_id}")
async def delete_subscription(user_id: int):
    deleted = await SubscriptionService.delete(user_id=user_id)
    return {"status": "ok"}
