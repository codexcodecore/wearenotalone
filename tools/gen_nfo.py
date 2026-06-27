#!/usr/bin/env python3
"""Generate Kodi/XBMC <movie> NFO sidecars for AARO/UAP DOD_*.mp4 videos
from each file's embedded XMP metadata. One .nfo per video, matching basename.
"""
import re
import sys
import glob
import os
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

SEASON_DIR = os.path.join(os.environ.get("UAP_MEDIA", "media"), "Season 01")

NS = {
    'x': 'adobe:ns:meta/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'photoshop': 'http://ns.adobe.com/photoshop/1.0/',
    'xmp': 'http://ns.adobe.com/xap/1.0/',
    'xmpDM': 'http://ns.adobe.com/xmp/1.0/DynamicMedia/',
    'Iptc4xmpCore': 'http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/',
}


def extract_xmp(path):
    with open(path, 'rb') as fh:
        data = fh.read()
    start = data.find(b'<x:xmpmeta')
    end = data.find(b'</x:xmpmeta>')
    if start == -1 or end == -1:
        return None
    return data[start:end + len(b'</x:xmpmeta>')].decode('utf-8', errors='replace')


def first_text(desc_el, dc_tag):
    """dc:title / dc:description -> rdf:Alt/rdf:li[x-default]"""
    el = desc_el.find(f'dc:{dc_tag}/rdf:Alt', NS)
    if el is None:
        return None
    lis = el.findall('rdf:li', NS)
    for li in lis:
        if li.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}lang') == 'x-default':
            return (li.text or '').strip()
    return (lis[0].text or '').strip() if lis else None


def bag_items(desc_el, ns_prefix, tag):
    el = desc_el.find(f'{ns_prefix}:{tag}/rdf:Bag', NS)
    if el is None:
        return []
    return [(li.text or '').strip() for li in el.findall('rdf:li', NS)]


def attr(desc_el, ns_prefix, name):
    return desc_el.get(f'{{{NS[ns_prefix]}}}{name}')


