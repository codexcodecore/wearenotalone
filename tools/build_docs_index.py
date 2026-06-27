#!/usr/bin/env python3
"""Build docs_index.json — the catalog of hosted images + documents (the small,
self-hostable media). Videos are intentionally excluded (those link out to the
official gov source). Metadata is parsed from the official filenames only —
nothing invented.
"""
import glob, os, re, json, subprocess, shutil

MEDIA = os.environ.get("UAP_MEDIA", "media")
OUT = os.path.join(os.environ.get("UAP_DATA", "data"), "docs_index.json")
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)

# extracted document bundles per release
SOURCES = [
    (1, r"Season 01\Release_1"),
    (2, r"Season 02\release_02_document_bundle"),
    (3, r"Season 03\release_03_documents"),
]
IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
DOC_EXT = {".pdf"}

HAVE_PDFINFO = shutil.which("pdfinfo") is not None

AGENCY_PREFIX = [
    (r"^DO[WS]-UAP", "DoW"), (r"^DOW-UAP", "DoW"), (r"^DoW-UAP", "DoW"),
    (r"^FBI", "FBI"), (r"^NASA", "NASA"), (r"^CIA", "CIA"),
    (r"^DOS-UAP", "State Dept"), (r"^DOE-UAP", "Energy Dept"),
    (r"^ODNI", "ODNI"), (r"^ICA-UAP", "ICA"), (r"^USG", "US Government"),
    (r"^USPER", "US Person"),
]

def agency_of(name):
    for pat, label in AGENCY_PREFIX:
        if re.match(pat, name, re.I):
            return label
    if re.match(r"^\d+_", name):   # NARA record-group numbered scans
        return "NARA / Historical"
    return "Other"

def doc_id_of(name):
    m = re.match(r"([A-Za-z]+-UAP-[A-Za-z]*\d+|[A-Za-z]+-Photo-[A-Za-z]?\d+)", name)
    return m.group(1) if m else None

def year_of(name):
    yrs = re.findall(r"(1[89]\d{2}|20[0-4]\d)", name)
    return yrs[-1] if yrs else None

def title_of(name):
    t = os.path.splitext(name)[0]
    t = re.sub(r"_", " ", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t

def pages_of(path):
    if not HAVE_PDFINFO:
        return None
    try:
        out = subprocess.run(["pdfinfo", path], capture_output=True, text=True, timeout=30)
        m = re.search(r"Pages:\s+(\d+)", out.stdout)
        return int(m.group(1)) if m else None
    except Exception:
        return None

def main():
    rows = []
    for season, sub in SOURCES:
        base = os.path.join(MEDIA, sub)
        for f in glob.glob(os.path.join(base, "**", "*.*"), recursive=True):
            ext = os.path.splitext(f)[1].lower()
            if ext not in IMG_EXT and ext not in DOC_EXT:
                continue
            name = os.path.basename(f)
            if name.startswith("._"):
                continue
            mtype = "image" if ext in IMG_EXT else "document"
            rel = os.path.relpath(f, MEDIA).replace("\\", "/")
            rows.append({
                "id": doc_id_of(name) or os.path.splitext(name)[0],
                "season": season,
                "agency": agency_of(name),
                "title": title_of(name),
                "year": year_of(name),
                "media_type": mtype,
                "ext": ext.lstrip("."),
                "filename": name,
                "source_path": rel,            # relative to the media root
                "size": os.path.getsize(f),
                "pages": pages_of(f) if mtype == "document" else None,
            })
    rows.sort(key=lambda r: (r["agency"], r["season"], r["title"]))
    json.dump(rows, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    from collections import Counter
    print(f"docs_index.json: {len(rows)} items -> {OUT}")
    print("by media_type:", dict(Counter(r["media_type"] for r in rows)))
    print("by agency:", dict(Counter(r["agency"] for r in rows)))
    tot = sum(r["size"] for r in rows)
    print(f"total hosted size: {tot/1024/1024:.0f} MB  (pdfinfo: {HAVE_PDFINFO})")

if __name__ == "__main__":
    main()
