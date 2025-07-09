# scraper.py  — optimized for Render free tier
from playwright.async_api import async_playwright
from utils.extract_content import extract_content

BLOCKED_RESOURCE_TYPES = (
    "image", "stylesheet", "font",
)
BLOCKED_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp",
    ".css", ".woff", ".woff2", ".ttf",
)

async def _should_block(route):
    """Abort loading of heavy/static resources."""
    req = route.request
    if req.resource_type in BLOCKED_RESOURCE_TYPES:
        return True
    if any(req.url.lower().endswith(ext) for ext in BLOCKED_EXTENSIONS):
        return True
    return False

# ────────────────────────────────────────────────────────────
async def scrape_site(url: str) -> dict:
    """
    Render the given URL and extract structured sections.

    Optimizations:
    • Blocks images/fonts/css
    • Waits only for DOMContentLoaded + body selector
    • 120 s overall timeout
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        page = await browser.new_page()
        page.set_default_timeout(120_000)          # 120 s global safety net

        # Block heavy resources
        await page.route("**/*", lambda r: r.abort()
                         if _should_block(r) else r.continue_())

        # Go to page quickly
        await page.goto(url, timeout=120_000, wait_until="domcontentloaded")

        # Ensure <body> is in the DOM (usually < 2 s after DOMContentLoaded)
        await page.wait_for_selector("body", timeout=8_000)

        html = await page.content()
        await browser.close()

    return extract_content(html)
