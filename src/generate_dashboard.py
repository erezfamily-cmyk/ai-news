import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data.json"
OUT_FILE = ROOT / "index.html"

# ── טאבים ראשיים: כל טאב = רשימת קטגוריות שהוא מציג ──────────────────────
TABS = [
    {"id": "חדשות",    "label": "חדשות",         "icon": "newspaper",        "cats": ["חדשות טכנולוגיה", "AI ישראל"]},
    {"id": "ממשל",     "label": "מחשוב וממשל",   "icon": "account_balance",  "cats": ["מחשוב וממשל"]},
    {"id": "סרטונים",  "label": "סרטונים",        "icon": "play_circle",      "cats": ["סרטונים"]},
    {"id": "הדרכות",   "label": "הדרכות",         "icon": "school",           "cats": ["הדרכות"]},
]

CATEGORY_STYLE = {
    "חדשות טכנולוגיה": {"color": "#f59e0b", "bg": "rgba(245,158,11,.08)", "icon": "newspaper"},
    "AI ישראל":        {"color": "#a78bfa", "bg": "rgba(167,139,250,.08)", "icon": "public"},
    "מחשוב וממשל":     {"color": "#34d399", "bg": "rgba(52,211,153,.08)",  "icon": "account_balance"},
    "כלים ומודלים":    {"color": "#34d399", "bg": "rgba(52,211,153,.08)",  "icon": "build"},
    "מחקר":            {"color": "#60a5fa", "bg": "rgba(96,165,250,.08)",  "icon": "science"},
    "קהילה":           {"color": "#f472b6", "bg": "rgba(244,114,182,.08)", "icon": "forum"},
    "סרטונים":         {"color": "#f87171", "bg": "rgba(248,113,113,.08)", "icon": "play_circle"},
    "הדרכות":          {"color": "#22d3ee", "bg": "rgba(34,211,238,.08)",  "icon": "school"},
}
DEFAULT_STYLE = {"color": "#94a3b8", "bg": "rgba(148,163,184,.08)", "icon": "article"}


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

    # ── בניית HTML לכל טאב ────────────────────────────────────────────────
    tabs_nav = ""
    tabs_content = ""

    for t_idx, tab in enumerate(TABS):
        tab_id   = tab["id"]
        tab_cats = tab["cats"]
        tab_items = [i for i in all_items if i.get("category") in tab_cats]
        count    = len(tab_items)
        is_first = t_idx == 0

        # ── כפתור טאב ──────────────────────────────────────────────────────
        active_cls = "tab-active" if is_first else ""
        tabs_nav += f"""
      <button onclick="switchTab(this,'{esc(tab_id)}')"
              data-tab="{esc(tab_id)}"
              class="tab-btn {active_cls} flex items-center gap-2 px-5 py-3 text-sm font-semibold
                     border-b-2 transition-all whitespace-nowrap">
        <span class="material-symbols-outlined" style="font-size:18px">{tab['icon']}</span>
        {tab['label']}
        <span class="tab-count text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">{count}</span>
      </button>"""

        # ── תוכן הטאב ──────────────────────────────────────────────────────
        display = "" if is_first else "display:none"
        articles = ""
        # ── Featured hero — פריט ראשון בטאב חדשות ──────────────────────────
        hero_html = ""
        items_to_list = tab_items
        if tab_id == "חדשות" and tab_items:
            hero = tab_items[0]
            items_to_list = tab_items[1:]
            hcat    = hero.get("category", "")
            hs      = CATEGORY_STYLE.get(hcat, DEFAULT_STYLE)
            hdate   = format_date(hero.get("date", ""))
            hsum    = esc(hero.get("summary", ""))
            htitle  = esc(hero.get("title", ""))
            hlink   = esc(hero.get("link", "#"))
            hsrc    = esc(hero.get("source", ""))
            himg    = esc(hero.get("image") or "")
            bg_style = f'background-image:url("{himg}");background-size:cover;background-position:center' if himg else f"background:{hs['bg']}"
            hero_html = f"""
      <a href="{hlink}" target="_blank" rel="noopener"
         class="featured-hero group relative overflow-hidden rounded-xl min-h-[320px] flex flex-col justify-end
                cursor-pointer block mb-2"
         style="{bg_style}">
        <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent"></div>
        {"" if himg else f'<div class="absolute inset-0 flex items-center justify-center opacity-10"><span class="material-symbols-outlined text-[120px]" style="color:{hs["color"]}">{hs["icon"]}</span></div>'}
        <div class="relative z-10 p-8 text-white">
          <div class="flex items-center gap-3 mb-4">
            <span class="px-3 py-1 rounded-sm text-xs font-bold uppercase tracking-wider"
                  style="background:{hs['color']}">{esc(hcat)}</span>
            <span class="text-xs opacity-70">{hdate}</span>
            <span class="text-xs opacity-50 mr-auto">{hsrc}</span>
          </div>
          <h2 class="text-2xl md:text-3xl font-extrabold leading-tight mb-3
                     group-hover:underline font-headline">{htitle}</h2>
          <p class="text-sm opacity-80 line-clamp-2 max-w-2xl">{hsum}</p>
          <div class="mt-5 flex items-center gap-2 text-sm font-bold opacity-90">
            <span>קרא עוד</span>
            <span class="material-symbols-outlined text-base
                         transition-transform group-hover:-translate-x-1">arrow_back</span>
          </div>
        </div>
      </a>"""

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
                media = f"""<div class="{'md:w-2/5' if is_video else 'md:w-1/4'} h-40 md:h-auto overflow-hidden shrink-0">
          <img src="{image}" alt="{title}" loading="lazy"
               class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
               onerror="this.parentElement.style.display='none'"/>
        </div>"""
            else:
                media = f"""<div class="md:w-1/4 h-28 md:h-auto flex items-center justify-center shrink-0"
             style="background:{s['bg']};border-left:4px solid {s['color']}">
          <span class="material-symbols-outlined" style="font-size:40px;color:{s['color']};opacity:.5">{s['icon']}</span>
        </div>"""

            wa_title   = (item.get("title",   "") or "")
            wa_summary = (item.get("summary", "") or "")[:220]
            wa_link    = item.get("link", "") or ""

            wa_btn = (f'<button onclick="shareWA(this)" '
                      f'data-title="{esc(wa_title)}" '
                      f'data-summary="{esc(wa_summary)}" '
                      f'data-link="{esc(wa_link)}" '
                      f'class="wa-btn flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-bold transition-all" '
                      f'title="שתף בוואטסאפ">'
                      f'<span class="material-symbols-outlined" style="font-size:15px">share</span>'
                      f'שתף</button>')

            cta = (f'<a href="{link}" target="_blank" rel="noopener" '
                   f'class="flex items-center gap-2 text-red-400 font-bold text-sm">'
                   f'<span class="material-symbols-outlined text-lg">play_circle</span>צפה</a>'
                   if is_video else
                   f'<a href="{link}" target="_blank" rel="noopener" onclick="markRead(this)" '
                   f'class="flex items-center gap-2 font-bold text-sm group/btn" style="color:var(--accent)">'
                   f'<span>קרא עוד</span>'
                   f'<span class="material-symbols-outlined text-base transition-transform group-hover/btn:-translate-x-1">arrow_back</span></a>')

            articles += f"""
      <article class="news-article group" data-link="{link}" style="--cat-color:{s['color']}">
        <div class="flex flex-col md:flex-row">
          {media}
          <div class="flex-1 p-5 md:p-7">
            <div class="flex items-center gap-3 mb-2 flex-wrap">
              <span class="text-xs font-bold tracking-wider uppercase" style="color:{s['color']}">{esc(cat)}</span>
              {hot_badge}
              <span class="text-xs" style="color:var(--muted)">{date_s}</span>
            </div>
            <h2 class="text-lg font-bold mb-2 leading-snug group-hover:underline transition-colors"
                style="color:var(--text)">
              <a href="{link}" target="_blank" rel="noopener" onclick="markRead(this)">{title}</a>
            </h2>
            <p class="text-sm line-clamp-2 mb-4" style="color:var(--muted)">{summary}</p>
            <div class="flex items-center justify-between gap-3 flex-wrap">
              <div class="flex items-center gap-3">
                {cta}
                {wa_btn}
              </div>
              <a href="{src_url}" target="_blank" rel="noopener"
                 class="text-xs transition-colors" style="color:var(--muted)">{source}</a>
            </div>
          </div>
        </div>
      </article>"""

        if not hero_html and not articles:
            articles = '<div class="py-20 text-center text-slate-400"><span class="material-symbols-outlined text-5xl block mb-3">inbox</span><p class="text-sm">אין תוכן עדיין</p></div>'

        tabs_content += f"""
    <div id="tab-{esc(tab_id)}" class="tab-panel" style="{display}">
      {hero_html}
      <div class="space-y-4 mt-4">{articles}</div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>AI Pulse — עדכוני בינה מלאכותית</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<style>
/* ── TOKENS ────────────────────────────────────────────────────── */
:root {{
  --bg:        #0d0f14;
  --surface:   #13161d;
  --card:      rgba(255,255,255,0.04);
  --card-h:    rgba(255,255,255,0.07);
  --border:    rgba(255,255,255,0.08);
  --border-h:  rgba(255,255,255,0.14);
  --text:      #e2e8f0;
  --muted:     #64748b;
  --accent:    #60a5fa;
  --accent2:   #818cf8;
}}

*, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
html {{ scroll-behavior:smooth; }}

body {{
  font-family:'Assistant',sans-serif;
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  direction:rtl;
  overflow-x:hidden;
}}

/* subtle dot grid */
body::before {{
  content:'';
  position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:radial-gradient(rgba(96,165,250,.07) 1px, transparent 1px);
  background-size:28px 28px;
}}

/* ambient glow top-right */
body::after {{
  content:'';
  position:fixed; top:-200px; right:-200px;
  width:600px; height:600px; z-index:0; pointer-events:none;
  background:radial-gradient(circle, rgba(129,140,248,.06) 0%, transparent 65%);
}}

.material-symbols-outlined {{
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
  vertical-align:middle;
}}

/* ── SCROLLBAR ───────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width:4px; height:4px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
::-webkit-scrollbar-thumb {{ background:var(--border-h); border-radius:4px; }}

/* ── NAV ─────────────────────────────────────────────────────────── */
.top-nav {{
  position:fixed; top:0; width:100%; z-index:100;
  background:rgba(13,15,20,.85);
  backdrop-filter:blur(24px) saturate(180%);
  border-bottom:1px solid var(--border);
}}

/* ── SIDEBAR ─────────────────────────────────────────────────────── */
.sidebar {{
  background:var(--surface);
  border-left:1px solid var(--border);
}}

.sidebar-btn {{
  color:var(--muted);
  border-radius:10px;
  transition:all .2s;
}}
.sidebar-btn:hover {{ background:var(--card-h); color:var(--text); }}
.sidebar-btn.sb-active {{
  background:rgba(96,165,250,.12);
  color:var(--accent);
  box-shadow:inset 0 0 0 1px rgba(96,165,250,.2);
}}

/* ── TABS ────────────────────────────────────────────────────────── */
.tab-btn {{
  color:var(--muted);
  border-bottom:2px solid transparent;
  transition:all .2s;
  white-space:nowrap;
}}
.tab-btn:hover {{ color:var(--text); }}
.tab-active {{
  color:var(--accent) !important;
  border-color:var(--accent) !important;
}}
.tab-count {{
  background:rgba(255,255,255,0.07);
  color:var(--muted);
  border-radius:999px;
}}
.tab-active .tab-count {{
  background:rgba(96,165,250,.15);
  color:var(--accent);
}}

/* ── SEARCH ──────────────────────────────────────────────────────── */
.search-input {{
  background:var(--card);
  border:1px solid var(--border);
  color:var(--text);
  border-radius:999px;
  transition:all .25s;
}}
.search-input:focus {{
  outline:none;
  border-color:var(--accent);
  background:rgba(96,165,250,.06);
  box-shadow:0 0 0 3px rgba(96,165,250,.12);
  width:220px !important;
}}
.search-input::placeholder {{ color:var(--muted); }}

/* ── CARDS ───────────────────────────────────────────────────────── */
.news-article {{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:14px;
  overflow:hidden;
  transition:transform .25s, box-shadow .25s, border-color .25s, background .25s;
  animation:fadeUp .35s ease both;
  position:relative;
}}
.news-article:hover {{
  background:var(--card-h);
  border-color:var(--border-h);
  transform:translateY(-2px);
  box-shadow:0 20px 48px rgba(0,0,0,.4);
}}

/* top accent line per category */
.news-article::before {{
  content:'';
  position:absolute; top:0; right:0; left:0;
  height:2px;
  background:var(--cat-color, var(--accent));
  opacity:.7;
}}

/* ── HERO ────────────────────────────────────────────────────────── */
.featured-hero {{
  min-height:300px;
  border-radius:16px;
  overflow:hidden;
  position:relative;
  border:1px solid var(--border);
  display:block;
  transition:box-shadow .3s, transform .3s;
}}
.featured-hero:hover {{
  transform:translateY(-2px);
  box-shadow:0 24px 64px rgba(0,0,0,.5);
}}

/* ── LINE CLAMP ──────────────────────────────────────────────────── */
.line-clamp-2 {{
  display:-webkit-box;
  -webkit-line-clamp:2;
  -webkit-box-orient:vertical;
  overflow:hidden;
}}

/* ── ANIMATIONS ──────────────────────────────────────────────────── */
@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(14px); }}
  to   {{ opacity:1; transform:translateY(0); }}
}}
@keyframes blink {{
  0%,100% {{ opacity:1; transform:scale(1); }}
  50%      {{ opacity:.4; transform:scale(.7); }}
}}

/* ── MOBILE ──────────────────────────────────────────────────────── */
@media(max-width:1023px) {{
  body {{ padding-bottom:68px; }}
}}
.mob-nav {{ background:rgba(13,15,20,.95); border-top:1px solid var(--border); backdrop-filter:blur(20px); }}
.mob-nav-btn {{ color:var(--muted); transition:color .2s; }}
.mob-nav-btn.mob-active .mat-icon {{ color:var(--accent); font-variation-settings:'FILL' 1,'wght' 600,'GRAD' 0,'opsz' 24; }}
.mob-nav-btn.mob-active .mob-label {{ color:var(--accent); font-weight:700; }}

/* ── NO SCROLLBAR ─────────────────────────────────────────────────── */
.no-scrollbar::-webkit-scrollbar {{ display:none; }}
.no-scrollbar {{ -ms-overflow-style:none; scrollbar-width:none; }}

/* ── HOT BADGE ───────────────────────────────────────────────────── */
.hot-badge {{
  display:inline-flex; align-items:center;
  background:rgba(239,68,68,.15);
  border:1px solid rgba(239,68,68,.3);
  color:#f87171;
  font-size:10px; font-weight:800;
  padding:1px 7px; border-radius:999px;
  letter-spacing:.05em;
  animation:blink 2.5s ease-in-out infinite;
}}

/* ── WHATSAPP BUTTON ─────────────────────────────────────────────── */
.wa-btn {{
  background: rgba(37,211,102,.1);
  border: 1px solid rgba(37,211,102,.25);
  color: #25d366;
}}
.wa-btn:hover {{
  background: rgba(37,211,102,.2);
  border-color: rgba(37,211,102,.5);
  transform: scale(1.04);
}}

/* ── SHARE MODAL ─────────────────────────────────────────────────── */
#wa-modal {{
  display:none;
  position:fixed; inset:0; z-index:200;
  align-items:center; justify-content:center;
  background:rgba(0,0,0,.65);
  backdrop-filter:blur(6px);
  padding:16px;
}}
#wa-modal.open {{ display:flex; }}
#wa-modal-box {{
  background:#1a1f2e;
  border:1px solid rgba(37,211,102,.25);
  border-radius:20px;
  width:100%; max-width:480px;
  padding:28px;
  box-shadow:0 32px 80px rgba(0,0,0,.6);
  animation:fadeUp .2s ease;
}}
#wa-text {{
  width:100%;
  min-height:180px;
  background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.1);
  border-radius:12px;
  color:#e2e8f0;
  font-family:'Assistant',sans-serif;
  font-size:14px;
  line-height:1.7;
  padding:14px;
  resize:vertical;
  direction:rtl;
  outline:none;
  transition:border-color .2s;
}}
#wa-text:focus {{ border-color:rgba(37,211,102,.4); }}
.wa-modal-send {{
  background:#25d366; color:#fff;
  border:none; border-radius:12px;
  padding:11px 22px;
  font-family:'Assistant',sans-serif;
  font-size:15px; font-weight:700;
  cursor:pointer; display:flex; align-items:center; gap:8px;
  transition:background .2s, transform .15s;
}}
.wa-modal-send:hover {{ background:#1ebe5d; transform:scale(1.03); }}
.wa-modal-copy {{
  background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.12);
  color:#e2e8f0;
  border-radius:12px;
  padding:11px 18px;
  font-family:'Assistant',sans-serif;
  font-size:14px; font-weight:600;
  cursor:pointer; display:flex; align-items:center; gap:6px;
  transition:background .2s;
}}
.wa-modal-copy:hover {{ background:rgba(255,255,255,.1); }}
.wa-modal-copy.copied {{ color:#25d366; border-color:rgba(37,211,102,.3); }}

/* ── READ STATE ──────────────────────────────────────────────────── */
.news-article.is-read {{
  opacity:.45;
}}
.news-article.is-read:hover {{
  opacity:.75;
}}
</style>
</head>
<body>

<!-- ══════ TOP NAV ══════ -->
<nav class="top-nav flex justify-between items-center px-6 py-3 z-50">
  <div class="flex items-center gap-5">
    <!-- logo -->
    <div class="flex items-center gap-2.5">
      <div class="w-8 h-8 rounded-xl flex items-center justify-center text-white text-sm"
           style="background:linear-gradient(135deg,#60a5fa,#818cf8);box-shadow:0 0 16px rgba(96,165,250,.3)">
        <span class="material-symbols-outlined" style="font-size:17px">psychology</span>
      </div>
      <span class="text-base font-black tracking-tight hidden sm:block"
            style="background:linear-gradient(90deg,#e2e8f0 30%,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent">
        AI Pulse
      </span>
    </div>
    <!-- live badge -->
    <span class="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold"
          style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);color:#ef4444;font-family:'Assistant',sans-serif;letter-spacing:.04em">
      <span style="width:6px;height:6px;border-radius:50%;background:#ef4444;animation:blink 1.8s ease-in-out infinite;display:inline-block"></span>
      LIVE
    </span>
  </div>
  <div class="flex items-center gap-4">
    <div class="relative hidden sm:block">
      <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2"
            style="font-size:16px;color:var(--muted)">search</span>
      <input id="search" type="text" placeholder="חיפוש..." oninput="filterSearch()"
             class="search-input pr-9 pl-4 py-2 text-sm w-48 text-right"/>
    </div>
    <span class="hidden md:block text-xs font-mono" style="color:var(--muted)">עודכן {updated}</span>
  </div>
</nav>

<!-- ══════ SIDEBAR ══════ -->
<aside class="sidebar fixed right-0 top-0 h-full w-56 flex flex-col p-4 pt-[68px] hidden lg:flex z-40">
  <div class="mb-5 px-2">
    <p class="text-xs font-bold uppercase tracking-widest mb-1" style="color:var(--muted)">ניווט</p>
  </div>
  <nav class="flex flex-col gap-1">
    {"".join(f'''
    <button onclick="switchTabById('{esc(t['id'])}')"
            data-sidebar="{esc(t['id'])}"
            class="sidebar-btn flex items-center gap-3 px-3 py-2.5 text-sm font-semibold text-right w-full">
      <span class="material-symbols-outlined" style="font-size:18px">{t['icon']}</span>
      {t['label']}
    </button>''' for t in TABS)}
  </nav>
  <div class="mt-auto border-t pt-4 space-y-1" style="border-color:var(--border)">
    <p class="px-2 py-1 text-xs font-mono" style="color:var(--muted)">{total} פריטים</p>
    <p class="px-2 py-1 text-xs font-mono" style="color:var(--muted)">{updated}</p>
  </div>
</aside>

<!-- ══════ MAIN ══════ -->
<main class="lg:mr-56 pt-[60px] min-h-screen relative z-10">
  <div class="max-w-5xl mx-auto px-5 py-8">

    <!-- header -->
    <header class="mb-8">
      <h1 class="text-3xl font-black tracking-tight mb-1"
          style="font-family:'Assistant',sans-serif;
                 background:linear-gradient(90deg,#e2e8f0 50%,#60a5fa);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent">
        עדכוני בינה מלאכותית
      </h1>
      <p class="text-sm" style="color:var(--muted)">{total} פריטים · מעודכן יומית</p>
    </header>

    <!-- TABS NAV -->
    <div class="flex gap-0 mb-7 overflow-x-auto no-scrollbar"
         style="border-bottom:1px solid var(--border)" id="tabs-nav">
      {tabs_nav}
    </div>

    <!-- TABS CONTENT -->
    <div id="tabs-content">{tabs_content}</div>

  </div>
</main>

<!-- ══════ FOOTER ══════ -->
<footer class="lg:mr-56 py-5 px-8 hidden lg:block relative z-10"
        style="border-top:1px solid var(--border)">
  <div class="max-w-5xl mx-auto flex justify-between items-center text-xs font-mono"
       style="color:var(--muted)">
    <span style="font-family:'Assistant',sans-serif;font-weight:800;color:var(--accent)">AI Pulse</span>
    <span>© {datetime.now().year} · {total} פריטים · {updated} UTC</span>
  </div>
</footer>

<!-- ══════ WHATSAPP SHARE MODAL ══════ -->
<div id="wa-modal" onclick="if(event.target===this)closeWA()">
  <div id="wa-modal-box">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined" style="color:#25d366;font-size:22px">share</span>
        <span class="font-bold text-base" style="color:#e2e8f0">פוסט לוואטסאפ</span>
      </div>
      <button onclick="closeWA()" style="color:var(--muted);background:none;border:none;cursor:pointer;font-size:22px;line-height:1">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>
    <p class="text-xs mb-3" style="color:var(--muted)">ערוך את הטקסט לפני השליחה:</p>
    <textarea id="wa-text" spellcheck="false"></textarea>
    <div class="flex gap-3 mt-5 justify-end">
      <button class="wa-modal-copy" onclick="copyWA(this)">
        <span class="material-symbols-outlined" style="font-size:17px">content_copy</span>
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
  {"".join(f'''
  <button onclick="switchTabById('{esc(t['id'])}')"
          data-mob="{esc(t['id'])}"
          class="mob-nav-btn flex flex-col items-center gap-0.5 flex-1 py-2">
    <span class="material-symbols-outlined mat-icon" style="font-size:22px">{t['icon']}</span>
    <span class="mob-label text-[10px] font-medium">{t['label']}</span>
  </button>''' for t in TABS)}
</nav>

<script>
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

  if (window.innerWidth < 1024) window.scrollTo({{top:0, behavior:'smooth'}});
}}

function filterSearch() {{
  const q = (document.getElementById('search')?.value || '').trim().toLowerCase();
  document.querySelectorAll('.tab-panel:not([style*="none"]) .news-article').forEach((a,i) => {{
    const text = (a.querySelector('h2')?.textContent||'') + ' ' + (a.querySelector('p')?.textContent||'');
    const show = !q || text.toLowerCase().includes(q);
    a.style.display = show ? '' : 'none';
    if (show) a.style.animationDelay = Math.min(i*40,300)+'ms';
  }});
}}

// ── WHATSAPP SHARE MODAL ──────────────────────────────────────────
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
    '🔗 לקריאה נוספת:' + '\\n' + link + '\\n\\n' +
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
  }} else {{
    fallbackCopy(text, done);
  }}
}}
function fallbackCopy(text, cb) {{
  const ta = document.getElementById('wa-text');
  ta.select();
  try {{ document.execCommand('copy'); cb(); }} catch(e) {{}}
}}
document.addEventListener('keydown', e => {{ if(e.key==='Escape') closeWA(); }});

// ── READ MARKING ──────────────────────────────────────────────────
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

// init
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
