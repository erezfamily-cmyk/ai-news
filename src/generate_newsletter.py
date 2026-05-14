import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data.json"
OUT_TXT = ROOT / "newsletter.txt"
OUT_MD = ROOT / "newsletter.md"

def generate_newsletter():
    if not DATA_FILE.exists():
        print("data.json not found")
        return

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    all_items = []
    for source, src_data in data.items():
        for item in src_data.get("items", []):
            all_items.append({
                **item,
                "source": source,
                "category": src_data.get("category", ""),
            })

    # Sort by date descending
    all_items.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Filter hot items (last 24-48 hours)
    now = datetime.now(timezone.utc)
    recent_items = []
    for item in all_items:
        try:
            dt = datetime.fromisoformat(item.get("date", "").replace("Z", "+00:00"))
            if now - dt < timedelta(days=2):
                recent_items.append(item)
        except Exception:
            pass

    # Fallback to just the latest 5 if not enough recent items
    if len(recent_items) < 5:
        recent_items = all_items[:5]

    top_5 = recent_items[:5]

    date_str = datetime.now().strftime("%d/%m/%Y")
    
    # Text format for WhatsApp
    txt_lines = [
        f"🤖 *עדכוני AI Pulse — {date_str}* 🤖\n",
        "הנה 5 הכתבות החמות של היום בבינה מלאכותית:\n"
    ]

    for i, item in enumerate(top_5, 1):
        title = item.get("title", "")
        link = item.get("link", "")
        source = item.get("source", "")
        cat = item.get("category", "")
        
        txt_lines.append(f"{i}. *{title}*")
        txt_lines.append(f"🏷️ קטגוריה: {cat} | 📰 מקור: {source}")
        txt_lines.append(f"🔗 {link}\n")

    txt_lines.append("לקריאת כל העדכונים (כולל מחקרים, קורסים חינמיים וסרטונים), היכנסו לדשבורד שלנו:")
    txt_lines.append("👉 https://erezfamily-cmyk.github.io/ai-news/")

    OUT_TXT.write_text("\n".join(txt_lines), encoding="utf-8")
    
    # Markdown format
    md_lines = [
        f"# 🤖 עדכוני AI Pulse — {date_str}\n",
        "הנה 5 הכתבות החמות של היום בבינה מלאכותית:\n"
    ]
    for i, item in enumerate(top_5, 1):
        title = item.get("title", "")
        link = item.get("link", "")
        source = item.get("source", "")
        cat = item.get("category", "")
        md_lines.append(f"### {i}. [{title}]({link})")
        md_lines.append(f"- **קטגוריה:** {cat}")
        md_lines.append(f"- **מקור:** {source}\n")
    
    md_lines.append("---\n* [לדשבורד המלא](https://erezfamily-cmyk.github.io/ai-news/)*")
    
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    
    print(f"Newsletter generated: {OUT_TXT} and {OUT_MD}")

if __name__ == "__main__":
    generate_newsletter()
