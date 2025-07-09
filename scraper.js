// scraper.js
const puppeteer = require('puppeteer');
const { extractSection } = require('./utils/extractContent');

async function scrapeSite(url) {
  console.log("🔍 Scraping:", url); // Log the URL being scraped

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();

  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
  } catch (err) {
    console.error("❌ Page load error:", err.message);
    await browser.close();
    return { error: "Failed to load site", detail: err.message };
  }

  const sections = ['about', 'services', 'team', 'contact', 'testimonials'];
  const results = {};

  for (const section of sections) {
    try {
      results[section] = await extractSection(page, section);
    } catch (err) {
      results[section] = null;
      console.warn(`⚠️ Error extracting "${section}":`, err.message);
    }
  }

  await browser.close();
  return results;
}

module.exports = scrapeSite;
