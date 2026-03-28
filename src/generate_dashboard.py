import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data.json"
OUT_FILE = ROOT / "index.html"

# ── טאבים ראשיים: כל טאב = רשימת קטגוריות שהוא מציג ──────────────────────
TABS = [
    {"id": "news",     "label": "חדשות",         "icon": "newspaper",         "cats": ["חדשות טכנולוגיה", "AI ישראל"]},
    {"id": "gov",      "label": "מחשוב וממשל",   "icon": "account_balance",   "cats": ["מחשוב וממשל"]},
    {"id": "campus",   "label": "קמפוס GOV",      "icon": "school",            "cats": ["קמפוס GOV"]},
    {"id": "videos",   "label": "סרטונים",        "icon": "play_circle",       "cats": ["סרטונים"]},
    {"id": "guides",   "label": "הדרכות",         "icon": "cast_for_education","cats": ["הדרכות"]},
]

CATEGORY_STYLE = {
    "חדשות טכנולוגיה": {"color": "#f59e0b", "rgb": "245,158,11",  "bg": "rgba(245,158,11,.1)",  "icon": "newspaper"},
    "AI ישראל":        {"color": "#a78bfa", "rgb": "167,139,250", "bg": "rgba(167,139,250,.1)", "icon": "public"},
    "מחשוב וממשל":     {"color": "#34d399", "rgb": "52,211,153",  "bg": "rgba(52,211,153,.1)",  "icon": "account_balance"},
    "קמפוס GOV":       {"color": "#fb923c", "rgb": "251,146,60",  "bg": "rgba(251,146,60,.1)",  "icon": "school"},
    "כלים ומודלים":    {"color": "#34d399", "rgb": "52,211,153",  "bg": "rgba(52,211,153,.1)",  "icon": "build"},
    "מחקר":            {"color": "#60a5fa", "rgb": "96,165,250",  "bg": "rgba(96,165,250,.1)",  "icon": "science"},
    "קהילה":           {"color": "#f472b6", "rgb": "244,114,182", "bg": "rgba(244,114,182,.1)", "icon": "forum"},
    "סרטונים":         {"color": "#f87171", "rgb": "248,113,113", "bg": "rgba(248,113,113,.1)", "icon": "play_circle"},
    "הדרכות":          {"color": "#22d3ee", "rgb": "34,211,238",  "bg": "rgba(34,211,238,.1)",  "icon": "school"},
}
DEFAULT_STYLE = {"color": "#94a3b8", "rgb": "148,163,184", "bg": "rgba(148,163,184,.1)", "icon": "article"}


def load_data():
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        months = ["ינואר","פברואר","מרץ","אפריל","מאי","יוני",
                  "יולי","אוגוסט","ספטמבר","אוקטובר","נובמבר","דצמבר"]
        return f"{dt.day} {months[dt.month-1]}, {dt.year}"
    except Exception:
        return ""


def esc(s):
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")


