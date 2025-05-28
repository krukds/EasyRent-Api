from typing import List

from sqlalchemy import insert, delete, select, func

from db.base import async_session_maker
from db.models import (
    UserModel,
    SessionModel,
    ListingModel,
    ListingTypeModel,
    HeatingTypeModel,
    ListingStatusModel,
    ImageModel,
    ReviewModel,
    ReviewStatusModel,
    ReviewTagModel,
    ReviewTagReviewModel,
    FavoritesModel,
    ListingTagCategoryModel,
    ListingTagModel,
    ListingTagListingModel, CityModel, StreetModel,
)
from db.services.base_service import BaseService


class UserService(BaseService[UserModel]):
    model = UserModel
    session_maker = async_session_maker

    @classmethod
    async def get_user_rating_stats(cls, user_id: int) -> dict:
        async with cls.session_maker() as session:
            # Середній рейтинг
            avg_rating_query = select(func.avg(ReviewModel.rating)).where(ReviewModel.owner_id == user_id)
            avg_rating_result = await session.execute(avg_rating_query)
            avg_rating = avg_rating_result.scalar()

            # Кількість відгуків
            count_query = select(func.count()).select_from(ReviewModel).where(ReviewModel.owner_id == user_id)
            count_result = await session.execute(count_query)
            review_count = count_result.scalar()

            return {
                "average_rating": float(avg_rating) if avg_rating is not None else None,
                "reviews_count": review_count or 0,
            }


class SessionService(BaseService[SessionModel]):
    model = SessionModel
    session_maker = async_session_maker


class ListingService(BaseService[ListingModel]):
    model = ListingModel
    session_maker = async_session_maker

    @classmethod
    async def add_tags_to_listing(cls, listing_id: int, tag_ids: List[int]):
        if not tag_ids:
            return

        async with cls.session_maker() as session:
            values = [
                {"listing_id": listing_id, "listing_tag_id": tag_id}
                for tag_id in tag_ids
            ]
            insert_query = insert(ListingTagListingModel).values(values)
            await session.execute(insert_query)
            await session.commit()


    @classmethod
    async def update_tags_for_listing(cls, listing_id: int, new_tag_ids: List[int]):
        async with cls.session_maker() as session:
            # 1. Видалити старі зв'язки
            await session.execute(
                delete(ListingTagListingModel).where(ListingTagListingModel.listing_id == listing_id)
            )

            # 2. Додати нові
            if new_tag_ids:
                insert_data = [
                    {"listing_id": listing_id, "listing_tag_id": tag_id}
                    for tag_id in new_tag_ids
                ]
                await session.execute(insert(ListingTagListingModel).values(insert_data))

            await session.commit()


class ListingTypeService(BaseService[ListingTypeModel]):
    model = ListingTypeModel
    session_maker = async_session_maker


class HeatingTypeService(BaseService[HeatingTypeModel]):
    model = HeatingTypeModel
    session_maker = async_session_maker


class ListingStatusService(BaseService[ListingStatusModel]):
    model = ListingStatusModel
    session_maker = async_session_maker


class ImageService(BaseService[ImageModel]):
    model = ImageModel
    session_maker = async_session_maker


class ReviewService(BaseService[ReviewModel]):
    model = ReviewModel
    session_maker = async_session_maker

    @classmethod
    async def add_tags_to_review(cls, review_id: int, tag_ids: list[int]):
        if not tag_ids:
            return

        async with cls.session_maker() as session:
            query = insert(ReviewTagReviewModel).values(
                [{"review_id": review_id, "review_tag_id": tag_id} for tag_id in tag_ids]
            )
            await session.execute(query)
            await session.commit()


class ReviewStatusService(BaseService[ReviewStatusModel]):
    model = ReviewStatusModel
    session_maker = async_session_maker


class ReviewTagService(BaseService[ReviewTagModel]):
    model = ReviewTagModel
    session_maker = async_session_maker


class ReviewTagReviewService(BaseService[ReviewTagReviewModel]):
    model = ReviewTagReviewModel
    session_maker = async_session_maker


class FavoritesService(BaseService[FavoritesModel]):
    model = FavoritesModel
    session_maker = async_session_maker


class ListingTagCategoryService(BaseService[ListingTagCategoryModel]):
    model = ListingTagCategoryModel
    session_maker = async_session_maker


class ListingTagService(BaseService[ListingTagModel]):
    model = ListingTagModel
    session_maker = async_session_maker

class ListingTagListingService(BaseService[ListingTagListingModel]):
    model = ListingTagListingModel
    session_maker = async_session_maker

class CityService(BaseService[CityModel]):
    model = CityModel
    session_maker = async_session_maker

class StreetService(BaseService[StreetModel]):
    model = StreetModel
    session_maker = async_session_maker
