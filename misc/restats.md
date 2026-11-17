# restats backfill log

Log of how `misc/backfill.sqlite` was produced, and what is in it. Tool docs: docstring of `misc/restats.py`.

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
PARKOUR_PASSWORD=... python restats.py compare --url test --user <user> --db backfill.sqlite --out cmp.tsv
```
Options: `--field F [F ...]` limits the fields, `--all` also lists equal rows, `--tol` sets the tolerance (default 1e-3). Tested against a stub HTTP server only; not yet run against a real deployment.

## Report: stored vs parsed (`restats_report.py`)
Read-only. GETs all sequence and lane statistics from `--url`, joins them with every row of the sqlite, and writes one self-contained HTML page (filters by run year, sequencer, library protocol, analysis type, project, field):
```
PARKOUR_PASSWORD=... python misc/restats_report.py --url test --user <user> --db misc/backfill.sqlite --out misc/restats_report_test.html --cache /tmp/rpt
```
Classes: `ZERO` (Parkour stores 0, files say otherwise, the old-parser bug), `WRONG` (non-zero and different; minor <1 %, moderate 1-10 %, major >=10 %), `MISSING` (API field exists, nothing stored), `NEW` (field the API does not expose: `fragment_*`, `peak_*`, `frip`, `fragments_total`), `NOENTRY` (no Parkour entry for that flowcell/barcode), `MATCH`.

The page is gitignored. It embeds the data and the private run-dir paths, so it is the place that lists every scanned flowcell dir (section 6: one row per `validate` run with its roots and URL, then every dir with its status). Regenerate it with the command above.

Result on `parkour-test` (2026-11-17, 164,875 values): MATCH 92,298, ZERO 844 (all `optical_duplicates`), WRONG 368 (major 162, moderate 50, minor 156), MISSING 9,967, NEW 39,290, NOENTRY 22,108. Of the 103,477 values that exist in Parkour and can be compared (MATCH + MISSING + ZERO + WRONG), 1,212 (1.2 %) are ZERO or WRONG.

| Field | ZERO + WRONG / comparable | ZERO | WRONG major |
|---|---|---|---|
| `optical_duplicates` | 970 / 20,659 (4.7 %) | 844 | 46 |
| `reads_pf_sequenced` | 126 / 20,659 (0.6 %) | 0 | 61 |
| `mapped_reads` | 47 / 17,806 (0.3 %) | 0 | 17 |
| `assigned_reads` | 34 / 3,146 (1.1 %) | 0 | 34 |
| `uniq_mapped` | 29 / 11,413 (0.3 %) | 0 | 0 |
| `insert_size` | 4 / 6,394 (0.1 %) | 0 | 2 |
| `dupped_reads` | 2 / 10,381 (0.0 %) | 0 | 2 |

### MATCH counts
`validate` writes the values that already equal Parkour into a `matches` table, so the report shows real percentages. `misc/backfill.sqlite` was rebuilt on 2026-11-17 with all three sources rerun (`--url dev`, GET only): 72,577 mismatching values over 642 flowcells and 92,298 matching values over 789 flowcells. `scanned` rows are now recorded by `validate` (2,554 dirs, `origin = validate`).

## What `validate` records
Besides `mismatches` and `matches`, every `validate` run writes:
- `scan_runs`: host, `--source` label, `--since`, deployment URL, the four roots, number of dirs, time. One row per invocation.
- `scanned`: every flowcell dir considered, its flowcell id, run date and status (`parsed`, `lane stats failed`, `library stats failed`, `skipped`) plus the error text. `lane stats failed` still has sequence rows; only lane (matrix) rows are missing.

`origin` is `validate` for rows recorded by the script and `reconstructed` for rows listed afterwards. `reconstructed` rows come from before the rerun (listed read-only on 2026-11-17); the current `backfill.sqlite` has `validate` rows.

## Rerun recipe (for the next agent)
Labels used so far: `processed_flowcells` (rapidus, `/data/manke/repository/processed_flowcells/*/*/` as positional dirs), `rapidus-2024+` (rapidus, `--since 2024-01-01`), `longus2-inbox` (longus2, `--since 2024-01-01` with `--illumina-root /scratch/INBOX/sequencing_data2 --aviti-root /scratch/INBOX/sequencing_data`). The exact roots and dir lists are in section 6 of the report.
1. Pipe `restats.py` over ssh stdin into a `mktemp -d` on the host and run `validate --url dev --user <user> --cert /etc/pki/tls/certs/ca-bundle.crt --db <tmp>/<label>.sqlite --source <label> ...`; copy the sqlite back as base64 on stdout. Credentials go over stdin or env only.
2. Merge: `python misc/restats_merge.py misc/backfill.sqlite rapidus-2024+.sqlite longus2-inbox.sqlite processed_flowcells.sqlite` (first source wins; `mismatches`, `matches`, `scanned`, `scan_runs` are all merged).
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
5. Result copied to `misc/backfill.sqlite` (12 MB; now larger with `scanned` rows). It is gitignored like `misc/restats.sqlite`; it lives on this machine only, regenerate with the steps above.

## Results
| Source | Rows | Flowcells | Run dates | Notes |
|---|---|---|---|---|
| `longus2` | 5957 | 27 | 2025-03-03 to 2026-06-16 | 5 flowcells not in Parkour dev; 794 rows skipped as CONFLICT |
| `since2024` | 19001 | 132 | 2024-07-02 to 2026-11-10 | 2030 CONFLICT lines; 32 flowcell/sequence lines not in Parkour dev; 16 matrix rows |
| `old` | 47619 | 483 | 2018-04-09 to 2024-06-21 | 598 CONFLICT lines; 178 not in Parkour dev; 1910 lane-stats failures (interop files gone) |
| merged (`misc/backfill.sqlite`) | 72577 | 642 | 2018-04-09 to 2026-11-10 | 72561 sequence rows, 16 matrix rows, no duplicate keys across sources |

New-key rows in the merged file: `fragment_median` 7399, `fragment_q1` 7399, `fragment_q3` 7396, `fragment_p10` 7400, `fragment_p90` 7385, `fragments_total` 4640, `peak_count` 1030, `frip` 1037, `peak_genome_coverage` 1081. `insert_size` has 2045 rows.

The `longus2` source overlapped no flowcell with the other two (0 duplicate keys), so the merge priority did not matter in this run.

## Known quirks
- CONFLICT rows: a barcode with two different values across run dirs of the same flowcell is skipped, not guessed. Example: `HLCH3DRX7 26L002823 mapped_reads [55.66, 55.68]`.
- `lane stats failed` lines for old runs: the Illumina interop files are gone. Lane (matrix) rows are missing for those flowcells. Sequence rows are unaffected.
- `not in Parkour (no sequence stats stored)`: flowcell has no entry on dev; nothing to compare, nothing to push.

## Next
- Compare numbers now on production with the values that would be pushed. Production is read-only for this: GET only.
- Review rows in the sqlite, mark `"update"`, then push to parkour-dev only, after confirmation.
