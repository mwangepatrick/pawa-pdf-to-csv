# PDF-to-CSV Web UI — Design Spec

## Overview

Add a public-facing web UI to the existing `pawa-pdf-to-csv` CLI tool. Users upload a PDF, the system extracts tables and converts them to CSV, and users can download the result immediately or receive a download link via email. Files expire after 24 hours.

## User Flow

1. **Landing** — User arrives at a clean page with a drag-and-drop upload zone.
2. **Upload** — User selects or drops a PDF. Client-side validation (file type, max 20MB). File is uploaded to the server.
3. **Processing** — Progress indicator shows conversion status (e.g., "Extracting tables from page 2/5..."). Frontend polls the status endpoint.
4. **Result** — Success screen displays:
   - Download CSV button (immediate)
   - Summary: row count, page count, original filename
   - Email input field to send the download link
5. **Email (optional)** — User enters their email address. System sends a transactional email with the download link. "Link expires in 24 hours" displayed clearly.

### Error States

- **Invalid file** — Not a PDF or exceeds 20MB size limit. Immediate rejection with clear message before upload.
- **No tables found** — PDF has no extractable tables. Offer text-fallback extraction option (raw text lines as single-column CSV, already supported in the CLI).
- **Processing failure** — Corrupt PDF or extraction error. Display "Something went wrong, try another file."
- **Expired link** — Download link accessed after 24 hours. Display "This link has expired. Upload again to convert."

## Architecture

### System Components

```
Browser (React SPA)  →  Nginx (reverse proxy)  →  FastAPI (API server)
                                                      ↓
                                          ┌───────────┼───────────┐
                                        SQLite    Local Disk    Brevo/Mailjet
                                       (metadata)  (files)       (email)
```

- **React SPA** — Vite + React + TypeScript. Upload UI, progress display, result screen, email form.
- **Nginx** — Serves the React static build, proxies `/api/*` requests to FastAPI, enforces rate limiting.
- **FastAPI** — Handles file uploads, runs PDF-to-CSV conversion, serves downloads, triggers email sends. Runs on Uvicorn.
- **SQLite** — Stores upload records, download tokens, expiry timestamps, and email send status.
- **Local Disk** — Uploaded PDFs stored in `data/uploads/`, generated CSVs in `data/outputs/`. Mounted as a Docker volume.
- **Brevo or Mailjet** — Transactional email API for sending download links. Configured via environment variable to select provider.
- **Cleanup Cron** — Hourly job that deletes files and DB records older than 24 hours.

### Project Structure

```
pdf-csv/
├── frontend/                  # React app (Vite + TypeScript)
│   ├── src/
│   │   ├── components/        # Upload, Progress, Result, EmailForm
│   │   ├── hooks/             # useUpload, useConversion
│   │   ├── api/               # API client functions
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── backend/                   # FastAPI app
│   ├── app/
│   │   ├── main.py            # FastAPI app + routes
│   │   ├── converter.py       # PDF→CSV logic (extracted from pdf_to_csv.py)
│   │   ├── models.py          # SQLite models (via aiosqlite)
│   │   ├── email.py           # Brevo/Mailjet integration
│   │   └── cleanup.py         # Expired file cleanup script
│   └── requirements.txt
├── nginx/
│   └── nginx.conf
├── data/                      # Mounted Docker volume
│   ├── uploads/               # Uploaded PDFs
│   ├── outputs/               # Generated CSVs
│   └── db.sqlite3
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── .env.example               # Template for secrets
└── pdf_to_csv.py              # Original CLI tool (kept as-is)
```

## API Design

### Endpoints

| Method | Endpoint              | Purpose                                              |
|--------|-----------------------|------------------------------------------------------|
| POST   | `/api/upload`         | Upload a PDF. Returns `{job_id}`.                    |
| GET    | `/api/status/{job_id}`| Poll conversion progress. Returns status + progress. |
| GET    | `/api/download/{token}`| Download the CSV file. 410 Gone if expired.         |
| POST   | `/api/email`          | Send download link email. Body: `{job_id, email}`.   |

