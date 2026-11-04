#!/usr/bin/env python3
"""Re-derive Parkour sequencing statistics from flowcell dirs, review, push.

Two steps, so a human decides what changes:

  restats.py validate ...   Parse flowcell dirs, GET what Parkour stores, and log
                            every difference in a SQLite DB. Never writes to Parkour.
  (review)                  python3 -c "import sqlite3; db=sqlite3.connect('restats.sqlite'); \\
                              [print(r) for r in db.execute('SELECT id, flowcell_id, key, field,'
                              ' old_value, new_value FROM mismatches WHERE \"update\" IS NULL')]"
                            (rapidus has no sqlite3 CLI; or copy the .sqlite file locally and
                            use any sqlite client)
                            mark to push:  UPDATE mismatches SET "update" = 1 WHERE ...;
                            mark to keep:  UPDATE mismatches SET "update" = 0 WHERE ...;
  restats.py push ...       Push rows with "update" = 1. Dry run unless --apply.

Table `mismatches`: old_value (Parkour), new_value (flowcell dir), timestamp
(validation time), "update" (NULL = unreviewed, 1 = push, 0 = keep), plus the
flowcell_id / kind / key / field that identify the value.

What is compared (kind -> Parkour endpoint, entry key):
  sequences -> /api/sequences_statistics/  barcode
      reads_pf_sequenced, optical_duplicates   <sample>.metrics | .duplicate.txt
      mapped_reads, dupped_reads, insert_size  Analysis_*/ Bowtie2, flagstat, deepTools (DNA)
      mapped_reads, uniq_mapped, multi_mapped, dupped_reads, assigned_reads
                                               Analysis_*/ STAR, flagstat, featureCounts (RNA)
  matrix    -> /api/run_statistics/        name ("Lane N")
      reads_pf, undetermined_indices, read_1, read_2, cluster_pf
                                               Illumina: interop + Reports/Quality_Metrics.csv
                                               Aviti: RunStats.json
Not compared: confident_reads (needs the library's organism label, which only
Parkour knows).

Why push does GET-merge-POST: the upload views replace a whole entry (per
barcode / per lane), so posting one field would drop the others. Push fetches
the stored entry, strips the fields the GET serializer adds at read time,
changes only the reviewed field(s), and posts the full dict. A row is skipped
if Parkour's current value no longer equals old_value (someone re-pushed since
validation).

Runs on rapidus (needs pandas, requests, and interop for Illumina), e.g.
  PARKOUR_PASSWORD=... /localenv/pipegrp/anaconda/miniconda3/bin/python restats.py \\
      validate --url https://parkour-dev.ie-freiburg.mpg.de --user <user> \\
      --cert /home/pipegrp/cert.pem --since 2026-08-01

NOTE: the parsing below mirrors dissectBCL fakeNews.pushParkour (matrix) and
BigRedButton BRB/ET.py (sequences: getNReads, DNA, RNA). If either changes
what it pushes or where it reads from, update this file too.
"""

import argparse
import datetime
import glob
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import requests


@dataclass
class Roots:
    illumina_root: str = "/rapidus/data/sequencing_data/Illumina/NovaSeq6000"
    illumina_raw: str = "/dont_touch_this/short_runs/Illumina/NovaSeq6000"
    aviti_root: str = "/rapidus/data/sequencing_data/ElementBiosciences"
    group_data: str = "/data"


ENDPOINT = {"sequences": "api/sequences_statistics/", "matrix": "api/run_statistics/"}
KEY = {"sequences": "barcode", "matrix": "name"}
# Added by the GET serializers at read time, never stored in the JSONField.
READ_TIME_KEYS = {
    "sequences": {
        "pk", "flowcell_id", "create_time", "sequencer", "request", "name", "lane",
        "pool", "library_protocol", "analysis_type", "reads_pf_requested",
    },
    "matrix": {
        "pk", "flowcell_id", "create_time", "sequencer", "read_length",
        "library_preparation", "analysis_type", "loading_concentration", "phix",
        "pool", "request",
    },
}  # fmt: skip
TIME = "%Y-%m-%dT%H:%M:%S"
# Parkour's GET filters on Flowcell.create_time, which precedes the run date.
WINDOW_BEFORE, WINDOW_AFTER = datetime.timedelta(days=180), datetime.timedelta(days=30)

