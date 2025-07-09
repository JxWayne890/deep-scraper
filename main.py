# main.py  — FastAPI entry point
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper import scrape_site

# ─── Configure uvicorn-style logger ────────────────────────────
# Render’s log viewer captures everything sent to stderr/stdout,
# so we hook into the default uvicorn logger.
logger = logging.getLogger("uvicorn.error")

app = FastAPI()

class ScrapeRequest(BaseModel):
    url: str


@app.post("/scrape")
async def scrape(req: ScrapeRequest):
    """
    POST body: { "url": "https://example.com" }

    Returns JSON sections extracted from the page or raises 4xx/5xx.
    """
    if not req.url:
        raise HTTPException(status_code=400, detail="url is required")

    try:
        data = await scrape_site(req.url)
        return data

    except Exception as e:
        # Log full traceback to Render logs for easier debugging
        logger.exception("Scrape failed for %s", req.url)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")  # simple health-check
async def health():
    return {"status": "OK"}
