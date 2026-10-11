import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}
TITLE_PREFIX = re.compile(r"^\s*(?:\[\s*(?:공고|모집|채용|지원사업|오디션)\s*\]|(?:공고|모집)\s*[:：-])\s*", re.I)


def clean_text(value) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_title(value) -> str:
    text = TITLE_PREFIX.sub("", clean_text(value))
    text = re.sub(r"^(?:19|20)\d{2}(?:년(?:도)?)?\s*", "", text)
    return re.sub(r"[^\w가-힣]", "", text, flags=re.UNICODE).lower()


def normalize_organization(value) -> str:
    text = re.sub(r"^(?:재단법인|사단법인|주식회사|\(재\)|\(사\)|\(주\))\s*", "", clean_text(value))
    return re.sub(r"[^\w가-힣]", "", text, flags=re.UNICODE).lower()


def canonicalize_url(value, base=None) -> str:
    absolute = urljoin(base or "", clean_text(value))
    parsed = urlsplit(absolute)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return ""
    host = parsed.hostname.lower().removeprefix("www.")
    if parsed.port:
        host = f"{host}:{parsed.port}"
    query = [(key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True) if key.lower() not in TRACKING_PARAMS]
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), host, path, urlencode(sorted(query)), ""))


def normalize_opportunity(row: dict) -> dict:
    result = dict(row)
    result["source"] = clean_text(result.get("source"))
    result["external_id"] = clean_text(result.get("external_id"))
    result["title"] = clean_text(result.get("title"))
    result["normalized_title"] = normalize_title(result["title"])
    result["organization"] = clean_text(result.get("organization"))
    result["normalized_organization"] = normalize_organization(result["organization"])
    result["source_url"] = canonicalize_url(result.get("source_url"))
    result["canonical_source_url"] = result["source_url"]
    original_url = clean_text(result.get("original_publisher_url"))
    application_url = clean_text(result.get("application_url"))
    result["original_publisher_url"] = canonicalize_url(original_url, result["source_url"]) if original_url else None
    result["application_url"] = canonicalize_url(application_url, result["source_url"]) if application_url else None
    result["target_audience"] = sorted({clean_text(item) for item in result.get("target_audience", []) if clean_text(item)})
    result["art_genres"] = sorted(set(result.get("art_genres") or ["all"]))
    for key in ("region", "summary", "description", "application_method", "contact", "thumbnail_url", "published_at", "application_start_at", "deadline"):
        result[key] = clean_text(result.get(key)) or None
    result.setdefault("opportunity_type", "other")
    result.setdefault("raw_data", {})
    return result
