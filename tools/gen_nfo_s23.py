#!/usr/bin/env python3
"""Generate NFO sidecars for Season 02/03 videos using DVIDS-crawled metadata
(dvids_map.json). NFO basename matches each video file exactly.
"""
import json, re, os, glob
from xml.sax.saxutils import escape

ROOT = os.environ.get("UAP_MEDIA", "media")
MAP = json.load(open(os.path.join(os.environ.get("UAP_DATA", "data"), "dvids_map.json"), encoding="utf-8"))

SEASON_DIRS = [
    (r"Season 02", os.path.join(ROOT, "Season 02", "video_2605_DOD_*.mp4")),
    (r"Season 03", os.path.join(ROOT, "Season 03", "AARO061226", "DOD_*-1920x1080-9000k.mp4")),
]

def virin_date(virin):
    if not virin:
        return None, None
    m = re.match(r'(\d{2})(\d{2})(\d{2})-', virin)
    if not m:
        return None, None
    yy, mm, dd = int(m.group(1)), m.group(2), m.group(3)
    year = 2000 + yy if yy <= 26 else 1900 + yy
    prem = None
    if 1 <= int(mm) <= 12 and 1 <= int(dd) <= 31:
        prem = f"{year}-{mm}-{dd}"
    return str(year), prem

def clean_title(t, stem):
    if not t:
        return stem
    t = t.replace('"', '').replace('“', '').replace('”', '')
    t = re.sub(r'\s{2,}', ' ', t).strip().rstrip(',').strip()
    return t or stem

def originator(title, desc):
    if title.startswith('FBI-UAP'):
        return 'Federal Bureau of Investigation (FBI)'
    if title.startswith('NASA-UAP'):
        return 'National Aeronautics and Space Administration (NASA)'
    # DOW-UAP and others: try to read a command from the description
    m = re.search(r'United States ([A-Za-z\- ]+?) (?:area of responsibility|Command)', desc or '')
    if m:
        return 'U.S. ' + m.group(1).strip()
    m = re.search(r'The (.{3,60}?) (?:submitted|provided) a report', desc or '')
    if m:
        c = m.group(1).strip()
        return ('U.S. ' + c[len('United States '):]) if c.startswith('United States ') else c
    return 'Department of War (via AARO)'

def genres_for(title):
    g = ['Documentary', 'UAP']
    if title.startswith('NASA-UAP'):
        g.append('Spaceflight')
    elif title.startswith('FBI-UAP'):
        g.append('Eyewitness Report')
    else:
        g.append('Military ISR')
    return g

def series_tag(title):
    m = re.match(r'([A-Z]+-UAP-[A-Za-z0-9]+)', title)
    return m.group(1) if m else None

def build(stem, info):
    title = clean_title(info.get('title'), stem)
    desc = (info.get('description') or '').strip()
    # strip stray wrapping quotes some DVIDS captions have around the whole text
    if desc.startswith('"') and desc.rstrip().endswith('"'):
        desc = desc.strip().strip('"').strip()
    elif desc.startswith('"'):
        desc = desc[1:].strip()
    virin = info.get('virin') or ''
    dvids = info.get('dvids_id') or ''
    dod = info.get('dod') or ''
    year, prem = virin_date(virin)
    orig = originator(title, desc)
    genres = genres_for(title)
    stag = series_tag(title)

    tagline = ' · '.join(filter(None, [orig, f'VIRIN {virin}' if virin else None,
                                            f'DVIDS {dvids}' if dvids else None]))
    L = []; a = L.append
    a('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    a('<movie>')
    a(f'  <title>{escape(title)}</title>')
    if virin:
        a(f'  <originaltitle>{escape(virin)}</originaltitle>')
    a(f'  <sorttitle>{escape(("UAP " + (prem or year or "") + " " + stem).strip())}</sorttitle>')
    if tagline:
        a(f'  <tagline>{escape(tagline)}</tagline>')
    if desc:
        a(f'  <plot>{escape(desc)}</plot>')
    if prem:
        a(f'  <premiered>{escape(prem)}</premiered>')
    if year:
        a(f'  <year>{escape(year)}</year>')
    a('  <studio>All-domain Anomaly Resolution Office (AARO)</studio>')
    a(f'  <director>{escape(orig)}</director>')
    a('  <mpaa>Unclassified // Public Domain</mpaa>')
    for g in genres:
        a(f'  <genre>{g}</genre>')
    for t in filter(None, [stag, 'AARO', f'DVIDS {dvids}' if dvids else None]):
        a(f'  <tag>{escape(t)}</tag>')
    if dod:
        a(f'  <uniqueid type="dod" default="true">{escape(dod)}</uniqueid>')
    if dvids:
        a(f'  <uniqueid type="dvids">{escape(dvids)}</uniqueid>')
    if virin:
        a(f'  <uniqueid type="virin">{escape(virin)}</uniqueid>')
    a('</movie>'); a('')
    return '\n'.join(L)

def main():
    total = 0; missing = []
    for label, pattern in SEASON_DIRS:
        for v in sorted(glob.glob(pattern)):
            stem = os.path.splitext(os.path.basename(v))[0]
            m = re.search(r'DOD_(\d+)', stem)
            dod = m.group(1) if m else None
            info = MAP.get(dod)
            if not info:
                missing.append(stem); continue
            nfo = build(stem, info)
            out = os.path.join(os.path.dirname(v), stem + '.nfo')
            open(out, 'w', encoding='utf-8').write(nfo)
            total += 1
            print(f'[{label}] {stem[:42]:<42} -> {info.get("title")[:60]}')
    print(f'\nWrote {total} NFOs. Missing metadata: {len(missing)}')
    for x in missing:
        print('  MISSING', x)

if __name__ == '__main__':
    main()
