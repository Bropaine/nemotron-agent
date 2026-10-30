from ddgs import DDGS


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

    return {
        "results": [
            {
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")[:500],
            }
            for item in results
        ]
    }


if __name__ == "__main__":
    import json

    result = search_web("site:docs.python.org/3/tutorial/ Python data structures")
    print(json.dumps(result, indent=2, ensure_ascii=False))