# restats backfill log

Log of how `misc/backfill.sqlite` was produced, and what is in it. Tool docs: docstring of `misc/restats.py`.

Status: all three runs done and merged on 2026-11-13. Nothing reviewed (`"update"` is NULL on every row) and nothing pushed.

## Rules for this backfill
- `validate` only: it reads flowcell directories and does GET requests against Parkour. It never writes to Parkour.
- URL is always `https://parkour-dev.ie-freiburg.mpg.de`. Production is never queried or pushed to.
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
4. Merge with first source winning on the UNIQUE key `(flowcell_id, kind, key, field)`. Priority: `since2024`, `longus2`, `old`.
5. Result copied to `misc/backfill.sqlite` (12 MB). It is gitignored like `misc/restats.sqlite`; it lives on this machine only, regenerate with the steps above.

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