SCHEMA = """
CREATE TABLE IF NOT EXISTS mismatches (
    id INTEGER PRIMARY KEY,
    flowcell_id TEXT NOT NULL,
    kind TEXT NOT NULL,          -- sequences | matrix
    key TEXT NOT NULL,           -- barcode | 'Lane N'
    field TEXT NOT NULL,
    old_value REAL,              -- in Parkour at validation time (NULL = absent)
    new_value REAL,              -- parsed from the flowcell dir
    timestamp TEXT NOT NULL,
    "update" INTEGER,            -- NULL unreviewed, 1 push, 0 keep old
    run_date TEXT NOT NULL,
    pushed_at TEXT,
    UNIQUE (flowcell_id, kind, key, field)
)
"""


def runInfo(runDir, roots):
    aviti = Path(roots.aviti_root) in runDir.parents  # Aviti dirs sit under AV<id>/
    parts = runDir.name.split("_")
    fcid = (parts[2] if aviti else parts[3][1:]).split("-")[-1]
    date = datetime.datetime.strptime(parts[0], "%Y%m%d" if aviti else "%y%m%d")
    return aviti, fcid, date


def discoverRuns(since, roots):
    runs = glob.glob(f"{roots.illumina_root}/*_lanes_*") + glob.glob(
        f"{roots.aviti_root}/*/*_lanes_*"
    )
    out = []
    for r in map(Path, sorted(runs)):
        if not r.is_dir():
            continue
        try:
            aviti, _, date = runInfo(r, roots)
        except (ValueError, IndexError):
            print(f"  skip {r}: cannot parse run name")
            continue
        if date < since:
            continue
        if aviti and not (r / "RunStats.json").exists():
            print(f"  skip {r.name}: no RunStats.json")
            continue
        out.append(r)
    return out


# ------------------------------------------------------------------ parsers
def add(cand, key, field, value):
    cand[(key, field)].add(round(float(value), 6))


def laneStats(runDir, aviti, roots):
    """{(lane, field): value}; mirrors dissectBCL fakeNews.pushParkour."""
    out = {}
    if aviti:
        data = json.loads((runDir / "RunStats.json").read_text())
        for ln in data["Lanes"]:
            name = f"Lane {ln['Lane']}"
            out[(name, "reads_pf")] = float(ln["NumPolonies"])
            out[(name, "read_1")] = ln["Reads"][0]["PercentQ30"]
            if len(ln["Reads"]) > 1:
                out[(name, "read_2")] = ln["Reads"][1]["PercentQ30"]
            out[(name, "cluster_pf")] = ln["PercentQ30"]
            out[(name, "undetermined_indices")] = round(
                100 - ln["PercentAssignedReads"], 2
            )
        return out

    import interop
    import pandas as pd

    raw = Path(roots.illumina_raw, re.sub(r"_lanes_.*$", "", runDir.name))
    iop = pd.DataFrame(interop.summary(interop.read(str(raw)), "Lane"))
    qdf = pd.read_csv(runDir / "Reports" / "Quality_Metrics.csv")
    for lane in qdf["Lane"].unique():
        sub = qdf[qdf["Lane"] == lane]
        name = f"Lane {lane}"
        sel = iop[(iop["ReadNumber"] == 1) & (iop["Lane"] == lane)]["Reads Pf"].values
        out[(name, "reads_pf")] = float(sel[0])
        sub_und = sub[sub["SampleID"] == "Undetermined"]
        if (
            not sub_und.empty
        ):  # lanes_1/lanes_2 dirs: only one has this lane's Undetermined
            out[(name, "undetermined_indices")] = round(
                sub_und["YieldQ30"].sum() / sub["YieldQ30"].sum() * 100, 2
            )
        real = sub[sub["SampleID"] != "Undetermined"]
        for read, q30 in real.groupby("ReadNumber")["% Q30"].mean().to_dict().items():
            if "I" not in str(read):
                out[(name, f"read_{read}")] = round(q30 * 100, 2)
        out[(name, "cluster_pf")] = round(
            real["YieldQ30"].sum() / real["Yield"].sum() * 100, 2
        )
    return out