### POST /api/upload

**Request:** `multipart/form-data` with a single `file` field.

**Validation:**
- File must be a PDF (validated by magic bytes, not just extension)
- Max file size: 20MB (enforced at both Nginx and FastAPI level)

**Response (202 Accepted):**
```json
{
  "job_id": "abc123",
  "status": "processing"
}
```

Conversion runs in a background thread (via `asyncio.to_thread` or `concurrent.futures.ThreadPoolExecutor`). No external task queue needed at this scale. The frontend polls `/api/status/{job_id}` every 1–2 seconds.

### GET /api/status/{job_id}

**Response (200):**
```json
{
  "job_id": "abc123",
  "status": "processing | completed | failed",
  "pages_processed": 2,
  "total_pages": 5,
  "download_token": "e4f7a9...",   // only present when status=completed
  "row_count": 142,                // only present when status=completed
  "filename": "invoice.pdf",
  "error": "No tables found"       // only present when status=failed
}
```

### GET /api/download/{token}

- Returns the CSV file with `Content-Disposition: attachment` header.
- Returns **410 Gone** if the token has expired (24 hours).
- Returns **404 Not Found** if the token doesn't exist.

### POST /api/email

**Request:**
```json
{
  "job_id": "abc123",
  "email": "user@example.com"
}
```

**Validation:**
- Basic email format validation
- Rate limited: max 3 emails per email address per hour

**Response (200):**
```json
{
  "sent": true
}
```

## Email

- **Provider:** Brevo or Mailjet, selected via `EMAIL_PROVIDER` environment variable.
- **Abstraction:** A common email service interface so providers can be swapped by changing config.
- **Email content:**
  - Subject: "Your CSV is ready to download"
  - Body: Download link, original PDF filename, expiry notice ("This link expires in 24 hours")
- **Configuration:** API keys stored in `.env`, loaded as environment variables in Docker.

## Cleanup

- A Python script (`cleanup.py`) runs hourly via cron inside the Docker container.
- Deletes files from `data/uploads/` and `data/outputs/` where the associated DB record is older than 24 hours.
- Deletes the corresponding DB records (marks as expired/removes).
- Uses the same DB connection logic as the main app.

## Security

Since this is public-facing:

- **File validation:** PDF magic bytes check, not just file extension.
- **Upload size limit:** Enforced at Nginx (client_max_body_size) and FastAPI level.
- **Download tokens:** Cryptographically random UUIDs — unguessable, not sequential.
- **Rate limiting:** Nginx rate-limits uploads per IP (10/hour). Email endpoint rate-limited per email address (3/hour).
- **No user accounts:** Stateless from the user's perspective. No auth needed.
- **CORS:** Restricted to the frontend origin in production.
- **Input sanitization:** Filenames sanitized before storage. No user input used in shell commands or SQL without parameterization.

## Deployment

### Docker Compose Services

| Service   | Image                          | Purpose                                 |
|-----------|--------------------------------|-----------------------------------------|
| `nginx`   | Nginx + built React static files | Reverse proxy, serve frontend, rate limit |
| `api`     | FastAPI + Uvicorn              | Backend API server                      |
| `cleanup` | Same backend image             | Runs cleanup.py on hourly cron schedule |

### Environment Variables (.env)

```
EMAIL_PROVIDER=brevo          # or "mailjet"
EMAIL_API_KEY=...
EMAIL_FROM=noreply@yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com
MAX_UPLOAD_SIZE_MB=20
FILE_EXPIRY_HOURS=24
```

### Volumes

- `data/` mounted as a shared volume between `api` and `cleanup` services.

## Tech Stack Summary

| Layer     | Technology                  |
|-----------|-----------------------------|
| Frontend  | React + TypeScript + Vite   |
| Backend   | Python + FastAPI + Uvicorn  |
| Database  | SQLite                      |
| Email     | Brevo or Mailjet API        |
| Proxy     | Nginx                       |
| Deploy    | Docker Compose              |
| PDF parse | pdfplumber + pandas (existing) |
