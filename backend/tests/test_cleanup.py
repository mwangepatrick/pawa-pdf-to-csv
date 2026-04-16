import pytest
import pytest_asyncio
from pathlib import Path

from app.db import init_db, create_job, update_job_status, get_job
from app.cleanup import run_cleanup


@pytest.mark.asyncio
async def test_cleanup_deletes_expired_files(tmp_data_dir):
    db_path = tmp_data_dir / "db.sqlite3"
    uploads = tmp_data_dir / "uploads"
    outputs = tmp_data_dir / "outputs"

    async with init_db(db_path) as conn:
        job_id = await create_job(conn, filename="old.pdf", upload_path=str(uploads / "old.pdf"))
        await update_job_status(
            conn, job_id, status="completed",
            output_path=str(outputs / "old.csv"),
            download_token="tok-old", total_pages=1, row_count=5,
        )
        await conn.execute(
            "UPDATE jobs SET created_at = datetime('now', '-25 hours') WHERE job_id = ?",
            (job_id,),
        )
        await conn.commit()

        (uploads / "old.pdf").write_bytes(b"fake pdf")
        (outputs / "old.csv").write_text("a,b\n1,2")

        fresh_id = await create_job(conn, filename="new.pdf", upload_path=str(uploads / "new.pdf"))
        (uploads / "new.pdf").write_bytes(b"new pdf")

        deleted_count = await run_cleanup(conn, expiry_hours=24)

        assert deleted_count == 1
        assert not (uploads / "old.pdf").exists()
        assert not (outputs / "old.csv").exists()
        assert (uploads / "new.pdf").exists()
        assert await get_job(conn, job_id) is None
        assert await get_job(conn, fresh_id) is not None


@pytest.mark.asyncio
async def test_cleanup_handles_missing_files(tmp_data_dir):
    db_path = tmp_data_dir / "db.sqlite3"

    async with init_db(db_path) as conn:
        job_id = await create_job(conn, filename="gone.pdf", upload_path="/nonexistent/gone.pdf")
        await conn.execute(
            "UPDATE jobs SET created_at = datetime('now', '-25 hours') WHERE job_id = ?",
            (job_id,),
        )
        await conn.commit()

        deleted_count = await run_cleanup(conn, expiry_hours=24)
        assert deleted_count == 1
        assert await get_job(conn, job_id) is None
