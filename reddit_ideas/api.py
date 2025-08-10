import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import praw
from praw.models import Submission, Comment
from tenacity import retry, stop_after_attempt, wait_fixed

def load_reddit_creds():
    load_dotenv()
    return {
        "client_id": os.getenv("REDDIT_CLIENT_ID"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
        "user_agent": os.getenv("REDDIT_USER_AGENT", "reddit-ideas-miner/0.1"),
    }

def get_reddit():
    creds = load_reddit_creds()
    return praw.Reddit(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        user_agent=creds["user_agent"],
        check_for_async=False,
    )

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_posts(
    reddit,
    subreddits: List[str],
    days: int = 60,
    sort: str = "top",
    limit: int = 500,
) -> List[Submission]:
    posts = []
    for sub in subreddits:
        subreddit = reddit.subreddit(sub.replace("r/", ""))
        if sort == "top":
            submissions = subreddit.top(time_filter="all", limit=limit)
        elif sort == "new":
            submissions = subreddit.new(limit=limit)
        else:
            submissions = subreddit.hot(limit=limit)
        for post in submissions:
            # Filter by age
            if (post.created_utc < (reddit_utc_now() - days * 86400)):
                continue
            posts.append(post)
    return posts

def reddit_utc_now():
    import time
    return int(time.time())

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_top_comments(post: Submission, limit: int = 5) -> List[Dict[str, Any]]:
    post.comment_sort = "top"
    post.comments.replace_more(limit=0)
    comments = []
    for c in post.comments[:limit]:
        if isinstance(c, Comment):
            comments.append({
                "id": c.id,
                "body": c.body,
                "score": c.score,
                "created_utc": c.created_utc,
                "author": str(c.author) if c.author else None,
                "permalink": f"https://reddit.com{c.permalink}",
            })
    return comments
