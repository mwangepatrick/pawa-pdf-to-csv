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

A browser-based interface where users upload a PDF, get a CSV download, and can optionally email the download link.

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

### Run with Docker (production)

```bash
# Copy and edit the env file with your email API key
cp .env.example .env

# Build and start all services
docker compose up -d
```

Visit **http://localhost**

Three services run: Nginx (serves frontend + proxies API), FastAPI (backend), and a cleanup cron (deletes expired files every hour).

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
| `EMAIL_FROM` | `noreply@example.com` | Sender email address |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS allowed origins (comma-separated) |
| `DOWNLOAD_BASE_URL` | `http://localhost:8000` | Base URL for download links in emails |
| `MAX_UPLOAD_SIZE_MB` | `20` | Max upload file size |
| `FILE_EXPIRY_HOURS` | `24` | Hours before files are cleaned up |
