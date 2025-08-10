import re
from typing import List, Dict, Any
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

KEYWORDS = [
    "feature request", "pain", "pricing", "onboarding", "churn"
]
QUESTION_RE = re.compile(r"\?$")
CATEGORIES = {
    "pain": re.compile(r"\b(pain|problem|struggle|issue|frustrat|blocker)\b", re.I),
    "feature idea": re.compile(r"\b(feature|request|add|build|improve|suggest)\b", re.I),
    "pricing": re.compile(r"\b(price|pricing|cost|expensive|cheap|free|discount)\b", re.I),
    "go-to-market": re.compile(r"\b(launch|release|market|growth|acquire|customer|user)\b", re.I),
}

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def score_post(post: Dict[str, Any], keywords: List[str]) -> float:
    score = post.get("score", 0) + post.get("num_comments", 0)
    text = (post.get("title", "") + " " + post.get("selftext", "")).lower()
    keyword_hits = sum(1 for kw in keywords if kw.lower() in text)
    question_bonus = 5 if QUESTION_RE.search(post.get("title", "")) else 0
    sentiment = analyzer.polarity_scores(text)["compound"]
    return score + 10 * keyword_hits + question_bonus + 5 * (sentiment < -0.3)

def tag_post(post: Dict[str, Any]) -> List[str]:
    tags = []
    text = (post.get("title", "") + " " + post.get("selftext", "")).lower()
    for cat, regex in CATEGORIES.items():
        if regex.search(text):
            tags.append(cat)
    if QUESTION_RE.search(post.get("title", "")):
        tags.append("question")
    return list(set(tags))

def detect_trending(posts: List[Dict[str, Any]], window_days: int = 30) -> List[Dict[str, Any]]:
    import numpy as np
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    for post in posts:
        age_hours = max((now.timestamp() - post["created_utc"]) / 3600, 1)
        post["engagement_rate"] = (post["score"] + post["num_comments"]) / age_hours

    # Baseline: median engagement rate for posts in window_days
    window_start = now.timestamp() - window_days * 86400
    window_rates = [p["engagement_rate"] for p in posts if p["created_utc"] >= window_start]
    baseline = float(np.median(window_rates)) if window_rates else 0.1

    # Trending: ≥2x baseline or top 10% in last 48h
    last_48h = now.timestamp() - 2 * 86400
    recent_posts = [p for p in posts if p["created_utc"] >= last_48h]
    if recent_posts:
        top_10pct = np.percentile([p["engagement_rate"] for p in recent_posts], 90)
    else:
        top_10pct = 0

    for post in posts:
        is_trending = (
            post["engagement_rate"] >= 2 * baseline or
            (post["created_utc"] >= last_48h and post["engagement_rate"] >= top_10pct)
        )
        post["is_trending"] = bool(is_trending)
    return posts

def deduplicate(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped = []
    for p in posts:
        key = p.get("permalink") or p.get("title", "").strip().lower()
        if key not in seen:
            deduped.append(p)
            seen.add(key)
    return deduped

def process_posts(posts: List[Dict[str, Any]], keywords: List[str], trending_only: bool = False) -> List[Dict[str, Any]]:
    for post in posts:
        post["title"] = clean_text(post.get("title", ""))
        post["selftext"] = clean_text(post.get("selftext", ""))
        post["score_value"] = score_post(post, keywords)
        post["tags"] = tag_post(post)
    posts = deduplicate(posts)
    posts = detect_trending(posts)
    if trending_only:
        posts = [p for p in posts if p.get("is_trending")]
    return posts
