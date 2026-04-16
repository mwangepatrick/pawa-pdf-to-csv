import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    upload_path TEXT NOT NULL,
    output_path TEXT,
    status TEXT NOT NULL DEFAULT 'processing',
    download_token TEXT,
    total_pages INTEGER,
    pages_processed INTEGER DEFAULT 0,
    row_count INTEGER,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_jobs_token ON jobs(download_token);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);
"""


@asynccontextmanager
async def init_db(db_path: Path):
    """Initialize DB, create tables, yield connection, then close."""
    conn = await aiosqlite.connect(str(db_path))
    conn.row_factory = aiosqlite.Row
    await conn.executescript(SCHEMA)
    await conn.commit()
    try:
        yield conn
    finally:
        await conn.close()


async def create_job(conn: aiosqlite.Connection, filename: str, upload_path: str) -> str:
    job_id = uuid.uuid4().hex[:12]
    await conn.execute(
        "INSERT INTO jobs (job_id, filename, upload_path) VALUES (?, ?, ?)",
        (job_id, filename, upload_path),
    )
    await conn.commit()
    return job_id


async def get_job(conn: aiosqlite.Connection, job_id: str) -> dict | None:
    cursor = await conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_job_status(
    conn: aiosqlite.Connection,
    job_id: str,
    status: str,
    output_path: str | None = None,
    download_token: str | None = None,
    total_pages: int | None = None,
    pages_processed: int | None = None,
    row_count: int | None = None,
    error: str | None = None,
) -> None:
    fields = ["status = ?"]
    values = [status]
    for col, val in [
        ("output_path", output_path),
        ("download_token", download_token),
        ("total_pages", total_pages),
        ("pages_processed", pages_processed),
        ("row_count", row_count),
        ("error", error),
    ]:
        if val is not None:
            fields.append(f"{col} = ?")
            values.append(val)
    values.append(job_id)
    await conn.execute(
        f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?",
        values,
    )
    await conn.commit()


async def get_job_by_token(conn: aiosqlite.Connection, token: str) -> dict | None:
    cursor = await conn.execute("SELECT * FROM jobs WHERE download_token = ?", (token,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_expired_jobs(conn: aiosqlite.Connection, expiry_hours: int = 24) -> list[dict]:
    cursor = await conn.execute(
        "SELECT * FROM jobs WHERE created_at < datetime('now', ? || ' hours')",
        (f"-{expiry_hours}",),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def delete_job(conn: aiosqlite.Connection, job_id: str) -> None:
    await conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
    await conn.commit()
