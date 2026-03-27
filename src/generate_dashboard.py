import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data.json"
OUT_FILE = ROOT / "index.html"

CATEGORIES = ["חברות AI", "כלים ומודלים", "חדשות", "מחקר"]

CATEGORY_COLORS = {
    "חברות AI": "#6366f1",
    "כלים ומודלים": "#10b981",
    "חדשות": "#f59e0b",
    "מחקר": "#3b82f6",
}


def load_data():
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return ""


def generate():
    data = load_data()
    updated = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")

    all_items = []
    for source, src_data in data.items():
        for item in src_data.get("items", []):
            all_items.append({
                **item,
                "source": source,
                "category": src_data.get("category", ""),
            })

    all_items.sort(key=lambda x: x.get("date", ""), reverse=True)

    sources_by_cat = {}
    for name, src in data.items():
        cat = src.get("category", "אחר")
        sources_by_cat.setdefault(cat, []).append(name)

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI News Dashboard</title>
<style>
  :root {{
    --bg: #0f172a;
    --surface: #1e293b;
    --border: #334155;
    --text: #f1f5f9;
    --muted: #94a3b8;
    --accent: #6366f1;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}
  header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }}
  header h1 {{ font-size: 1.4rem; font-weight: 700; }}
  header h1 span {{ color: var(--accent); }}
  .updated {{ font-size: 12px; color: var(--muted); }}
  .filters {{ padding: 16px 24px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
  .filter-btn {{ padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border); background: transparent; color: var(--muted); cursor: pointer; font-size: 13px; transition: all .2s; }}
  .filter-btn:hover, .filter-btn.active {{ color: #fff; border-color: var(--accent); background: var(--accent); }}
  .search {{ margin-right: auto; }}
  .search input {{ background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 7px 14px; border-radius: 8px; font-size: 13px; width: 220px; }}
  .search input:focus {{ outline: none; border-color: var(--accent); }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; padding: 0 24px 32px; }}
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 8px; transition: border-color .2s; }}
  .card:hover {{ border-color: var(--accent); }}
  .card-top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }}
  .cat-badge {{ font-size: 11px; padding: 2px 8px; border-radius: 10px; color: #fff; white-space: nowrap; flex-shrink: 0; }}
  .card-date {{ font-size: 11px; color: var(--muted); }}
  .card-title {{ font-size: 14px; font-weight: 600; line-height: 1.4; }}
  .card-title a {{ color: var(--text); text-decoration: none; }}
  .card-title a:hover {{ color: var(--accent); }}
  .card-summary {{ font-size: 12px; color: var(--muted); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
  .card-source {{ font-size: 11px; color: var(--muted); border-top: 1px solid var(--border); padding-top: 8px; }}
  .no-results {{ text-align: center; color: var(--muted); padding: 60px 24px; grid-column: 1/-1; }}
  @media(max-width:600px) {{ .grid {{ grid-template-columns: 1fr; padding: 0 12px 24px; }} header, .filters {{ padding: 12px; }} }}
</style>
</head>
<body>

<header>
  <h1>🤖 <span>AI</span> News Dashboard</h1>
  <span class="updated">עודכן: {updated} UTC</span>
</header>

<div class="filters">
  <button class="filter-btn active" onclick="filterCat('all')">הכל ({len(all_items)})</button>
"""

    for cat in CATEGORIES:
        count = sum(1 for i in all_items if i.get("category") == cat)
        if count:
            color = CATEGORY_COLORS.get(cat, "#6366f1")
            html += f'  <button class="filter-btn" onclick="filterCat(\'{cat}\')" style="--cat:{color}">{cat} ({count})</button>\n'

    html += """  <div class="search"><input type="text" id="search" placeholder="חיפוש..." oninput="doSearch(this.value)"></div>
</div>

<div class="grid" id="grid">
"""

    colors_js = json.dumps(CATEGORY_COLORS)

    for item in all_items:
        cat = item.get("category", "")
        color = CATEGORY_COLORS.get(cat, "#6366f1")
        date_str = format_date(item.get("date", ""))
        summary = item.get("summary", "").replace("<", "&lt;").replace(">", "&gt;")
        title = item.get("title", "").replace("<", "&lt;").replace(">", "&gt;")
        link = item.get("link", "#")
        source = item.get("source", "").replace("<", "&lt;")

        html += f"""  <div class="card" data-cat="{cat}" data-text="{title.lower()} {source.lower()}">
    <div class="card-top">
      <span class="cat-badge" style="background:{color}">{cat}</span>
      <span class="card-date">{date_str}</span>
    </div>
    <div class="card-title"><a href="{link}" target="_blank" rel="noopener">{title}</a></div>
    <div class="card-summary">{summary}</div>
    <div class="card-source">{source}</div>
  </div>
"""

    html += f"""</div>

<script>
let activecat = 'all';
let searchVal = '';
const colors = {colors_js};

function filterCat(cat) {{
  activecat = cat;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  render();
}}

function doSearch(val) {{
  searchVal = val.toLowerCase();
  render();
}}

function render() {{
  const cards = document.querySelectorAll('.card');
  let visible = 0;
  cards.forEach(c => {{
    const matchCat = activecat === 'all' || c.dataset.cat === activecat;
    const matchSearch = !searchVal || c.dataset.text.includes(searchVal);
    c.style.display = matchCat && matchSearch ? '' : 'none';
    if (matchCat && matchSearch) visible++;
  }});
  const nr = document.querySelector('.no-results');
  if (nr) nr.style.display = visible === 0 ? '' : 'none';
}}
</script>

</body>
</html>"""

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"נוצר index.html ({len(all_items)} פריטים)")


if __name__ == "__main__":
    generate()
