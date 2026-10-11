import re
from datetime import datetime, timezone
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup

from crawlers.common import fetch_text, session

SOURCE = "artnuri"
LIST_URL = "https://www.artnuri.or.kr/crawler/info/search.do?key=2301170002"
DETAIL_URL = "https://www.artnuri.or.kr/crawler/info/view.do"


def clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_dates(value: str) -> list[str]:
    matches = re.findall(r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})(?:일)?(?:\s*(\d{1,2}):(\d{2}))?", value)
    return [f"{year}-{int(month):02d}-{int(day):02d}T{int(hour or 23):02d}:{minute or '59'}:00+09:00" for year, month, day, hour, minute in matches]


def parse_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    seen, rows = set(), []
    for anchor in soup.select("a.title[onclick*='goView(']"):
        match = re.search(r"goView\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*,\s*['\"]([^'\"]+)['\"]", anchor.get("onclick", ""))
        if not match or match.group(1) in seen:
            continue
        external_id, organization, se_no = match.groups()
        seen.add(external_id)
        query = urlencode({"docid": external_id, "source": organization, "seNo": se_no, "key": "2301170002"})
        rows.append({"external_id": external_id, "title": clean(anchor.get_text(" ")), "organization": clean(organization), "source_url": f"{DETAIL_URL}?{query}"})
    return rows


def _list_value(soup: BeautifulSoup, label: str):
    for item in soup.select(".info-txt > li"):
        heading = item.select_one("strong")
        if heading and clean(heading.get_text(" ")).startswith(label):
            return item
    return None


def parse_detail(html: str, item: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.select_one(".info-tit .ti")
    period_node = _list_value(soup, "신청기간")
    period = clean(period_node.get_text(" ")) if period_node else ""
    dates = parse_dates(period)
    genre_node = _list_value(soup, "분야")
    genres_raw = [clean(node.get_text(" ")) for node in genre_node.select("li")] if genre_node else []
    genre_map = {"무용": "dance", "음악": "music", "연극": "theatre_musical", "뮤지컬": "theatre_musical", "전통": "traditional", "시각": "visual", "다원": "interdisciplinary"}
    genres = {mapped for value in genres_raw for token, mapped in genre_map.items() if token in value} or {"all"}
    target_node = _list_value(soup, "지원대상")
    region_node = _list_value(soup, "지역")
    site_link = soup.select_one(".info-txt .site-link[href]")
    application_url = urljoin(item["source_url"], site_link.get("href")) if site_link else None
    description_node = soup.select_one(".supt-content:not(.file-wrap)")
    image = soup.select_one(".supt-content img[src]")
    return {
        "source": SOURCE,
        "external_id": item["external_id"],
        "title": clean(title_el.get_text(" ")) if title_el else item["title"],
        "organization": item["organization"],
        "source_url": item["source_url"],
        "original_publisher_url": application_url,
        "application_url": application_url,
        "opportunity_type": "grant",
        "target_audience": [clean(node.get_text(" ")) for node in target_node.select("li")] if target_node else [],
        "art_genres": sorted(genres),
        "region": clean(region_node.select_one("li").get_text(" ")) if region_node and region_node.select_one("li") else None,
        "summary": None,
        "description": clean(description_node.get_text(" ")) if description_node else None,
        "application_method": None,
        "contact": clean(soup.select_one(".supt-inqu .list2").get_text(" ")) if soup.select_one(".supt-inqu .list2") else None,
        "thumbnail_url": urljoin(item["source_url"], image.get("src")) if image else None,
        "published_at": None,
        "application_start_at": dates[0] if dates else None,
        "deadline": dates[-1] if dates else None,
        "raw_data": {"parser_version": 1, "scraped_at": datetime.now(timezone.utc).isoformat(), "period_text": period, "genres_raw": genres_raw},
    }


def fetch_opportunities(max_pages=1, max_items=20, delay=0.8) -> list[dict]:
    client = session()
    discovered = {}
    for page in range(1, max_pages + 1):
        url = f"{LIST_URL}&pageIndex={page}"
        page_rows = parse_list(fetch_text(client, url, delay=delay if page > 1 else 0))
        before = len(discovered)
        for row in page_rows:
            discovered[row["external_id"]] = row
        if not page_rows or len(discovered) == before or len(discovered) >= max_items:
            break
    results = []
    for index, item in enumerate(list(discovered.values())[:max_items]):
        results.append(parse_detail(fetch_text(client, item["source_url"], delay=delay if index else 0), item))
    return results

