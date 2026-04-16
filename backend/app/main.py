import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.converter import convert_pdf, is_valid_pdf
from app.db import create_job, get_job, get_job_by_token, init_db, update_job_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with init_db(config.DB_PATH) as conn:
        app.state.db = conn
        yield


class EmailRequest(BaseModel):
    job_id: str
    email: str


def create_app() -> FastAPI:
    app = FastAPI(title="PDF to CSV Converter", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.post("/api/upload", status_code=202)
    async def upload(file: UploadFile = File(...), text_fallback: bool = False):
        content = await file.read()
        if len(content) > config.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=400, detail=f"File exceeds {config.MAX_UPLOAD_SIZE_MB}MB limit.")

        safe_name = uuid.uuid4().hex + ".pdf"
        upload_path = config.UPLOAD_DIR / safe_name
        upload_path.write_bytes(content)

        if not is_valid_pdf(upload_path):
            upload_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid file. Please upload a PDF.")

        original_name = file.filename or "upload.pdf"
        job_id = await create_job(app.state.db, filename=original_name, upload_path=str(upload_path))

        output_path = config.OUTPUT_DIR / f"{job_id}.csv"
        asyncio.create_task(_run_conversion(app.state.db, job_id, upload_path, output_path, text_fallback))

        return {"job_id": job_id, "status": "processing"}

    @app.get("/api/status/{job_id}")
    async def status(job_id: str):
        job = await get_job(app.state.db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")

        result = {
            "job_id": job["job_id"],
            "status": job["status"],
            "filename": job["filename"],
            "total_pages": job["total_pages"],
            "pages_processed": job["pages_processed"],
        }
        if job["status"] == "completed":
            result["download_token"] = job["download_token"]
            result["row_count"] = job["row_count"]
        if job["status"] == "failed":
            result["error"] = job["error"]
        return result

    @app.get("/api/download/{token}")
    async def download(token: str):
        from fastapi.responses import FileResponse
        from datetime import datetime, timedelta, timezone

        job = await get_job_by_token(app.state.db, token)
        if not job:
            raise HTTPException(status_code=404, detail="Download not found.")

        created_str = job["created_at"]
        created_at = datetime.fromisoformat(created_str).replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - created_at > timedelta(hours=config.FILE_EXPIRY_HOURS):
            raise HTTPException(status_code=410, detail="This link has expired. Upload again to convert.")

        output_path = Path(job["output_path"])
        if not output_path.exists():
            raise HTTPException(status_code=410, detail="File no longer available.")

        download_name = Path(job["filename"]).stem + ".csv"
        return FileResponse(
            path=str(output_path),
            filename=download_name,
            media_type="text/csv",
        )

    @app.post("/api/email")
    async def send_email(req: EmailRequest):
        from app.email_service import send_download_email

        job = await get_job(app.state.db, req.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job is not completed yet.")

        download_url = f"{config.DOWNLOAD_BASE_URL}/api/download/{job['download_token']}"
        success = await send_download_email(
            provider_name=config.EMAIL_PROVIDER,
            api_key=config.EMAIL_API_KEY,
            from_email=config.EMAIL_FROM,
            to_email=req.email,
            download_url=download_url,
            filename=job["filename"],
        )
        if not success:
            raise HTTPException(status_code=502, detail="Failed to send email.")
        return {"sent": True}

    return app


async def _run_conversion(
    db: aiosqlite.Connection,
    job_id: str,
    pdf_path: Path,
    output_path: Path,
    text_fallback: bool = False,
) -> None:
    try:
        result = await asyncio.to_thread(convert_pdf, pdf_path, output_path, text_fallback)
        token = uuid.uuid4().hex
        await update_job_status(
            db, job_id,
            status=result["status"],
            output_path=str(output_path) if result["status"] == "completed" else None,
            download_token=token if result["status"] == "completed" else None,
            total_pages=result.get("total_pages"),
            row_count=result.get("row_count"),
            error=result.get("error"),
        )
    except Exception as e:
        await update_job_status(db, job_id, status="failed", error=str(e))


app = create_app()
