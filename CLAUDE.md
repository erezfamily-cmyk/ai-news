# AI News Dashboard

## סקירה
מערכת שסורקת RSS feeds מאתרי AI מובילים פעם ביום בבוקר, ומציגה דשבורד עברי לצוות דרך GitHub Pages.

## ארכיטקטורה
- **סריקה:** Python + feedparser (RSS)
- **תזמון:** GitHub Actions cron (07:00 UTC = 09:00 ישראל)
- **דשבורד:** HTML סטטי — מתארח על GitHub Pages
- **נתונים:** `data.json` בריפו

## מקורות RSS
- OpenAI Blog
- Anthropic Blog
- Google DeepMind Blog
- HuggingFace Blog
- TechCrunch AI
- The Verge AI
- MIT Technology Review AI
- arXiv cs.AI (מחקרים)
- YouTube channels רלוונטיים (וובינרים/סרטונים)

## קבצים מרכזיים
- `src/scraper.py` — סורק RSS ושומר ל-data.json
- `src/generate_dashboard.py` — מייצר index.html מ-data.json
- `.github/workflows/daily.yml` — GitHub Actions cron job
- `index.html` — הדשבורד (מוגש דרך GitHub Pages)
- `data.json` — נתונים נסרקים

## הרצה מקומית
```bash
pip install -r requirements.txt
python src/scraper.py
python src/generate_dashboard.py
```

## GitHub Pages
הדשבורד מוגש מ-branch `main`, תיקייה root.
URL: `https://<username>.github.io/<repo-name>/`

## שפה
ממשק בעברית. כותרות וסיכומים מוצגים בעברית (אם RSS באנגלית — מוצג כמות שהוא).

## אבטחה
- אין API keys נדרשים (RSS חינמי)
- אין סודות בריפו
