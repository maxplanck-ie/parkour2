# restats backfill log

Log of how `misc/restats_backfill.sqlite` was produced, and what is in it. Tool docs: docstring of `misc/restats.py`.

Status: all three runs done and merged on 2026-11-13. Nothing reviewed (`"update"` is NULL on every row) and nothing pushed.

## Choosing the deployment
Every subcommand that talks to Parkour (`validate`, `push`, `compare`) has a required `--url`. It takes a full URL or a short name:

| Name | URL |
|---|---|
| `prod` | `https://parkour.ie-freiburg.mpg.de` |
| `test` | `https://parkour-test.ie-freiburg.mpg.de` |
| `dev` | `https://parkour-dev.ie-freiburg.mpg.de` |

There is no default, so nothing hits a deployment by accident. `push --apply --url prod` exits with an error; use `dev` or `test`.

`compare` is read-only (GET only, sqlite opened read-only). It lists, per field, the value stored on the deployment next to the value parsed into the sqlite, with the state `same`, `differs`, `absent` (nothing stored) or `not on deployment`:
```
PARKOUR_PASSWORD=... python restats.py compare --url test --user <user> --db restats_backfill.sqlite --out cmp.tsv
```
Options: `--field F [F ...]` limits the fields, `--all` also lists equal rows, `--tol` sets the tolerance (default 1e-3). Tested against a stub HTTP server only; not yet run against a real deployment.

## Report: stored vs parsed (`restats_report.py`)
Read-only. GETs all sequence and lane statistics from `--url`, joins them with every row of the sqlite, and writes one self-contained HTML page (filters by run year, sequencer, library protocol, analysis type, project, field):
```
PARKOUR_PASSWORD=... python misc/restats_report.py --url test --user <user> --db misc/restats_backfill.sqlite --out misc/restats_report_test.html --cache /tmp/rpt
```
Classes: `ZERO` (Parkour stores 0, files say otherwise, the old-parser bug), `WRONG` (non-zero and different; minor <1 %, moderate 1-10 %, major >=10 %), `MISSING` (API field exists, nothing stored), `NEW` (field the API does not expose: `fragment_*`, `peak_*`, `frip`, `fragments_total`), `NOENTRY` (no Parkour entry for that flowcell/barcode), `MATCH`.

The page is gitignored. It embeds the data and the private run-dir paths, so it is the place that lists every scanned flowcell dir (section 6: one row per `validate` run with its roots and URL, then every dir with its status). Regenerate it with the command above.

Result on `parkour-test` (2026-11-17, before the review fixes, 164,875 values): MATCH 92,298, ZERO 844 (all `optical_duplicates`), WRONG 368 (major 162, moderate 50, minor 156), MISSING 9,967, NEW 39,290, NOENTRY 22,108. Of the 93,510 values Parkour stores and that were compared (MATCH + ZERO + WRONG), 1,212 (1.3 %) are ZERO or WRONG. MISSING is not in the denominator, nothing is stored there. This table and the figure are from before the 2026-11-17 review fixes and need a regenerated report.

| Field | ZERO + WRONG / comparable | ZERO | WRONG major |
|---|---|---|---|
| `optical_duplicates` | 970 / 20,659 (4.7 %, MISSING included) | 844 | 46 |
| `reads_pf_sequenced` | 126 / 20,659 (0.6 %) | 0 | 61 |
| `mapped_reads` | 47 / 17,806 (0.3 %) | 0 | 17 |
| `assigned_reads` | 34 / 3,146 (1.1 %) | 0 | 34 |
| `uniq_mapped` | 29 / 11,413 (0.3 %) | 0 | 0 |
| `insert_size` | 4 / 6,394 (0.1 %) | 0 | 2 |
| `dupped_reads` | 2 / 10,381 (0.0 %) | 0 | 2 |

### MATCH counts
`validate` writes the values that already equal Parkour into a `matches` table, so the report shows real percentages. `misc/restats_backfill.sqlite` was rebuilt on 2026-11-17 with all three sources rerun (`--url dev`, GET only): 72,577 mismatching values over 642 flowcells and 92,298 matching values over 789 flowcells. `scanned` rows are now recorded by `validate` (2,554 dirs, `origin = validate`).

## Protocol coverage (2026-11-17, `parkour-test`)
Share of libraries on scanned flowcells with any parsed value in `restats_backfill.sqlite`: 85-96 % for the big RNA, ATAC and CUT_and_x protocols; low for NEBNext Ultra II DNA (30 %), Cel-Seq 2 (6 %), 10x scRNA (59 %), Hi-C (74 %, base stats only). "Other - ..." protocols are out of scope. Causes:

