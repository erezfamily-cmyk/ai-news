import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime

AGENT_PATH = Path(__file__).resolve().parent / '.agent.md'
if not AGENT_PATH.exists():
    raise FileNotFoundError(f"Agent file not found: {AGENT_PATH}")

raw = AGENT_PATH.read_text(encoding='utf-8')

name = re.search(r'^name:\s*"([^"]+)"', raw, flags=re.MULTILINE)
summary = re.search(r'^summary:\s*"([^"]+)"', raw, flags=re.MULTILINE)
example_prompts = re.findall(r'^\s*-\s*"([^"]+)"', raw, flags=re.MULTILINE)

agent = {
    'name': name.group(1) if name else 'Unnamed agent',
    'summary': summary.group(1) if summary else '',
    'example_prompts': example_prompts,
}

print(f"Agent: {agent['name']}")
print(f"Summary: {agent['summary']}")
print('Detected example prompts:', len(agent['example_prompts']))

query_he = 'סרטוני הדרכה על כלים של AI בעברית'


def fetch_youtube_api(query, max_results=8):
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        raise RuntimeError('YOUTUBE_API_KEY env var is not set')

    q = urllib.parse.quote_plus(query)
    url = (
        'https://www.googleapis.com/youtube/v3/search'
        f'?part=snippet&type=video&maxResults={max_results}'
        f'&q={q}&relevanceLanguage=he&videoCaption=any&videoSyndicated=true&key={api_key}'
    )
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    })

    with urllib.request.urlopen(req, timeout=15) as res:
        res_body = res.read().decode('utf-8', errors='ignore')
    data = json.loads(res_body)

    results = []
    for item in data.get('items', []):
        video_id = item.get('id', {}).get('videoId')
        snippet = item.get('snippet', {})
        if not video_id:
            continue
        results.append({
            'source': 'YouTube API',
            'title': snippet.get('title', '(no title)'),
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'description': snippet.get('description', ''),
            'publishedAt': snippet.get('publishedAt'),
            'channelTitle': snippet.get('channelTitle'),
        })

    return results

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
}


def fetch_youtube_scrape(query, max_results=8):
    u = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote_plus(query)
    req = urllib.request.Request(u, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as res:
        body = res.read().decode('utf-8', errors='ignore')

    ids = []
    for m in re.finditer(r"/watch\?v=([A-Za-z0-9_-]{11})", body):
        video_id = m.group(1)
        if video_id not in ids:
            ids.append(video_id)
        if len(ids) >= max_results:
            break

    titles = re.findall(r'"title":\{"runs":\[\{"text":"([^\"]+)"\}\]\}', body)
    links = []
    for i, video_id in enumerate(ids):
        title = titles[i] if i < len(titles) else 'Unknown title'
        links.append({
            'source': 'YouTube Scrape',
            'title': title,
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'description': '',
            'publishedAt': None,
            'channelTitle': None,
        })

    return links

print('Running Hebrew YouTube query:', query_he)

results = []
try:
    results = fetch_youtube_api(query_he, max_results=8)
    print('Fetched using YouTube Data API')
except Exception as e:
    print('YouTube API fetch failed:', e)
    try:
        results = fetch_youtube_scrape(query_he, max_results=8)
        print('Fetched via HTML scrape fallback')
    except Exception as e2:
        print('YouTube scrape fallback failed:', e2)
        results = []

if not results:
    print('No results found, creating placeholder entries.')
    results = [
        {'source': 'YouTube', 'title': 'אין תוצאות אוטומטיות', 'url': 'https://www.youtube.com', 'description': ''},
    ]

timestamp = datetime.utcnow().isoformat() + 'Z'
output = {
    'agent': agent,
    'query': query_he,
    'fetched_at': timestamp,
    'results': results,
}

with open('ai_tutorials_hebrew.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

md_lines = [
    '# AI Tutorials Extractor Report',
    f'*Agent: {agent["name"]}',
    f'*Query: {query_he}',
    f'*Fetched at: {timestamp}',
    '',
]
for i, item in enumerate(results, 1):
    md_lines.append(f'## {i}. {item.get("title","Unknown")}')
    md_lines.append(f'- Source: {item.get("source")}')
    md_lines.append(f'- URL: {item.get("url")}')
    if item.get('channelTitle'):
        md_lines.append(f'- Channel: {item.get("channelTitle")}')
    if item.get('publishedAt'):
        md_lines.append(f'- PublishedAt: {item.get("publishedAt")}')
    if item.get('description'):
        dlg = item.get('description', '').replace('\n', ' ').strip()
        md_lines.append(f'- Description: {dlg[:200]}')
    md_lines.append('')

with open('ai_tutorials_hebrew.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

print('Done. Wrote ai_tutorials_hebrew.json and ai_tutorials_hebrew.md')
