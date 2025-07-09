// scraper.js
const puppeteer = require('puppeteer');
const { extractSection } = require('./utils/extractContent');

async function scrapeSite(url) {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();

  await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

  const sections = ['about', 'services', 'team', 'contact', 'testimonials'];
  const results = {};

  for (const section of sections) {
    results[section] = await extractSection(page, section);
  }

  await browser.close();
  return results;
}

module.exports = scrapeSite;
