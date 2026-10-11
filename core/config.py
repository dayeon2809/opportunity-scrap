import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "opportunities").strip()
CRAWLER_USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT",
    "POPOKOpportunityBot/0.1 (+contact: admin@popok.kr)",
).strip()

raw_sqlite_path = Path(os.getenv("SQLITE_PATH", "data/opportunities.sqlite"))
SQLITE_PATH = raw_sqlite_path if raw_sqlite_path.is_absolute() else PROJECT_ROOT / raw_sqlite_path

