from bs4 import BeautifulSoup

_SECTION_KEYWORDS = {
    "about":    ["about", "our story", "who we are"],
    "services": ["services", "what we offer", "our services"],
    "team":     ["team", "meet the team", "our team"],
    "contact":  ["contact", "get in touch"],
}

def _grab_section_text(soup, keywords):
    for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = heading.get_text(strip=True).lower()
        if any(k in text for k in keywords):
            section = heading.find_parent(["section", "div"]) or heading
            return section.get_text(" ", strip=True)[:2000]  # trim long blobs
    return None

def extract_content(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    data = {k: _grab_section_text(soup, v) for k, v in _SECTION_KEYWORDS.items()}
    return data
