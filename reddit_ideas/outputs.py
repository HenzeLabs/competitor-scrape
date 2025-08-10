import os
import csv
import json
import sqlite3
from typing import List, Dict, Any
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def save_csv(posts: List[Dict[str, Any]], filename: str):
    ensure_data_dir()
    path = os.path.join(DATA_DIR, filename)
    df = pd.DataFrame(posts)
    df.to_csv(path, index=False)

def save_jsonl(posts: List[Dict[str, Any]], filename: str):
    ensure_data_dir()
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        for post in posts:
            f.write(json.dumps(post, ensure_ascii=False) + "\n")

def save_sqlite(posts: List[Dict[str, Any]], filename: str):
    ensure_data_dir()
    path = os.path.join(DATA_DIR, filename)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            title TEXT,
            selftext TEXT,
            score INTEGER,
            num_comments INTEGER,
            created_utc REAL,
            permalink TEXT,
            tags TEXT,
            is_trending INTEGER,
            score_value REAL,
            engagement_rate REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            post_id TEXT,
            body TEXT,
            score INTEGER,
            created_utc REAL,
            author TEXT,
            permalink TEXT
        )
    """)
    for post in posts:
        c.execute("""
            INSERT OR REPLACE INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post.get("id"),
            post.get("title"),
            post.get("selftext"),
            post.get("score"),
            post.get("num_comments"),
            post.get("created_utc"),
            post.get("permalink"),
            ",".join(post.get("tags", [])),
            int(post.get("is_trending", False)),
            post.get("score_value"),
            post.get("engagement_rate"),
        ))
        for comment in post.get("top_comments", []):
            c.execute("""
                INSERT OR REPLACE INTO comments VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                comment.get("id"),
                post.get("id"),
                comment.get("body"),
                comment.get("score"),
                comment.get("created_utc"),
                comment.get("author"),
                comment.get("permalink"),
            ))
    conn.commit()
    conn.close()
