# We Are Not Alone — UAP Media Library Kit

Ready-to-use **metadata sidecars** (`.nfo`) and the tooling that builds them, so
you can turn the U.S. Government's officially released UAP videos into a rich,
browsable library in **Plex, Jellyfin, Emby, or Kodi** — with real titles,
dates, agencies, and the full official descriptions instead of bare
`DOD_#########` filenames.

Companion to **[wearenotalone.space](https://wearenotalone.space)**.

> **No invented data.** Every title and description comes from the video's own
> embedded metadata (Release 01) or its official DVIDS page (Releases 02–03).
> If a fact can't be sourced, it isn't here.

---

## What's in here

```
nfo/            93 ready-to-use sidecars, by release
  release-01/   28  (DoW/AARO, May 8 2026)
  release-02/   56  (DoW/AARO + NASA audio, May 22 2026)
  release-03/   9   (FBI recreations + NASA, June 12 2026)
data/
  catalog.csv         index: id, title, agency, type, year, DVIDS link, filename
  catalog.json        full 93-video dataset
  docs_index.json     199 released documents/images (FBI, CIA, NASA, DoW, NARA)
tools/          the Python pipeline that generated everything (stdlib only)
nfo_pack.zip    one-click bundle: all 93 sidecars + catalog.csv + a rename helper
```

---

## Quick start — add the videos to your media server

### 1. Get the videos (official, public domain)
The videos are distributed by the DoD on **DVIDS**:
- Browse the AARO unit: <https://www.dvidshub.net/unit/AARO>, or
- Open the DVIDS link for any specific video in `data/catalog.csv`.
- Click **Download** — files arrive named `DOD_<id>.mp4` (e.g. `DOD_111688723.mp4`).
- Bulk batches are also mirrored at <https://www.war.gov/ufo/>.

Sort them into folders if you like (the sidecars are grouped `release-01/02/03`).

### 2. Drop in the sidecars
A media server reads a sidecar when the **`.nfo` basename exactly matches the
video basename, in the same folder**:

```
DOD_111688723.mp4   ←→   DOD_111688723.nfo   ✓
```

The sidecars here are already named `DOD_<id>.nfo` to match DVIDS downloads —
just place each next to its video. If your downloads were renamed by a mirror,
run the included helper (matches by the 9-digit DOD id inside the filename):

```bash
python tools/rename_nfo.py  /path/to/your/videos
```

### 3. Turn on NFO reading
- **Plex** — use a **Movies** library + the **XBMCnfoMoviesImport** agent (the
  default *Plex Movie* agent ignores `.nfo`). Put it above *Local Media Assets*,
  enable “Import movie.nfo”, then **Refresh Metadata**.
- **Jellyfin / Emby** — NFO reading is built in. Enable the **Nfo** metadata
  reader for the library and **Refresh Metadata**.
- **Kodi** — uses the `.nfo` directly via the local information provider.

That's it — your UAP library now shows proper titles, dates, agencies, and the
official descriptions.

---

## Build it yourself

Pure Python 3 (standard library only — no `pip install`). Point the scripts at
your media with environment variables (defaults are relative):

```bash
export UAP_MEDIA=./media      # holds Season 01/02/03 folders (mp4s + bundles)
export UAP_DATA=./data        # where indexes / dvids_map.json are written

# Release 01 — read embedded XMP metadata from each mp4:
python tools/gen_nfo.py

# Releases 02/03 — recover metadata from the official DVIDS pages:
python tools/dvids_crawl.py <comma,separated,DOD,ids>
python tools/gen_nfo_s23.py
python tools/finalize_s23.py && python tools/gen_nfo_s23.py

# Rebuild the indexes + the public pack:
python tools/build_catalog.py
python tools/build_docs_index.py
python tools/make_public_pack.py
```

See `tools/README.md` for what each script does and the method behind it.

---

## Source & license

- **The UAP records** (videos, documents, images, and the descriptions quoted in
  the sidecars) are **U.S. Government works in the public domain**.
- **The code** in `tools/` is released under the **MIT License** (see `LICENSE`).

Compiled from official **AARO / DVIDS / War.gov** sources. Share freely. 🛸
