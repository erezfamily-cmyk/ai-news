import feedparser
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent

# מילות מפתח לסינון AI — רק פריטים שמכילים לפחות אחת מהן יעברו
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "gpt", "chatgpt", "claude", "gemini", "copilot", "openai",
    "anthropic", "deepmind", "huggingface", "midjourney", "stable diffusion",
    "neural network", "generative", "בינה מלאכותית", "למידת מכונה",
    "בינה", "מודל שפה", "צ'אט", "רובוט", "אוטומציה", "אלגוריתם",
    "nlp", "computer vision", "transformer", "diffusion",
]

FEEDS = {
    # ── חדשות טכנולוגיה (ישראל) — מסוננות לפי מילות מפתח ──────────────
    "גיקטיים": {
        "url": "https://www.geektime.co.il/feed/",
        "category": "חדשות טכנולוגיה",
        "filter_ai": True,
    },
    "כלכליסט טק": {
        "url": "https://www.calcalist.co.il/rss/AjaxPage,1342,L-CalculistRssList,00.xml",
        "category": "חדשות טכנולוגיה",
        "filter_ai": True,
    },
    "TheMarker טכנולוגיה": {
        "url": "https://www.themarker.com/cmlink/1.4658981",
        "category": "חדשות טכנולוגיה",
        "filter_ai": True,
    },
    "וואלה טק": {
        "url": "https://rss.walla.co.il/feed/22",
        "category": "חדשות טכנולוגיה",
        "filter_ai": True,
    },
    "ynet טכנולוגיה": {
        "url": "https://www.ynet.co.il/Integration/StoryRss3785.xml",
        "category": "חדשות טכנולוגיה",
        "filter_ai": True,
    },
    "הארץ טכנולוגיה": {
        "url": "https://www.haaretz.co.il/srv/haaretz-main-rss",
        "category": "חדשות טכנולוגיה",
        "filter_ai": True,
    },

    # ── AI ישראל — ייעודי AI, ללא סינון ─────────────────────────────────
    "ספארקס — בינה מלאכותית": {
        "url": "https://sparks.news/feed/",
        "category": "AI ישראל",
        "filter_ai": False,
    },
    "ICT Israel": {
        "url": "https://ictisrael.com/feed/",
        "category": "AI ישראל",
        "filter_ai": True,
    },

    # ── מחשוב וממשל — מגזר ציבורי, IT, דיגיטל ישראל ────────────────────
    "גיקטיים — מגזר ציבורי": {
        "url": "https://www.geektime.co.il/feed/",
        "category": "מחשוב וממשל",
        "filter_ai": True,
        "filter_extra": ["ממשלה", "ממשלתי", "מגזר ציבורי", "דיגיטל ישראל", "משרד", "רגולציה",
                         "סייבר", "cyber", "govtech", "government", "public sector",
                         "מחשוב", "it ", "cloud", "ענן", "נתונים", "data", "אוטומציה",
                         "automation", "productivity", "copilot", "microsoft", "google workspace"],
    },
    "כלכליסט — מגזר ציבורי": {
        "url": "https://www.calcalist.co.il/rss/AjaxPage,1342,L-CalculistRssList,00.xml",
        "category": "מחשוב וממשל",
        "filter_ai": True,
        "filter_extra": ["ממשלה", "ממשלתי", "מגזר ציבורי", "דיגיטל", "משרד", "רגולציה",
                         "סייבר", "cyber", "מחשוב", "ענן", "נתונים", "אוטומציה"],
    },

    # קמפוס GOV נסרק דרך scrape_campus_gov() — ראה להלן
    # סרטונים והדרכות נסרקים דרך האייג'נט — ראה scrape_youtube_hebrew()
}

MAX_ITEMS_PER_SOURCE = 10
MAX_YOUTUBE_PER_QUERY = 6

# שאילתות YouTube לפי טאב
YOUTUBE_QUERIES = {
    "סרטונים": [
        "בינה מלאכותית כלים עברית",
        "ChatGPT עברית הדרכה",
        "Gemini AI עברית",
        "AI ישראל סרטון",
    ],
    "הדרכות": [
        "קורס בינה מלאכותית עברית",
        "הדרכת ChatGPT עברית",
        "וובינר AI ישראל",
        "למידת מכונה עברית",
    ],
}

