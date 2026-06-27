#!/usr/bin/env python3
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
