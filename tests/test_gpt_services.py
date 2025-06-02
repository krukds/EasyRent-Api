
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock, mock_open
from services import gpt_services
from services.gpt_services import (
    passport_documents_verification,
    ownership_documents_verification,
    text_and_image_verification,
    IdVerificationGptResult,
    OwnershipVerificationGptResult,
    TextVerificationGptResult
)

@pytest.mark.asyncio
async def test_passport_documents_verification_success():
    fake_file_id = "file-123"
    fake_response = {
        "image_quality": "high",
        "valid_data": True,
        "first_name": "Ivan",
        "second_name": "Ivanov",
        "patronymic": "Ivanovich",
        "birth_date": "1990-01-01",
        "error_details": "",
        "is_front_side": True
    }

    with patch("builtins.open", mock_open(read_data=b"data")), \
         patch.object(gpt_services.client.files, "create", new=AsyncMock(return_value=MagicMock(id=fake_file_id))), \
         patch.object(gpt_services.client.beta.threads, "create", new=AsyncMock(return_value=MagicMock(id="thread-id"))), \
         patch.object(gpt_services.client.beta.threads.messages, "create", new=AsyncMock()), \
         patch.object(gpt_services.client.beta.threads.runs, "create", new=AsyncMock(return_value=MagicMock(id="run-id"))), \
         patch.object(gpt_services.client.beta.threads.runs, "retrieve", new=AsyncMock(return_value=MagicMock(status="completed"))), \
         patch.object(gpt_services.client.beta.threads.messages, "list", new=AsyncMock(return_value=MagicMock(
             data=[MagicMock(role="assistant", content=[MagicMock(text=MagicMock(value=json.dumps(fake_response)))])]
         ))):
        result = await passport_documents_verification(["any_path.jpg"])
        assert result.valid_data is True
        assert result.first_name == "Ivan"


@pytest.mark.asyncio
async def test_ownership_documents_verification_success():
    fake_file_id = "file-456"
    fake_response = {
        "valid": True,
        "belongs_to_user": True,
        "error_details": ""
    }

    with patch("builtins.open", mock_open(read_data=b"data")), \
         patch.object(gpt_services.client.files, "create", new=AsyncMock(return_value=MagicMock(id=fake_file_id))), \
         patch.object(gpt_services.client.beta.threads, "create", new=AsyncMock(return_value=MagicMock(id="thread-id"))), \
         patch.object(gpt_services.client.beta.threads.messages, "create", new=AsyncMock()), \
         patch.object(gpt_services.client.beta.threads.runs, "create", new=AsyncMock(return_value=MagicMock(id="run-id"))), \
         patch.object(gpt_services.client.beta.threads.runs, "retrieve", new=AsyncMock(return_value=MagicMock(status="completed"))), \
         patch.object(gpt_services.client.beta.threads.messages, "list", new=AsyncMock(return_value=MagicMock(
             data=[MagicMock(role="assistant", content=[MagicMock(text=MagicMock(value=json.dumps(fake_response)))])]
         ))):
        result = await ownership_documents_verification("Ivan", "Ivanov", "Ivanovich", "1990-01-01", "any_path.jpg")
        assert result.valid is True
        assert result.belongs_to_user is True

@pytest.mark.asyncio
async def test_text_verification_success():
    fake_response = {
        "is_ok": True,
        "reason_details": "Clean text"
    }

    with patch.object(gpt_services.client.beta.threads, "create", new=AsyncMock(return_value=MagicMock(id="thread-id"))),              patch.object(gpt_services.client.beta.threads.messages, "create", new=AsyncMock()),              patch.object(gpt_services.client.beta.threads.runs, "create", new=AsyncMock(return_value=MagicMock(id="run-id"))),              patch.object(gpt_services.client.beta.threads.runs, "retrieve", new=AsyncMock(return_value=MagicMock(status="completed"))),              patch.object(gpt_services.client.beta.threads.messages, "list", new=AsyncMock(return_value=MagicMock(data=[MagicMock(role="assistant", content=[MagicMock(text=MagicMock(value=json.dumps(fake_response)))])]))):

        result = await text_and_image_verification("some clean input text")
        assert isinstance(result, TextVerificationGptResult)
        assert result.is_ok is True
