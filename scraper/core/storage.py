# storage.py
import os
import json
from typing import Any, Iterable, Dict
from pathlib import Path
import orjson

def save_json(data: Any, filepath: str) -> None:
    """
    Saves data as JSON to the specified filepath.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> Any:
    """
    Loads JSON data from the specified filepath.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_raw(site: str, today: str, url: str, content: bytes, ext: str = "html") -> None:
    """
    Writes raw content to data/raw/{site}/{today}/{hash}.{ext}
    """
    import hashlib
    out_dir = os.path.join("data", "raw", site, today)
    os.makedirs(out_dir, exist_ok=True)
    url_hash = hashlib.sha256(url.encode("utf-8", errors="ignore")).hexdigest()
    out_path = os.path.join(out_dir, f"{url_hash}.{ext}")
    with open(out_path, "wb") as f:
        f.write(content)


def jsonl_path(site: str, date: str) -> Path:
    """Return the path for the processed JSONL file for a given site/date."""
    base = Path("data/processed") / site
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{date}.jsonl"


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]):
    """Append rows to a JSONL file."""
    with path.open("ab") as f:
        for r in rows:
            f.write(orjson.dumps(r))
            f.write(b"\n")
