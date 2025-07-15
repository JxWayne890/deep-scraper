# main.py  — FastAPI entry point
import logging
from asyncio import Semaphore

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scraper import scrape_site   # your existing Playwright helper

# ─── Configure uvicorn-style logger ────────────────────────────
# Render captures anything on stderr/stdout, so hook uvicorn’s logger.
logger = logging.getLogger("uvicorn.error")

app = FastAPI()

# ─── Concurrency guard ─────────────────────────────────────────
# Playwright + Chromium are RAM-heavy; on the free 512 MB container we
# allow **one** page at a time to prevent OOM → 502/503 storms.
BROWSER_SEM = Semaphore(1)

class ScrapeRequest(BaseModel):
    url: str


@app.post("/scrape")
async def scrape(req: ScrapeRequest):
    """
    POST body: { "url": "https://example.com" }

    Returns JSON sections extracted from the page.
    If Playwright fails, logs traceback and returns 500.
    """
    if not req.url:
        raise HTTPException(status_code=400, detail="url is required")

    try:
        async with BROWSER_SEM:           # ← one scrape at a time
            data = await scrape_site(req.url)
        return data or {"error": "no data extracted"}  # never empty JSON

    except Exception as e:
        # full traceback appears in Render ► Logs
        logger.exception("Scrape failed for %s", req.url)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def health():
    """Simple health-check endpoint used by n8n wake-loop."""
    return {"status": "OK"}
