import datetime

from db.models import ListingModel
from db.services.main_services import ListingService, UserService
from listing_app.schemes import MODERATION_STATUS_ID, DISCARD_STATUS_ID
from services.gpt_services import ownership_documents_verification, text_verification


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

        if not listing.document_ownership_path or not listing.name or not listing.description:
            continue

        # Content Verification
        verification_result = await text_verification(f"Оголошення про нерухомість:\n{listing.name}\n{listing.description}")
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
            listing.document_ownership_path
        )
        if not verification_result.valid or not verification_result.belongs_to_user or verification_result.error_details:
            await discard_listing_service(
                listing,
                discard_reason=f"Ваше фото документу 'Право власності' не пройшло модерацію. Причина: {verification_result.error_details or '-'}"
            )
            continue

