#!/usr/bin/env python3
"""Build public_pack/nfo_pack.zip: all 93 NFO sidecars renamed to DOD_<id>.nfo
(matching the canonical DVIDS/DoD download filename DOD_<id>.mp4), plus a
README, a CSV index, and a cross-platform rename helper.
"""
import json, os, re, csv, io, zipfile

MEDIA = os.environ.get("UAP_MEDIA", "media")
DATA = os.environ.get("UAP_DATA", "data")
catalog = json.load(open(os.path.join(DATA, "catalog.json"), encoding="utf-8"))
zip_path = os.environ.get("UAP_OUT_ZIP", "nfo_pack.zip")

def fix_sorttitle(text, dod):
    return re.sub(r'(<sorttitle>UAP [^<]*?)\s+\S+(</sorttitle>)',
                  lambda m: f'{m.group(1)} DOD_{dod}{m.group(2)}', text)

readme = """WE ARE NOT ALONE  -  AARO / PURSUE UAP Video Metadata Pack
============================================================

This pack contains 93 Kodi/XBMC-style .nfo metadata sidecars for the official
U.S. Government UAP videos released by the Department of War / AARO under the
PURSUE program (Releases 01-03, May-June 2026). Every field is sourced from the
videos' own embedded metadata or their official DVIDS pages - nothing invented.

WHY: so you can build a rich, browsable UAP video library in Plex / Jellyfin /
Kodi with real titles, dates, agencies, and full official descriptions instead
of raw "DOD_#########" filenames.

--------------------------------------------------------------------
WHAT YOU GET
--------------------------------------------------------------------
  Season 01/  - 28 sidecars (Release 01, embedded-metadata sourced)
  Season 02/  - 56 sidecars (Release 02, DVIDS-sourced)
  Season 03/  - 9  sidecars (Release 03, DVIDS-sourced)
  catalog.csv - index: id, title, agency, year, type, DVIDS link, filename
  rename_nfo.py - helper to match sidecars to your downloaded files

--------------------------------------------------------------------
STEP 1 - DOWNLOAD THE VIDEOS (from the official source)
--------------------------------------------------------------------
The videos are public domain. Get them from DVIDS (the DoD's distribution site):
  * Open the DVIDS link in catalog.csv for each video (or browse the AARO unit:
    https://www.dvidshub.net/unit/AARO ).
  * Click Download. Files arrive named  DOD_<id>.mp4  (e.g. DOD_111688723.mp4).
  * Bulk releases also live at War.gov's UAP media library.

--------------------------------------------------------------------
STEP 2 - PLACE THE .NFO FILES
--------------------------------------------------------------------
A media server reads a sidecar when the .nfo basename EXACTLY matches the video
basename, in the SAME folder:
    DOD_111688723.mp4   <-  DOD_111688723.nfo      (correct)
The sidecars here are already named DOD_<id>.nfo to match DVIDS downloads.
Just drop each .nfo next to its matching .mp4.

If your download has a different name (some mirrors rename files), run:
    python rename_nfo.py  /path/to/your/videos
It matches by the DOD id inside the filename and renames each .nfo to match.

--------------------------------------------------------------------
STEP 3 - POINT YOUR MEDIA SERVER AT THEM
--------------------------------------------------------------------
PLEX  : use a Movies library + the "XBMCnfoMoviesImport" agent (the default
        "Plex Movie" agent ignores .nfo). Put it above "Local Media Assets",
        enable .nfo import, then Refresh Metadata.
JELLYFIN / EMBY : NFO reading is built in - just Refresh Metadata.
KODI  : enable the local information provider / use the NFO directly.

--------------------------------------------------------------------
SOURCE & LICENSE
--------------------------------------------------------------------
Videos: U.S. Government work, Public Domain. Metadata compiled from official
AARO/DVIDS sources. Pack assembled for wearenotalone.space. Share freely.
"""

rename_helper = r'''#!/usr/bin/env python3
"""Rename the .nfo files in this pack to match your downloaded video files.
Usage: python rename_nfo.py /path/to/your/videos
Matches by the DOD id (the 9-digit number) found in each filename.
"""
import sys, os, re, glob, shutil
if len(sys.argv) < 2:
    print("Usage: python rename_nfo.py /path/to/your/videos"); sys.exit(1)
vid_dir = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
vids = {}
for v in glob.glob(os.path.join(vid_dir, "**", "*.*"), recursive=True):
    if v.lower().endswith((".mp4", ".mov", ".mkv", ".m4v")):
        m = re.search(r'(\d{9})', os.path.basename(v))
        if m: vids[m.group(1)] = v
n = 0
for nfo in glob.glob(os.path.join(here, "**", "*.nfo"), recursive=True):
    m = re.search(r'(\d{9})', os.path.basename(nfo))
    if m and m.group(1) in vids:
        dst = os.path.splitext(vids[m.group(1)])[0] + ".nfo"
        shutil.copyfile(nfo, dst); n += 1
        print("placed", os.path.basename(dst))
print(f"placed {n} sidecars next to matching videos in {vid_dir}")
'''

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("README.txt", readme)
    z.writestr("rename_nfo.py", rename_helper)
    # CSV index
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["dod_id", "title", "agency", "media_type", "year", "season",
                "suggested_filename", "dvids_url"])
    for e in catalog:
        w.writerow([e["id"], e["title"], e["agency"], e["media_type"],
                    e["year"] or "", e["season"], f'DOD_{e["id"]}.mp4',
                    e["dvids_url"] or ""])
    z.writestr("catalog.csv", buf.getvalue())
    # the sidecars, renamed
    count = 0
    for e in catalog:
        src = os.path.join(MEDIA, e["nfo_file"].replace("/", os.sep))
        txt = open(src, encoding="utf-8").read()
        txt = fix_sorttitle(txt, e["id"])
        arc = f'Season 0{e["season"]}/DOD_{e["id"]}.nfo'
        z.writestr(arc, txt)
        count += 1

print(f"wrote {zip_path}")
print(f"  {count} sidecars + README.txt + catalog.csv + rename_nfo.py")
print(f"  size: {os.path.getsize(zip_path):,} bytes")