- **Empty stats file crash (fixed).** 121 scanned dirs on 103 flowcells (2025-26, NovaSeq and AVITI, about 3,650 libraries) failed with `ValueError: not enough values to unpack (expected 2, got 0)`: an empty `<sample>.duplicate.txt`. `seqStats` lost the whole flowcell, including the Analysis-based stats. It now skips the empty file and keeps going. Those 121 dirs were rerun on 2026-11-17 (`--url dev`, source `rapidus-2024+`) and merged in front of the existing results. BRB `getNReads` has the same `s.split()` unpack and cannot send base stats for those runs either.
- **Old runs have no per-library stats files.** None of the 2,004 `processed_flowcells` dirs (2018-2024) has a `.metrics` or `.duplicate.txt`. NEBNext Ultra II DNA, 10x scRNA and Cel-Seq 2 are mostly such runs, so there is nothing to parse. `getNReads` falls back to counting R1 lines and reports `optical_duplicates = 0.0` for them (`BRB/ET.py`), so a stored 0 on an old run is a placeholder, not a measurement.
- **`# Reads` is not `reads_pf_sequenced`.** `Reports/Demultiplex_Stats.csv` (2022-24 runs) equals Parkour's value for 215 sampled libraries but is 4-8 % higher for more than 1,000. Do not use it as a fallback: it would create false WRONG rows. Pre-2022 `Stats/DemultiplexingStats.xml` names samples by free text, not barcode.
- **Hi-C.** Parkour stored no mapping stats for Hi-C (0 of 265 libraries from 2025-26). `multiqc_hicexplorer.txt` has one row per matrix named `<sample>_bs<binsize>.cool`, and `<sample>` is the Parkour library name. `restats.py` now reads `Pairs mappable, unique and high quality_pct` into `uniq_mapped` (first bin size wins), and BRB `HiC()` sends the same value. Checked read-only on one AVITI flowcell (24 Hi-C libraries). The 106 Hi-C dirs in the backfill were NOT rerun with this parser yet, so the sqlite has no Hi-C `uniq_mapped` values.
- **10x scRNA and Cel-Seq 2.** All libraries are from 2018-2023 (Cel-Seq 2: 2018-2020); no stats files, nothing to add.

## What `validate` records
Besides `mismatches` and `matches`, every `validate` run writes:
- `scan_runs`: host, `--source` label, `--since`, deployment URL, the four roots, number of dirs, time. One row per invocation.
- `scanned`: every flowcell dir considered, its flowcell id, run date and status (`parsed`, `lane stats failed`, `library stats failed`, `skipped`) plus the error text. `lane stats failed` still has sequence rows; only lane (matrix) rows are missing.

`origin` is `validate` for rows recorded by the script and `reconstructed` for rows listed afterwards. `reconstructed` rows come from before the rerun (listed read-only on 2026-11-17); the current `backfill.sqlite` has `validate` rows.

## Rerun recipe (for the next agent)
Labels used so far: `processed_flowcells` (rapidus, `/data/manke/repository/processed_flowcells/*/*/` as positional dirs), `rapidus-2024+` (rapidus, `--since 2024-01-01`), `longus2-inbox` (longus2, `--since 2024-01-01` with `--illumina-root /scratch/INBOX/sequencing_data2 --aviti-root /scratch/INBOX/sequencing_data`). The exact roots and dir lists are in section 6 of the report.
1. Pipe `restats.py` over ssh stdin into a `mktemp -d` on the host and run `validate --url dev --user <user> --cert /etc/pki/tls/certs/ca-bundle.crt --db <tmp>/<label>.sqlite --source <label> ...`; copy the sqlite back as base64 on stdout. Credentials go over stdin or env only.
2. Merge: `python misc/restats_merge.py misc/restats_backfill.sqlite rapidus-2024+.sqlite longus2-inbox.sqlite processed_flowcells.sqlite` (first source wins; `mismatches`, `matches`, `scanned`, `scan_runs` are all merged).
3. Regenerate the report.

## Rules for this backfill
- `validate` only: it reads flowcell directories and does GET requests against Parkour. It never writes to Parkour.
- The backfill runs below used `--url https://parkour-dev.ie-freiburg.mpg.de` (now `--url dev`). Production was not queried by them; pushing to it is refused by `push --apply`.
- The Parkour login is the production account from `~/configs/dissectBCL_prod.ini` on rapidus (section `[parkour]`). It is only used against the dev URL. It travels through ssh stdin or env vars and is never written to disk or logs.
- `push --apply` to parkour-dev needs separate, explicit confirmation. Not part of this log yet.

