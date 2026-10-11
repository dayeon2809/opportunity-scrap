import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.dedupe import dedupe_run
from core.normalize import normalize_opportunity
from core.sqlite_store import save_rows
from core.supabase_sync import sync_rows
from core.validate import validate_opportunity

SOURCES = ("artnuri", "artmore")


def run_source(source: str, args) -> dict:
    module = importlib.import_module(f"crawlers.{source}")
    raw_rows = module.fetch_opportunities(max_pages=args.max_pages, max_items=args.limit, delay=args.delay)
    normalized, raw_by_key, errors_by_key = [], {}, {}
    for raw in raw_rows:
        row = normalize_opportunity(raw)
        key = (row["source"], row["external_id"])
        raw_by_key[key] = raw
        errors_by_key[key] = validate_opportunity(row)
        normalized.append(row)
    normalized = dedupe_run(normalized)
    save_rows(normalized, raw_by_key, errors_by_key)
    valid = [row for row in normalized if not errors_by_key[(row["source"], row["external_id"])]]
    sync = sync_rows(valid, dry_run=not args.apply)
    return {
        "source": source,
        "fetched": len(raw_rows),
        "normalized": len(normalized),
        "valid": len(valid),
        "held_for_review": len(normalized) - len(valid),
        "validation_errors": [
            {"external_id": row["external_id"], "reasons": errors_by_key[(row["source"], row["external_id"])]}
            for row in normalized if errors_by_key[(row["source"], row["external_id"])]
        ],
        "supabase": sync,
    }


def main():
    parser = argparse.ArgumentParser(description="Crawl opportunity sources and safely synchronize reviewed drafts.")
    parser.add_argument("--source", choices=(*SOURCES, "all"), default="all")
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--delay", type=float, default=0.8)
    parser.add_argument("--apply", action="store_true", help="Write valid rows to Supabase as draft/needs_review.")
    args = parser.parse_args()
    if not 1 <= args.max_pages <= 20 or not 1 <= args.limit <= 200 or args.delay < 0.2:
        parser.error("Safety limits: max-pages 1..20, limit 1..200, delay >= 0.2")
    sources = SOURCES if args.source == "all" else (args.source,)
    reports = []
    for source in sources:
        try:
            reports.append(run_source(source, args))
        except Exception as error:
            reports.append({"source": source, "error": f"{type(error).__name__}: {error}"})
    print(json.dumps({"mode": "apply" if args.apply else "dry-run", "reports": reports}, ensure_ascii=False, indent=2))
    if any("error" in report for report in reports):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

