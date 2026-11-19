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
      fragment_q1/median/q3/p10/p90, fragments_total
                                               deepTools fragmentSize.metric.tsv, flagstat read1_passed
      peak_count, frip, peak_genome_coverage   Analysis_*/ MACS2_QC (ATAC)
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

Every subcommand that talks to Parkour (validate, push, compare) takes a required
--url: a full URL, or the short names prod / test / dev. There is no default, so
nothing hits a deployment by accident. `push --apply` refuses the prod URL.
`compare` is read-only: it GETs the same flowcells from --url and lists, per
field, the stored value next to the value parsed into --db.

Runs on rapidus (needs pandas, requests, and interop for Illumina), e.g.
  PARKOUR_PASSWORD=... /localenv/pipegrp/anaconda/miniconda3/bin/python restats.py \\
      validate --url dev --user <user> --cert /home/pipegrp/cert.pem --since 2026-08-01
  ... restats.py compare --url test --user <user> --db restats_backfill.sqlite --out cmp.tsv

NOTE: the parsing below mirrors dissectBCL fakeNews.pushParkour (matrix) and
BigRedButton BRB/ET.py (sequences: getNReads, DNA, RNA). If either changes
what it pushes or where it reads from, update this file too.
"""

import argparse
import csv
import datetime
import glob
import json
import os
import re
import socket
import sqlite3
import urllib.parse
import xml.etree.ElementTree as ET
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


# Mirrors BRB ET.FRAGMENT_COLS (deepTools fragmentSize.metric.tsv columns, bp).
FRAGMENT_COLS = {
    "fragment_q1": "Frag. Len. 1st. Qu.",
    "fragment_median": "Frag. Len. Median",
    "fragment_q3": "Frag. Len. 3rd Qu.",
    "fragment_p10": "Frag. Len. 10%",
    "fragment_p90": "Frag. Len. 90%",
}

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
);
-- parsed values that already equal Parkour at validation time; lets the report
-- count real MATCHes (a value that differs is in `mismatches` instead).
CREATE TABLE IF NOT EXISTS matches (
    flowcell_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    key TEXT NOT NULL,
    field TEXT NOT NULL,
    value REAL,
    run_date TEXT NOT NULL,
    UNIQUE (flowcell_id, kind, key, field)
);
-- every flowcell dir validate considered, so a rerun knows what was scanned
CREATE TABLE IF NOT EXISTS scanned (
    run_dir TEXT NOT NULL,
    host TEXT NOT NULL,
    source TEXT NOT NULL,
    flowcell_id TEXT,
    run_date TEXT,
    status TEXT NOT NULL,   -- parsed | lane stats failed | library stats failed | skipped
    detail TEXT,
    scanned_at TEXT NOT NULL,
    origin TEXT NOT NULL DEFAULT 'validate',  -- validate | reconstructed
    UNIQUE (host, run_dir)
);
-- one row per validate invocation: roots and deployment, to reproduce the scan
CREATE TABLE IF NOT EXISTS scan_runs (
    host TEXT NOT NULL,
    source TEXT NOT NULL,
    since TEXT,
    url TEXT NOT NULL,
    illumina_root TEXT,
    raw_root TEXT,
    aviti_root TEXT,
    group_root TEXT,
    n_dirs INTEGER NOT NULL,
    scanned_at TEXT NOT NULL,
    origin TEXT NOT NULL DEFAULT 'validate',
    UNIQUE (host, source, scanned_at)
)
"""


def runInfo(runDir, roots):
    aviti = Path(roots.aviti_root) in runDir.parents  # Aviti dirs sit under AV<id>/
    parts = runDir.name.split("_")
    fcid = (parts[2] if aviti else parts[3][1:]).split("-")[-1]
    date = datetime.datetime.strptime(parts[0], "%Y%m%d" if aviti else "%y%m%d")
    return aviti, fcid, date


