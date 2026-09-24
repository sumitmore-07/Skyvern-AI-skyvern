"""Loads .env before Skyvern is imported (Skyvern reads its settings at import time)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
# Skyvern blocks localhost by default (SSRF guard). Allow only it, so the local demo shops work.
os.environ.setdefault("ALLOWED_HOSTS", '["localhost"]')

PRODUCTS_FILE = ROOT / "data" / "products.yaml"
SITES_FILE = ROOT / "data" / "sites.yaml"
OUTPUT_DIR = ROOT / "output"
DEMO_SHOPS_DIR = ROOT / "demo_shops"

RUN_TIMEOUT_SECONDS = float(os.environ.get("RUN_TIMEOUT_SECONDS", "300"))
MAX_STEPS = int(os.environ.get("MAX_STEPS_PER_RUN", "10"))


def require_env(*names: str) -> None:
    """Fail early with a clear message if required variables are missing."""
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise RuntimeError(f"Missing required .env variables: {', '.join(missing)}")
