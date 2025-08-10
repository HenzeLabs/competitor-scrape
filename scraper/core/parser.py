# parser.py
import csv
from typing import Any, List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class HTMLParser:
    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "html.parser")

    def select(self, selector: str) -> Any:
        return self.soup.select(selector)

    def get_text(self, selector: str) -> str:
        el = self.soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

def parse_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Parses a CSV file and returns a list of dictionaries.
    """
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def filter_rows(rows: List[Dict[str, Any]], **criteria) -> List[Dict[str, Any]]:
    """
    Filters rows based on key-value criteria.
    """
    def matches(row):
        return all(row.get(k) == v for k, v in criteria.items())
    return [row for row in rows if matches(row)]

def all_attr(html: str, selector: str, attr: str, base_url: str | None = None) -> list[str]:
    """Return all values of a given attribute from elements matching selector.
    Resolves relative URLs if base_url is provided.
    """
    out: list[str] = []
    if not selector or not attr:
        return out
    try:
        tree = HTMLParser(html)
        for n in tree.select(selector):
            v = n.get(attr) if hasattr(n, 'get') else n.attributes.get(attr)
            if v:
                if base_url:
                    v = urljoin(base_url, v)
                out.append(v)
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        for el in soup.select(selector):
            v = el.get(attr)
            if v:
                if base_url:
                    v = urljoin(base_url, v)
                out.append(v)
    # Dedupe while preserving order
    seen = set()
    deduped = []
    for v in out:
        if v not in seen:
            seen.add(v)
            deduped.append(v)
    return deduped

def first_text(html: str, selector: str) -> str | None:
    """Return the stripped text of the first element matching selector, or None."""
    if not selector:
        return None
    try:
        tree = HTMLParser(html)
        node = tree.select(selector)
        if node:
            return node[0].get_text(strip=True)
    except Exception:
        pass
    soup = BeautifulSoup(html, "html.parser")
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else None
