from difflib import SequenceMatcher


def dedupe_run(rows: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for row in rows:
        key = (row.get("source"), row.get("external_id"))
        if not all(key) or key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def probable_duplicate(left: dict, right: dict) -> bool:
    if left.get("source") == right.get("source") and left.get("external_id") == right.get("external_id"):
        return True
    if left.get("canonical_source_url") and left.get("canonical_source_url") == right.get("canonical_source_url"):
        return True
    if left.get("normalized_organization") != right.get("normalized_organization") or left.get("deadline") != right.get("deadline"):
        return False
    score = SequenceMatcher(None, left.get("normalized_title", ""), right.get("normalized_title", "")).ratio()
    return score >= 0.82

