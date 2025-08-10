from abc import ABC, abstractmethod
from typing import List
from ..models import Product

class BaseSiteAdapter(ABC):
    site_name: str

    @abstractmethod
    async def discover_product_urls(self) -> List[str]:
        pass

    @abstractmethod
    async def fetch_product(self, url: str) -> str:
        pass

    @abstractmethod
    def parse_product(self, html_or_page) -> Product:
        pass
