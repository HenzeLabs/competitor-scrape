import argparse
import os
import yaml
import copy
from .runner import run_all

from reddit_ideas import (
    get_reddit,
    fetch_posts,
    fetch_top_comments,
    process_posts,
    save_csv,
    save_jsonl,
    save_sqlite,
)

def deep_merge(a, b):
    """Recursively merge dict b into dict a (a is mutated and returned)."""
    for k, v in b.items():
        if isinstance(v, dict) and k in a and isinstance(a[k], dict):
            deep_merge(a[k], v)
        else:
            a[k] = copy.deepcopy(v)
    return a

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_effective_config(args):
    # 1. Module defaults
    config = {}
    module_default_path = os.path.join(os.path.dirname(__file__), "..", "reddit_ideas", "config.yaml")
    if os.path.exists(module_default_path):
        config = load_yaml(module_default_path)

    # 2. Brand profile
    if getattr(args, "brand", None):
        brand_path = os.path.join(os.path.dirname(__file__), "..", "configs", "brands", f"{args.brand}.yaml")
        if os.path.exists(brand_path):
            config = deep_merge(config, load_yaml(brand_path))

    # 3. Explicit config file
    if getattr(args, "config", None):
        if os.path.exists(args.config):
            config = deep_merge(config, load_yaml(args.config))

    # 4. CLI overrides
    if getattr(args, "subs", None):
        config["subs"] = args.subs
    if getattr(args, "days", None):
        config["days"] = args.days
    if getattr(args, "sort", None):
        config["sort"] = args.sort
    if getattr(args, "keywords", None):
        config["keywords"] = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if getattr(args, "comments", None):
        config["comments"] = args.comments
    if getattr(args, "limit", None):
        config["limit"] = args.limit
    if getattr(args, "trending", None):
        config["trending_only"] = args.trending

    # Validation
    if not config.get("subs") or not isinstance(config["subs"], list) or not config["subs"]:
        raise ValueError("At least one subreddit must be specified in config or CLI.")
    if config.get("days", 0) < 1 or config.get("limit", 0) < 1:
        raise ValueError("Config values for 'days' and 'limit' must be positive integers.")

    return config

def add_reddit_ideas_parser(subparsers):
    reddit_parser = subparsers.add_parser(
        "reddit-ideas",
        help="Mine Reddit for marketing/product ideas"
    )
    reddit_parser.add_argument("--subs", nargs="+", help="Subreddits")
    reddit_parser.add_argument("--days", type=int)
    reddit_parser.add_argument("--sort", choices=["top", "new", "hot"])
    reddit_parser.add_argument("--keywords", type=str)
    reddit_parser.add_argument("--comments", type=int)
    reddit_parser.add_argument("--limit", type=int)
    reddit_parser.add_argument("--trending", action="store_true")
    reddit_parser.add_argument("--brand", type=str, help="Brand config profile name")
    reddit_parser.add_argument("--config", type=str, help="Explicit config file (YAML)")

def run_reddit_ideas(args):
    config = load_effective_config(args)
    trending_params = config.get("trending", {})
    # ensure window_days flows through from root-level config
    trending_params["window_days"] = config.get(
        "trending_window_days",
        trending_params.get("window_days", 30)
    )
    thresholds = config.get("thresholds", {})
    outputs = config.get("outputs", {})
    trending_only = getattr(args, "trending", False) or config.get("trending_only", False)

    # Print effective config summary
    print(f"[Config] brand={getattr(args, 'brand', None) or 'default'} | subs={len(config['subs'])} | days={config['days']} | limit={config['limit']} | trending={trending_params}")

    reddit = get_reddit()
    print(f"Fetching posts from: {config['subs']}")
    posts_raw = fetch_posts(
        reddit,
        config["subs"],
        days=config["days"],
        sort=config.get("sort", "top"),
        limit=config["limit"]
    )

    posts = []
    for post in posts_raw:
        post_data = {
            "id": post.id,
            "title": post.title,
            "selftext": post.selftext,
            "score": post.score,
            "num_comments": post.num_comments,
            "created_utc": post.created_utc,
            "permalink": f"https://reddit.com{post.permalink}",
        }
        post_data["top_comments"] = fetch_top_comments(post, limit=config.get("comments", 5))
        posts.append(post_data)

    posts = process_posts(
        posts,
        config.get("keywords", []),
        trending_only=trending_only,
        trending_params=trending_params,
        thresholds=thresholds
    )

    # Output filenames
    csv_file = outputs.get("csv", "reddit_ideas.csv")
    jsonl_file = outputs.get("jsonl", "reddit_ideas.jsonl")
    sqlite_file = outputs.get("sqlite", "reddit_ideas.db")
    trending_csv = outputs.get("trending_csv", "trending.csv")

    save_csv(posts, csv_file)
    save_jsonl(posts, jsonl_file)
    save_sqlite(posts, sqlite_file)
    if trending_only:
        save_csv(posts, trending_csv)
    print(f"Saved {len(posts)} posts to /data/")
    print(f"Output files: {csv_file}, {jsonl_file}, {sqlite_file}{', ' + trending_csv if trending_only else ''}")

    # Google Docs append
    import os
    try:
        from reddit_ideas.google_docs_writer import write_to_google_doc
        doc_id = os.getenv("GOOGLE_DOC_ID_REDDIT")
        if doc_id:
            summary = "\n".join([f"• {p['title']} ({p['permalink']})" for p in posts])
            write_to_google_doc(doc_id, f"[{getattr(args, 'brand', None) or 'default'}] {len(posts)} posts\n{summary}")
            print(f"Appended summary to Reddit Doc {doc_id}")
        else:
            print("GOOGLE_DOC_ID_REDDIT not set; skipping Reddit Doc append.")
    except Exception as e:
        print(f"[WARN] Could not append to Google Doc: {e}")

def main():
    parser = argparse.ArgumentParser(description="Competitor scraper CLI")
    subparsers = parser.add_subparsers(dest="command")

    scrape_parser = subparsers.add_parser("scrape", help="Scrape all configured sites")
    scrape_parser.add_argument("--site", default="all", help="Site name or 'all'")

    # Register reddit-ideas command
    add_reddit_ideas_parser(subparsers)

    args = parser.parse_args()

    if args.command == "scrape":
        run_all()
    elif args.command == "reddit-ideas":
        run_reddit_ideas(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