## Code versions
| What | Where | Commit |
|---|---|---|
| `restats.py` (fragment keys + `fragments_total`) | `feat/atac-plan` | `1409cc6c` |
| BRB `fragmentQC` (sends the same keys on new runs) | `feat/chromatin-et-stats` | `b615723` |

New keys, all protocols with the DNA pipeline (ChIP, CUT&Tag, CUT&RUN, ATAC): `fragment_q1`, `fragment_median`, `fragment_q3`, `fragment_p10`, `fragment_p90`, `fragments_total`. ATAC only: `peak_count`, `frip`, `peak_genome_coverage`. Details: `atac_plan.md`.

## Sources
| Source | Host | Scope | Command arguments |
|---|---|---|---|
| `old` | rapidus | `/data/manke/repository/processed_flowcells/*/*/` (2004 dirs, 2018 to mid 2024) | the dirs as positional arguments |
| `since2024` | rapidus | NovaSeq6000 and Aviti roots, runs from 2024-01-01 | `--since 2024-01-01` |
| `longus2` | longus2 | `/scratch/INBOX/sequencing_data2` (146 run dirs, 107 flowcells), flowcells processed while rapidus was offline | `--illumina-root /scratch/INBOX/sequencing_data2 --raw-root /dont_touch_this/short_runs/Illumina/NovaSeq6000 --aviti-root /scratch/INBOX/sequencing_data --group-root /data --since 2024-01-01` |

Every run: `restats.py validate --url https://parkour-dev.ie-freiburg.mpg.de --user <prod user> --cert /etc/pki/tls/certs/ca-bundle.crt --db <tmp>/<source>.sqlite <args>`, using `/localenv/pipegrp/anaconda/miniconda3/bin/python`.

## How it was run (2026-11-13)
1. `restats.py` piped over ssh stdin into a `mktemp -d /tmp/restats_bf.*` directory on the host. The directory is deleted on exit; nothing else on rapidus or longus2 is touched.
2. Credentials read on rapidus (or passed through stdin to longus2), exported as `PARKOUR_PASSWORD`.
3. The finished sqlite goes back to this machine as base64 on stdout.
4. Merge with `misc/restats_merge.py` (first source wins on the UNIQUE key `(flowcell_id, kind, key, field)`). Priority: `since2024`, `longus2`, `old`. The first merge was done with an earlier ad-hoc copy of that script.
5. Result copied to `misc/restats_backfill.sqlite` (12 MB; now larger with `scanned` rows). It is gitignored like `misc/restats.sqlite`; it lives on this machine only, regenerate with the steps above.

## Results
| Source | Rows | Flowcells | Run dates | Notes |
|---|---|---|---|---|
| `longus2` | 5957 | 27 | 2025-03-03 to 2026-06-16 | 5 flowcells not in Parkour dev; 794 rows skipped as CONFLICT |
| `since2024` | 19001 | 132 | 2024-07-02 to 2026-11-10 | 2030 CONFLICT lines; 32 flowcell/sequence lines not in Parkour dev; 16 matrix rows |
| `old` | 47619 | 483 | 2018-04-09 to 2024-06-21 | 598 CONFLICT lines; 178 not in Parkour dev; 1910 lane-stats failures (interop files gone) |
| merged (`misc/restats_backfill.sqlite`) | 72577 | 642 | 2018-04-09 to 2026-11-10 | 72561 sequence rows, 16 matrix rows, no duplicate keys across sources |

New-key rows in the merged file: `fragment_median` 7399, `fragment_q1` 7399, `fragment_q3` 7396, `fragment_p10` 7400, `fragment_p90` 7385, `fragments_total` 4640, `peak_count` 1030, `frip` 1037, `peak_genome_coverage` 1081. `insert_size` has 2045 rows.

The `longus2` source overlapped no flowcell with the other two (0 duplicate keys), so the merge priority did not matter in this run.

## Known quirks
- CONFLICT rows: a barcode with two different values across run dirs of the same flowcell is skipped, not guessed. Example: `HLCH3DRX7 26L002823 mapped_reads [55.66, 55.68]`.
- `lane stats failed` lines for old runs: the Illumina interop files are gone. Lane (matrix) rows are missing for those flowcells. Sequence rows are unaffected.
- `not in Parkour (no sequence stats stored)`: flowcell has no entry on dev; nothing to compare, nothing to push.

## Next
- Compare numbers now on production with the values that would be pushed. Production is read-only for this: GET only.
- Review rows in the sqlite, mark `"update"`, then push to parkour-dev only, after confirmation.
