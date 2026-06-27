#!/usr/bin/env python3
"""Crawl DVIDS AARO video pages, extract per-video metadata, match to local
Season 02/03 DOD ids. Writes dvids_map.json {dodid: {...}}.
"""
import urllib.request, urllib.parse, re, html, json, time, sys
import os

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
TARGETS = set(sys.argv[1].split(',')) if len(sys.argv) > 1 else set()

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        b = r.read()
    # Promote cp1252 smart punctuation to valid UTF-8 (curly quotes stay curly so
    # they do NOT collide with the ASCII '"' that delimits meta content attributes).
    for bad, good in [(b'\x93', b'\xe2\x80\x9c'), (b'\x94', b'\xe2\x80\x9d'),
                      (b'\x92', b'\xe2\x80\x99'), (b'\x91', b'\xe2\x80\x98'),
                      (b'\x96', b'-'), (b'\x97', b'-'), (b'\x85', b'...'),
                      (b'\xa0', b' '), (b'\xc2\xa0', b' ')]:
        b = b.replace(bad, good)
    return b.decode('utf-8', errors='replace')

def harvest_urls():
    """Collect unique /video/<id>/<slug> links across search queries."""
    queries = [
        'DOW-UAP-PR', 'AARO UAP', 'Western United States Event',
        'unresolved UAP report', 'UAP',
    ]
    found = {}
    for q in queries:
        for page in range(1, 9):
            u = ('https://www.dvidshub.net/search/?q=' + urllib.parse.quote(q) +
                 '&filter%5Btype%5D=video&page=' + str(page))
            try:
                t = get(u)
            except Exception as e:
                print(f'  harvest fail {q} p{page}: {e}'); break
            links = re.findall(r'/video/(\d+)/([a-z0-9][a-z0-9-]+)', t)
            new = 0
            for vid, slug in links:
                if vid not in found:
                    found[vid] = slug; new += 1
            print(f'  q="{q}" p{page}: +{new} (total {len(found)})')
            if new == 0:
                break
            time.sleep(0.25)
    return found

def parse_video(vid, slug):
    u = f'https://www.dvidshub.net/video/{vid}/{slug}'
    t = get(u)
    def find(pat, flags=0):
        m = re.search(pat, t, flags)
        return html.unescape(m.group(1)).strip() if m else None
    title = find(r'property="og:title"\s+content="([^"]*)"')
    desc = find(r'property="og:description"\s+content="([^"]*)"')
    # scrub any stray replacement chars left from undecodable bytes
    title = title.replace('�', '').strip() if title else title
    desc = desc.replace('�', '').strip() if desc else desc
    dod = re.search(r'DOD_(\d+)', t)
    virin = re.search(r'(\d{6}-[A-Z]-[A-Z0-9]{4,6}-\d+)', t)
    date_taken = find(r'Date Taken[:\s]*</[^>]+>\s*([\d.]{8,10})') or find(r'Date Taken[:\s]*([\d.]{8,10})')
    # country / location
    loc = find(r'Location[:\s]*</[^>]+>\s*([A-Za-z ,()]+?)\s*<') or find(r'Location[:\s]*([A-Za-z ,()]{2,40})')
    return {
        'dvids_id': vid, 'url': u, 'title': title, 'description': desc,
        'dod': dod.group(1) if dod else None,
        'virin': virin.group(1) if virin else None,
        'date_taken': date_taken, 'location': loc,
    }

def main():
    print('== harvesting video URLs ==')
    urls = harvest_urls()
    print(f'harvested {len(urls)} unique video pages\n== crawling pages ==')
    mp = {}
    remaining = set(TARGETS)
    crawled = 0
    # crawl higher DVIDS ids first (release 02/03 are 1007xxx+ / June batch)
    for vid in sorted(urls, key=lambda x: int(x), reverse=True):
        if TARGETS and not remaining:
            break
        try:
            info = parse_video(vid, urls[vid])
        except Exception as e:
            print(f'  {vid} ERROR {e}'); continue
        crawled += 1
        d = info.get('dod')
        if d and (not TARGETS or d in TARGETS):
            mp[d] = info
            remaining.discard(d)
            print(f'  MATCH DOD_{d}  <- {info.get("title")}  ({len(mp)}/{len(TARGETS) if TARGETS else "?"})')
        if crawled % 20 == 0:
            print(f'  ...crawled {crawled}, matched {len(mp)}, remaining {len(remaining)}')
        time.sleep(0.2)
    out = os.path.join(os.environ.get("UAP_DATA", "data"), "dvids_map.json")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    json.dump(mp, open(out, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print(f'\nwrote {out}: {len(mp)} matched')
    if TARGETS:
        print(f'UNMATCHED ({len(remaining)}): {" ".join(sorted(remaining))}')

if __name__ == '__main__':
    main()
