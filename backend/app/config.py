import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True), override=False)

BASE_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent.parent / "data"))
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
DB_PATH = BASE_DIR / "db.sqlite3"

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
FILE_EXPIRY_HOURS = int(os.getenv("FILE_EXPIRY_HOURS", "24"))

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "brevo")
EMAIL_API_KEY = os.getenv("EMAIL_API_KEY", "")
EMAIL_SECRET_KEY = os.getenv("EMAIL_SECRET_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@example.com")
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY", "")
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "")
TURNSTILE_VERIFY_URL = os.getenv(
    "TURNSTILE_VERIFY_URL",
    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
)
EMAIL_SEND_COOLDOWN_SECONDS = int(os.getenv("EMAIL_SEND_COOLDOWN_SECONDS", "60"))
EMAIL_SEND_MAX_ATTEMPTS = int(os.getenv("EMAIL_SEND_MAX_ATTEMPTS", "5"))

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

DOWNLOAD_BASE_URL = os.getenv("DOWNLOAD_BASE_URL", "http://localhost:8000")
