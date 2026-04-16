import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
from app.db import init_db, create_job, get_job, update_job_status, get_job_by_token, get_expired_jobs, delete_job


@pytest_asyncio.fixture
async def db(tmp_data_dir):
    db_path = tmp_data_dir / "db.sqlite3"
    async with init_db(db_path) as conn:
        yield conn


@pytest.mark.asyncio
async def test_create_and_get_job(db):
    job_id = await create_job(db, filename="test.pdf", upload_path="/uploads/test.pdf")
    job = await get_job(db, job_id)
    assert job is not None
    assert job["filename"] == "test.pdf"
    assert job["status"] == "processing"
    assert job["upload_path"] == "/uploads/test.pdf"


@pytest.mark.asyncio
async def test_update_job_completed(db):
    job_id = await create_job(db, filename="test.pdf", upload_path="/uploads/test.pdf")
    await update_job_status(
        db, job_id,
        status="completed",
        output_path="/outputs/test.csv",
        download_token="abc-123",
        total_pages=5,
        row_count=142,
    )
    job = await get_job(db, job_id)
    assert job["status"] == "completed"
    assert job["download_token"] == "abc-123"
    assert job["total_pages"] == 5
    assert job["row_count"] == 142


@pytest.mark.asyncio
async def test_update_job_failed(db):
    job_id = await create_job(db, filename="test.pdf", upload_path="/uploads/test.pdf")
    await update_job_status(db, job_id, status="failed", error="No tables found")
    job = await get_job(db, job_id)
    assert job["status"] == "failed"
    assert job["error"] == "No tables found"


@pytest.mark.asyncio
async def test_get_job_by_token(db):
    job_id = await create_job(db, filename="test.pdf", upload_path="/uploads/test.pdf")
    await update_job_status(
        db, job_id, status="completed",
        output_path="/outputs/test.csv", download_token="tok-999",
        total_pages=1, row_count=10,
    )
    job = await get_job_by_token(db, "tok-999")
    assert job is not None
    assert job["job_id"] == job_id


@pytest.mark.asyncio
async def test_get_job_by_token_not_found(db):
    job = await get_job_by_token(db, "nonexistent")
    assert job is None


@pytest.mark.asyncio
async def test_get_expired_jobs(db):
    job_id = await create_job(db, filename="old.pdf", upload_path="/uploads/old.pdf")
    await db.execute(
        "UPDATE jobs SET created_at = datetime('now', '-25 hours') WHERE job_id = ?",
        (job_id,),
    )
    await db.commit()
    expired = await get_expired_jobs(db, expiry_hours=24)
    assert len(expired) == 1
    assert expired[0]["job_id"] == job_id


@pytest.mark.asyncio
async def test_delete_job(db):
    job_id = await create_job(db, filename="test.pdf", upload_path="/uploads/test.pdf")
    await delete_job(db, job_id)
    job = await get_job(db, job_id)
    assert job is None