def seqStats(runDir, roots):
    """{(barcode, field): {values}}; mirrors BRB ET.getNReads / DNA / RNA."""
    import pandas as pd

    cand, s2l = defaultdict(set), {}
    # splitFastq: "<optical_dups> <total_reads>" in <sample>.metrics, older runs
    # <sample>.duplicate.txt. Project_* holds .metrics for runs before dissectBCL
    # v1.3.5, FASTQC_Project_* after.
    for sdir in runDir.glob("*Project_*/Sample_*"):
        bc = sdir.name[len("Sample_") :]
        for f in list(sdir.glob("*.metrics")) or list(sdir.glob("*.duplicate.txt")):
            opt, total = map(int, f.read_text().split())
            add(cand, bc, "reads_pf_sequenced", total - opt)
            add(cand, bc, "optical_duplicates", 100.0 * opt / total if total else -1.0)
        for z in sdir.glob("*_R1_fastqc.zip"):
            s2l[z.name[: -len("_R1_fastqc.zip")]] = bc

    adirs = glob.glob(f"{runDir}/Analysis_*/*") + glob.glob(
        f"{roots.group_data}/*/sequencing_data*/{runDir.name}/Analysis_*/*"
    )
    for adir in map(Path, adirs):
        if (adir / "RELACS_sampleSheet.txt").exists():
            continue  # BRB pushes no analysis stats for RELACS
        mq = adir / "multiQC" / "multiqc_data"
        dup = {}
        if (mq / "multiqc_samtools_flagstat.txt").exists():
            df = pd.read_csv(
                mq / "multiqc_samtools_flagstat.txt",
                sep="\t",
                usecols=["Sample", "total_passed", "duplicates_passed"],
            )
            dup = dict(
                zip(
                    df["Sample"].astype(str),
                    df["duplicates_passed"] / df["total_passed"] * 100,
                )
            )
        # DNA
        for f in (adir / "Bowtie2").glob("*.Bowtie2_summary.txt"):
            sample = f.name.split(".Bowtie2_summary")[0]
            if sample not in s2l:
                continue
            add(
                cand,
                s2l[sample],
                "mapped_reads",
                f.read_text().split("\n")[-2].split("%")[0],
            )
            if sample in dup:
                add(cand, s2l[sample], "dupped_reads", dup[sample])
        frag = adir / "deepTools_qc/bamPEFragmentSize/fragmentSize.metric.tsv"
        if frag.exists() and (adir / "Bowtie2").exists():
            fdf = pd.read_csv(frag, sep="\t", index_col=0)
            for sample, bc in s2l.items():
                row = f"filtered_bam/{sample}.filtered.bam"
                if row in fdf.index:
                    add(cand, bc, "insert_size", int(fdf.loc[row, "Frag. Len. Median"]))
        # RNA
        assigned = {}
        if (mq / "multiqc_featurecounts.txt").exists():
            adf = pd.read_csv(
                mq / "multiqc_featurecounts.txt",
                sep="\t",
                usecols=["Sample", "Total", "Assigned"],
            )
            assigned = dict(
                zip(adf["Sample"].astype(str), adf["Assigned"] / adf["Total"] * 100)
            )
        for f in adir.glob("STAR/*/*.Log.final.out"):
            sample = f.name.split(".")[0]
            if sample not in s2l:
                continue
            tot = uniq = multi = 0.0
            for line in f.read_text().splitlines():
                if "Uniquely mapped reads %" in line:
                    uniq = float(line.strip().split("\t")[-1][:-1])
                    tot += uniq
                elif "% of reads mapped to multiple loci" in line:
                    multi = float(line.strip().split("\t")[-1][:-1])
                    tot += multi
            bc = s2l[sample]
            add(cand, bc, "mapped_reads", tot)
            add(cand, bc, "uniq_mapped", uniq)
            add(cand, bc, "multi_mapped", multi)
            if sample in dup:
                add(cand, bc, "dupped_reads", dup[sample])
            if sample + ".filtered" in assigned:
                add(cand, bc, "assigned_reads", assigned[sample + ".filtered"])
    return cand


# ------------------------------------------------------------------ Parkour
def session(args):
    s = requests.Session()
    s.auth = (args.user, os.environ["PARKOUR_PASSWORD"])
    s.verify = args.cert
    return s


def endpoint(args, kind):
    return args.url.rstrip("/") + "/" + ENDPOINT[kind]


