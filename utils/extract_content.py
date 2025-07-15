# utils/extract_content.py
from bs4 import BeautifulSoup
import re, urllib.parse, asyncio

_SECTION_KEYWORDS = {
    "about":    ["about", "our story", "who we are"],
    "services": ["services", "treatments", "what we offer"],
    "team":     ["team", "meet the team", "our team"],
    "contact":  ["contact", "get in touch", "contact us"],
}

_MIN_LEN = 80                     # skip tiny matches
_SKIP_TAGS = {"script", "style", "noscript"}

def _match_keywords(text: str, keywords) -> bool:
    """Case-insensitive keyword match."""
    t = text.lower()
    return any(k in t for k in keywords)

def _grab_first_block(soup: BeautifulSoup, keywords) -> str | None:
    """
    Scan all tags. When a keyword appears, bubble up to the nearest
    <section> or <div>, strip, collapse whitespace, and return if
    the text length meets _MIN_LEN.
    """
    for tag in soup.find_all(True):
        if tag.name in _SKIP_TAGS:
            continue
        if not tag.string:
            continue
        if _match_keywords(tag.string, keywords):
            parent = tag.find_parent(["section", "div"]) or tag
            txt = parent.get_text(" ", strip=True)
            if len(txt) >= _MIN_LEN:
                return txt[:2500]  # cap for sanity
    return None

async def _follow_if_needed(page, base_url, soup, kws):
    """
    If the main page lacked a Services block, follow the first
    nav/link whose anchor text matches the keywords and re-extract.
    """
    link = soup.find("a", string=lambda s: s and _match_keywords(s, kws))
    if not link or not link.get("href"):
        return None

    href = urllib.parse.urljoin(base_url, link["href"])
    if href.startswith("#"):                 # in-page anchor
        return None
    try:
        await page.goto(href, timeout=60_000, wait_until="domcontentloaded")
        await page.wait_for_selector("body", state="attached", timeout=10_000)
        html = await page.content()
        return _grab_first_block(BeautifulSoup(html, "lxml"), kws)
    except Exception:
        return None

def _meta_description(soup: BeautifulSoup) -> str | None:
    meta = soup.find("meta", attrs={"name": re.compile("description", re.I)})
    if meta and meta.get("content") and len(meta["content"].strip()) >= _MIN_LEN:
        return meta["content"].strip()
    og = soup.find("meta", attrs={"property": "og:description"})
    if og and og.get("content") and len(og["content"].strip()) >= _MIN_LEN:
        return og["content"].strip()
    return None

# ──────────────────────────────────────────────────────────────
async def extract_content(page, base_url: str) -> dict:
    """Main entry called by scraper.py."""
    html = await page.content()
    soup = BeautifulSoup(html, "lxml")

    data = {}
    for key, kws in _SECTION_KEYWORDS.items():
        text = _grab_first_block(soup, kws)

        # For Services, follow a nav link if main page empty
        if not text and key == "services":
            text = await _follow_if_needed(page, base_url, soup, kws)

        data[key] = text

    # Fallback for About
    if not data["about"]:
        data["about"] = _meta_description(soup)

    return data
