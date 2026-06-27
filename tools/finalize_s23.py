#!/usr/bin/env python3
"""Recover full titles for entries whose og:title was truncated, scrub any
U+FFFD, save map. Reuses dvids_crawl.get() for consistent decoding."""
import sys, re, html, json
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import dvids_crawl as dc

MAPP = os.path.join(os.environ.get("UAP_DATA", "data"), "dvids_map.json")
FFFD = chr(0xFFFD)
m = json.load(open(MAPP, encoding="utf-8"))

def clean(s):
    return (s or '').replace(FFFD, "'")

fixed = 0
for d, v in m.items():
    t = v.get('title') or ''
    if t.rstrip().endswith(',') or len(t) < 18:
        page = dc.get(v['url'])
        tt = re.search(r'<title>(.*?)</title>', page, re.S)
        if tt:
            full = html.unescape(tt.group(1)).strip()
            full = re.sub(r'^DVIDS\s*-\s*Video\s*-\s*', '', full)
            full = re.sub(r'\s*\|\s*DVIDS.*$', '', full)
            full = re.sub(r'\s{2,}', ' ', clean(full)).strip()
            v['title'] = full
            fixed += 1
            print("title fixed DOD_%s -> %s" % (d, full))
    v['title'] = clean(v.get('title'))
    v['description'] = clean(v.get('description'))

json.dump(m, open(MAPP, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print("titles fixed:", fixed, "| total entries:", len(m))