_YT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

# Regex to pull first <img src="..."> from HTML
_IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)


def parse_date(entry):
    for field in ("published_parsed", "updated_parsed"):
        val = getattr(entry, field, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def extract_image(entry):
    """Try several RSS fields to find a thumbnail URL."""
    # 1. media:thumbnail
    media_thumb = getattr(entry, "media_thumbnail", None)
    if media_thumb and isinstance(media_thumb, list) and media_thumb:
        url = media_thumb[0].get("url", "")
        if url:
            return url

    # 2. media:content
    media_content = getattr(entry, "media_content", None)
    if media_content and isinstance(media_content, list):
        for mc in media_content:
            if mc.get("medium") in ("image", None) and mc.get("url", ""):
                url = mc["url"]
                if any(ext in url.lower() for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif")):
                    return url

    # 3. enclosures
    enclosures = getattr(entry, "enclosures", [])
    for enc in enclosures:
        if enc.get("type", "").startswith("image/") and enc.get("href"):
            return enc["href"]

    # 4. YouTube video thumbnail via yt:videoid
    yt_id = getattr(entry, "yt_videoid", None)
    if yt_id:
        return f"https://img.youtube.com/vi/{yt_id}/mqdefault.jpg"

    # 5. first <img> in content or summary
    for field in ("content", "summary", "description"):
        val = getattr(entry, field, None)
        if isinstance(val, list):
            val = " ".join(v.get("value", "") for v in val)
        if val:
            m = _IMG_RE.search(val)
            if m:
                url = m.group(1)
                if url.startswith("http"):
                    return url

    return None


def is_ai_related(title, summary):
    """Return True if the item mentions AI in title or summary."""
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def clean_summary(entry):
    """Return plain-text summary, strip HTML tags."""
    for field in ("summary", "description"):
        val = getattr(entry, field, None)
        if val:
            text = re.sub(r"<[^>]+>", " ", val)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                return text[:400]
    return ""


def _yt_api(query, max_results):
    """YouTube Data API v3 — דורש YOUTUBE_API_KEY."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("no YOUTUBE_API_KEY")
    q = urllib.parse.quote_plus(query)
    url = (
        "https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&type=video&maxResults={max_results}"
        f"&q={q}&relevanceLanguage=he&key={api_key}"
    )
    req = urllib.request.Request(url, headers=_YT_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8", errors="ignore"))
    items = []
    for item in data.get("items", []):
        vid = item.get("id", {}).get("videoId")
        s = item.get("snippet", {})
        if not vid:
            continue
        thumb = (s.get("thumbnails", {}).get("medium") or
                 s.get("thumbnails", {}).get("default") or {}).get("url")
        items.append({
            "title":   s.get("title", ""),
            "link":    f"https://www.youtube.com/watch?v={vid}",
            "summary": s.get("description", "")[:300],
            "date":    s.get("publishedAt", datetime.now(timezone.utc).isoformat()),
            "image":   thumb,
        })
    return items


def _yt_scrape(query, max_results):
    """Fallback — scrape YouTube search HTML (ללא API key)."""
    u = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
    req = urllib.request.Request(u, headers=_YT_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        body = r.read().decode("utf-8", errors="ignore")

    ids, titles = [], []
    for m in re.finditer(r"/watch\?v=([A-Za-z0-9_-]{11})", body):
        vid = m.group(1)
        if vid not in ids:
            ids.append(vid)
        if len(ids) >= max_results:
            break

    for m in re.finditer(r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]\}', body):
        titles.append(m.group(1))

    items = []
    for i, vid in enumerate(ids):
        title = titles[i] if i < len(titles) else query
        items.append({
            "title":   title,
            "link":    f"https://www.youtube.com/watch?v={vid}",
            "summary": "",
            "date":    datetime.now(timezone.utc).isoformat(),
            "image":   f"https://img.youtube.com/vi/{vid}/mqdefault.jpg",
        })
    return items


_CAMPUS_SITEMAPS = [
    "https://campus.gov.il/course-sitemap.xml",
    "https://campus.gov.il/course-sitemap2.xml",
    "https://campus.gov.il/course-sitemap3.xml",
]

_CAMPUS_AI_SLUGS = [
    "ai", "beai", "leadai", "aiedu", "chatgpt", "gpt", "llm",
    "machinelearning", "deeplearning", "generative",
]

_META_DESC = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{10,})["\']', re.IGNORECASE)
_META_DESC2 = re.compile(r'<meta[^>]+content=["\']([^"\']{10,})["\'][^>]+name=["\']description["\']', re.IGNORECASE)
_TITLE_RE   = re.compile(r'<title[^>]*>([^<]+)</title>', re.IGNORECASE)
_H1_RE      = re.compile(r'<h1[^>]*>([^<]+)</h1>', re.IGNORECASE)


def _campus_fetch_page(url):
    """Fetch a campus.gov.il course page and return (title, description)."""
    try:
        req = urllib.request.Request(url, headers=_YT_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", errors="ignore")
        # title: prefer h1, fallback to <title>
        h1 = _H1_RE.search(body)
        title_tag = _TITLE_RE.search(body)
        title = (h1.group(1) if h1 else (title_tag.group(1) if title_tag else "")).strip()
        title = re.sub(r"\s*[-|].*$", "", title).strip()  # cut " | campus.gov.il"
        # description
        desc = ""
        for pat in (_META_DESC, _META_DESC2):
            m = pat.search(body)
            if m:
                desc = m.group(1).strip()[:400]
                break
        return title, desc
    except Exception as e:
        return "", ""


def scrape_campus_gov(results):
    """סורק קמפוס GOV ומחזיר קורסי AI רלוונטיים."""
    print("\nסורק קמפוס GOV...")
    seen_urls = set()
    course_urls = []

    # שלב 1: איסוף URLs מה-sitemaps
    seen_slugs = set()
    for sitemap_url in _CAMPUS_SITEMAPS:
        try:
            req = urllib.request.Request(sitemap_url, headers=_YT_HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                xml = r.read().decode("utf-8", errors="ignore")
            for m in re.finditer(r"<loc>([^<]+)</loc>", xml):
                url = m.group(1).strip()
                # Hebrew only (suffix -he)
                if not url.rstrip("/").endswith("-he"):
                    continue
                slug = url.rstrip("/").split("/")[-1].lower()
                base_slug = re.sub(r"-he$", "", slug)
                if url not in seen_urls and base_slug not in seen_slugs and any(kw in slug for kw in _CAMPUS_AI_SLUGS):
                    seen_urls.add(url)
                    seen_slugs.add(base_slug)
                    course_urls.append(url)
        except Exception as e:
            print(f"  ERR sitemap {sitemap_url}: {e}")

    print(f"  נמצאו {len(course_urls)} קורסים רלוונטיים")

    # שלב 2: שליפת פרטים לכל קורס — רק אם כותרת/תיאור קשורים ל-AI
    items = []
    for url in course_urls:
        if len(items) >= MAX_ITEMS_PER_SOURCE:
            break
        title, desc = _campus_fetch_page(url)
        if not title:
            continue
        if not is_ai_related(title, desc):
            continue
        items.append({
            "title":   title,
            "link":    url,
            "summary": desc,
            "date":    datetime.now(timezone.utc).isoformat(),
            "image":   None,
        })
        print(f"  + {title[:60]}")

    results["קמפוס GOV"] = {
        "url":        "https://campus.gov.il",
        "category":   "קמפוס GOV",
        "items":      items,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "error":      None,
    }
    print(f"  קמפוס GOV: {len(items)} קורסים")


def scrape_youtube_hebrew(results):
    """מריץ את האייג'נט: שולף סרטונים והדרכות בעברית מ-YouTube."""
    seen = set()
    for category, queries in YOUTUBE_QUERIES.items():
        items = []
        for query in queries:
            if len(items) >= MAX_ITEMS_PER_SOURCE:
                break
            print(f"  YouTube ({category}): {query}")
            try:
                fetched = _yt_api(query, MAX_YOUTUBE_PER_QUERY)
                print(f"    API: {len(fetched)} תוצאות")
            except Exception as e:
                print(f"    API failed ({e}), scraping...")
                try:
                    fetched = _yt_scrape(query, MAX_YOUTUBE_PER_QUERY)
                    print(f"    Scrape: {len(fetched)} תוצאות")
                except Exception as e2:
                    print(f"    Scrape failed: {e2}")
                    fetched = []

            for item in fetched:
                if item["link"] not in seen:
                    seen.add(item["link"])
                    items.append(item)

        results[f"YouTube — {category}"] = {
            "url":        "https://www.youtube.com",
            "category":   category,
            "items":      items[:MAX_ITEMS_PER_SOURCE],
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "error":      None,
        }
        print(f"  YouTube {category}: {len(items[:MAX_ITEMS_PER_SOURCE])} פריטים")


HISTORY_DAYS = 14  # שומר פריטים עד 14 יום אחורה


def merge_with_history(existing, new_results):
    """מאחד תוצאות חדשות עם היסטוריה, מסנן פריטים ישנים מ-14+ יום."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)
    merged = {}

    all_sources = set(existing) | set(new_results)
    for source in all_sources:
        base = new_results.get(source) or existing.get(source, {})
        old_items = {i["link"]: i for i in existing.get(source, {}).get("items", []) if i.get("link")}
        new_items = {i["link"]: i for i in new_results.get(source, {}).get("items", []) if i.get("link")}

        # new_items גוברים על old_items לאותו link
        combined = {**old_items, **new_items}

        # סינון לפי גיל
        kept = []
        for item in combined.values():
            try:
                dt = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
                if dt >= cutoff:
                    kept.append(item)
            except Exception:
                kept.append(item)

        kept.sort(key=lambda x: x.get("date", ""), reverse=True)
        merged[source] = {**base, "items": kept}

    return merged


def scrape():
    results = {}
    for name, meta in FEEDS.items():
        print(f"סורק: {name}...")
        try:
            feed = feedparser.parse(meta["url"])
            items = []
            do_filter    = meta.get("filter_ai", False)
            extra_kws    = [k.lower() for k in meta.get("filter_extra", [])]
            for entry in feed.entries:
                if len(items) >= MAX_ITEMS_PER_SOURCE:
                    break
                title   = entry.get("title", "ללא כותרת")
                summary = clean_summary(entry)
                if do_filter and not is_ai_related(title, summary):
                    continue
                if extra_kws:
                    text = (title + " " + summary).lower()
                    if not any(kw in text for kw in extra_kws):
                        continue
                items.append({
                    "title":   title,
                    "link":    entry.get("link", ""),
                    "summary": summary,
                    "date":    parse_date(entry),
                    "image":   extract_image(entry),
                })
            results[name] = {
                "url":        meta["url"],
                "category":   meta["category"],
                "items":      items,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "error":      None,
            }
            print(f"  OK {len(items)} פריטים")
        except Exception as e:
            results[name] = {
                "url":        meta["url"],
                "category":   meta["category"],
                "items":      [],
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "error":      str(e),
            }
            print(f"  ERR {e}")

    # ── קמפוס GOV ────────────────────────────────────────────────────────
    scrape_campus_gov(results)

    # ── אייג'נט YouTube בעברית ───────────────────────────────────────────
    print("\nמריץ אייג'נט YouTube עברית...")
    scrape_youtube_hebrew(results)

    # ── מיזוג עם היסטוריה ────────────────────────────────────────────────
    out = ROOT / "data.json"
    existing = {}
    if out.exists():
        try:
            existing = json.loads(out.read_text(encoding="utf-8"))
        except Exception:
            pass
    results = merge_with_history(existing, results)

    total = sum(len(s.get("items", [])) for s in results.values())
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nנשמר ל-{out} ({total} פריטים כולל היסטוריה)")


if __name__ == "__main__":
    scrape()
