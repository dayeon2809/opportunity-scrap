import time

import requests

from core.config import CRAWLER_USER_AGENT


def session() -> requests.Session:
    client = requests.Session()
    client.headers.update({"User-Agent": CRAWLER_USER_AGENT})
    return client


def fetch_text(client: requests.Session, url: str, *, method="get", data=None, timeout=20, delay=0.0) -> str:
    if delay:
        time.sleep(delay)
    response = client.request(method, url, data=data, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return response.text

