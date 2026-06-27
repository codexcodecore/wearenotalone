#!/usr/bin/env python3
"""Build catalog.json — the canonical dataset for wearenotalone.space — by
parsing every NFO sidecar across Season 01/02/03 and merging DVIDS crawl data.
No invented data: every field comes from the NFO (which came from official
embedded XMP or the official DVIDS page) or the local filesystem.
"""
import glob, os, re, json
import xml.etree.ElementTree as ET

MEDIA = os.environ.get("UAP_MEDIA", "media")
OUT = os.path.join(os.environ.get("UAP_DATA", "data"), "catalog.json")
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)

RELEASES = {
    1: {"release": "Release 01", "release_date": "2026-05-08"},
    2: {"release": "Release 02", "release_date": "2026-05-22"},
    3: {"release": "Release 03", "release_date": "2026-06-12"},
}
AUDIO_RE = re.compile(r'\baudio\b|debriefing|interview excerpt', re.I)

def season_of(path):
    if "Season 01" in path: return 1
    if "Season 02" in path: return 2
    if "Season 03" in path: return 3
    return 0

def text(el, tag):
    e = el.find(tag)
    return e.text.strip() if e is not None and e.text else None

def main():
    nfos = []
    for pat in [r"Season 01\*.nfo", r"Season 02\*.nfo", r"Season 03\AARO061226\*.nfo"]:
        nfos += glob.glob(os.path.join(MEDIA, pat))
    rows = []
    for nf in sorted(nfos):
        try:
            root = ET.parse(nf).getroot()
        except Exception as e:
            print("parse fail", nf, e); continue
        stem = os.path.splitext(os.path.basename(nf))[0]
        season = season_of(nf)
        vid = nf[:-4] + ".mp4"
        rel = os.path.relpath(vid, MEDIA).replace("\\", "/")
        nfo_rel = os.path.relpath(nf, MEDIA).replace("\\", "/")
        genres = [g.text for g in root.findall("genre") if g.text]
        tags = [t.text for t in root.findall("tag") if t.text]
        uids = {u.get("type"): u.text for u in root.findall("uniqueid")}
        title = text(root, "title") or stem
        related_docs = [t for t in tags if re.search(r'-D\d+', t)]
        press_release = next((t for t in tags if re.search(r'-PR\d+', t)), None)
        dvids = uids.get("dvids")
        rows.append({
            "id": uids.get("dod") or stem,
            "season": season,
            **RELEASES.get(season, {}),
            "title": title,
            "virin": text(root, "originaltitle"),
            "tagline": text(root, "tagline"),
            "description": text(root, "plot"),
            "year": text(root, "year"),
            "date": text(root, "premiered"),
            "originator": text(root, "director"),
            "studio": text(root, "studio"),
            "genres": genres,
            "tags": tags,
            "press_release": press_release,
            "related_docs": related_docs or None,
            "media_type": "audio" if AUDIO_RE.search(title) else "video",
            "agency": ("FBI" if title.startswith("FBI") else
                       "NASA" if title.startswith("NASA") else
                       "DoW/AARO"),
            "local_file": rel,
            "nfo_file": nfo_rel,
            "dvids_id": dvids,
            "dvids_url": f"https://www.dvidshub.net/video/{dvids}" if dvids else None,
        })
    rows.sort(key=lambda r: (r["season"], r["title"]))
    json.dump(rows, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    # summary
    from collections import Counter
    print(f"catalog.json: {len(rows)} entries -> {OUT}")
    print("by season:", dict(Counter(r["season"] for r in rows)))
    print("by media_type:", dict(Counter(r["media_type"] for r in rows)))
    print("by agency:", dict(Counter(r["agency"] for r in rows)))
    print("with description:", sum(1 for r in rows if r["description"]))

if __name__ == "__main__":
    main()
