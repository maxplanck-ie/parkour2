#!/usr/bin/env python3
"""Self-contained HTML report: what Parkour stores vs what restats.py parsed.

Read-only. GETs sequences/run statistics from --url and compares them with the
`new_value` of every row in --db (a restats.sqlite / restats_backfill.sqlite). Nothing
is written to Parkour or to the sqlite.

Classes per (library or lane, field):
  MATCH     stored value equals the parsed value (within --tol); needs the sqlite
            `matches` table (written by restats.py validate), else only
            mismatching rows are known and MATCH counts are zero
  ZERO      stored value is 0, parsed value is not (old parser wrote 0)
  WRONG_*   stored value is non-zero and differs; minor <1 %, mod 1-10 %, major >=10 %
  WRONG     text field (polony_density, custom_recipe, sequencer_side,
            lane_loading_format): stored text differs from parsed text (one class)
  MISSING   field exists in the API but nothing is stored for this entry
  NEW       field the API does not expose at all (fragment_*, peak_*, ...)
  NOENTRY   no Parkour entry for this flowcell/barcode on --url

Segments (filters in the page): run year, sequencer family, library protocol,
analysis type, request (project).

  PARKOUR_PASSWORD=... python restats_report.py --url test --user U \\
      --db backfill.sqlite --out restats_report_test.html [--cache /tmp/rpt]
"""

import argparse
import datetime
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from restats import ENDPOINT, KEY, TEXT_FIELDS, resolveUrl

CLASSES = [
    "MATCH",
    "ZERO",
    "WRONG_minor",
    "WRONG_mod",
    "WRONG_major",
    "WRONG",
    "MISSING",
    "NEW",
    "NOENTRY",
]


def family(sequencer):
    s = (sequencer or "").lower()
    for tag, name in (
        ("aviti", "AVITI"),
        ("novaseq", "NovaSeq"),
        ("miseq", "MiSeq"),
        ("hiseq", "HiSeq"),
        ("nextseq", "NextSeq"),
    ):
        if tag in s:
            return name
    return "other" if s else "unknown"


def as_text(v):
    """TEXT field as str; sqlite REAL affinity reads '220' back as 220.0."""
    if v is None or isinstance(v, str):
        return v
    return str(int(v)) if float(v).is_integer() else str(v)


def classify(stored, new, tol, field=None):
    if stored is None or stored == "":
        return "MISSING"
    if field in TEXT_FIELDS:
        return "MATCH" if as_text(stored) == as_text(new) else "WRONG"
    stored, new = float(stored), float(new)
    if abs(stored - new) <= tol:
        return "MATCH"
    if stored == 0:
        return "ZERO"
    rel = abs(stored - new) / max(abs(stored), abs(new))
    return "WRONG_minor" if rel < 0.01 else "WRONG_mod" if rel < 0.10 else "WRONG_major"


def load(args):
    """kind -> list of API entries, cached as JSON when --cache is given."""
    out = {}
    s = None
    for kind in ("sequences", "matrix"):
        cache = (
            Path(args.cache) / f"{args.url.split('//')[1]}_{kind}.json"
            if args.cache
            else None
        )
        if cache and cache.exists() and not args.refresh:
            out[kind] = json.loads(cache.read_text())
            continue
        if s is None:
            s = requests.Session()
            s.auth = (args.user, os.environ["PARKOUR_PASSWORD"])
            s.verify = args.cert
        r = s.get(
            f"{args.url}/{ENDPOINT[kind]}",
            params={
                "start": "2015-01-01T00:00:00",
                "end": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            },
            timeout=900,
        )
        r.raise_for_status()
        out[kind] = r.json()
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            cache.write_text(json.dumps(out[kind]))
    return out


