import datetime

from db.models import ListingModel
from db.services.main_services import ListingService, UserService, CityService, StreetService, ImageService
from listing_app.schemes import MODERATION_STATUS_ID, DISCARD_STATUS_ID, ACTIVE_STATUS_ID
from services.gpt_services import ownership_documents_verification, text_and_image_verification


async def discard_listing_service(listing: ListingModel, discard_reason: str):
    listing.listing_status_id = DISCARD_STATUS_ID
    listing.discard_reason = discard_reason
    await ListingService.save(listing)


async def worker_moderate_listings():
    print(f"[{datetime.datetime.now()}] worker_moderate_listings запущений")
    listings = await ListingService.select(
        listing_status_id=MODERATION_STATUS_ID
    )
    for listing in listings:
        user = await UserService.select_one(id=listing.owner_id)
        city = await CityService.select_one(id=listing.city_id)
        street = await StreetService.select_one(id=listing.street_id)
        images = await ImageService.select(listing_id=listing.id)

        if not listing.document_ownership_path or not listing.name or not listing.description:
            continue

        # Content Verification
        verification_result = await text_and_image_verification(
            f"Оголошення про нерухомість:\n{listing.name}\n{listing.description}",
            [f"static/listing_photos/{image.image_url}" for image in images]
        )
        if not verification_result.is_ok:
            await discard_listing_service(
                listing,
                discard_reason=f"Ваше оголошення не пройшло модерацію. Причина: {verification_result.reason_details or '-'}"
            )
            continue

        # Ownership Verification
        verification_result = await ownership_documents_verification(
            user.first_name,
            user.last_name,
            user.patronymic,
            user.birth_date,
            listing.document_ownership_path,
            city.name_ukr,
            street.name_ukr,
        )
        if not verification_result.valid or not verification_result.belongs_to_user or verification_result.error_details:
            await discard_listing_service(
                listing,
                discard_reason=f"Ваше фото документу 'Право власності' не пройшло модерацію. Причина: {verification_result.error_details or '-'}"
            )
            continue

        listing.listing_status_id = ACTIVE_STATUS_ID
        await ListingService.save(listing)
