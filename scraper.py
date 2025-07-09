# scraper.py  – Python FastAPI / Playwright service
from playwright.async_api import async_playwright
from utils.extract_content import extract_content

# ──────────────────────────────────────────────────────────────
# Scraping function
# ──────────────────────────────────────────────────────────────
async def scrape_site(url: str) -> dict:
    """
    Launches a headless Chromium browser, navigates to the URL,
    captures the rendered HTML, and extracts key sections.

    The default Playwright timeout is bumped to 120 seconds so
    large or slow pages do not raise the 30 000 ms exception.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                # optional: block images / css to speed up scraping
                # "--disable-loading-image",
            ],
        )
        page = await browser.new_page()

        # 🔧 NEW: increase default timeout for *all* waits on this page
        page.set_default_timeout(120_000)  # 120 000 ms = 120 s

        # Navigate and wait until network is (mostly) idle
        await page.goto(url, timeout=120_000)
        await page.wait_for_load_state("networkidle", timeout=120_000)

        # Pull the fully rendered HTML
        html = await page.content()

        await browser.close()

    # Hand the HTML off to your content extractor
    return extract_content(html)
