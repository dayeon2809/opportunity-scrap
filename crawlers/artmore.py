import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup

from crawlers.common import fetch_text, session
from crawlers.artnuri import clean, parse_dates

SOURCE = "artmore"
LIST_URL = "https://artmore.kr/sub/recruit/search_list.do"


def parse_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = {}
    for anchor in soup.select("a[href*='/sub/recruit/'][href*='rec_idx=']"):
        url = urljoin(LIST_URL, anchor.get("href", ""))
        external_id = (parse_qs(urlsplit(url).query).get("rec_idx") or [""])[0]
        title = clean(anchor.get_text(" "))
        if external_id and title:
            rows[external_id] = {"external_id": external_id, "title": title, "source_url": url}
    return list(rows.values())


def _label(soup: BeautifulSoup, names: tuple[str, ...]):
    for node in soup.select("dt, th, strong, b, span"):
        key = clean(node.get_text(" "))
        if any(key == name or key.startswith(name) for name in names):
            sibling = node.find_next_sibling(["dd", "td", "span", "div", "p"])
            if sibling:
                return clean(sibling.get_text(" "))
    return None


def parse_detail(html: str, item: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    body = clean(soup.get_text(" "))
    dates = parse_dates(body)
    title_node = soup.select_one("h1,h2,h3,.title,th.subject")
    organization = _label(soup, ("주관기관", "기관명", "회사명")) or "기관 미상"
    application = None
    for anchor in soup.select("a[href]"):
        if re.search(r"신청사이트|온라인신청|홈페이지|지원하기", clean(anchor.get_text(" "))):
            application = urljoin(item["source_url"], anchor.get("href"))
            break
    description_node = soup.select_one(".view_cont,.board_view,.job_view,.content,#contents")
    image = soup.select_one(".view_cont img,.job_view img")
    return {
        "source": SOURCE, "external_id": item["external_id"],
        "title": clean(title_node.get_text(" ")) if title_node else item["title"],
        "organization": organization, "source_url": item["source_url"],
        "original_publisher_url": application, "application_url": application,
        "opportunity_type": "job", "target_audience": [], "art_genres": ["all"],
        "region": _label(soup, ("지역",)), "summary": None,
        "description": clean(description_node.get_text(" ")) if description_node else None,
        "application_method": None, "contact": _label(soup, ("문의", "연락처")),
        "thumbnail_url": urljoin(item["source_url"], image.get("src")) if image and image.get("src") else None,
        "published_at": None, "application_start_at": dates[0] if dates else None,
        "deadline": dates[-1] if dates else None,
        "raw_data": {"parser_version": 1, "scraped_at": datetime.now(timezone.utc).isoformat()},
    }


def fetch_opportunities(max_pages=1, max_items=20, delay=0.8) -> list[dict]:
    client = session()
    discovered = {}
    for page in range(1, max_pages + 1):
        separator = "&" if "?" in LIST_URL else "?"
        rows = parse_list(fetch_text(client, f"{LIST_URL}{separator}pageIndex={page}", delay=delay if page > 1 else 0))
        before = len(discovered)
        for row in rows:
            discovered[row["external_id"]] = row
        if not rows or len(discovered) == before or len(discovered) >= max_items:
            break
    return [parse_detail(fetch_text(client, row["source_url"], delay=delay if index else 0), row) for index, row in enumerate(list(discovered.values())[:max_items])]

