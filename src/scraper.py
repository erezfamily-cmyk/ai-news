import feedparser
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent

FEEDS = {
    "OpenAI": {
        "url": "https://openai.com/blog/rss.xml",
        "category": "חברות AI"
    },
    "Anthropic": {
        "url": "https://www.anthropic.com/rss.xml",
        "category": "חברות AI"
    },
    "Google DeepMind": {
        "url": "https://deepmind.google/blog/rss.xml",
        "category": "חברות AI"
    },
    "HuggingFace": {
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "כלים ומודלים"
    },
    "TechCrunch AI": {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "חדשות"
    },
    "The Verge AI": {
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "category": "חדשות"
    },
    "MIT Technology Review": {
        "url": "https://www.technologyreview.com/feed/",
        "category": "מחקר"
    },
    "arXiv cs.AI": {
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "category": "מחקר"
    },
    "Wired AI": {
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "category": "חדשות"
    },
    "AWS Machine Learning": {
        "url": "https://aws.amazon.com/blogs/machine-learning/feed/",
        "category": "כלים ומודלים"
    },
}

MAX_ITEMS_PER_SOURCE = 10


def parse_date(entry):
    for field in ("published_parsed", "updated_parsed"):
        val = getattr(entry, field, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def scrape():
    results = {}
    for name, meta in FEEDS.items():
        print(f"סורק: {name}...")
        try:
            feed = feedparser.parse(meta["url"])
            items = []
            for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
                items.append({
                    "title": entry.get("title", "ללא כותרת"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:300],
                    "date": parse_date(entry),
                })
            results[name] = {
                "url": meta["url"],
                "category": meta["category"],
                "items": items,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
            print(f"  ✓ {len(items)} פריטים")
        except Exception as e:
            results[name] = {
                "url": meta["url"],
                "category": meta["category"],
                "items": [],
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            }
            print(f"  ✗ שגיאה: {e}")

    out = ROOT / "data.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nנשמר ל-{out}")


if __name__ == "__main__":
    scrape()
