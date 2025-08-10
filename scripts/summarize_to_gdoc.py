#!/usr/bin/env python3
import os, base64, json
from pathlib import Path
from datetime import datetime, timezone
import orjson
from google.oauth2 import service_account
from googleapiclient.discovery import build

def load_service_account():
    b64 = os.getenv("GCP_CREDENTIALS_JSON", "").strip()
    if not b64:
        raise RuntimeError("GCP_CREDENTIALS_JSON not set (base64 of service account JSON).")
    info = json.loads(base64.b64decode(b64).decode("utf-8"))
    scopes = ["https://www.googleapis.com/auth/documents"]
    return service_account.Credentials.from_service_account_info(info, scopes=scopes)

def read_jsonl(p: Path):
    rows = []
    if not p.exists():
        return rows
    with p.open("rb") as f:
        for line in f:
            if line.strip():
                rows.append(orjson.loads(line))
    return rows

def latest_date(site_dir: Path) -> str | None:
    files = sorted(site_dir.glob("*.jsonl"))
    return files[-1].stem if files else None

def load_stats():
    processed_root = Path("data/processed")
    diffs_root = Path("data/diffs")
    sites = [p.name for p in processed_root.iterdir() if p.is_dir()] if processed_root.exists() else []
    summary = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "sites": [],
        "totals": {"products":0,"new":0,"gone":0,"price_up":0,"price_down":0,"back_in_stock":0,"out_of_stock":0},
    }
    for site in sites:
        site_dir = processed_root / site
        d = latest_date(site_dir)
        if not d: 
            continue
        rows = read_jsonl(site_dir / f"{d}.jsonl")
        summary["totals"]["products"] += len(rows)

        stats = {}
        diff_json = diffs_root / site / f"{d}.json"
        if diff_json.exists():
            payload = orjson.loads(diff_json.read_bytes())
            stats = payload.get("stats", {})
            for k in summary["totals"].keys():
                if k in stats:
                    summary["totals"][k] += int(stats.get(k, 0))

        summary["sites"].append({"site": site, "date": d, "products": len(rows), "stats": stats})
    return summary

def render_markdown(s):
    lines = [f"## Weekly Summary — {s['date']}", ""]
    t = s["totals"]
    lines += [
        f"- **Total products scraped:** {t['products']}",
        f"- **New SKUs:** {t['new']} | **Gone:** {t['gone']}",
        f"- **Price up:** {t['price_up']} | **Price down:** {t['price_down']}",
        f"- **Back in stock:** {t['back_in_stock']} | **Out of stock:** {t['out_of_stock']}",
        "", "### Per-site",
    ]
    for site in sorted(s["sites"], key=lambda x: x["site"]):
        ls = site["stats"]
        lines.append(
            f"- **{site['site']}** ({site['date']}): {site['products']} products"
            + (f" — new {ls.get('new',0)}, gone {ls.get('gone',0)}, ↑ {ls.get('price_up',0)}, ↓ {ls.get('price_down',0)}" if ls else "")
        )
    lines.append("\n---\n")
    return "\n".join(lines)

def append_to_doc(doc_id: str, text: str, creds):
    service = build("docs", "v1", credentials=creds)
    # Insert at top (index 1) so latest summary appears first
    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests":[{"insertText":{"location":{"index":1},"text":text+"\n"}}]}
    ).execute()

def main():
    doc_id = os.getenv("GOOGLE_DOC_ID", "").strip()
    if not doc_id:
        raise RuntimeError("GOOGLE_DOC_ID not set.")
    summary = load_stats()
    md = render_markdown(summary)
    creds = load_service_account()
    append_to_doc(doc_id, md, creds)
    print("Summary appended to Google Doc.")

if __name__ == "__main__":
    main()
