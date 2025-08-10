import asyncio
from typing import List
from ..models import Product
from ..core import parser, fetch, browser
from .base import BaseSiteAdapter
from datetime import datetime

class ExampleSiteAdapter(BaseSiteAdapter):
    site_name = "example-shop-1.com"

    def __init__(self, config):
        self.config = config

    async def discover_product_urls(self) -> List[str]:
        urls = []
        max_pages = self.config.get("max_pages", None)
        max_urls = self.config.get("max_urls", None)
        for i, url in enumerate(self.config["start_urls"], start=1):
            try:
                status, content, final_url = fetch.fetch_httpx(
                    url, user_agent=self.config.get("user_agent", "Mozilla/5.0")
                )
            except Exception as e:
                print(f"[WARN] Failed to fetch {url}: {e}")
                continue
            links = parser.all_attr(content.decode(), self.config["selectors"]["product_link"], "href", final_url)
            urls.extend(links)
            if max_pages and i >= max_pages:
                break
        urls = list(set(urls))
        if max_urls:
            urls = urls[:max_urls]
        return urls

    async def fetch_product(self, url: str) -> str:
        try:
            if self.config.get("use_playwright"):
                async with browser.browser_context(user_agent=self.config.get("user_agent", "Mozilla/5.0")) as ctx:
                    status, html, final_url = await fetch.fetch_playwright(ctx, url, user_agent=self.config.get("user_agent", "Mozilla/5.0"))
                    return html.decode()
            else:
                try:
                    _, content, _ = fetch.fetch_httpx(url, user_agent=self.config.get("user_agent", "Mozilla/5.0"))
                    return content.decode()
                except Exception as e:
                    print(f"[WARN] Failed to fetch {url}: {e}")
                    return ""
        except Exception as e:
            print(f"[ERROR] Unexpected error fetching {url}: {e}")
            return ""

    def parse_product(self, html: str) -> Product:
        cfg = self.config["selectors"]
        categories_val = parser.first_text(html, cfg.get("categories"))
        prod = Product(
            site=self.site_name,
            url="",
            title=parser.first_text(html, cfg.get("title")),
            price=self._parse_price(parser.first_text(html, cfg.get("price"))),
            sku=parser.first_text(html, cfg.get("sku")),
            images=parser.all_attr(html, cfg.get("images"), "src"),
            in_stock=self._parse_stock(parser.first_text(html, cfg.get("in_stock")), cfg.get("stock_text_contains")),
            stock_text=parser.first_text(html, cfg.get("in_stock")),
            categories=[categories_val] if categories_val else [],
            captured_at=datetime.utcnow().isoformat() + "Z"
        )
        return prod.ensure_hash()

    def _parse_price(self, price_str):
        if not price_str:
            return None
        return float(price_str.replace("$", "").replace(",", "").strip())

    def _parse_stock(self, stock_text, keyword):
        if stock_text and keyword and keyword.lower() in stock_text.lower():
            return True
        return False
