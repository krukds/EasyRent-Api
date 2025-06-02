import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from services import worker_checking_listing_relevance


@pytest.mark.asyncio
async def test_worker_checking_listing_relevance_success():
    fake_listing = MagicMock()
    fake_listing.name = "Test Listing"
    fake_listing.owner_id = 1

    fake_user = MagicMock()
    fake_user.email = "test@example.com"

    with patch("services.worker_checking_listing_relevance.ListingService.select", new=AsyncMock(return_value=[fake_listing])), \
         patch("services.worker_checking_listing_relevance.UserService.select_one", new=AsyncMock(return_value=fake_user)), \
         patch("services.worker_checking_listing_relevance.send_email_async", new=AsyncMock()) as mock_send_email, \
         patch("services.worker_checking_listing_relevance.ListingService.save", new=AsyncMock()) as mock_save:

        await worker_checking_listing_relevance.worker_checking_listing_relevance()

        mock_send_email.assert_awaited_once_with(
            "test@example.com",
            subject="EasyRent - повідомлення про архівацію оголошення",
            body=ANY
        )
        mock_save.assert_awaited_once()


@pytest.mark.asyncio
async def test_worker_checking_listing_relevance_no_listings():
    with patch("services.worker_checking_listing_relevance.ListingService.select", new=AsyncMock(return_value=[])), \
         patch("services.worker_checking_listing_relevance.send_email_async") as mock_send_email, \
         patch("services.worker_checking_listing_relevance.ListingService.save") as mock_save:

        await worker_checking_listing_relevance.worker_checking_listing_relevance()

        mock_send_email.assert_not_called()
        mock_save.assert_not_called()


@pytest.mark.asyncio
async def test_worker_checking_listing_relevance_user_not_found():
    fake_listing = MagicMock()
    fake_listing.name = "Test"
    fake_listing.owner_id = 1

    with patch("services.worker_checking_listing_relevance.ListingService.select", new=AsyncMock(return_value=[fake_listing])), \
         patch("services.worker_checking_listing_relevance.UserService.select_one", new=AsyncMock(return_value=None)), \
         patch("services.worker_checking_listing_relevance.send_email_async") as mock_send_email, \
         patch("services.worker_checking_listing_relevance.ListingService.save") as mock_save:

        await worker_checking_listing_relevance.worker_checking_listing_relevance()

        mock_send_email.assert_not_called()
        mock_save.assert_not_called()


@pytest.mark.asyncio
async def test_worker_checking_listing_relevance_multiple():
    fake_listings = [MagicMock(name=f"Listing {i}", owner_id=i) for i in range(3)]
    fake_user = MagicMock()
    fake_user.email = "multi@example.com"

    with patch("services.worker_checking_listing_relevance.ListingService.select", new=AsyncMock(return_value=fake_listings)), \
         patch("services.worker_checking_listing_relevance.UserService.select_one", new=AsyncMock(return_value=fake_user)), \
         patch("services.worker_checking_listing_relevance.send_email_async", new=AsyncMock()) as mock_send_email, \
         patch("services.worker_checking_listing_relevance.ListingService.save", new=AsyncMock()) as mock_save:

        await worker_checking_listing_relevance.worker_checking_listing_relevance()

        assert mock_send_email.await_count == 3
        assert mock_save.await_count == 3


def test_start_scheduler_adds_job(monkeypatch):
    scheduler_mock = MagicMock()
    monkeypatch.setattr("services.worker_checking_listing_relevance.AsyncIOScheduler", lambda: scheduler_mock)

    worker_checking_listing_relevance.start_scheduler()

    scheduler_mock.add_job.assert_called_once()
    scheduler_mock.start.assert_called_once()
