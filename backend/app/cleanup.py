"""Cleanup expired jobs and their files. Run via cron or directly."""

import asyncio
import sys
from pathlib import Path

import aiosqlite

from app.db import delete_job, get_expired_jobs, init_db
from app import config


async def run_cleanup(conn: aiosqlite.Connection, expiry_hours: int = 24) -> int:
    expired = await get_expired_jobs(conn, expiry_hours)
    deleted = 0

    for job in expired:
        upload_path = Path(job["upload_path"])
        if upload_path.exists():
            upload_path.unlink()

        if job.get("output_path"):
            output_path = Path(job["output_path"])
            if output_path.exists():
                output_path.unlink()

        await delete_job(conn, job["job_id"])
        deleted += 1

    return deleted


async def main():
    async with init_db(config.DB_PATH) as conn:
        deleted = await run_cleanup(conn, config.FILE_EXPIRY_HOURS)
        print(f"Cleanup complete: {deleted} expired job(s) removed.")


if __name__ == "__main__":
    asyncio.run(main())
