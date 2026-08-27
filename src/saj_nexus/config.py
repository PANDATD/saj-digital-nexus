from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = PROJECT_ROOT / "public"
load_dotenv(PROJECT_ROOT / ".env", override=False)


class Config:
    SITE_URL = os.getenv("SITE_URL", "").rstrip("/")
    CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "").strip()
    CONTACT_WEBHOOK_URL = os.getenv("CONTACT_WEBHOOK_URL", "").strip()
    BRAND_PHONE = os.getenv("BRAND_PHONE", "").strip()
    BRAND_LOCATION = os.getenv("BRAND_LOCATION", "").strip()
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-only-change-before-production"
    MAX_CONTENT_LENGTH = 32 * 1024
    TEMPLATES_AUTO_RELOAD = False
    SEND_FILE_MAX_AGE_DEFAULT = 31536000
    PUBLIC_DIR = PUBLIC_DIR
