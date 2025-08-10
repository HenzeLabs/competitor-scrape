import requests
from typing import Optional, Dict, Any

import httpx
import time
from typing import Tuple
import os
from .log import get_logger
logger = get_logger("fetch")

def fetch_url(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Optional[str]:
    """
    Fetches the content of a URL. Returns the text if successful, else None.
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception:
        return None

def fetch_httpx(
    url: str,
    user_agent: str,
    proxy: Optional[str] = None,
    timeout: httpx.Timeout = None
) -> Tuple[int, bytes, str]:
    """Fetch a URL over HTTP using httpx. Returns (status, content, final_url)."""
    def allowed(url, user_agent):
        return True
    class RobotsDisallowed(Exception):
        pass
    DEFAULT_HEADERS = {}
    DEFAULT_TIMEOUT = httpx.Timeout(10.0)
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    if not allowed(url, user_agent):
        raise RobotsDisallowed(f"robots.txt disallows {url}")
    headers = dict(DEFAULT_HEADERS)
    headers["User-Agent"] = user_agent
    proxy_arg = proxy or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    t0 = time.time()
    with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True, proxy=proxy_arg) as client:
        resp = client.get(url)
        elapsed = int((time.time() - t0) * 1000)
        logger.info("fetched via httpx", extra={"url": url, "status": resp.status_code, "elapsed_ms": elapsed})
        resp.raise_for_status()
        return resp.status_code, resp.content, str(resp.url)