def build(args):
    entries = load(args)
    index = {}
    apifields = {}
    for kind, lst in entries.items():
        index[kind] = {(e["flowcell_id"], e[KEY[kind]]): e for e in lst}
        apifields[kind] = {k for e in lst for k in e}
    db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    rows = db.execute(
        "SELECT flowcell_id, kind, key, field, new_value, run_date FROM mismatches"
    ).fetchall()
    has_matches = bool(
        db.execute("SELECT 1 FROM sqlite_master WHERE name='matches'").fetchone()
        and db.execute("SELECT 1 FROM matches LIMIT 1").fetchone()
    )
    if has_matches:  # values that equalled the validated deployment: real MATCH counts
        rows += db.execute(  # a key that is also a mismatch counts once, as the mismatch
            "SELECT flowcell_id, kind, key, field, value, run_date FROM matches m"
            " WHERE NOT EXISTS (SELECT 1 FROM mismatches x WHERE x.flowcell_id=m.flowcell_id"
            " AND x.kind=m.kind AND x.key=m.key AND x.field=m.field)"
        ).fetchall()
    # sequencer per flowcell from any entry, so rows without an entry stay segmentable
    fcseq = {}
    for lst in entries.values():
        for e in lst:
            fcseq.setdefault(e["flowcell_id"], e.get("sequencer"))

    vocab = defaultdict(dict)  # dim -> value -> index

    def vi(dim, v):
        return vocab[dim].setdefault(v, len(vocab[dim]))

    agg = Counter()
    detail = []
    for fc, kind, key, field, new, run_date in rows:
        if field in TEXT_FIELDS:
            new = as_text(new)
        e = index[kind].get((fc, key))
        year = (run_date or "")[:4] or "?"
        if e is None:
            seg, cls, stored = (
                (family(fcseq.get(fc)), "(no entry)", "(no entry)", "(no entry)"),
                "NOENTRY",
                None,
            )
        else:
            seg = (
                family(e.get("sequencer")),
                e.get("library_protocol") or e.get("library_preparation") or "?",
                e.get("analysis_type") or "?",
                e.get("request") or "?",
            )
            if field not in apifields[kind]:
                cls, stored = "NEW", None
            else:
                stored = e.get(field)
                cls = classify(stored, new, args.tol, field)
        d = (
            vi("year", year),
            vi("fam", seg[0]),
            vi("proto", seg[1]),
            vi("atype", seg[2]),
            vi("req", seg[3]),
            vi("field", field),
            CLASSES.index(cls),
        )
        agg[d] += 1
        if cls in ("ZERO", "MISSING") or cls.startswith("WRONG"):
            detail.append([fc, key, *d[:6], d[6], stored, new])

    tables = {
        r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    scanned = scan_runs = []
    if "scanned" in tables:
        scanned = [
            list(r)
            for r in db.execute(
                "SELECT source, host, run_dir, flowcell_id, run_date, status, detail, scanned_at, origin"
                " FROM scanned ORDER BY source, run_date, run_dir"
            )
        ]
    if "scan_runs" in tables:
        scan_runs = [
            list(r)
            for r in db.execute(
                "SELECT source, host, since, url, illumina_root, raw_root, aviti_root, group_root,"
                " n_dirs, scanned_at, origin FROM scan_runs ORDER BY scanned_at"
            )
        ]

    def vocab_list(dim):
        return [v for v, _ in sorted(vocab[dim].items(), key=lambda kv: kv[1])]

    return {
        "meta": {
            "url": args.url,
            "db": os.path.basename(args.db),
            "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "rows": len(rows),
            "has_matches": has_matches,
            "entries": {k: len(v) for k, v in entries.items()},
            "tol": args.tol,
        },
        "classes": CLASSES,
        "dims": {
            d: vocab_list(d) for d in ("year", "fam", "proto", "atype", "req", "field")
        },
        "agg": [[*k, n] for k, n in agg.items()],
        "detail": detail,
        "scanned": scanned,
        "scan_runs": scan_runs,
    }


TEMPLATE = Path(__file__).with_name("restats_report.tpl.html")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--url",
        required=True,
        type=resolveUrl,
        help="Parkour deployment: URL or prod/test/dev",
    )
    ap.add_argument("--user", required=True)
    ap.add_argument("--cert", default=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tol", type=float, default=1e-3)
    ap.add_argument(
        "--cache", help="directory for the downloaded API JSON (reused on next run)"
    )
    ap.add_argument("--refresh", action="store_true", help="ignore cached API JSON")
    args = ap.parse_args()
    data = build(args)
    html = TEMPLATE.read_text().replace(
        "/*DATA*/null",
        json.dumps(data, separators=(",", ":"))
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029"),
    )
    Path(args.out).write_text(html)
    print(
        f"wrote {args.out}: {data['meta']['rows']} rows, {len(data['agg'])} groups, {len(data['detail'])} detail rows"
    )


if __name__ == "__main__":
    main()
