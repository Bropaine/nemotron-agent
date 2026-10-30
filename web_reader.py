import ipaddress
import re
import socket
import time
from urllib.parse import quote, urlsplit

import certifi
import urllib3
from bs4 import BeautifulSoup

MAX_BYTES = 2_000_000
MAX_TEXT_CHARS = 6000
READ_SECONDS = 10
BODY_SECONDS = 20
USER_AGENT = "NemotronDiscovery/0.1 (https://github.com/Bropaine)"


def is_public_address(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    if not ip.is_global or ip.is_multicast:
        return False
    if isinstance(ip, ipaddress.IPv6Address):
        return not (ip.ipv4_mapped or ip.sixtofour or ip.teredo)
    return True


def parse_public_url(url: str):
    if not isinstance(url, str) or not url:
        raise ValueError("URL must be a nonempty string.")
    if any(character.isspace() or ord(character) < 32 for character in url):
        raise ValueError("Whitespace and control characters are not allowed in URLs.")
    if "\\" in url:
        raise ValueError("Backslashes are not allowed in URLs.")
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.port not in (None, 443):
        raise ValueError("Only HTTPS on port 443 is allowed.")
    if parts.username is not None or parts.password is not None:
        raise ValueError("URLs containing credentials are not allowed.")
    host = (parts.hostname or "").encode("idna").decode("ascii").lower()
    if not host or "%" in host:
        raise ValueError("Invalid hostname.")
    validate_hostname(host)
    return parts, host


def validate_hostname(host: str) -> None:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        labels = host.rstrip(".").split(".")
        valid = all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                    for label in labels)
        if len(host) > 253 or len(labels) < 2 or not valid:
            raise ValueError("Invalid public hostname.")
        return
    if not is_public_address(host):
        raise ValueError("Non-public IP addresses are not allowed.")


def is_public_https_url(url: str) -> bool:
    """Check URL syntax only. DNS is checked again before each connection."""
    try:
        parse_public_url(url)
        return True
    except (ValueError, UnicodeError):
        return False


def resolve_public_address(host: str) -> str:
    answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    addresses = list(dict.fromkeys(answer[4][0] for answer in answers))
    if not addresses or not all(is_public_address(ip) for ip in addresses):
        raise ValueError("Hostname must resolve exclusively to public IP addresses.")
    return addresses[0]


def read_html_body(response) -> bytes:
    if 300 <= response.status < 400:
        raise ValueError("Redirects are not followed. Choose a direct HTTPS page URL.")
    if response.status != 200:
        raise ValueError(f"Page request returned HTTP {response.status}.")
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if content_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError("Only HTML pages are supported.")
    encoding = response.headers.get("Content-Encoding", "identity").strip().lower()
    if encoding not in {"", "identity"}:
        raise ValueError("Compressed responses are not supported in this version.")
    return read_limited_body(response)


def read_limited_body(response) -> bytes:
    deadline = time.monotonic() + BODY_SECONDS
    body = bytearray()
    while True:
        if time.monotonic() > deadline:
            raise ValueError("Page body download exceeded its time budget.")
        chunk = response.read1(min(65536, MAX_BYTES + 1 - len(body)), decode_content=False)
        if not chunk:
            return bytes(body)
        body.extend(chunk)
        if len(body) > MAX_BYTES:
            raise ValueError("Page exceeds the download size limit.")


def fetch_html(url: str) -> bytes:
    parts, host = parse_public_url(url)
    address = resolve_public_address(host)
    path = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
    if parts.query:
        path += "?" + quote(parts.query, safe="/%?:@!$&'()*+,;=-._~")
    host_header = f"[{host}]" if ":" in host else host
    # Connect to the validated IP, but verify TLS and send SNI for the original host.
    pool = urllib3.HTTPSConnectionPool(
        address, port=443, server_hostname=host, assert_hostname=host,
        cert_reqs="CERT_REQUIRED", ca_certs=certifi.where(),
        timeout=urllib3.Timeout(connect=5, read=READ_SECONDS), retries=False,
    )
    response = None
    try:
        response = pool.urlopen(
            "GET", path, headers={"Host": host_header, "User-Agent": USER_AGENT,
                                  "Accept": "text/html, application/xhtml+xml",
                                  "Accept-Encoding": "identity"},
            preload_content=False, decode_content=False, redirect=False,
            retries=False, assert_same_host=False,
        )
        return read_html_body(response)
    finally:
        if response is not None:
            response.close()
        pool.close()


def extract_text(html: bytes) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("script, style, nav, header, footer, aside, a.headerlink"):
        tag.decompose()
    content = (soup.select_one("main") or soup.select_one('[role="main"]')
               or soup.select_one("article") or soup.body or soup)
    text = " ".join(content.get_text(" ", strip=True).split())
    if len(text) > MAX_TEXT_CHARS:
        return text[:MAX_TEXT_CHARS] + "\n[Page text truncated.]"
    return text or "Error: no readable page text was found."


def read_page(url: str) -> str:
    """Read a public HTTPS HTML page. Redirects and private addresses are blocked.

    Args:
        url: The direct HTTPS URL of the public page to read.
    """
    try:
        return extract_text(fetch_html(url))
    except ValueError as error:
        return f"Error: {error}"
    except (OSError, urllib3.exceptions.HTTPError) as error:
        return f"Error: could not read page ({type(error).__name__})."


if __name__ == "__main__":
    print(read_page("https://example.com"))
