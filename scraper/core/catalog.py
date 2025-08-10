import csv
from typing import List, Dict, Any

def load_catalog(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads the catalog CSV and returns a list of dictionaries.
    """
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def save_catalog(rows: List[Dict[str, Any]], filepath: str) -> None:
    """
    Saves a list of dictionaries to a CSV file.
    """
    if not rows:
        return
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def price_delta_vs_catalog(sku: str, price: float, cat_map: list[dict]) -> float | None:
    """
    Returns the price difference between the given price and the catalog price for the SKU.
    If SKU is not found or price is None, returns None.
    """
    if not sku or price is None:
        return None
    for row in cat_map:
        if row.get("sku") == sku and row.get("price") is not None:
            try:
                catalog_price = float(row["price"])
                return price - catalog_price
            except Exception:
                return None
    return None
