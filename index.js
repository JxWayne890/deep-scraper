// index.js
const express = require('express');
const app = express();

app.use(express.json());

// Basic test route
app.post('/scrape', async (req, res) => {
  console.log("📥 Received request body:", req.body);

  const { url } = req.body;
  if (!url) {
    return res.status(400).json({ error: 'Missing URL' });
  }

  // Temporary mock response
  res.json({
    about: "This is a mock 'About Us' section.",
    services: "This is a mock 'Services' section."
  });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`🚀 Scraper running on port ${PORT}`);
});
