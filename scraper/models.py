from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib

def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

class Product(BaseModel):
    site: str
    url: str
    title: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    sku: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    in_stock: Optional[bool] = None
    stock_text: Optional[str] = None
    reviews_count: Optional[int] = None
    rating: Optional[float] = None
    categories: List[str] = Field(default_factory=list)
    captured_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    hash: Optional[str] = None
    price_delta_vs_catalog: Optional[float] = None
    changes: Dict[str, Any] = Field(default_factory=dict)

    def dedupe_key(self) -> str:
        if self.sku:
            return f"{self.site}::{self.sku}"
        return f"{self.site}::{content_hash(self.url)}"

    def ensure_hash(self):
        payload = f"{self.title}|{self.price}|{self.in_stock}|{','.join(self.images)}"
        self.hash = content_hash(payload)
        return self