def fetch(s, args, kind, start, end):
    r = s.get(
        endpoint(args, kind),
        params={
            "start": (start - WINDOW_BEFORE).strftime(TIME),
            "end": (end + WINDOW_AFTER).strftime(TIME),
        },
    )
    r.raise_for_status()
    byFc = defaultdict(dict)
    for e in r.json():
        byFc[e["flowcell_id"]][e[KEY[kind]]] = e
    return byFc


def differs(old, new, tol):
    if old == "":  # Parkour stores '' for "never set"
        old = None
    if old is None or new is None:
        return old is not new
    return abs(float(old) - new) > tol


# --------------------------------------------------------------- validate
def validate(args):
    roots = Roots(
        illumina_root=args.illumina_root,
        illumina_raw=args.raw_root,
        aviti_root=args.aviti_root,
        group_data=args.group_root,
    )
    runs = [Path(r) for r in args.runDirs]
    if args.since:
        runs += discoverRuns(datetime.datetime.strptime(args.since, "%Y-%m-%d"), roots)
    ok = []
    for r in runs:
        try:
            runInfo(r, roots)
        except (ValueError, IndexError):
            print(f"  skip {r}: not a short-read flowcell dir name")
            continue
        ok.append(r)
    runs = ok
    if not runs:
        sys.exit("no flowcell dirs given / found")

    cand = {
        "sequences": defaultdict(lambda: defaultdict(set)),
        "matrix": defaultdict(lambda: defaultdict(set)),
    }
    dates = {}
    # Aviti: every lanes_N dir's RunStats.json lists all lanes, but assigned-read
    # percentages are per dir, and dissectBCL pushes once per dir (last write wins
    # in Parkour). Compare Aviti lane stats against the highest lanes_N dir only.
    lastAviti = {}
    for runDir in runs:
        aviti, fcid, _ = runInfo(runDir, roots)
        if aviti:
            n = int(re.search(r"_lanes_(\d+)", runDir.name).group(1))
            lastAviti[fcid] = max(lastAviti.get(fcid, (0, runDir)), (n, runDir))
    for runDir in runs:
        aviti, fcid, date = runInfo(runDir, roots)
        dates[fcid] = min(date, dates.get(fcid, date))
        if not aviti or lastAviti[fcid][1] == runDir:
            try:
                for k, v in laneStats(runDir, aviti, roots).items():
                    cand["matrix"][fcid][k].add(round(float(v), 6))
            except Exception as e:  # noqa: BLE001 - report, carry on with other runs
                print(f"  {runDir.name}: lane stats failed: {e!r}")
        try:
            for k, vs in seqStats(runDir, roots).items():
                cand["sequences"][fcid][k] |= vs
        except Exception as e:  # noqa: BLE001
            print(f"  {runDir.name}: library stats failed: {e!r}")
    print(f"parsed {len(runs)} run dirs, {len(dates)} flowcells")

    s = session(args)
    start, end = min(dates.values()), max(dates.values())
    db = sqlite3.connect(args.db)
    db.execute(SCHEMA)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    stats = Counter()
    for kind in ("sequences", "matrix"):
        stored = fetch(s, args, kind, start, end)
        for fcid, fields in cand[kind].items():
            entries = stored.get(fcid)
            if not entries:
                print(f"  {fcid} [{kind}]: not in Parkour (archived / outside window)")
                stats[kind, "flowcell not in Parkour"] += 1
                continue
            for (key, field), vals in fields.items():
                if key not in entries:
                    continue  # not an entry Parkour has
                if len(vals) != 1:
                    print(f"  CONFLICT {fcid} {key} {field}: {sorted(vals)} (skipped)")
                    stats[kind, "conflict"] += 1
                    continue
                new = next(iter(vals))
                old = entries[key].get(field)
                stats[kind, "compared"] += 1
                if not differs(old, new, args.tol):
                    continue
                stats[kind, f"mismatch {field}"] += 1
                row = db.execute(
                    "SELECT old_value, new_value FROM mismatches "
                    "WHERE flowcell_id=? AND kind=? AND key=? AND field=?",
                    (fcid, kind, key, field),
                ).fetchone()
                if row is None:
                    db.execute(
                        "INSERT INTO mismatches (flowcell_id, kind, key, field, old_value,"
                        " new_value, timestamp, run_date) VALUES (?,?,?,?,?,?,?,?)",
                        (
                            fcid,
                            kind,
                            key,
                            field,
                            old,
                            new,
                            now,
                            dates[fcid].isoformat(),
                        ),
                    )
                elif row != (old, new):  # changed since last validation: re-review
                    db.execute(
                        'UPDATE mismatches SET old_value=?, new_value=?, timestamp=?, "update"=NULL,'
                        " pushed_at=NULL WHERE flowcell_id=? AND kind=? AND key=? AND field=?",
                        (old, new, now, fcid, kind, key, field),
                    )
    db.commit()
    for (kind, what), n in sorted(stats.items()):
        print(f"{kind:9} {what:32} {n}")
    pending = db.execute(
        'SELECT COUNT(*) FROM mismatches WHERE "update" IS NULL'
    ).fetchone()[0]
    print(f"{pending} unreviewed rows in {args.db}")


