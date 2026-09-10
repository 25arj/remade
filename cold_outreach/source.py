import logging
import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_SKIP_PREFIXES = ("noreply", "no-reply", "donotreply", "privacy", "abuse", "postmaster", "webmaster")
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; lead-research-bot/1.0)"}


@dataclass
class CompanyLead:
    company: str
    website: str
    email: str


def _search(api_key: str, cx: str, query: str, num: int) -> list:
    """Google Programmable Search Engine (Custom Search JSON API). Free
    tier: 100 queries/day. This reads public search results only - no
    scraping of a walled-off or logged-in platform.
    """
    results = []
    start = 1
    while len(results) < num:
        resp = requests.get(
            _SEARCH_URL,
            params={"key": api_key, "cx": cx, "q": query, "start": start, "num": min(10, num - len(results))},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.error("Custom Search failed (%s): %s", resp.status_code, resp.text[:200])
            break
        items = resp.json().get("items", [])
        if not items:
            break
        results.extend(items)
        start += len(items)
        if start > 91:  # API only paginates through the first ~100 results
            break
    return results[:num]


def _find_email_on_page(url: str) -> str:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=8)
        resp.raise_for_status()
    except requests.RequestException:
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    for link in soup.select("a[href^=mailto]"):
        candidate = link["href"].split("mailto:", 1)[1].split("?")[0].strip()
        if candidate and not candidate.lower().startswith(_SKIP_PREFIXES):
            return candidate

    match = _EMAIL_RE.search(soup.get_text(" "))
    if match and not match.group(0).lower().startswith(_SKIP_PREFIXES):
        return match.group(0)
    return ""


def find_candidate_companies(config, seen_emails: set) -> list:
    """Finds public business contact emails: Custom Search finds company
    websites matching your ICP queries, then a plain GET of that site's
    homepage (and /contact as a fallback) picks up any publicly listed
    email. No login, no auth bypass - just reading pages that are already
    public, same as any search engine crawler would.
    """
    found = {}
    for query in config.search_queries:
        for item in _search(config.google_search_api_key, config.google_search_cx, query, config.results_per_query):
            website = item.get("link", "")
            company = (item.get("title") or website).strip()
            if not website or website in found:
                continue

            email = _find_email_on_page(website)
            if not email:
                email = _find_email_on_page(website.rstrip("/") + "/contact")

            if email and email not in seen_emails:
                found[website] = CompanyLead(company=company, website=website, email=email)

    return list(found.values())
