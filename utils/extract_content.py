from bs4 import BeautifulSoup
import re, urllib.parse, asyncio
from playwright.async_api import async_playwright

_SECTION_KEYWORDS = {
    "about":    ["about", "our story", "who we are"],
    "services": ["services", "treatments", "what we offer"],
    "team":     ["team", "meet the team", "our team"],
    "contact":  ["contact", "get in touch", "contact us"],
}

def _match_keywords(text, keywords):
    t = text.lower()
    return any(k in t for k in keywords)

def _grab_first_block(soup: BeautifulSoup, keywords) -> str | None:
    """
    Scan **all** tags, not just headings, then bubble up to a
    parent <section>/<div> for context.
    """
    for tag in soup.find_all(True):
        if not tag.string:
            continue
        if _match_keywords(tag.string, keywords):
            parent = tag.find_parent(["section", "div"]) or tag
            return parent.get_text(" ", strip=True)[:2500]
    return None

async def _follow_if_needed(page, base_url, soup, key, kws):
    """If nav link exists, try to fetch its page and extract again."""
    link = soup.find("a", string=lambda s: s and _match_keywords(s, kws))
    if not link or not link.get("href"):
        return None

    href = urllib.parse.urljoin(base_url, link["href"])
    if href.startswith("#"):        # in-page anchor → ignore
        return None
    try:
        await page.goto(href, timeout=60_000)
        await page.wait_for_load_state("networkidle")
        html = await page.content()
        return _grab_first_block(BeautifulSoup(html, "lxml"), kws)
    except Exception:
        return None

async def extract_content(page, base_url: str) -> dict:
    html = await page.content()
    soup = BeautifulSoup(html, "lxml")

    data = {}
    for key, kws in _SECTION_KEYWORDS.items():
        text = _grab_first_block(soup, kws)
        if not text and key == "services":          # only follow for Services (heavy pages)
            text = await _follow_if_needed(page, base_url, soup, key, kws)
        data[key] = text
    return data
