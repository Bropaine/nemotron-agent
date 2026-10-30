from unittest.mock import patch
from web_search import search_web

seen = "https://docs.python.org/3/tutorial/"
new = "https://docs.python.org/3/tutorial/datastructures.html"

with (
    patch("web_search.initialize_database"),
    patch("web_search.get_recommended_urls", return_value={seen}),
    patch("web_search.DDGS") as mock_search,
):
    mock_search.return_value.text.return_value = [
        {"title": "Already seen", "href": seen, "body": "Old page"},
        {"title": "New page", "href": new, "body": "New page"},
        {"title": "Other site", "href": "https://outside.invalid/page", "body": "Blocked"},
        {"title": "Test domain", "href": "https://example.com", "body": "Placeholder"},
        {"title": "Insecure URL", "href": "http://docs.python.org/3/", "body": "Blocked"},
    ]

    result = search_web("Python")
    urls = [item["url"] for item in result["results"]]
    assert urls == [new], result
    print("Passed: only the unseen, permitted discovery URL remains.")