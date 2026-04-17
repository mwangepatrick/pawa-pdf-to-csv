# pawa-pdf-to-csv

Extract tables (or text) from PDF files and save them as CSV. Available as a CLI tool and a web UI.

For PDF files whose name contains `mpesa statement` after normalizing spaces, underscores, and hyphens, the converter automatically removes the M-PESA summary rows and drops the `_page`, `TRANSACTION TYPE`, `PAID IN`, `PAID OUT`, and verification-code columns.

## CLI Usage

```bash
pip install pdfplumber pandas

# Extract tables from a PDF
python pdf_to_csv.py invoice.pdf

# Specify output file
python pdf_to_csv.py invoice.pdf -o results.csv

# Fall back to text extraction if no tables found
python pdf_to_csv.py report.pdf --text-fallback
```

## Web UI

A browser-based interface where users upload a PDF, wait for Turnstile verification, and receive the finished CSV only by email. The UI does not expose a direct CSV download action.

### Run locally (development)

Start the backend and frontend in separate terminals:

```bash
# Terminal 1 — Backend API
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend dev server
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173**

The backend auto-loads a root-level `.env` file when it starts, so you can keep local email/API settings in `D:\cp\tools\pdf-csv\.env` and run `uvicorn` directly without exporting variables first.

For local Turnstile testing on **http://localhost:5173/**, keep your production site key in `TURNSTILE_SITE_KEY` and set `TURNSTILE_SITE_KEY_OVERRIDE` to Cloudflare's test key or a local-dev-allowed site key. The frontend uses the override in development and test mode, while production builds still require the real site key.

### Run with Docker (production)

```bash
# Copy and edit the env file with your email API key
cp .env.example .env

# Build and start all services
docker compose up -d
```

Visit **http://localhost**

Three services run: Nginx (serves frontend + proxies API), FastAPI (backend), and a cleanup cron (deletes expired files every hour).

The frontend build only needs the public Turnstile site key. Docker Compose forwards `TURNSTILE_SITE_KEY` into the frontend build as `VITE_TURNSTILE_SITE_KEY`; the backend secret stays in the API container and never goes into the frontend image.

### Run backend tests

```bash
cd backend
pip install -r requirements.txt
pip install reportlab    # needed for PDF generation in tests
python -m pytest -v
```

### Environment variables

See `.env.example` for all available settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `EMAIL_PROVIDER` | `brevo` | `brevo` or `mailjet` |
| `EMAIL_API_KEY` | — | API key for the email provider |
| `EMAIL_SECRET_KEY` | — | Mailjet secret key; leave blank for Brevo |
| `EMAIL_FROM` | `noreply@example.com` | Sender email address |
| `TURNSTILE_SITE_KEY` | — | Public Cloudflare Turnstile site key used by the browser |
| `TURNSTILE_SECRET_KEY` | — | Private Cloudflare Turnstile secret key used only by the backend |
| `TURNSTILE_VERIFY_URL` | `https://challenges.cloudflare.com/turnstile/v0/siteverify` | Turnstile verification endpoint |
| `EMAIL_SEND_COOLDOWN_SECONDS` | `60` | Minimum seconds between email sends for a job |
| `EMAIL_SEND_MAX_ATTEMPTS` | `5` | Maximum email send attempts allowed for a job |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS allowed origins (comma-separated) |
| `DOWNLOAD_BASE_URL` | `http://localhost:8000` | Base URL for download links in emails |
| `MAX_UPLOAD_SIZE_MB` | `20` | Max upload file size |
| `FILE_EXPIRY_HOURS` | `24` | Hours before files are cleaned up |

### Email provider notes

- Brevo uses `EMAIL_API_KEY` plus a verified sender in `EMAIL_FROM`.
- Mailjet uses `EMAIL_API_KEY` plus `EMAIL_SECRET_KEY` with HTTP Basic Auth.
- `TURNSTILE_SITE_KEY` is safe to expose to the frontend; `TURNSTILE_SECRET_KEY` must remain server-side only.
- For local dev/test, set `TURNSTILE_SITE_KEY_OVERRIDE` in `D:\cp\tools\pdf-csv\.env` so the widget works on `http://localhost:5173/` without changing the production key.
- If you build with Docker Compose, only the public site key is forwarded to the frontend build. `TURNSTILE_SECRET_KEY` stays in the backend service and is not baked into the frontend image.
- Email sending is Turnstile-protected, and the completed CSV is delivered only through email.
- Email sending should fail closed if Turnstile validation is unavailable or fails.
- If you switch providers, restart the backend so it picks up the new environment values.
