from ddgs import DDGS
from discovery_store import initialize_database, get_recommended_urls
from urllib.parse import urlsplit
from web_reader import ALLOWED_HOSTS


def is_discovery_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
        return (
                parts.scheme == "https"
                and parts.hostname in ALLOWED_HOSTS
                and parts.hostname != "example.com"
                and parts.port in (None, 443)
                and parts.username is None
                and parts.password is None
        )
    except ValueError:
        return False


def search_web(query: str) -> dict:
    """Search for web pages about a topic.

    Args:
        query: A short search query describing the user's interest.
    """
    query = query.strip()
    if not query:
        return {"error": "Search query cannot be empty."}

    try:
        results = DDGS().text(query, max_results=5)
    except Exception as error:
        return {"error": f"Search failed ({type(error).__name__})."}
    initialize_database()
    seen_urls = get_recommended_urls()
    return {
        "results": [
            {
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")[:500],
            }
            for item in results
            if is_discovery_url(item.get("href", ""))
            and item.get("href", "") not in seen_urls
        ]
    }


if __name__ == "__main__":
    import json

    result = search_web("site:docs.python.org/3/tutorial/ Python data structures")
    print(json.dumps(result, indent=2, ensure_ascii=False))