def discoverRuns(since, roots):
    runs = (
        glob.glob(f"{roots.illumina_root}/*_lanes_*")
        + glob.glob(f"{roots.aviti_root}/*/*_lanes_*")  # rapidus: AV<instrument>/<run>
        + glob.glob(
            f"{roots.aviti_root}/*_lanes_*"
        )  # longus2: runs directly under the root
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
# Text fields: compared by string equality, never parsed as numbers. Stored in the
# same sqlite columns as numbers (SQLite keeps non-numeric text as TEXT).
TEXT_FIELDS = {
    "polony_density",
    "custom_recipe",
    "sequencer_side",
    "lane_loading_format",
}


def add(cand, key, field, value):
    if field in TEXT_FIELDS:
        cand[(key, field)].add(str(value))
        return
    value = float(value)
    if value != value:  # NaN: BRB would send null, nothing to compare
        return
    cand[(key, field)].add(round(value, 6))


# Illumina Lane summary (interop, Read 1): column -> (Parkour field, scale).
ILLUMINA_LANE_COLS = {
    "% Occupied": ("percent_occupied", 1),
    "Projected Yield G": ("gb_yield", 1),
    "% Aligned": ("phix_alignment_rate", 100),
    "% Pf": ("percent_pf", 1),
}


def parseAvitiRunParameters(path):
    """AVITI RunParameters.json -> run-level fields; a missing key is left out."""
    data = json.loads(Path(path).read_text())
    adv = data.get("AdvancedSettings")
    if not isinstance(adv, dict):
        adv = {}
    pmg = data.get("ShiftPMGBy")
    if pmg is None:
        pmg = adv.get("ShiftPmgBy")
    recipe = adv.get("CustomRecipeName")
    side = data.get("Side")
    fields = {
        "polony_density": adv.get("PolonyDensity"),
        "pmg_shift": pmg,
        "custom_recipe": None if recipe is None else str(recipe).removesuffix(".rec"),
        "occupancy_score": adv.get("OccupancyScore"),
        "sequencer_side": None if side is None else side.replace("Side", ""),
    }
    return {k: v for k, v in fields.items() if v is not None}


def parseAvitiLoadingFormat(path):
    """RunManifest.csv [SAMPLES] Lane column: "1+2" -> "1 pool"; lanes 1 and 2 -> "2 pools"."""
    lanes, inSamples, header = set(), False, None
    with open(path, newline="") as f:
        for row in csv.reader(f):
            if not row:
                continue
            if row[0].startswith("["):
                inSamples, header = row[0] == "[SAMPLES]", None
            elif inSamples and header is None:
                header = row
            elif inSamples and "Lane" in header and len(row) == len(header):
                lanes.add(row[header.index("Lane")].strip())
    if "1+2" in lanes:
        return "1 pool"
    if {"1", "2"} <= lanes:
        return "2 pools"
    return "1 pool" if lanes else None


def aviti_run_params(runDir):
    """Run-level AVITI fields from the run dir; a missing file leaves its fields out."""
    out = {}
    if (runDir / "RunParameters.json").exists():
        out = parseAvitiRunParameters(runDir / "RunParameters.json")
    if (runDir / "RunManifest.csv").exists():
        loading = parseAvitiLoadingFormat(runDir / "RunManifest.csv")
        if loading:
            out["lane_loading_format"] = loading
    return out


def laneStats(runDir, aviti, roots):
    """{(lane, field): value}; mirrors dissectBCL fakeNews.pushParkour."""
    out = {}
    if aviti:
        data = json.loads((runDir / "RunStats.json").read_text())
        run = aviti_run_params(runDir)
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
            if ln.get("TotalYield") is not None:
                out[(name, "gb_yield")] = round(ln["TotalYield"], 2)
            for field, value in run.items():
                out[(name, field)] = value
        return out

    import interop
    import pandas as pd

    raw = Path(roots.illumina_raw, re.sub(r"_lanes_.*$", "", runDir.name))
    iop = pd.DataFrame(interop.summary(interop.read(str(raw)), "Lane"))
    qdf = pd.read_csv(runDir / "Reports" / "Quality_Metrics.csv")
    raw_rp = raw / "RunParameters.xml"
    loading = None
    if raw_rp.exists():
        wf = ET.parse(raw_rp).getroot().findtext(".//WorkflowType")
        # unknown non-empty values are kept raw, like dissectBCL parseIlluminaRunParameters
        loading = {"NovaSeqXp": "XP", "NovaSeqStandard": "Standard"}.get(wf, wf or None)
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
        row = iop[(iop["ReadNumber"] == 1) & (iop["Lane"] == lane)]
        for col, (field, scale) in ILLUMINA_LANE_COLS.items():
            vals = row[col].values if col in row else []
            if len(vals) and not pd.isna(vals[0]):
                out[(name, field)] = round(float(vals[0]) * scale, 2)
        if loading:
            out[(name, "lane_loading_format")] = loading
    return out


def pairsStats(fname):
    """{key: int} from a pairtools *.dedup.stats file (tab separated key/value lines)."""
    out = {}
    with open(fname) as f:
        for line in f:
            key, _, val = line.rstrip("\n").partition("\t")
            if val.isdigit():
                out[key] = int(val)
    return out


def firstByKey(keys, values):
    """BRB _multiqcRows takes the first row of a sample; dict(zip()) would keep the last."""
    out = {}
    for k, v in zip(keys, values):
        out.setdefault(k, v)
    return out


def seqStats(runDir, roots):
    """{(barcode, field): {values}}; mirrors BRB ET.getNReads / DNA / RNA."""
    import pandas as pd

    cand, s2lAll = defaultdict(set), {}
    # splitFastq: "<optical_dups> <total_reads>" in <sample>.metrics, older runs
    # <sample>.duplicate.txt. Project_* holds .metrics for runs before dissectBCL
    # v1.3.5, FASTQC_Project_* after.
    for fdir in sorted(runDir.glob("FASTQC_Project_*/Sample_*")):
        bc = fdir.name[len("Sample_") :]
        project = fdir.parent.name.split("Project_", 1)[1]
        # BRB scopes sample names to one project (Analysis_<p> pairs with FASTQC_Project_<p>)
        s2l = s2lAll.setdefault(project, {})
        zips = list(fdir.glob("*_R1_fastqc.zip"))
        if not zips:
            continue  # BRB drops a library without a R1 fastqc zip: no stats at all
        # BRB keeps only the first R1 sample of a library (baseDict[lib][0])
        first = min(zips)
        s2l[first.name[: -len("_R1_fastqc.zip")]] = bc
        # same rule as BRB getNReads: FASTQC_Project_* first, then Project_*; in each
        # the first usable file wins (.metrics before .duplicate.txt); a usable file is
        # "<digits> <digits>" with optical <= total
        for sdir in (fdir, runDir / f"Project_{project}" / fdir.name):
            files = sorted(sdir.glob("*.metrics")) + sorted(
                sdir.glob("*.duplicate.txt")
            )
            found = False
            for f in files:
                text = f.read_text().split()
                if (
                    len(text) != 2
                    or not all(t.isdigit() for t in text)
                    or int(text[0]) > int(text[1])
                ):
                    print(
                        f"  {runDir.name}: {f.name}: not '<opt> <total>' ({text[:3]}), skipped"
                    )
                    continue
                opt, total = map(int, text)
                add(cand, bc, "reads_pf_sequenced", total - opt)
                add(
                    cand,
                    bc,
                    "optical_duplicates",
                    100.0 * opt / total if total else -1.0,
                )
                found = True
                break
            if found:
                break

    adirs = glob.glob(f"{runDir}/Analysis_*/*") + glob.glob(
        f"{roots.group_data}/*/sequencing_data*/{runDir.name}/Analysis_*/*"
    )
    for adir in map(Path, adirs):
        s2l = s2lAll.get(adir.parent.name[len("Analysis_") :], {})
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
            dup = firstByKey(
                df["Sample"].astype(str),
                df["duplicates_passed"] / df["total_passed"] * 100,
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
                    for key, col in FRAGMENT_COLS.items():
                        add(cand, bc, key, int(fdf.loc[row, col]))
        fs = mq / "multiqc_samtools_flagstat.txt"
        if fs.exists() and (adir / "Bowtie2").exists():
            rdf = pd.read_csv(fs, sep="\t", usecols=["Sample", "read1_passed"])
            r1 = firstByKey(rdf["Sample"].astype(str), rdf["read1_passed"])
            for sample, bc in s2l.items():
                if sample in r1:
                    add(cand, bc, "fragments_total", int(r1[sample]))
        # RNA
        assigned = {}
        if (mq / "multiqc_featurecounts.txt").exists():
            adf = pd.read_csv(
                mq / "multiqc_featurecounts.txt",
                sep="\t",
                usecols=["Sample", "Total", "Assigned"],
            )
            assigned = firstByKey(
                adf["Sample"].astype(str), adf["Assigned"] / adf["Total"] * 100
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
            if sample not in dup or sample + ".filtered" not in assigned:
                continue  # BRB RNA() needs STAR, flagstat and featureCounts: else base only
            bc = s2l[sample]
            add(cand, bc, "mapped_reads", tot)
            add(cand, bc, "uniq_mapped", uniq)
            add(cand, bc, "multi_mapped", multi)
            add(cand, bc, "dupped_reads", dup[sample])
            add(cand, bc, "assigned_reads", assigned[sample + ".filtered"])
        # Hi-C: one multiqc_hicexplorer row per matrix file, named <sample>_bs<binsize>.cool
        hic = mq / "multiqc_hicexplorer.txt"
        if hic.exists():
            hdf = pd.read_csv(
                hic,
                sep="\t",
                usecols=["Sample", "Pairs mappable, unique and high quality_pct"],
            )
            rate = {}  # several bin sizes per sample: the 10kb row wins, else the first row
            for name, pct in zip(hdf["Sample"].astype(str), hdf.iloc[:, 1]):
                sample = re.sub(r"_bs\d+[A-Za-z]*\.cool$", "", name)
                if sample in s2l and (
                    sample not in rate or name.endswith("_bs10kb.cool")
                ):
                    rate[sample] = pct
            for sample, pct in rate.items():
                add(cand, s2l[sample], "uniq_mapped", pct)
        # peak QC (ATAC / ChIP / CUT&Tag runs with peak calling); mirrors ET.peakQC
        for f in adir.glob("MACS2_QC/*.filtered.BAM_peaks.qc.txt"):
            sample = f.name.removesuffix(".filtered.BAM_peaks.qc.txt")
            if sample not in s2l:
                continue
            row = pd.read_csv(f, sep="\t").iloc[0]
            add(cand, s2l[sample], "peak_count", int(row["peak_count"]))
            add(cand, s2l[sample], "frip", float(row["FRiP"]))
            add(
                cand,
                s2l[sample],
                "peak_genome_coverage",
                float(row["peak_genome_coverage"]),
            )
        # micro-C: pairtools dedup summary per sample; mirrors BRB ET.makePairs
        for sample, bc in s2l.items():
            pf = adir / "pairs" / f"{sample}.pairs.dedup.stats"
            if not pf.exists():
                continue
            st = pairsStats(pf)
            if {"total", "total_mapped", "total_dups"} <= st.keys():
                tot, mp, dup = st["total"], st["total_mapped"], st["total_dups"]
                if tot:
                    add(cand, bc, "mapped_reads", 100.0 * mp / tot)
                if mp:
                    add(cand, bc, "dupped_reads", 100.0 * dup / mp)
    return cand


# ------------------------------------------------------------------ Parkour
# Short names for --url. Anything else must be a full http(s) URL.
DEPLOYMENTS = {
    "prod": "https://parkour.ie-freiburg.mpg.de",
    "test": "https://parkour-test.ie-freiburg.mpg.de",
    "dev": "https://parkour-dev.ie-freiburg.mpg.de",
}


def resolveUrl(value):
    url = DEPLOYMENTS.get(value, value)
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise argparse.ArgumentTypeError(
            f"{value!r}: expected a URL or one of {sorted(DEPLOYMENTS)}"
        )
    if parts.username or parts.password:
        raise argparse.ArgumentTypeError("credentials in the URL are not accepted")
    return url.rstrip("/")


def isProd(url):
    prod = urllib.parse.urlsplit(DEPLOYMENTS["prod"]).hostname
    return (urllib.parse.urlsplit(url).hostname or "").lower().rstrip(".") == prod


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


def differs(old, new, tol, field=None):
    if old == "":  # Parkour stores '' for "never set"
        old = None
    if new == "":
        new = None
    if old is None or new is None:
        return old is not new
    if field in TEXT_FIELDS:
        return str(old) != str(new)
    try:
        return abs(float(old) - float(new)) > tol
    except (TypeError, ValueError):  # non-numeric stored value: report it, do not crash
        return True


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
    scan = {}  # run dir -> [flowcell_id, run_date, status, detail]

    def mark(runDir, status, detail):
        row = scan[str(runDir)]
        row[2] = status if row[2] == "parsed" else f"{row[2]}, {status}"
        row[3] = f"{row[3]}; {detail}" if row[3] else detail

    for r in runs:
        try:
            _, fcid, date = runInfo(r, roots)
        except (ValueError, IndexError):
            print(f"  skip {r}: not a short-read flowcell dir name")
            scan[str(r)] = [None, None, "skipped", "not a short-read flowcell dir name"]
            continue
        scan[str(r)] = [fcid, date.isoformat(), "parsed", None]
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
            m = re.search(r"_lanes_(\d+)", runDir.name)
            n = int(m.group(1)) if m else 0  # name without lanes_N: lowest priority
            lastAviti[fcid] = max(lastAviti.get(fcid, (0, runDir)), (n, runDir))
    for runDir in runs:
        aviti, fcid, date = runInfo(runDir, roots)
        dates[fcid] = min(date, dates.get(fcid, date))
        if not aviti or lastAviti[fcid][1] == runDir:
            try:
                for k, v in laneStats(runDir, aviti, roots).items():
                    add(cand["matrix"][fcid], k[0], k[1], v)
            except Exception as e:  # noqa: BLE001 - report, carry on with other runs
                print(f"  {runDir.name}: lane stats failed: {e!r}")
                mark(runDir, "lane stats failed", repr(e))
        try:
            for k, vs in seqStats(runDir, roots).items():
                cand["sequences"][fcid][k] |= vs
        except Exception as e:  # noqa: BLE001
            print(f"  {runDir.name}: library stats failed: {e!r}")
            mark(runDir, "library stats failed", repr(e))
    print(f"parsed {len(runs)} run dirs, {len(dates)} flowcells")

    s = session(args)
    start, end = min(dates.values()), max(dates.values())
    db = sqlite3.connect(args.db)
    db.executescript(SCHEMA)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    host = socket.gethostname()
    db.executemany(
        "INSERT OR REPLACE INTO scanned VALUES (?,?,?,?,?,?,?,?,'validate')",
        [(d, host, args.source, *v, now) for d, v in scan.items()],
    )
    db.execute(
        "INSERT OR REPLACE INTO scan_runs VALUES (?,?,?,?,?,?,?,?,?,?,'validate')",
        (
            host,
            args.source,
            args.since,
            args.url,
            args.illumina_root,
            args.raw_root,
            args.aviti_root,
            args.group_root,
            len(scan),
            now,
        ),
    )
    stats = Counter()
    fetched = {k: fetch(s, args, k, start, end) for k in ("matrix", "sequences")}
    for kind in ("sequences", "matrix"):
        stored = fetched[kind]
        for fcid, fields in cand[kind].items():
            entries = stored.get(fcid)
            empty = not entries
            if empty:
                reason = (
                    "no sequence stats stored"
                    if kind == "sequences"
                    else "archived / outside window"
                )
                print(f"  {fcid} [{kind}]: not in Parkour ({reason})")
                stats[kind, "flowcell not in Parkour"] += 1
                if kind != "sequences" or fcid not in fetched["matrix"]:
                    continue  # flowcell unknown to Parkour: nothing to push to
                entries = {}  # record disk values against an empty stored side
            for (key, field), vals in fields.items():
                if key not in entries and not empty:
                    stats[kind, "library without Parkour entry"] += 1
                    continue  # not an entry Parkour has
                if len(vals) != 1:
                    print(f"  CONFLICT {fcid} {key} {field}: {sorted(vals)} (skipped)")
                    stats[kind, "conflict"] += 1
                    continue
                new = next(iter(vals))
                old = entries.get(key, {}).get(field)
                stats[kind, "compared"] += 1
                if not differs(old, new, args.tol, field):
                    db.execute(
                        "INSERT OR REPLACE INTO matches VALUES (?,?,?,?,?,?)",
                        (fcid, kind, key, field, new, dates[fcid].isoformat()),
                    )
                    db.execute(  # fixed in Parkour since the last validate
                        "DELETE FROM mismatches WHERE flowcell_id=? AND kind=? AND key=?"
                        " AND field=? AND pushed_at IS NULL",
                        (fcid, kind, key, field),
                    )
                    continue
                db.execute(
                    "DELETE FROM matches WHERE flowcell_id=? AND kind=? AND key=? AND field=?",
                    (fcid, kind, key, field),
                )
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
    if args.apply and isProd(args.url):
        sys.exit("refusing --apply against production; use --url dev or test")
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

    matrix = (
        stored["matrix"]
        if "matrix" in stored
        else fetch(s, args, "matrix", min(dates), max(dates))
    )
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
            if (
                e is None
                and old is None
                and kind == "sequences"
                and fcid
                in matrix  # flowcell known to Parkour, only its sequence stats are empty
                and not entries  # a flowcell WITH entries is never extended by a stub
            ):
                e = {KEY[kind]: key}
            elif e is None:
                print(f"  SKIP {fcid} {key}: not in Parkour")
                continue
            if differs(e.get(field), old, 1e-9, field):
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


# ---------------------------------------------------------------- compare
def compare(args):
    """Read-only: stored value on --url vs the value parsed into the sqlite."""
    db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    rows = db.execute(
        "SELECT flowcell_id, kind, key, field, new_value, run_date FROM mismatches"
        + (
            " WHERE field IN (%s)" % ",".join("?" * len(args.field))
            if args.field
            else ""
        ),
        args.field or [],
    ).fetchall()
    if not rows:
        sys.exit("no rows in " + args.db)
    s = session(args)
    stored = {}
    for kind in ("matrix", "sequences"):
        dates = [
            datetime.datetime.fromisoformat(r[5][:10]) for r in rows if r[1] == kind
        ]
        if dates:
            stored[kind] = fetch(s, args, kind, min(dates), max(dates))
    stats, out = Counter(), []
    for fcid, kind, key, field, new, _ in rows:
        entry = stored.get(kind, {}).get(fcid, {}).get(key)
        if entry is None:
            stats["not on deployment"] += 1
            continue
        old = entry.get(field)
        old = None if old == "" else old
        if old is None:
            state = "absent"
        elif differs(old, new, args.tol, field):
            state = "differs"
        else:
            state = "same"
        stats[state] += 1
        if state != "same" or args.all:
            out.append((fcid, kind, key, field, old, new, state))
    if args.out:
        with open(args.out, "w") as fh:
            fh.write("flowcell_id\tkind\tkey\tfield\tstored\tnew\tstate\n")
            for r in out:
                fh.write("\t".join("" if v is None else str(v) for v in r) + "\n")
    print(f"deployment {args.url}: {len(rows)} rows from {args.db}")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    if args.out:
        print(f"wrote {len(out)} rows to {args.out}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    parkour = argparse.ArgumentParser(add_help=False)
    parkour.add_argument(
        "--url",
        required=True,
        type=resolveUrl,
        help="Parkour deployment: full URL or one of %s"
        % "/".join(sorted(DEPLOYMENTS)),
    )
    parkour.add_argument("--user", required=True)
    parkour.add_argument("--cert", default=True, help="CA bundle (default: system)")
    parkour.add_argument(
        "--db", default=str(Path(__file__).with_name("restats.sqlite"))
    )
    p = sub.add_parser("validate", parents=[parkour])
    p.add_argument("runDirs", nargs="*", help="flowcell dirs (…_lanes_N)")
    p.add_argument("--since", help="also scan the rapidus roots, runs from YYYY-MM-DD")
    p.add_argument("--tol", type=float, default=1e-3, help="abs. tolerance")
    p.add_argument(
        "--illumina-root", default="/rapidus/data/sequencing_data/Illumina/NovaSeq6000"
    )
    p.add_argument(
        "--raw-root", default="/dont_touch_this/short_runs/Illumina/NovaSeq6000"
    )
    p.add_argument(
        "--aviti-root", default="/rapidus/data/sequencing_data/ElementBiosciences"
    )
    p.add_argument("--group-root", default="/data")
    p.add_argument(
        "--source",
        default="adhoc",
        help="label recorded with the scanned dirs, e.g. rapidus-2024+, longus2-inbox, processed_flowcells",
    )
    p = sub.add_parser("push", parents=[parkour])
    p.add_argument("--apply", action="store_true", help="POST (default: dry run)")
    p = sub.add_parser("compare", parents=[parkour], help="read-only stored vs parsed")
    p.add_argument("--tol", type=float, default=1e-3, help="abs. tolerance")
    p.add_argument("--field", nargs="+", help="only these fields")
    p.add_argument("--all", action="store_true", help="also list rows that are equal")
    p.add_argument("--out", help="write the listed rows as TSV")
    args = ap.parse_args()
    return {"validate": validate, "push": push, "compare": compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
