import asyncio
from datetime import datetime
from pathlib import Path
import importlib

from .core import storage, diff, catalog
from .models import Product
import yaml
import os

def load_config(brand: str | None = None):
    with open("config/config.yml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg

async def run_site(site_cfg, today: str, cat_map):
    module_name = f"scraper.sites.{site_cfg['name'].replace('.', '_')}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        from .sites.example_site import ExampleSiteAdapter as Adapter
    else:
        Adapter = getattr(module, "Adapter", None) or getattr(module, "ExampleSiteAdapter")
    adapter = Adapter(site_cfg)
    urls = await adapter.discover_product_urls()
    products: list[dict] = []
    for url in urls:
        html = await adapter.fetch_product(url)
        prod = adapter.parse_product(html)
        prod.url = url
        prod.price_delta_vs_catalog = catalog.price_delta_vs_catalog(prod.sku, prod.price, cat_map)
        products.append(prod.dict())
        storage.write_raw(site_cfg["name"], today, url, html.encode(), "html")
    storage.write_jsonl(storage.jsonl_path(site_cfg["name"], today), products)
    prev_path = find_previous_jsonl(site_cfg["name"], today)
    if prev_path:
        stats, changes = diff.compute_diff(list(storage.read_jsonl(prev_path)), products)
        diff.write_diff_outputs(site_cfg["name"], today, stats, changes)

def find_previous_jsonl(site: str, today: str) -> Path | None:
    base = Path("data/processed") / site
    if not base.exists():
        return None
    files = sorted(p for p in base.glob("*.jsonl") if p.stem < today)
    return files[-1] if files else None

def run_all():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cfg = load_config()
    cat_map = catalog.load_catalog(cfg.get("catalog_csv", ""))
    loop = asyncio.get_event_loop()
    for site_cfg in cfg["sites"]:
        loop.run_until_complete(run_site(site_cfg, today, cat_map))
