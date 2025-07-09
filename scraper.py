# scraper.py  — final resilient build
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from utils.extract_content import extract_content

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


async def _scrape_once(browser, url: str):
    """Scrape a single URL inside its own fresh context/page."""
    ctx = await browser.new_context(
        ignore_https_errors=True,
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0 Safari/537.36"),
    )
    page = await ctx.new_page()
    page.set_default_timeout(120_000)
    await page.route("**/*", lambda r: r.abort() if _should_abort(r) else r.continue_())

    try:
        await page.goto(url, timeout=120_000, wait_until="domcontentloaded")
        await page.wait_for_selector("body", timeout=8_000)

        # dismiss common modal pop-ups
        try:
            await page.locator(
                "button[aria-label*=close], "
                ".close-modal, .mfp-close, "
                ".elementor-popup-modal button[aria-label]"
            ).first.click(timeout=2_000)
        except Exception:
            pass

        html = await page.content()
        data = await extract_content(html, url)   # <- async util
        await ctx.close()
        return data

    except Exception as e:
        await ctx.close()
        raise e


async def scrape_site(url: str) -> dict:
    """Try original URL, then HTTPS fallback — each in a fresh context."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )

        candidates = [url]
        if url.startswith("http://"):
            candidates.append(url.replace("http://", "https://", 1))

        last_err = None
        for target in candidates:
            try:
                return await _scrape_once(browser, target)
            except (PWTimeout, Exception) as e:
                last_err = e

        await browser.close()
        raise RuntimeError(f"Could not load page: {last_err}")