def is_hot(iso_str):
    """Returns True if the item was published in the last 24 hours."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - dt < timedelta(hours=24)
    except Exception:
        return False


def generate():
    data = load_data()
    updated = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")

    # ── איסוף כל הפריטים ───────────────────────────────────────────────────
    all_items = []
    for source, src_data in data.items():
        raw_url = src_data.get("url", "")
        try:
            from urllib.parse import urlparse
            p = urlparse(raw_url)
            source_home = f"{p.scheme}://{p.netloc}"
        except Exception:
            source_home = raw_url
        for item in src_data.get("items", []):
            all_items.append({
                **item,
                "source":     source,
                "source_url": source_home,
                "category":   src_data.get("category", ""),
            })

    all_items.sort(key=lambda x: x.get("date", ""), reverse=True)
    total = len(all_items)

    # ── סיידבר ניווט ──────────────────────────────────────────────────────
    sidebar_nav = ""
    for t_idx, tab in enumerate(TABS):
        tab_items = [i for i in all_items if i.get("category") in tab["cats"]]
        count = len(tab_items)
        active_cls = "sb-active" if t_idx == 0 else ""
        sidebar_nav += f"""
    <button onclick="switchTabById('{esc(tab['id'])}')"
            data-sidebar="{esc(tab['id'])}"
            aria-label="{esc(tab['label'])}"
            class="sidebar-btn {active_cls}">
      <span class="material-symbols-outlined" style="font-size:22px" aria-hidden="true">{tab['icon']}</span>
      <span style="flex:1">{tab['label']}</span>
      <span class="tab-count-pill">{count}</span>
    </button>"""

    # ── Category pills لـ sidebar ──────────────────────────────────────────
    all_cats = set()
    for item in all_items:
        if item.get("category"):
            all_cats.add(item["category"])

    # build category→tab mapping for JS
    cat_tab_map = {}
    for tab in TABS:
        for cat in tab["cats"]:
            cat_tab_map[cat] = tab["id"]
    cat_tab_map_js = json.dumps(cat_tab_map, ensure_ascii=False)

    cat_pills = ""
    for cat in sorted(all_cats):
        s = CATEGORY_STYLE.get(cat, DEFAULT_STYLE)
        cat_count = len([i for i in all_items if i.get("category") == cat])
        cat_pills += f"""
      <button onclick="filterCat('{esc(cat)}')"
              data-cat="{esc(cat)}"
              class="cat-pill" style="--cat-c:{s['color']};--cat-rgb:{s['rgb']}">
        <span class="material-symbols-outlined" style="font-size:13px">{s['icon']}</span>
        {esc(cat)}
        <span class="cat-pill-count">{cat_count}</span>
      </button>"""

    # ── בניית תוכן הטאבים ─────────────────────────────────────────────────
    tabs_content = ""

    for t_idx, tab in enumerate(TABS):
        tab_id   = tab["id"]
        tab_cats = tab["cats"]
        tab_items = [i for i in all_items if i.get("category") in tab_cats]
        is_first = t_idx == 0
        display  = "" if is_first else "display:none"

        # ── Hero (פריט ראשון בטאב) ──────────────────────────────────────
        hero_html = ""
        items_to_list = tab_items

        if tab_items:
            hero = tab_items[0]
            items_to_list = tab_items[1:]
            hcat   = hero.get("category", "")
            hs     = CATEGORY_STYLE.get(hcat, DEFAULT_STYLE)
            hdate  = format_date(hero.get("date", ""))
            hsum   = esc(hero.get("summary", ""))
            htitle = esc(hero.get("title", ""))
            hlink  = esc(hero.get("link", "#"))
            hsrc   = esc(hero.get("source", ""))
            himg   = esc(hero.get("image") or "")
            hot    = is_hot(hero.get("date", ""))

            bg_style = f'background-image:url("{himg}");background-size:cover;background-position:center' if himg else f"background:linear-gradient(135deg,rgba({hs['rgb']},.15) 0%,rgba(19,22,29,0) 100%)"

            hot_badge = '<span class="hot-badge">חם</span>' if hot else ""

            hero_html = f"""
      <a href="{hlink}" target="_blank" rel="noopener"
         class="hero-card group block relative overflow-hidden rounded-2xl mb-8"
         style="{bg_style}">
        <div class="hero-overlay absolute inset-0"></div>
        {'<div class="hero-icon-bg absolute inset-0 flex items-center justify-center pointer-events-none"><span class="material-symbols-outlined" style="font-size:160px;color:' + hs['color'] + ';opacity:.04">' + hs['icon'] + '</span></div>' if not himg else ''}
        <div class="relative z-10 p-8 md:p-10 flex flex-col justify-end min-h-[340px]">
          <div class="flex items-center gap-3 mb-5 flex-wrap">
            <span class="cat-badge" style="background:rgba({hs['rgb']},.2);color:{hs['color']};border-color:rgba({hs['rgb']},.35)">
              <span class="material-symbols-outlined" style="font-size:13px">{hs['icon']}</span>
              {esc(hcat)}
            </span>
            {hot_badge}
            <span class="text-xs opacity-60" style="color:#e2e8f0">{hdate}</span>
            <span class="text-xs opacity-40 mr-auto" style="color:#e2e8f0">{hsrc}</span>
          </div>
          <h2 class="hero-title group-hover:opacity-90 transition-opacity">{htitle}</h2>
          <p class="hero-summary mt-3">{hsum}</p>
          <div class="mt-6 flex items-center gap-2 font-bold text-sm" style="color:{hs['color']}">
            <span>קרא עוד</span>
            <span class="material-symbols-outlined text-base transition-transform group-hover:-translate-x-1">arrow_forward</span>
          </div>
        </div>
      </a>"""

        # ── Article stream ──────────────────────────────────────────────
        articles_html = ""
        for item in items_to_list:
            cat     = item.get("category", "")
            s       = CATEGORY_STYLE.get(cat, DEFAULT_STYLE)
            date_s  = format_date(item.get("date", ""))
            summary = esc(item.get("summary", ""))
            title   = esc(item.get("title", ""))
            link    = esc(item.get("link", "#"))
            source  = esc(item.get("source", ""))
            src_url = esc(item.get("source_url", "#"))
            image   = esc(item.get("image") or "")
            is_video = (cat in ("סרטונים", "הדרכות"))
            hot     = is_hot(item.get("date", ""))
            hot_badge = '<span class="hot-badge">חם</span>' if hot else ""

            if image:
                media_html = f"""<div class="article-img-wrap shrink-0">
            <img src="{image}" alt="{title}" loading="lazy"
                 class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                 onerror="this.parentElement.style.display='none'"/>
          </div>"""
            else:
                media_html = f"""<div class="article-img-placeholder shrink-0"
               style="background:rgba({s['rgb']},.07);border-inline-end:3px solid {s['color']}">
            <span class="material-symbols-outlined" style="font-size:36px;color:{s['color']};opacity:.45">{s['icon']}</span>
          </div>"""

            wa_title   = (item.get("title",   "") or "")
            wa_summary = (item.get("summary", "") or "")[:220]
            wa_link    = item.get("link", "") or ""

            wa_btn = (f'<button onclick="shareWA(this)" '
                      f'data-title="{esc(wa_title)}" '
                      f'data-summary="{esc(wa_summary)}" '
                      f'data-link="{esc(wa_link)}" '
                      f'class="wa-btn" title="שתף בוואטסאפ">'
                      f'<span class="material-symbols-outlined" style="font-size:14px">share</span>'
                      f'שתף</button>')

            cta = (f'<a href="{link}" target="_blank" rel="noopener" '
                   f'class="read-btn video-btn flex items-center gap-1.5 font-bold text-sm">'
                   f'<span class="material-symbols-outlined" style="font-size:18px">play_circle</span>צפה</a>'
                   if is_video else
                   f'<a href="{link}" target="_blank" rel="noopener" onclick="markRead(this)" '
                   f'class="read-btn flex items-center gap-1.5 font-bold text-sm" style="color:{s["color"]}">'
                   f'<span>קרא עוד</span>'
                   f'<span class="material-symbols-outlined text-base transition-transform group-hover/btn:-translate-x-1">arrow_forward</span></a>')

            articles_html += f"""
      <article class="news-article group" data-link="{link}" style="--cat-color:{s['color']};--cat-rgb:{s['rgb']}">
        <div class="article-inner flex flex-col md:flex-row">
          {media_html}
          <div class="flex-1 p-5 md:p-6">
            <div class="flex items-center gap-2 mb-2.5 flex-wrap">
              <span class="cat-badge" style="background:rgba({s['rgb']},.12);color:{s['color']};border-color:rgba({s['rgb']},.25)">
                <span class="material-symbols-outlined" style="font-size:12px">{s['icon']}</span>
                {esc(cat)}
              </span>
              {hot_badge}
              <span class="text-xs" style="color:var(--muted)">{date_s}</span>
            </div>
            <h3 class="article-title mb-2">
              <a href="{link}" target="_blank" rel="noopener" onclick="markRead(this)">{title}</a>
            </h3>
            <p class="article-summary">{summary}</p>
            <div class="flex items-center justify-between gap-3 flex-wrap mt-4 pt-4" style="border-top:1px solid var(--border)">
              <div class="flex items-center gap-3">
                {cta}
                {wa_btn}
              </div>
              <a href="{src_url}" target="_blank" rel="noopener"
                 class="source-tag">{source}</a>
            </div>
          </div>
        </div>
      </article>"""

        empty = '<div class="py-24 text-center"><span class="material-symbols-outlined" style="font-size:48px;color:var(--muted)">inbox</span><p class="mt-3 text-sm" style="color:var(--muted)">אין תוכן עדיין</p></div>' if not hero_html and not articles_html else ""

        tabs_content += f"""
  <div id="tab-{esc(tab_id)}" class="tab-panel" style="{display}">
    {hero_html}
    <div class="space-y-4">{articles_html or empty}</div>
  </div>"""

    # ── Mobile bottom nav ──────────────────────────────────────────────────
    mob_nav_btns = "".join(f"""
  <button onclick="switchTabById('{esc(t['id'])}')"
          data-mob="{esc(t['id'])}"
          class="mob-nav-btn flex flex-col items-center gap-0.5 flex-1 py-2">
    <span class="material-symbols-outlined mat-icon" style="font-size:22px">{t['icon']}</span>
    <span class="mob-label" style="font-size:12px;font-weight:600">{t['label']}</span>
  </button>""" for t in TABS)

    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>AI Pulse — עדכוני בינה מלאכותית</title>
<meta name="description" content="דשבורד עדכוני AI יומי — חדשות, כלים, מחקרים וסרטונים בבינה מלאכותית"/>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Assistant:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<style>
/* ══════════════════════════════════════════════════
   TOKENS
══════════════════════════════════════════════════ */
:root {{
  --bg:        #0b0e15;
  --surface:   #111520;
  --surface2:  #171c27;
  --card:      rgba(255,255,255,0.035);
  --card-h:    rgba(255,255,255,0.06);
  --border:    rgba(255,255,255,0.07);
  --border-h:  rgba(255,255,255,0.13);
  --text:      #e2e8f0;
  --text-2:    #cbd5e1;
  --muted:     #64748b;
  --accent:    #60a5fa;
  --accent2:   #818cf8;
  --green:     #25d366;
  --red:       #ef4444;
  --font-head: 'Plus Jakarta Sans', 'Assistant', sans-serif;
  --font-body: 'Assistant', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --sidebar-w: 220px;
  --nav-h:     64px;
  --radius:    14px;
  --radius-sm: 8px;
}}

*, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
html {{ scroll-behavior:smooth; }}

body {{
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  direction: rtl;
  overflow-x: hidden;
}}

/* dot grid background */
body::before {{
  content:'';
  position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image: radial-gradient(rgba(96,165,250,.055) 1px, transparent 1px);
  background-size: 30px 30px;
}}

/* ambient glow */
body::after {{
  content:'';
  position:fixed; top:-250px; right:-250px;
  width:700px; height:700px; z-index:0; pointer-events:none;
  background: radial-gradient(circle, rgba(129,140,248,.05) 0%, transparent 65%);
}}

.material-symbols-outlined {{
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
  vertical-align:middle;
}}

/* ── SCROLLBAR ─────────────────────────────────── */
::-webkit-scrollbar {{ width:4px; height:4px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
::-webkit-scrollbar-thumb {{ background:var(--border-h); border-radius:4px; }}
.no-scrollbar::-webkit-scrollbar {{ display:none; }}
.no-scrollbar {{ -ms-overflow-style:none; scrollbar-width:none; }}

/* ══════════════════════════════════════════════════
   TOP NAV
══════════════════════════════════════════════════ */
.top-nav {{
  position:fixed; top:0; width:100%; z-index:100;
  height: var(--nav-h);
  background: rgba(11,14,21,.88);
  backdrop-filter: blur(28px) saturate(180%);
  border-bottom: 1px solid var(--border);
  display:flex; align-items:center;
  padding: 0 20px;
  gap: 16px;
}}

.logo-wrap {{
  display:flex; align-items:center; gap:10px;
  flex-shrink:0;
}}

.logo-icon {{
  width:36px; height:36px; border-radius:10px;
  background: linear-gradient(135deg,#60a5fa,#818cf8);
  box-shadow: 0 0 20px rgba(96,165,250,.28);
  display:flex; align-items:center; justify-content:center;
  color:#fff;
}}

.logo-text {{
  font-family: var(--font-head);
  font-size:1rem; font-weight:800; letter-spacing:-.3px;
  background: linear-gradient(90deg,#e2e8f0 30%,#60a5fa);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}}

.live-badge {{
  display:flex; align-items:center; gap:6px;
  background: rgba(239,68,68,.1);
  border: 1px solid rgba(239,68,68,.25);
  border-radius:999px;
  padding: 3px 10px;
  font-family: var(--font-mono);
  font-size:10px; color:#ef4444; letter-spacing:1px;
  flex-shrink:0;
}}

.live-dot {{
  width:6px; height:6px; border-radius:50%;
  background:#ef4444;
  animation: blink 1.8s ease-in-out infinite;
  display:inline-block;
}}

.nav-end {{
  margin-right:auto;
  display:flex; align-items:center; gap:12px;
}}

.search-wrap {{ position:relative; }}

.search-input {{
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 36px 8px 14px;
  border-radius: 10px;
  font-size:13px; font-family:var(--font-body);
  width:200px; direction:rtl;
  transition: all .25s;
}}
.search-input:focus {{
  outline:none;
  border-color: var(--accent);
  background: rgba(96,165,250,.06);
  box-shadow: 0 0 0 3px rgba(96,165,250,.12);
  width:240px;
}}
.search-input::placeholder {{ color:var(--muted); }}

.search-icon {{
  position:absolute; right:11px; top:50%; transform:translateY(-50%);
  color:var(--muted); font-size:15px; pointer-events:none;
}}

.updated-ts {{
  font-family: var(--font-mono);
  font-size:11px; color:var(--muted);
  display:none;
}}
@media(min-width:900px) {{ .updated-ts {{ display:block; }} }}

/* ══════════════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════════════ */
.sidebar {{
  position:fixed; right:0; top:0;
  width: var(--sidebar-w);
  height:100%;
  background: var(--surface);
  border-inline-start: 1px solid var(--border);
  display:flex; flex-direction:column;
  padding: calc(var(--nav-h) + 20px) 12px 20px;
  z-index:40;
  display:none;
}}
@media(min-width:1100px) {{ .sidebar {{ display:flex; }} }}

.sidebar-section-label {{
  font-family: var(--font-head);
  font-size:10px; font-weight:700;
  text-transform:uppercase; letter-spacing:.12em;
  color:var(--muted);
  padding: 0 8px 10px;
}}

.sidebar-btn {{
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  color: var(--muted);
  border-radius: var(--radius-sm);
  border:none; background:none;
  cursor:pointer;
  transition: all .2s;
  padding: 12px 14px;
  width: 100%;
  text-align: right;
  display: flex;
  align-items: center;
  gap: 10px;
}}
.sidebar-btn:hover {{
  background: var(--card-h);
  color: var(--text-2);
}}
.sidebar-btn.sb-active {{
  background: rgba(96,165,250,.1);
  color: var(--accent);
  box-shadow: inset 0 0 0 1px rgba(96,165,250,.2);
}}
.sidebar-btn.sb-active .material-symbols-outlined {{
  font-variation-settings:'FILL' 1,'wght' 500,'GRAD' 0,'opsz' 24;
}}

.tab-count-pill {{
  font-size:10px; font-family:var(--font-mono);
  background: rgba(255,255,255,.07);
  color: var(--muted);
  padding: 1px 7px; border-radius:999px;
}}
.sb-active .tab-count-pill {{
  background: rgba(96,165,250,.15);
  color: var(--accent);
}}

/* ── Sidebar category pills ──────────────────────── */
.sidebar-cats {{
  display:flex; flex-direction:column; gap:2px;
  flex: 1; overflow-y:auto; padding-top:6px;
}}

.cat-pill {{
  display:flex; align-items:center; gap:6px;
  padding: 6px 10px; border-radius:var(--radius-sm);
  border: 1px solid transparent;
  background: none;
  cursor:pointer;
  color: var(--muted);
  font-size:14px; font-family:var(--font-body); font-weight:500;
  text-align:right; width:100%;
  transition: all .2s;
}}
.cat-pill:hover {{
  background: rgba(var(--cat-rgb),.08);
  color: var(--cat-c);
  border-color: rgba(var(--cat-rgb),.2);
}}
.cat-pill.active {{
  background: rgba(var(--cat-rgb),.12);
  color: var(--cat-c);
  border-color: rgba(var(--cat-rgb),.3);
  font-weight:600;
}}

.cat-pill-count {{
  margin-right:auto;
  font-size:10px; font-family:var(--font-mono);
  background: rgba(255,255,255,.06);
  color:var(--muted);
  padding:0 5px; border-radius:999px;
}}
.cat-pill.active .cat-pill-count {{
  background: rgba(var(--cat-rgb),.2);
  color: var(--cat-c);
}}

/* ── Sidebar footer ──────────────────────────────── */
.sidebar-footer {{
  border-top: 1px solid var(--border);
  padding-top: 14px;
  margin-top:12px;
}}

.sidebar-stat {{
  font-family: var(--font-mono);
  font-size:11px; color:var(--muted);
  padding: 4px 8px;
}}

/* ══════════════════════════════════════════════════
   TABS NAV (horizontal, under header on mobile/md)
══════════════════════════════════════════════════ */
.tabs-bar {{
  position:sticky; top:var(--nav-h); z-index:90;
  background: rgba(11,14,21,.88);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  display:flex; gap:0;
  overflow-x:auto;
  padding: 0 16px;
}}
@media(min-width:1100px) {{ .tabs-bar {{ display:none; }} }}

.tab-btn {{
  font-family:var(--font-body);
  color:var(--muted);
  border:none; background:none;
  border-bottom: 2px solid transparent;
  padding: 14px 16px;
  font-size:13px; font-weight:600;
  cursor:pointer;
  display:flex; align-items:center; gap:6px;
  white-space:nowrap;
  transition: all .2s;
}}
.tab-btn:hover {{ color:var(--text-2); }}
.tab-btn.tab-active {{
  color: var(--accent) !important;
  border-color: var(--accent) !important;
}}
.tab-btn .badge-sm {{
  font-size:10px; font-family:var(--font-mono);
  background: rgba(255,255,255,.07);
  color:var(--muted);
  padding:1px 6px; border-radius:999px;
}}
.tab-btn.tab-active .badge-sm {{
  background: rgba(96,165,250,.15);
  color:var(--accent);
}}

/* ══════════════════════════════════════════════════
   MAIN
══════════════════════════════════════════════════ */
.main-content {{
  padding-top: var(--nav-h);
  min-height: 100vh;
  position:relative; z-index:10;
}}
@media(min-width:1100px) {{
  .main-content {{ margin-right: var(--sidebar-w); }}
}}

.content-inner {{
  max-width:840px;
  margin:0 auto;
  padding: 40px 28px 100px;
}}

.tab-panel {{
  padding-top: 12px;
}}

/* ── Page header ────────────────────────────────── */
.page-header {{
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}}

.page-title {{
  font-family: var(--font-head);
  font-size:clamp(1.5rem, 4vw, 2.1rem);
  font-weight:800; letter-spacing:-.4px;
  background: linear-gradient(90deg,#e2e8f0 50%,#60a5fa);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  line-height:1.2;
}}

.page-sub {{
  font-size:13px; color:var(--muted); margin-top:6px;
}}

/* ══════════════════════════════════════════════════
   HERO CARD
══════════════════════════════════════════════════ */
.hero-card {{
  border-radius: var(--radius);
  border: 1px solid var(--border);
  overflow:hidden;
  display:block;
  text-decoration:none;
  transition: transform .3s, box-shadow .3s;
  position:relative;
}}
.hero-card:hover {{
  transform: translateY(-3px);
  box-shadow: 0 28px 72px rgba(0,0,0,.55);
}}

.hero-overlay {{
  background: linear-gradient(to top, rgba(0,0,0,.88) 0%, rgba(0,0,0,.3) 55%, rgba(0,0,0,.05) 100%);
}}

.hero-title {{
  font-family: var(--font-head);
  font-size:clamp(1.25rem, 3vw, 1.75rem);
  font-weight:800; line-height:1.3;
  color:#fff;
}}

.hero-summary {{
  font-size:14px; color:rgba(255,255,255,.72);
  line-height:1.65;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
  max-width:600px;
}}

/* ══════════════════════════════════════════════════
   CATEGORY BADGE
══════════════════════════════════════════════════ */
.cat-badge {{
  display:inline-flex; align-items:center; gap:4px;
  font-size:10px; font-weight:700; letter-spacing:.04em;
  padding: 3px 9px; border-radius:999px;
  border: 1px solid;
  white-space:nowrap;
}}

/* ══════════════════════════════════════════════════
   ARTICLE CARD
══════════════════════════════════════════════════ */
.news-article {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow:hidden;
  transition: transform .25s, box-shadow .25s, border-color .25s, background .25s;
  animation: fadeUp .35s ease both;
  position:relative;
}}
.news-article::before {{
  content:'';
  position:absolute; top:0; right:0; left:0; height:2px;
  background: var(--cat-color, var(--accent));
  opacity:.65;
}}
.news-article:hover {{
  background: var(--card-h);
  border-color: var(--border-h);
  transform: translateY(-2px);
  box-shadow: 0 18px 48px rgba(0,0,0,.4);
}}
.news-article.is-read {{ opacity:.55; }}
.news-article.is-read:hover {{ opacity:.8; }}

.article-img-wrap {{
  width:200px; flex-shrink:0;
  height:160px;
  overflow:hidden;
}}
@media(max-width:767px) {{
  .article-img-wrap {{ width:100%; height:180px; }}
  .article-img-placeholder {{ width:100% !important; height:120px !important; }}
}}

.article-img-placeholder {{
  width:160px; height:160px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center;
}}

.article-title {{
  font-family: var(--font-head);
  font-size:15px; font-weight:700; line-height:1.5;
  color:var(--text);
}}
.article-title a {{
  color:inherit; text-decoration:none;
  transition: color .2s;
}}
.article-title a:hover {{ color:var(--cat-color, var(--accent)); }}

.article-summary {{
  font-size:13px; color:var(--muted); line-height:1.65;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
}}

.source-tag {{
  font-size:11px; color:var(--muted);
  text-decoration:none; transition: color .2s;
  font-family:var(--font-mono);
}}
.source-tag:hover {{ color:var(--text-2); }}

/* ══════════════════════════════════════════════════
   READ BTN / WA BTN
══════════════════════════════════════════════════ */
.read-btn {{
  display:inline-flex; align-items:center; gap:6px;
  font-size:12px; font-weight:700;
  text-decoration:none; transition: opacity .2s;
}}
.read-btn:hover {{ opacity:.8; }}

.video-btn {{ color:#f87171 !important; }}

.wa-btn {{
  display:inline-flex; align-items:center; gap:5px;
  font-size:12px; font-weight:700;
  padding: 5px 10px; border-radius:8px;
  border: 1px solid rgba(37,211,102,.25);
  background: rgba(37,211,102,.08);
  color: #25d366;
  cursor:pointer; transition: all .2s;
}}
.wa-btn:hover {{
  background: rgba(37,211,102,.18);
  border-color: rgba(37,211,102,.45);
  transform: scale(1.04);
}}

/* ══════════════════════════════════════════════════
   HOT BADGE
══════════════════════════════════════════════════ */
.hot-badge {{
  display:inline-flex; align-items:center;
  background: rgba(239,68,68,.14);
  border: 1px solid rgba(239,68,68,.28);
  color: #f87171;
  font-size:10px; font-weight:800;
  padding: 1px 7px; border-radius:999px;
  letter-spacing:.05em;
  animation: blink 2.5s ease-in-out infinite;
}}

/* ══════════════════════════════════════════════════
   WHATSAPP MODAL
══════════════════════════════════════════════════ */
#wa-modal {{
  display:none;
  position:fixed; inset:0; z-index:200;
  align-items:center; justify-content:center;
  background: rgba(0,0,0,.7);
  backdrop-filter: blur(8px);
  padding:16px;
}}
#wa-modal.open {{ display:flex; }}
#wa-modal-box {{
  background:#151a27;
  border: 1px solid rgba(37,211,102,.2);
  border-radius:20px;
  width:100%; max-width:480px;
  padding:28px;
  box-shadow: 0 40px 80px rgba(0,0,0,.7);
  animation: fadeUp .2s ease;
}}
#wa-text {{
  width:100%; min-height:180px;
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.1);
  border-radius:12px;
  color:#e2e8f0;
  font-family:var(--font-body); font-size:14px; line-height:1.7;
  padding:14px; resize:vertical; direction:rtl; outline:none;
  transition:border-color .2s;
}}
#wa-text:focus {{ border-color:rgba(37,211,102,.4); }}
.wa-modal-send {{
  background:#25d366; color:#fff;
  border:none; border-radius:12px;
  padding:11px 22px;
  font-family:var(--font-body); font-size:15px; font-weight:700;
  cursor:pointer; display:flex; align-items:center; gap:8px;
  transition:background .2s, transform .15s;
}}
.wa-modal-send:hover {{ background:#1ebe5d; transform:scale(1.03); }}
.wa-modal-copy {{
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.12);
  color:#e2e8f0; border-radius:12px;
  padding:11px 18px;
  font-family:var(--font-body); font-size:14px; font-weight:600;
  cursor:pointer; display:flex; align-items:center; gap:6px;
  transition:background .2s;
}}
.wa-modal-copy:hover {{ background:rgba(255,255,255,.1); }}
.wa-modal-copy.copied {{ color:#25d366; border-color:rgba(37,211,102,.3); }}

/* ══════════════════════════════════════════════════
   MOBILE BOTTOM NAV
══════════════════════════════════════════════════ */
.mob-nav {{
  background: rgba(11,14,21,.96);
  border-top: 1px solid var(--border);
  backdrop-filter: blur(20px);
}}
.mob-nav-btn {{ color:var(--muted); transition:color .2s; border:none; background:none; cursor:pointer; }}
.mob-nav-btn.mob-active .mat-icon {{
  color:var(--accent);
  font-variation-settings:'FILL' 1,'wght' 600,'GRAD' 0,'opsz' 24;
}}
.mob-nav-btn.mob-active .mob-label {{ color:var(--accent); font-weight:700; }}

@media(max-width:1099px) {{ body {{ padding-bottom:64px; }} }}

/* ══════════════════════════════════════════════════
   ANIMATIONS
══════════════════════════════════════════════════ */
@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(14px); }}
  to   {{ opacity:1; transform:translateY(0); }}
}}
@keyframes blink {{
  0%,100% {{ opacity:1; transform:scale(1); }}
  50%      {{ opacity:.4; transform:scale(.75); }}
}}
</style>
</head>
<body>

<!-- ══════ TOP NAV ══════ -->
<nav class="top-nav">
  <div class="logo-wrap">
    <div class="logo-icon">
      <span class="material-symbols-outlined" style="font-size:18px">psychology</span>
    </div>
    <span class="logo-text">AI Pulse</span>
  </div>
  <div class="live-badge">
    <span class="live-dot"></span>
    LIVE
  </div>
  <div class="nav-end">
    <span class="updated-ts">עודכן {updated}</span>
    <div class="search-wrap">
      <span class="material-symbols-outlined search-icon">search</span>
      <input id="search" type="text" placeholder="חיפוש..." oninput="filterSearch()"
             aria-label="חיפוש בכתבות" class="search-input"/>
    </div>
  </div>
</nav>

<!-- ══════ SIDEBAR ══════ -->
<aside class="sidebar">
  <p class="sidebar-section-label">ניווט</p>
  <nav style="display:flex;flex-direction:column;gap:2px;margin-bottom:20px">
{sidebar_nav}
  </nav>

  <p class="sidebar-section-label" style="margin-top:8px">קטגוריות</p>
  <div class="sidebar-cats no-scrollbar">
    <button onclick="filterCat('all')" data-cat="all"
            class="cat-pill active" style="--cat-c:var(--accent);--cat-rgb:96,165,250">
      <span class="material-symbols-outlined" style="font-size:13px">apps</span>
      הכל
      <span class="cat-pill-count">{total}</span>
    </button>
{cat_pills}
  </div>

  <div class="sidebar-footer">
    <p class="sidebar-stat">{total} פריטים סה"כ</p>
    <p class="sidebar-stat" style="font-size:10px">{updated} UTC</p>
  </div>
</aside>

<!-- ══════ TABS BAR (mobile/md only) ══════ -->
<div class="tabs-bar no-scrollbar">
{"".join(f'''
  <button onclick="switchTab(this,'{esc(t['id'])}')"
          data-tab="{esc(t['id'])}"
          class="tab-btn {'tab-active' if i==0 else ''}">
    <span class="material-symbols-outlined" style="font-size:16px">{t['icon']}</span>
    {t['label']}
    <span class="badge-sm">{len([x for x in all_items if x.get('category') in t['cats']])}</span>
  </button>''' for i,t in enumerate(TABS))}
</div>

<!-- ══════ MAIN ══════ -->
<main class="main-content">
  <div class="content-inner">

    <header class="page-header">
      <h1 class="page-title">עדכוני בינה מלאכותית</h1>
      <p class="page-sub">{total} פריטים · מתעדכן יומית בשעה 09:00</p>
    </header>

    <!-- TABS CONTENT -->
    <div id="tabs-content">
{tabs_content}
    </div>

  </div>
</main>

<!-- ══════ WHATSAPP MODAL ══════ -->
<div id="wa-modal" onclick="if(event.target===this)closeWA()">
  <div id="wa-modal-box">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:8px">
        <span class="material-symbols-outlined" style="color:#25d366;font-size:22px">share</span>
        <span style="font-weight:700;font-size:15px;color:#e2e8f0">פוסט לוואטסאפ</span>
      </div>
      <button onclick="closeWA()" style="color:var(--muted);background:none;border:none;cursor:pointer;font-size:22px;line-height:1">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>
    <p style="font-size:12px;color:var(--muted);margin-bottom:10px">ערוך את הטקסט לפני השליחה:</p>
    <textarea id="wa-text" spellcheck="false"></textarea>
    <div style="display:flex;gap:10px;margin-top:16px;justify-content:flex-end">
      <button class="wa-modal-copy" onclick="copyWA(this)">
        <span class="material-symbols-outlined" style="font-size:16px">content_copy</span>
        העתק
      </button>
      <button class="wa-modal-send" onclick="sendWA()">
        <span class="material-symbols-outlined" style="font-size:18px">send</span>
        פתח בוואטסאפ
      </button>
    </div>
  </div>
</div>

<!-- ══════ MOBILE BOTTOM NAV ══════ -->
<nav class="mob-nav lg:hidden fixed bottom-0 inset-x-0 z-50 flex justify-around items-center h-[60px]">
{mob_nav_btns}
</nav>

<script>
// ── TAB SWITCHING ──────────────────────────────────────────────────────
function switchTabById(tabId) {{
  const btn = document.querySelector('.tab-btn[data-tab="' + tabId + '"]');
  switchTab(btn, tabId);
}}

function switchTab(btn, tabId) {{
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('tab-active'));
  if (btn?.classList?.contains('tab-btn')) btn.classList.add('tab-active');

  document.querySelectorAll('.sidebar-btn').forEach(b => {{
    b.classList.toggle('sb-active', b.dataset.sidebar === tabId);
  }});

  document.querySelectorAll('.mob-nav-btn').forEach(b => {{
    b.classList.toggle('mob-active', b.dataset.mob === tabId);
  }});

  document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
  const panel = document.getElementById('tab-' + tabId);
  if (panel) {{ panel.style.display = ''; filterSearch(); }}

  // reset cat filter
  document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
  const allPill = document.querySelector('.cat-pill[data-cat="all"]');
  if (allPill) allPill.classList.add('active');

  if (window.innerWidth < 1100) window.scrollTo({{top:0, behavior:'smooth'}});
}}

// ── SEARCH ────────────────────────────────────────────────────────────
function filterSearch() {{
  const q = (document.getElementById('search')?.value || '').trim().toLowerCase();
  const panel = document.querySelector('.tab-panel:not([style*="none"])');
  if (!panel) return;
  let visible = 0;
  panel.querySelectorAll('.news-article').forEach((a, i) => {{
    const h2 = a.querySelector('.article-title')?.textContent || '';
    const p  = a.querySelector('.article-summary')?.textContent || '';
    const show = !q || (h2 + ' ' + p).toLowerCase().includes(q);
    a.style.display = show ? '' : 'none';
    if (show) {{ a.style.animationDelay = Math.min(i * 40, 300) + 'ms'; visible++; }}
  }});
  // hero card
  const hero = panel.querySelector('.hero-card');
  if (hero) {{
    const show = !q || (hero.textContent||'').toLowerCase().includes(q);
    hero.style.display = show ? '' : 'none';
    if (show) visible++;
  }}
  // empty state
  let emptyEl = panel.querySelector('.search-empty');
  if (!emptyEl) {{
    emptyEl = document.createElement('div');
    emptyEl.className = 'search-empty';
    emptyEl.style.cssText = 'text-align:center;padding:60px 20px;color:var(--muted);display:none';
    emptyEl.innerHTML = '<span class="material-symbols-outlined" style="font-size:48px;display:block;margin-bottom:12px">search_off</span><p style="font-size:15px">לא נמצאו תוצאות עבור "<strong>' + q + '</strong>"</p>';
    panel.appendChild(emptyEl);
  }} else {{
    emptyEl.querySelector('strong') && (emptyEl.querySelector('strong').textContent = q);
  }}
  emptyEl.style.display = (visible === 0 && q) ? '' : 'none';
}}

// ── CATEGORY FILTER (sidebar) ─────────────────────────────────────────
const CAT_TAB = {cat_tab_map_js};

function filterCat(cat) {{
  document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
  const btn = document.querySelector('.cat-pill[data-cat="' + cat + '"]');
  if (btn) btn.classList.add('active');

  // switch to the tab that owns this category
  if (cat !== 'all' && CAT_TAB[cat]) {{
    switchTabById(CAT_TAB[cat]);
  }}

  // reset all items in the now-visible tab
  document.querySelectorAll('.tab-panel:not([style*="none"]) .news-article').forEach(a => a.style.display = '');
  document.querySelectorAll('.tab-panel:not([style*="none"]) .hero-card').forEach(h => h.style.display = '');

  // if a specific category was chosen, hide items from other cats in the same tab
  if (cat !== 'all') {{
    document.querySelectorAll('.tab-panel:not([style*="none"]) .news-article').forEach(a => {{
      const badge = a.querySelector('.cat-badge');
      const text  = badge ? badge.textContent.trim() : '';
      a.style.display = text.includes(cat) ? '' : 'none';
    }});
    document.querySelectorAll('.tab-panel:not([style*="none"]) .hero-card').forEach(h => {{
      const badge = h.querySelector('.cat-badge');
      const text  = badge ? badge.textContent.trim() : '';
      h.style.display = text.includes(cat) ? '' : 'none';
    }});
  }}
}}

// ── WHATSAPP MODAL ────────────────────────────────────────────────────
function shareWA(btn) {{
  const title   = btn.dataset.title   || '';
  const summary = btn.dataset.summary || '';
  const link    = btn.dataset.link    || '';
  const text =
    '📋 *עדכון טכנולוגיה למגזר הציבורי — משרד הבריאות*' + '\\n' +
    '──────────────────' + '\\n\\n' +
    '🔹 *' + title + '*' + '\\n\\n' +
    summary + '\\n\\n' +
    '💡 *איך זה רלוונטי לנו?*' + '\\n' +
    'ניתן להשתמש בכך ל: [רישום תהליכים / אוטומציה / ניתוח נתונים / שיפור שירות]' + '\\n\\n' +
    '🔗 לקריאה נוספת:\\n' + link + '\\n\\n' +
    '_מוזמנים להעביר לצוות IT / מחשוב / מנהל_ 🙏';
  document.getElementById('wa-text').value = text;
  document.getElementById('wa-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}}
function closeWA() {{
  document.getElementById('wa-modal').classList.remove('open');
  document.body.style.overflow = '';
}}
function sendWA() {{
  const text = document.getElementById('wa-text').value;
  window.open('https://wa.me/?text=' + encodeURIComponent(text), '_blank');
  closeWA();
}}
function copyWA(btn) {{
  const text = document.getElementById('wa-text').value;
  const done = () => {{
    btn.classList.add('copied');
    btn.querySelector('span.material-symbols-outlined').textContent = 'check';
    setTimeout(() => {{
      btn.classList.remove('copied');
      btn.querySelector('span.material-symbols-outlined').textContent = 'content_copy';
    }}, 2000);
  }};
  if (navigator.clipboard) {{
    navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
  }} else {{ fallbackCopy(text, done); }}
}}
function fallbackCopy(text, cb) {{
  const ta = document.getElementById('wa-text');
  ta.select();
  try {{ document.execCommand('copy'); cb(); }} catch(e) {{}}
}}
document.addEventListener('keydown', e => {{ if(e.key==='Escape') closeWA(); }});

// ── READ STATE ────────────────────────────────────────────────────────
const READ_KEY = 'ai_pulse_read';
function getRead() {{ try {{ return JSON.parse(localStorage.getItem(READ_KEY)||'[]'); }} catch{{return[];}} }}
function saveRead(arr) {{ localStorage.setItem(READ_KEY, JSON.stringify(arr)); }}

function markRead(anchor) {{
  const article = anchor.closest('.news-article');
  const link = article?.dataset?.link;
  if (!link) return;
  const read = getRead();
  if (!read.includes(link)) {{ read.push(link); saveRead(read); }}
  article.classList.add('is-read');
}}

function applyReadState() {{
  const read = getRead();
  document.querySelectorAll('.news-article[data-link]').forEach(el => {{
    if (read.includes(el.dataset.link)) el.classList.add('is-read');
  }});
}}

// ── INIT ──────────────────────────────────────────────────────────────
document.querySelectorAll('.sidebar-btn')[0]?.classList.add('sb-active');
document.querySelectorAll('.mob-nav-btn')[0]?.classList.add('mob-active');
document.querySelectorAll('.tab-btn')[0]?.classList.add('tab-active');
applyReadState();
</script>
</body>
</html>"""

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"index.html ({total} items)")


if __name__ == "__main__":
    generate()
