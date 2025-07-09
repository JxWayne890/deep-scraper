# scraper.py  – optimized & robust
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

# ────────────────────────────────────────────────────────────
async def scrape_site(url: str) -> dict:
    """
    Fast, Render-friendly scraper:
    • Blocks images/css/fonts
    • Falls back to HTTPS
    • Ignores TLS errors
    • Closes common pop-ups
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )

        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0 Safari/537.36"),
        )
        page = await context.new_page()
        page.set_default_timeout(120_000)  # 120 s safety net
        await page.route("**/*", lambda r: r.abort() if _should_abort(r) else r.continue_())

        # Try original URL, then HTTPS fallback
        last_error = None
        candidates = [url]
        if url.startswith("http://"):
            candidates.append(url.replace("http://", "https://", 1))

        for target in candidates:
            try:
                await page.goto(target, timeout=120_000, wait_until="domcontentloaded")
                await page.wait_for_selector("body", timeout=8_000)

                # Attempt to dismiss common modal pop-ups
                try:
                    await page.locator(
                        "button[aria-label*=close], "
                        ".close-modal, "
                        ".mfp-close, "
                        ".elementor-popup-modal button[aria-label]"
                    ).first.click(timeout=2_000)
                except Exception:
                    pass

                html = await page.content()
                await browser.close()
                return extract_content(html, target)  # ← pass base_url
            except (PWTimeout, Exception) as e:
                last_error = e

        await browser.close()
        raise RuntimeError(f"Could not load page: {last_error}")
