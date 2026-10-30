import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit

ALLOWED_HOSTS = {
    "example.com",
    "docs.python.org",
    "en.wikipedia.org",
}


def read_page(url: str) -> str:
    """Read a public HTML page from an allowed website.

    Args:
        url: An HTTPS URL on example.com, docs.python.org,
            or en.wikipedia.org.
    """
    try:
        parts = urlsplit(url)
        allowed = (
                parts.scheme == "https"
                and parts.hostname in ALLOWED_HOSTS
                and parts.port in (None, 443)
                and parts.username is None
                and parts.password is None
        )
    except ValueError:
        return "Error: malformed URL."

    if not allowed:
        return "Error: URL must use HTTPS on an allowed website."

    try:
        response = requests.get(url, timeout=10, allow_redirects=False)
        if 300 <= response.status_code < 400:
            return "Error: redirects are not allowed in this first test."
        response.raise_for_status()
    except requests.RequestException as error:
        return f"Error: could not read page ({type(error).__name__})."

    soup = BeautifulSoup(response.content, "html.parser")

    for tag in soup.select("script, style, nav, header, footer, aside"):
        tag.decompose()

    content = (
            soup.select_one("main")
            or soup.select_one('[role="main"]')
            or soup.select_one("article")
            or soup.body
            or soup
    )
    text = content.get_text(" ", strip=True)
    text = " ".join(text.split())

    for tag in soup.select("script, style, nav, header, footer, aside, a.headerlink"):
        tag.decompose()

    if len(text) > 6000:
        return text[:6000] + "\n[Page text truncated.]"
    return text


if __name__ == "__main__":
    print(read_page("https://example.com"))
