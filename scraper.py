from playwright.async_api import async_playwright
from utils.extract_content import extract_content

async def scrape_site(url: str) -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await browser.new_page()
        await page.goto(url, timeout=60_000)
        await page.wait_for_load_state("networkidle")
        html = await page.content()
        await browser.close()

    return extract_content(html)
