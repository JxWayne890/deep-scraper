from bs4 import BeautifulSoup

from utils.extract_content import _grab_first_block, _SECTION_KEYWORDS


def test_grab_first_block_handles_nested_tags():
    html = """
    <html><body>
      <section>
        <h2><span>About Us</span></h2>
        <p>We are a company that loves code and open source projects. {extra}</p>
      </section>
    </body></html>
    """.format(extra="We build tools. " * 10)
    soup = BeautifulSoup(html, "lxml")
    result = _grab_first_block(soup, _SECTION_KEYWORDS['about'])

    assert result is not None
    assert "About Us" in result
