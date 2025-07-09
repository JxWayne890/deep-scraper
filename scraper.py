# scraper.py  — robust & async-safe
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

async def scrape_site(url: str) -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        ctx = await browser.new_context(
            ignore_https_errors=True,
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0 Safari/537.36"),
        )
        page = await ctx.new_page()
        page.set_default_timeout(120_000)
        await page.route("**/*", lambda r: r.abort() if _should_abort(r) else r.continue_())

        last_err = None
        candidates = [url] + ([url.replace("http://", "https://", 1)]
                              if url.startswith("http://") else [])

        for target in candidates:
            try:
                await page.goto(target, timeout=120_000, wait_until="domcontentloaded")
                await page.wait_for_selector("body", timeout=8_000)
                try:  # close common pop-ups
                    await page.locator(
                        "button[aria-label*=close], .close-modal, .mfp-close, "
                        ".elementor-popup-modal button[aria-label]"
                    ).first.click(timeout=2_000)
                except Exception:
                    pass

                html = await page.content()
                await browser.close()
                data = await extract_content(html, target)  # <-- await here
                return data

            except (PWTimeout, Exception) as e:
                last_err = e

        await browser.close()
        raise RuntimeError(f"Could not load page: {last_err}")
