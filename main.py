from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper import scrape_site

app = FastAPI()

class ScrapeRequest(BaseModel):
    url: str

@app.post("/scrape")
async def scrape(req: ScrapeRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="url is required")
    try:
        data = await scrape_site(req.url)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")          # simple health-check
async def health():
    return {"status": "OK"}