# ------------------------------------------------------------------- push
def push(args):
    db = sqlite3.connect(args.db)
    rows = db.execute(
        "SELECT id, flowcell_id, kind, key, field, old_value, new_value, run_date "
        'FROM mismatches WHERE "update" = 1 AND pushed_at IS NULL'
    ).fetchall()
    if not rows:
        sys.exit("nothing to push: no rows with update=1 that are not yet pushed")
    s = session(args)
    dates = [datetime.datetime.fromisoformat(r[7]) for r in rows]
    stored = {
        k: fetch(s, args, k, min(dates), max(dates)) for k in {r[2] for r in rows}
    }

    groups = defaultdict(list)
    for r in rows:
        groups[r[1], r[2]].append(r)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    rc = 0
    for (fcid, kind), rs in groups.items():
        entries = stored[kind].get(fcid, {})
        out, ids = {}, []
        for rid, _, _, key, field, old, new, _ in rs:
            e = entries.get(key)
            if e is None:
                print(f"  SKIP {fcid} {key}: not in Parkour")
                continue
            if differs(e.get(field), old, 1e-9):
                print(
                    f"  SKIP {fcid} {key} {field}: Parkour now {e.get(field)}, "
                    f"was {old} at validation; re-run validate"
                )
                continue
            if key not in out:
                out[key] = {k: v for k, v in e.items() if k not in READ_TIME_KEYS[kind]}
            out[key][field] = new
            ids.append(rid)
            print(f"  {fcid} {key} {field}: {old} -> {new}")
        if not out:
            continue
        if not args.apply:
            continue
        r = s.post(
            endpoint(args, kind) + "upload/",
            data={"flowcell_id": fcid, kind: json.dumps(list(out.values()))},
        )
        print(
            f"  POST {fcid} [{kind}] {len(out)} entries -> {r.status_code} {r.text[:120]}"
        )
        if r.status_code == 200:
            db.executemany(
                "UPDATE mismatches SET pushed_at=? WHERE id=?", [(now, i) for i in ids]
            )
            db.commit()
        else:
            rc = 1
    if not args.apply:
        print("dry run; pass --apply to POST")
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "push"):
        p = sub.add_parser(name)
        p.add_argument("--url", required=True, help="Parkour base URL")
        p.add_argument("--user", required=True)
        p.add_argument("--cert", default=True, help="CA bundle (default: system)")
        p.add_argument("--db", default=str(Path(__file__).with_name("restats.sqlite")))
        if name == "validate":
            p.add_argument("runDirs", nargs="*", help="flowcell dirs (…_lanes_N)")
            p.add_argument(
                "--since", help="also scan the rapidus roots, runs from YYYY-MM-DD"
            )
            p.add_argument("--tol", type=float, default=1e-3, help="abs. tolerance")
            p.add_argument(
                "--illumina-root",
                default="/rapidus/data/sequencing_data/Illumina/NovaSeq6000",
            )
            p.add_argument(
                "--raw-root", default="/dont_touch_this/short_runs/Illumina/NovaSeq6000"
            )
            p.add_argument(
                "--aviti-root",
                default="/rapidus/data/sequencing_data/ElementBiosciences",
            )
            p.add_argument("--group-root", default="/data")
        else:
            p.add_argument(
                "--apply", action="store_true", help="POST (default: dry run)"
            )
    args = ap.parse_args()
    return validate(args) if args.cmd == "validate" else push(args)


if __name__ == "__main__":
    sys.exit(main())
