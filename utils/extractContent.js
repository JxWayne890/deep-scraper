// utils/extractContent.js
const selectorsMap = {
  about: [
    'section:has(h2:contains("About"))',
    'div:has(h1:contains("About"))',
    '*:contains("Our Story")',
    '*:contains("Who We Are")',
  ],
  services: [
    'section:has(h2:contains("Services"))',
    '*:contains("What We Offer")',
    '*:contains("Our Services")',
  ],
  team: [
    'section:has(h2:contains("Team"))',
    '*:contains("Meet the Team")',
    '*:contains("Our Team")',
  ],
  contact: [
    'section:has(h2:contains("Contact"))',
    'footer',
    '*:contains("Get in Touch")',
  ],
  testimonials: [
    'section:has(h2:contains("Testimonials"))',
    '*:contains("Reviews")',
    '*:contains("What Our Clients Say")',
  ],
};

async function extractSection(page, type) {
  const selectors = selectorsMap[type] || [];

  for (const sel of selectors) {
    try {
      const content = await page.$eval(sel, el => el.innerText.trim());
      if (content && content.length > 50) return content;
    } catch (e) {
      // Continue to next selector
    }
  }

  return null;
}

module.exports = { extractSection };
