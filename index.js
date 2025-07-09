// index.js
const express = require('express');
const scrapeSite = require('./scraper');

const app = express();
app.use(express.json());

app.post('/scrape', async (req, res) => {
  console.log("📥 Received request body:", req.body);  // Log incoming request

  const { url } = req.body;
  if (!url) {
    console.log("❌ No URL received!");
    return res.status(400).json({ error: 'URL is required' });
  }

  try {
    const data = await scrapeSite(url);
    res.json(data);
  } catch (err) {
    console.error("❌ Scraper error:", err.message);
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Scraper running on port ${PORT}`));
