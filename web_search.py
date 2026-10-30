import json

from ddgs import DDGS

from discovery_store import initialize_database, get_recommended_urls
from web_reader import is_public_https_url


def is_discovery_url(url: str) -> bool:
    return is_public_https_url(url)


def filter_search_results(results: list, seen_urls: set[str]) -> dict:
    candidates = []
    excluded_by_policy = 0
    excluded_as_seen = 0

    for item in results:
        url = item.get("href", "")
        if not is_discovery_url(url):
            excluded_by_policy += 1
            continue
        if url in seen_urls:
            excluded_as_seen += 1
            continue
        candidates.append({
            "title": item.get("title", ""),
            "url": url,
            "snippet": item.get("body", "")[:500],
        })

    return {
        "results": candidates,
        "diagnostics": {
            "provider_count": len(results),
            "excluded_by_url_policy": excluded_by_policy,
            "excluded_as_seen": excluded_as_seen,
            "returned_count": len(candidates),
        },
        "reading_policy": (
            "Public HTTPS HTML pages only. DNS is validated before connecting; "
            "redirects are not followed. Search snippets are not read-page evidence."
        ),
    }


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
    return filter_search_results(results, get_recommended_urls())


if __name__ == "__main__":
    result = search_web("most widely used Python libraries")
    print(json.dumps(result, indent=2, ensure_ascii=False))
