# scraper.py  — resilient, final build
from urllib.parse import urlparse
import inspect

from playwright.async_api import (
    async_playwright,
    TimeoutError as PWTimeout,
)
from utils.extract_content import extract_content

# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------
BLOCK_EXT = (
    ".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp",
    ".css", ".woff", ".woff2", ".ttf",
)

def _should_abort(route):
    url = route.request.url.lower()
    if route.request.resource_type in ("image", "stylesheet", "font"):
        return True
    if any(url.endswith(ext) for ext in BLOCK_EXT):
        return True
    return False

def _normalise(url: str) -> str:
    """Ensure URL has http/https scheme so Playwright accepts it."""
    if not urlparse(url).scheme:
        return "http://" + url
    return url

# -----------------------------------------------------------------
# Core single-attempt scraper
# -----------------------------------------------------------------
async def _scrape_once(browser, url: str):
    """Scrape one URL in its own fresh context & page."""
    ctx = await browser.new_context(
        ignore_https_errors=True,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
    )
    page = await ctx.new_page()
    page.set_default_timeout(120_000)  # 120 s global cap
    await page.route("**/*", lambda r: r.abort() if _should_abort(r) else r.continue_())

    try:
        await page.goto(url, timeout=120_000, wait_until="domcontentloaded")

        # Prefer visible <body>; if hidden, fall back to just attached
        try:
            await page.wait_for_selector("body", timeout=8_000, state="visible")
        except PWTimeout:
            await page.wait_for_selector("body", timeout=12_000, state="attached")

        # Attempt to close common pop-ups
        try:
            await page.locator(
                "button[aria-label*=close], "
                ".close-modal, .mfp-close, "
                ".elementor-popup-modal button[aria-label]"
            ).first.click(timeout=2_000)
        except Exception:
            pass

        # Pass PAGE object to extractor
        if inspect.iscoroutinefunction(extract_content):
            data = await extract_content(page, url)
        else:
            data = extract_content(page, url)

        await ctx.close()
        return data

    except Exception as e:
        await ctx.close()
        raise e

# -----------------------------------------------------------------
# Public entry
# -----------------------------------------------------------------
async def scrape_site(raw_url: str) -> dict:
    """Scrape a site with HTTP➜HTTPS fallback and robust retries."""
    raw_url = _normalise(raw_url)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )

        # Try original URL, then HTTPS variant if needed
        candidates = [raw_url]
        if raw_url.startswith("http://"):
            candidates.append(raw_url.replace("http://", "https://", 1))

        last_err = None
        for target in candidates:
            try:
                return await _scrape_once(browser, target)
            except (PWTimeout, Exception) as e:
                last_err = e  # keep last error and retry next candidate

        await browser.close()
        raise RuntimeError(f"Could not load page: {last_err}")
