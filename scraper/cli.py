
import argparse
import os
import yaml
from .runner import run_all

# Reddit ideas imports
from reddit_ideas import (
    get_reddit,
    fetch_posts,
    fetch_top_comments,
    process_posts,
    save_csv,
    save_jsonl,
    save_sqlite,
)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "reddit_ideas", "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}

def add_reddit_ideas_parser(subparsers):
    reddit_parser = subparsers.add_parser(
        "reddit-ideas",
        help="Mine Reddit for marketing/product ideas"
    )
    reddit_parser.add_argument("--subs", nargs="+", help="Subreddits")
    reddit_parser.add_argument("--days", type=int)
    reddit_parser.add_argument("--sort", choices=["top", "new", "hot"], default="top")
    reddit_parser.add_argument("--keywords", type=str)
    reddit_parser.add_argument("--comments", type=int, default=5)
    reddit_parser.add_argument("--limit", type=int, default=500)
    reddit_parser.add_argument("--trending", action="store_true")

def run_reddit_ideas(args):
    config = load_config()
    subs = args.subs or config.get("subs", ["r/Entrepreneur", "r/marketing", "r/SaaS", "r/startups"])
    days = args.days or config.get("days", 60)
    sort = args.sort or config.get("sort", "top")
    comments_limit = args.comments or config.get("comments", 5)
    keywords = args.keywords.split(",") if args.keywords else config.get("keywords", [
        "feature request", "pain", "pricing", "onboarding", "churn"
    ])
    limit = args.limit or config.get("limit", 500)
    trending_only = args.trending

    reddit = get_reddit()
    print(f"Fetching posts from: {subs}")
    posts_raw = fetch_posts(reddit, subs, days=days, sort=sort, limit=limit)

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
        post_data["top_comments"] = fetch_top_comments(post, limit=comments_limit)
        posts.append(post_data)

    posts = process_posts(posts, keywords, trending_only=trending_only)

    save_csv(posts, "reddit_ideas.csv")
    save_jsonl(posts, "reddit_ideas.jsonl")
    save_sqlite(posts, "reddit_ideas.db")
    if trending_only:
        save_csv(posts, "trending.csv")
    print(f"Saved {len(posts)} posts to /data/")

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
