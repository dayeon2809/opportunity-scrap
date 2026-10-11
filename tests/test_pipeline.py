import unittest

from core.dedupe import dedupe_run, probable_duplicate
from core.normalize import canonicalize_url, normalize_opportunity, normalize_title
from core.validate import validate_opportunity
from crawlers.artnuri import parse_dates


class PipelineTests(unittest.TestCase):
    def test_title_and_url_normalization(self):
        self.assertEqual(normalize_title("[공고] 2026년도 무용 지원 사업"), "무용지원사업")
        self.assertEqual(canonicalize_url("https://www.EXAMPLE.com/a/?utm_source=x&b=2"), "https://example.com/a?b=2")

    def test_artnuri_dates(self):
        self.assertEqual(parse_dates("2026. 8. 1 ~ 2026. 8. 31 18:00"), ["2026-08-01T23:59:00+09:00", "2026-08-31T18:00:00+09:00"])

    def test_run_dedupe_and_cross_source_candidate(self):
        base = normalize_opportunity({"source": "artnuri", "external_id": "1", "title": "청년예술 지원사업", "organization": "한국문화재단", "source_url": "https://example.com/1", "application_url": "https://apply.example.com/1", "application_start_at": "2026-08-01T00:00:00+09:00", "deadline": "2026-08-31T23:59:00+09:00", "art_genres": ["dance"]})
        other = normalize_opportunity({**base, "source": "manual", "external_id": "2", "source_url": "https://other.example.com/2", "canonical_source_url": ""})
        self.assertEqual(len(dedupe_run([base, base])), 1)
        self.assertTrue(probable_duplicate(base, other))

    def test_validation_holds_missing_application_url(self):
        row = normalize_opportunity({"source": "artnuri", "external_id": "1", "title": "지원", "organization": "기관", "source_url": "https://example.com/1", "application_start_at": "2026-08-01T00:00:00+09:00", "deadline": "2026-08-31T23:59:00+09:00"})
        self.assertIn("invalid:application_url", validate_opportunity(row))


if __name__ == "__main__":
    unittest.main()

