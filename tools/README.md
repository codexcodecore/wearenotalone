# tools/ — the metadata pipeline

Plain Python 3 (standard library only — `urllib`, `re`, `xml.etree`, `json`,
`zipfile`). No `pip install`. Paths are driven by environment variables with
relative defaults:

| Env var | Default | Meaning |
|---------|---------|---------|
| `UAP_MEDIA` | `media` | Root holding `Season 01/`, `Season 02/`, `Season 03/` (the mp4s, and the extracted document bundles). Sidecars are written next to the videos. |
| `UAP_DATA` | `data` | Where indexes and `dvids_map.json` are written/read. |
| `UAP_OUT_ZIP` | `nfo_pack.zip` | Output path for `make_public_pack.py`. |

## Scripts

| Script | Purpose |
|--------|---------|
| `gen_nfo.py` | Release 01: extract the embedded XMP metadata from each `.mp4` → `.nfo` sidecars next to the videos. |
| `dvids_crawl.py` | Releases 02/03: crawl the official DVIDS AARO video pages → `data/dvids_map.json`. Pass the target `DOD` ids as a comma-separated argument. |
| `gen_nfo_s23.py` | Build the Release 02/03 sidecars from `dvids_map.json`. |
| `finalize_s23.py` | Recover any titles DVIDS truncated in its OpenGraph tag (from the page `<title>`); re-run `gen_nfo_s23.py` after. |
| `build_catalog.py` | Parse all sidecars → `data/catalog.json` (the 93-video dataset). |
| `build_docs_index.py` | Index the released documents/images → `data/docs_index.json`. |
| `make_public_pack.py` | Bundle the sidecars (renamed `DOD_<id>.nfo`) + a CSV + a rename helper into `nfo_pack.zip`. |
| `rename_nfo.py` | Match the bundled sidecars to your downloaded video files by DOD id. |

## Method notes (why it works)

- **Release 01** mp4s carry a full XMP packet (title, date, agency, the complete
  AARO description, the linked mission report) — read straight from the files.
- **Releases 02/03** were re-encoded and stripped of embedded metadata, so each
  record's title + verbatim description is recovered from its official **DVIDS**
  page. DVIDS doesn't index by the `DOD_<id>` download id, so the video page
  itself is the bridge (it exposes the `DOD_<id>` filename + the description).
- **Encoding gotcha:** DVIDS serves Windows-1252 smart punctuation. Convert the
  smart-quote bytes to *curly* UTF-8 (not ASCII `"`), or `og:description`
  capture truncates at the first embedded quote.
- The date for each Release 02/03 record is derived from its **VIRIN** prefix
  (`YYMMDD`).

Re-running any generator is idempotent.
