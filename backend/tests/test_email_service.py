import pytest
from unittest.mock import AsyncMock, patch

from app.email_service import send_download_email, get_email_provider


def test_get_email_provider_brevo():
    provider = get_email_provider("brevo")
    assert provider.name == "brevo"


def test_get_email_provider_mailjet():
    provider = get_email_provider("mailjet")
    assert provider.name == "mailjet"


def test_get_email_provider_invalid():
    with pytest.raises(ValueError, match="Unknown email provider"):
        get_email_provider("sendgrid")


@pytest.mark.asyncio
async def test_send_download_email_brevo():
    with patch("app.email_service.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.return_value = AsyncMock(status_code=201)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await send_download_email(
            provider_name="brevo",
            api_key="test-key",
            from_email="noreply@example.com",
            to_email="user@example.com",
            download_url="https://example.com/api/download/abc123",
            filename="report.pdf",
        )
        assert result is True
        mock_client.post.assert_called_once()
