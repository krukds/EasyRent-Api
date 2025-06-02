import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services import worker_moderate_listings
from listing_app.schemes import ACTIVE_STATUS_ID, DISCARD_STATUS_ID

pytestmark = pytest.mark.asyncio


@pytest.fixture
def fake_listing():
    listing = MagicMock()
    listing.id = 1
    listing.name = "Test Listing"
    listing.description = "Nice flat"
    listing.document_ownership_path = "/fake/path.jpg"
    listing.owner_id = 123
    return listing


@pytest.fixture
def fake_user():
    user = MagicMock()
    user.first_name = "Ivan"
    user.last_name = "Ivanov"
    user.patronymic = "Ivanovich"
    user.birth_date = "1990-01-01"
    return user


async def test_skip_listing_with_missing_fields():
    listing = MagicMock(name=None, description="desc", document_ownership_path=None)
    with patch("services.worker_moderate_listings.ListingService.select", new=AsyncMock(return_value=[listing])), \
         patch("services.worker_moderate_listings.UserService.select_one", new=AsyncMock()):
        await worker_moderate_listings.worker_moderate_listings()


async def test_listing_discarded_due_to_text_verification(fake_listing, fake_user):
    with patch("services.worker_moderate_listings.ListingService.select", new=AsyncMock(return_value=[fake_listing])), \
         patch("services.worker_moderate_listings.UserService.select_one", new=AsyncMock(return_value=fake_user)), \
         patch("services.worker_moderate_listings.text_verification", new=AsyncMock(return_value=MagicMock(is_ok=False, reason_details="bad text"))), \
         patch("services.worker_moderate_listings.ownership_documents_verification"), \
         patch("services.worker_moderate_listings.ListingService.save", new=AsyncMock()) as mock_save:

        await worker_moderate_listings.worker_moderate_listings()
        assert fake_listing.listing_status_id == DISCARD_STATUS_ID
        mock_save.assert_awaited_once()


async def test_listing_discarded_due_to_document_verification(fake_listing, fake_user):
    with patch("services.worker_moderate_listings.ListingService.select", new=AsyncMock(return_value=[fake_listing])), \
         patch("services.worker_moderate_listings.UserService.select_one", new=AsyncMock(return_value=fake_user)), \
         patch("services.worker_moderate_listings.text_verification", new=AsyncMock(return_value=MagicMock(is_ok=True))), \
         patch("services.worker_moderate_listings.ownership_documents_verification", new=AsyncMock(return_value=MagicMock(valid=False, belongs_to_user=False, error_details="not valid"))), \
         patch("services.worker_moderate_listings.ListingService.save", new=AsyncMock()) as mock_save:

        await worker_moderate_listings.worker_moderate_listings()
        assert fake_listing.listing_status_id == DISCARD_STATUS_ID
        mock_save.assert_awaited_once()


async def test_listing_passes_all_checks(fake_listing, fake_user):
    with patch("services.worker_moderate_listings.ListingService.select", new=AsyncMock(return_value=[fake_listing])), \
         patch("services.worker_moderate_listings.UserService.select_one", new=AsyncMock(return_value=fake_user)), \
         patch("services.worker_moderate_listings.text_verification", new=AsyncMock(return_value=MagicMock(is_ok=True))), \
         patch("services.worker_moderate_listings.ownership_documents_verification", new=AsyncMock(return_value=MagicMock(valid=True, belongs_to_user=True, error_details=""))), \
         patch("services.worker_moderate_listings.ListingService.save", new=AsyncMock()) as mock_save:

        await worker_moderate_listings.worker_moderate_listings()
        assert fake_listing.listing_status_id == ACTIVE_STATUS_ID
        mock_save.assert_awaited()