def build_nfo(stem, fields):
    asset = fields.get('asset') or ''
    headline = fields.get('headline') or ''
    plot = fields.get('plot') or ''
    year = fields.get('year') or ''
    premiered = fields.get('premiered') or ''
    dvids = fields.get('dvids') or ''
    country = fields.get('country') or ''
    seconds = fields.get('seconds') or 0
    originator = fields.get('originator')  # may be None -> omit <director>
    pr = fields.get('pr') or ''
    misrep = fields.get('misrep') or ''
    runtime_min = max(1, round(seconds / 60)) if seconds else 1

    # genres adapt to the originator
    genres = ['Documentary', 'UAP']
    if originator and re.search(r'Command|Army|Navy|Air Force|Marine', originator):
        genres.append('Military ISR')
    elif originator and 'NASA' in originator:
        genres.append('Spaceflight')

    tags = ['UAPVIDEOS', 'AARO']
    if pr:
        tags.append(pr)
    if misrep:
        tags.append(misrep)
    if dvids:
        tags.append(f'DVIDS {dvids}')

    # Display title: clean headline form (drop the redundant "Unresolved UAP Report"),
    # e.g. "DOW-UAP-PR19, Middle East, May 2022". Fall back to filename if no headline.
    if headline:
        display_title = re.sub(r',?\s*Unresolved UAP Report', '', headline)
        display_title = re.sub(r'\s{2,}', ' ', display_title).strip().strip(',').strip()
    else:
        display_title = stem

    # Tagline: provenance subtitle (originator / mission report / DVIDS)
    tagline = ' · '.join(filter(None, [
        originator,
        f'Mission report {misrep}' if misrep else None,
        f'DVIDS {dvids}' if dvids else None,
    ]))

    lines = []
    a = lines.append
    a('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    a('<movie>')
    a(f'  <title>{escape(display_title)}</title>')
    if asset:
        a(f'  <originaltitle>{escape(asset)}</originaltitle>')
    sort_date = premiered or year
    a(f'  <sorttitle>{escape(("UAP " + sort_date + " " + stem).strip())}</sorttitle>')
    if tagline:
        a(f'  <tagline>{escape(tagline)}</tagline>')
    if plot:
        a(f'  <plot>{escape(plot)}</plot>')
    a(f'  <runtime>{runtime_min}</runtime>')
    if premiered:
        a(f'  <premiered>{escape(premiered)}</premiered>')
    a('  <releasedate>2025-10-07</releasedate>')
    if year:
        a(f'  <year>{escape(year)}</year>')
    a('  <studio>All-domain Anomaly Resolution Office (AARO)</studio>')
    if originator:
        a(f'  <director>{escape(originator)}</director>')
    if country:
        a(f'  <country>{escape(country)}</country>')
    a('  <mpaa>Unclassified // Public Domain</mpaa>')
    for g in genres:
        a(f'  <genre>{g}</genre>')
    for t in tags:
        a(f'  <tag>{escape(t)}</tag>')
    num = stem.replace('DOD_', '')
    a(f'  <uniqueid type="dod" default="true">{escape(num)}</uniqueid>')
    if dvids:
        a(f'  <uniqueid type="dvids">{escape(dvids)}</uniqueid>')
    if asset:
        a(f'  <uniqueid type="asset">{escape(asset)}</uniqueid>')
    a('  <fileinfo>')
    a('    <streamdetails>')
    a('      <video>')
    a('        <codec>h264</codec>')
    a('        <aspect>1.778</aspect>')
    a('        <width>1920</width>')
    a('        <height>1080</height>')
    if seconds:
        a(f'        <durationinseconds>{seconds}</durationinseconds>')
    a('      </video>')
    a('      <audio>')
    a('        <codec>aac</codec>')
    a('        <channels>2</channels>')
    a('      </audio>')
    a('    </streamdetails>')
    a('  </fileinfo>')
    a('</movie>')
    a('')
    return '\n'.join(lines)


def parse_fields(xmp):
    root = ET.fromstring(xmp)
    desc = root.find('rdf:RDF/rdf:Description', NS)
    if desc is None:
        return None
    f = {}
    f['asset'] = first_text(desc, 'title')
    plot = first_text(desc, 'description') or ''
    f['plot'] = plot
    f['headline'] = attr(desc, 'photoshop', 'Headline')
    f['country'] = attr(desc, 'photoshop', 'Country')
    datecreated = attr(desc, 'photoshop', 'DateCreated') or ''
    # premiered = date portion of DateCreated
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', datecreated)
    if m:
        f['premiered'] = f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
        f['year'] = m.group(1)
    elif datecreated[:4].isdigit():
        f['year'] = datecreated[:4]
    # DVIDS id
    dvids = None
    for ident in bag_items(desc, 'xmp', 'Identifier'):
        dm = re.search(r'DVIDS Video ID\s*(\d+)', ident)
        if dm:
            dvids = dm.group(1)
    f['dvids'] = dvids
    # duration -> seconds
    dur = desc.find('xmpDM:duration', NS)
    if dur is not None:
        val = dur.get(f'{{{NS["xmpDM"]}}}value')
        scale = dur.get(f'{{{NS["xmpDM"]}}}scale')
        try:
            num, den = scale.split('/')
            f['seconds'] = round(int(val) * int(num) / int(den))
        except Exception:
            f['seconds'] = None
    # originator from the opening sentence; leave None if unknown (don't assume CENTCOM)
    f['originator'] = None
    om = re.search(r'The (.{3,60}?) (?:submitted|provided) a report of an unidentified', plot)
    if om:
        cmd = om.group(1).strip()
        if cmd.startswith('United States '):
            cmd = 'U.S. ' + cmd[len('United States '):]
        f['originator'] = cmd
    elif 'NASA' in plot or 'NASA' in (f.get('headline') or ''):
        f['originator'] = 'National Aeronautics and Space Administration (NASA)'
    # PR number from headline
    if f.get('headline'):
        pm = re.match(r'\s*(DOW-UAP-PR\d+)', f['headline'], re.I)
        if pm:
            f['pr'] = pm.group(1).upper()
    # mission report ref from plot (DoW-UAP-Dnn)
    mm = re.search(r'(DoW-UAP-D\d+)', plot, re.I)
    if mm:
        f['misrep'] = mm.group(1).upper()
    return f


def main():
    vids = sorted(glob.glob(os.path.join(SEASON_DIR, 'DOD_*.mp4')))
    print(f'Found {len(vids)} videos\n')
    print(f'{"FILE":<22} {"PR":<14} {"MISREP":<14} {"DVIDS":<9} {"SEC":>4}  HEADLINE')
    print('-' * 110)
    ok = 0
    skipped = []
    for v in vids:
        stem = os.path.splitext(os.path.basename(v))[0]
        xmp = extract_xmp(v)
        if not xmp:
            skipped.append((stem, 'no XMP'))
            print(f'{stem:<22} -- NO XMP FOUND --')
            continue
        try:
            fields = parse_fields(xmp)
        except Exception as e:
            skipped.append((stem, f'parse error: {e}'))
            print(f'{stem:<22} -- PARSE ERROR: {e} --')
            continue
        if fields is None:
            skipped.append((stem, 'no rdf:Description'))
            continue
        nfo = build_nfo(stem, fields)
        out = os.path.join(SEASON_DIR, stem + '.nfo')
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(nfo)
        ok += 1
        print(f'{stem:<22} {fields.get("pr",""):<14} {fields.get("misrep",""):<14} '
              f'{fields.get("dvids",""):<9} {str(fields.get("seconds","")):>4}  {fields.get("headline","")}')
    print('-' * 110)
    print(f'\nWrote {ok} .nfo files. Skipped {len(skipped)}.')
    for s in skipped:
        print('  SKIP', s)


if __name__ == '__main__':
    main()
