import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.db import create_job, update_job_status
from app.main import create_app


@pytest_asyncio.fixture
async def app(tmp_data_dir, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_data_dir))
    import app.config as config
    config.BASE_DIR = tmp_data_dir
    config.UPLOAD_DIR = tmp_data_dir / "uploads"
    config.OUTPUT_DIR = tmp_data_dir / "outputs"
    config.DB_PATH = tmp_data_dir / "db.sqlite3"
    config.UPLOAD_DIR.mkdir(exist_ok=True)
    config.OUTPUT_DIR.mkdir(exist_ok=True)

    application = create_app()
    async with application.router.lifespan_context(application):
        yield application


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_email_rejects_missing_turnstile_token(client):
    response = await client.post("/api/email", json={"job_id": "job-1", "email": "user@example.com"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_email_rejects_invalid_turnstile_token(client):
    with patch("app.main.verify_turnstile", AsyncMock(return_value=False)):
        response = await client.post(
            "/api/email",
            json={"job_id": "job-1", "email": "user@example.com", "turnstile_token": "bad"},
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "Turnstile verification failed."


@pytest.mark.asyncio
async def test_email_throttles_repeat_requests(client, app):
    job_id = await create_job(app.state.db, filename="test.pdf", upload_path="/tmp/test.pdf")
    await update_job_status(
        app.state.db,
        job_id,
        status="completed",
        output_path="/tmp/test.csv",
        download_token="tok-123",
        row_count=10,
    )

    with patch("app.main.verify_turnstile", AsyncMock(return_value=True)), patch(
        "app.email_service.send_download_email", AsyncMock(return_value=True)
    ):
        first = await client.post(
            "/api/email",
            json={"job_id": job_id, "email": "user@example.com", "turnstile_token": "ok"},
        )
        second = await client.post(
            "/api/email",
            json={"job_id": job_id, "email": "user@example.com", "turnstile_token": "ok"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
