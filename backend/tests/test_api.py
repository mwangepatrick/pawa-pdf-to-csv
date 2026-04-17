import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
from unittest.mock import patch

from httpx import AsyncClient, ASGITransport

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


def _make_pdf(tmp_path: Path) -> Path:
    pytest.importorskip("reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table
    from reportlab.lib import colors

    pdf_path = tmp_path / "test.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    table_data = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
    from reportlab.platypus import TableStyle
    style = TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])
    t = Table(table_data)
    t.setStyle(style)
    doc.build([t])
    return pdf_path


@pytest.mark.asyncio
async def test_upload_valid_pdf(client, tmp_data_dir):
    pdf_path = _make_pdf(tmp_data_dir)
    with open(pdf_path, "rb") as f:
        response = await client.post("/api/upload", files={"file": ("test.pdf", f, "application/pdf")})
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "processing"


@pytest.mark.asyncio
async def test_upload_non_pdf(client, tmp_data_dir):
    txt_file = tmp_data_dir / "test.txt"
    txt_file.write_text("not a pdf")
    with open(txt_file, "rb") as f:
        response = await client.post("/api/upload", files={"file": ("test.txt", f, "text/plain")})
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


@pytest.mark.asyncio
async def test_status_not_found(client):
    response = await client.get("/api/status/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_and_poll_until_complete(client, tmp_data_dir):
    pdf_path = _make_pdf(tmp_data_dir)
    with open(pdf_path, "rb") as f:
        resp = await client.post("/api/upload", files={"file": ("test.pdf", f, "application/pdf")})
    job_id = resp.json()["job_id"]

    for _ in range(20):
        status_resp = await client.get(f"/api/status/{job_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        if data["status"] in ("completed", "failed"):
            break
        await asyncio.sleep(0.5)

    assert data["status"] == "completed"
    assert "download_token" not in data
    assert data["row_count"] >= 2
