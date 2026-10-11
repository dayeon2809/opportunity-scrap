from datetime import datetime, timezone

from core.config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_TABLE, SUPABASE_URL

MUTABLE_COLUMNS = (
    "source_url", "canonical_source_url", "original_publisher_url", "title", "normalized_title",
    "organization", "normalized_organization", "opportunity_type", "target_audience", "art_genres",
    "region", "summary", "description", "application_method", "application_url", "contact",
    "thumbnail_url", "published_at", "application_start_at", "deadline", "last_scraped_at", "raw_data",
)


def _payload(row: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        **{key: row.get(key) for key in MUTABLE_COLUMNS},
        "source": row["source"],
        "external_id": row["external_id"],
        "ingestion_type": "scraped",
        "publication_status": "draft",
        "review_status": "needs_review",
        "is_verified": False,
        "is_featured": False,
        "last_scraped_at": now,
    }


def sync_rows(rows: list[dict], dry_run=True) -> dict:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return {"configured": False, "dry_run": dry_run, "new": len(rows), "updated": 0, "unchanged": 0}
    from supabase import create_client

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    response = client.table(SUPABASE_TABLE).select("*").execute()
    existing = {(row.get("source"), row.get("external_id")): row for row in response.data or []}
    new_rows, updates, unchanged = [], [], 0
    for row in rows:
        payload = _payload(row)
        current = existing.get((row["source"], row["external_id"]))
        if current is None:
            new_rows.append(payload)
            continue
        changed = {key: payload[key] for key in MUTABLE_COLUMNS if payload.get(key) != current.get(key)}
        if changed:
            changed["last_scraped_at"] = payload["last_scraped_at"]
            updates.append((row["source"], row["external_id"], changed))
        else:
            unchanged += 1
    if not dry_run:
        if new_rows:
            client.table(SUPABASE_TABLE).insert(new_rows).execute()
        for source, external_id, changes in updates:
            client.table(SUPABASE_TABLE).update(changes).eq("source", source).eq("external_id", external_id).execute()
    return {"configured": True, "dry_run": dry_run, "new": len(new_rows), "updated": len(updates), "unchanged": unchanged}
