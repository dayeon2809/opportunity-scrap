from datetime import datetime
from urllib.parse import urlsplit

ALLOWED_GENRES = {"dance", "music", "theatre_musical", "traditional", "visual", "interdisciplinary", "culture_planning", "all"}


def _valid_url(value) -> bool:
    parsed = urlsplit(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def _valid_date(value) -> bool:
    if not value:
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_opportunity(row: dict) -> list[str]:
    reasons = []
    for key in ("source", "external_id", "title", "organization"):
        if not str(row.get(key) or "").strip():
            reasons.append(f"missing:{key}")
    if row.get("organization") == "기관 미상":
        reasons.append("invalid:organization")
    if not _valid_url(row.get("source_url")):
        reasons.append("invalid:source_url")
    if not _valid_url(row.get("application_url") or row.get("original_publisher_url")):
        reasons.append("invalid:application_url")
    for key in ("application_start_at", "deadline"):
        if not _valid_date(row.get(key)):
            reasons.append(f"invalid:{key}")
    if _valid_date(row.get("application_start_at")) and _valid_date(row.get("deadline")):
        start = datetime.fromisoformat(row["application_start_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(row["deadline"].replace("Z", "+00:00"))
        if end < start:
            reasons.append("invalid:date_range")
    if any(genre not in ALLOWED_GENRES for genre in row.get("art_genres", [])):
        reasons.append("invalid:art_genres")
    return sorted(set(reasons))

