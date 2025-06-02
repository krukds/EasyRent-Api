import pytest
from unittest.mock import patch, MagicMock

import pytest

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.mailing import send_email, send_email_async


def test_send_email_success():
    with patch("smtplib.SMTP") as mock_smtp:
        instance = mock_smtp.return_value.__enter__.return_value
        send_email("test@example.com", "Test Subject", "Test Body")

        instance.starttls.assert_called_once()
        instance.login.assert_called_once()
        instance.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_send_email_async_success():
    with patch("services.mailing.send_email") as mock_send_email:
        await send_email_async("test@example.com", "Test", "Body")
        mock_send_email.assert_called_once_with("test@example.com", "Test", "Body")
