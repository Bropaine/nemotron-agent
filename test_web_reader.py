from unittest.mock import patch
import requests

from web_reader import read_page

with patch("web_reader.requests.get", side_effect=requests.Timeout):
    result = read_page("https://example.com")

assert result == "Error: could not read page (Timeout)."
print("Timeout handled correctly")
print("Timeout handled correctly")