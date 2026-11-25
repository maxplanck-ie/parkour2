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
Classes: `ZERO` (Parkour stores 0, files say otherwise, the old-parser bug), `WRONG_minor` / `WRONG_mod` / `WRONG_major` (non-zero and different; <1 %, 1-10 %, >=10 %), `WRONG` (text field whose stored string differs from the parsed one; one class, no size band), `MISSING` (API field exists, nothing stored), `NEW` (field the API does not expose: `fragment_*`, `peak_*`, `frip`, `fragments_total`), `NOENTRY` (no Parkour entry for that flowcell/barcode), `MATCH`.

The page is gitignored. It embeds the data and the private run-dir paths, so it is the place that lists every scanned flowcell dir (section 6: one row per `validate` run with its roots and URL, then every dir with its status). Regenerate it with the command above.

Result on `parkour-test` (2026-11-18, after the review fixes, a full rerun and the longus2 Aviti discovery fix, 183,342 values): MATCH 103,613, ZERO 844 (all `optical_duplicates`), WRONG 362 (major 156, moderate 50, minor 156), MISSING 10,217, NEW 45,127, NOENTRY 23,179. Of the 104,819 values Parkour stores and that were compared (MATCH + ZERO + WRONG), 1,206 (1.15 %) are ZERO or WRONG. MISSING is not in the denominator, nothing is stored there. The Parkour values come from `parkour-test`; the sqlite `old_value` comes from `parkour-dev` at validate time.

| Field | ZERO + WRONG / comparable | ZERO | WRONG major |
|---|---|---|---|
| `optical_duplicates` | 970 / 22,333 (4.3 %) | 844 | 46 |
| `reads_pf_sequenced` | 126 / 22,333 (0.6 %) | 0 | 61 |
| `mapped_reads` | 41 / 18,511 (0.2 %) | 0 | 11 |
| `assigned_reads` | 34 / 4,057 (0.8 %) | 0 | 34 |
| `uniq_mapped` | 29 / 8,835 (0.3 %) | 0 | 0 |
| `insert_size` | 4 / 6,332 (0.1 %) | 0 | 2 |
| `dupped_reads` | 2 / 11,537 (0.0 %) | 0 | 2 |

### MATCH counts
`validate` writes the values that already equal Parkour into a `matches` table, so the report shows real percentages. `misc/restats_backfill.sqlite` was rebuilt on 2026-11-18 with all three sources rerun with the fixed code (`--url dev`, GET only, merged by `restats_merge.py`): 79,729 mismatching values over 705 flowcells and 103,613 matching values over 845 flowcells. `scanned` rows are recorded by `validate` (2,616 dirs: `rapidus-2024+` 404, `longus2-inbox` 208, `processed_flowcells` 2,004; `origin = validate`).

## Protocol coverage (2026-11-18, `parkour-test`)
Per-protocol result after the full rerun of 2026-11-18 (values compared against `parkour-test`; `MISSING` = parsed value, Parkour empty, so backfillable). "Other - ..." protocols are out of scope.

| Protocol | MATCH | ZERO + WRONG | MISSING | Note |
|---|---|---|---|---|
| HI-C | 1,020 | 16 (ZERO) | 232 | all MISSING are `uniq_mapped`, now parsed |
| NEBNext Ultra II DNA Library Prep Kit for Illumina | 4,824 | 0 | 48 (`mapped_reads` 24, `insert_size` 24) | 5,465 NEW `fragment_*` values |
| NEBNext Single Cell RNA Library Preparation | 3,265 | 94 (ZERO 60 `optical_duplicates`, WRONG 34 `assigned_reads`) | 4 | |
| scRNA-Seq 10xGenomics | 690 | 16 (WRONG: `reads_pf_sequenced` 8, `optical_duplicates` 8) | 0 | |
| Cel-Seq 2 for single cell RNA-Seq | 64 | 0 | 0 | |

Causes of the remaining gaps:

- **Empty stats files on rapidus are stubs of runs moved to longus2 (fixed).** 121 scanned dirs on 103 flowcells (2025-03 to 2026-06, NovaSeq and AVITI, 4,628 libraries) have a 0-byte fastq and a 0-byte `.duplicate.txt` on rapidus, and an adjacent `<run>.is_on_longus2` flag. The real data (non-empty `.duplicate.txt`) is on longus2 under `/scratch/INBOX/sequencing_data*`. Before the fix the empty file crashed `seqStats` (`ValueError: not enough values to unpack (expected 2, got 0)`) and lost the whole flowcell, including the Analysis-based stats. `seqStats` now skips unusable files and keeps going; BRB `getNReads` does the same and falls back to the next usable file or to the R1 read count. The `longus2-inbox` source supplies the values. `restats.py` first missed longus2's Aviti runs because they sit directly under the root (`<root>/<run>_lanes_N`, not `<root>/AV<id>/<run>`); now fixed, so 62 Aviti runs are scanned. After the rerun 120 of the 121 runs are covered at flowcell level; the 121st has no entries in Parkour. 227 stub samples still have no value because Parkour has no entry for that (flowcell, barcode) on dev or test.
- **Old runs have no per-library stats files.** None of the 2,004 `processed_flowcells` dirs (2018-2024) has a `.metrics` or `.duplicate.txt`. NEBNext Ultra II DNA, 10x scRNA and Cel-Seq 2 are mostly such runs, so there is nothing to parse. `getNReads` falls back to counting R1 lines and reports `optical_duplicates = 0.0` for them (`BRB/ET.py`), so a stored 0 on an old run is a placeholder, not a measurement.
- **`# Reads` is not `reads_pf_sequenced`.** `Reports/Demultiplex_Stats.csv` (2022-24 runs) equals Parkour's value for 215 sampled libraries but is 4-8 % higher for more than 1,000. Do not use it as a fallback: it would create false WRONG rows. Pre-2022 `Stats/DemultiplexingStats.xml` names samples by free text, not barcode.
- **Hi-C.** Parkour stored no mapping stats for Hi-C (0 of 265 libraries from 2025-26). `multiqc_hicexplorer.txt` has one row per matrix named `<sample>_bs<binsize>.cool`, and `<sample>` is the Parkour library name. `restats.py` reads `Pairs mappable, unique and high quality_pct` into `uniq_mapped` (the `_bs10kb` row wins, else the first row), and BRB `HiC()` sends the same value. Verified on the full rerun: 232 Hi-C `uniq_mapped` values are MISSING in Parkour and ready to backfill.
- **10x scRNA and Cel-Seq 2.** All libraries are from 2018-2023 (Cel-Seq 2: 2018-2020); no stats files, nothing to add.

## Parity with BRB (`ET.py`)

`restats.py` is meant to reproduce what BRB sends. Known differences, so a mismatch is not read as a bug in one side:

- Base statistics only exist for a library with a `*_R1_fastqc.zip` in `FASTQC_Project_<p>/Sample_<lib>`. Without one, neither side reports anything for it. With several zips, both sides use the first (sorted) as the sample for Hi-C, micro-C and the sample map.
- A stats file is usable if it holds `<digits> <digits>` with optical <= total. Both sides look in `FASTQC_Project_<p>/Sample_<lib>` first, then `Project_<p>/Sample_<lib>`, and keep the first usable file (`.metrics` before `.duplicate.txt`). They never sum.
- No usable stats file: BRB counts R1 reads and sends `optical_duplicates = 0` (no stats files at all) or leaves it out (files present but unusable). `restats.py` records nothing for these libraries, so they show as MISSING or NEW, never as a computed value. This is the one known deviation.
- Duplicate rows of one sample in `multiqc_samtools_flagstat.txt` or `multiqc_featurecounts.txt`: both sides take the first row.
- A sample missing from the flagstat table: both sides leave `dupped_reads` out.
- RNA: a library needs STAR `Log.final.out`, a flagstat row and a featureCounts row (`<sample>.filtered`). Without all three neither side sends STAR values.
- `confident_reads`: restats gets the organism label per library from `GET /api/analysis_list/analysis_list/?flowcell_id=<id>` (the call BRB's inputs come from), then mirrors `getOffSpeciesRate`: first `*rep` file in `FASTQC_Project_<p>/Sample_<lib>`, group per label (`h38`, `mm10`, `m39`, `lambda`, `nematode`, `drosophila`), `1 - pct/100` of the last matching line. No matching line, a label outside that map, no label from Parkour or no `*rep` file: nothing is recorded, never 0 (BRB sends NaN, which `dropNaN` removes). BRB and restats both take the first `*rep` by name.
- ATAC, ChIP, CUT&Tag (BRB `chromatin()` = `DNA()` + `fragmentQC` + `peakQC`), checked field by field with a harness (12 fixtures, values compared at full precision, no rounding): `peak_*`, `frip`, `fragment_*`, `fragments_total` agree. Peak QC file: `MACS2_QC/<sample>.filtered.BAM_peaks.qc.txt` if it exists, else `MACS2/<sample>...` (ATAC keeps it in `MACS2_QC/`; ChIP and RELACS runs keep it in `MACS2/`). A broken source costs only its own values, on both sides: no Bowtie2 output, a sample with no row in the fragment or flagstat file, a flagstat cell that is not a number, a header-only peak file or a peak file with a missing column. The other samples and the other values of the same sample are still sent. Only a library with nothing readable falls back to the base statistics. `insert_size` is read for samples that have a Bowtie2 summary, like BRB `DNA()`. restats prints a warning to stderr for each skipped source.
- RELACS: mapping runs on the demultiplexed samples from `RELACS_sampleSheet.txt`, not on the library. The sheet is read like `demultiplex_relacs` does: tab separated, 3 columns (`Sample_<library>`, barcode, label) or 4 columns (`Sample_<library>`, position, barcode, label); the label is the last column and its spaces become `_`, which is how the files are named. BRB sends the base stats at library level and one dict per demuxed sample under `demuxed_samples` (`mapped_reads`, `dupped_reads`, `insert_size`, `fragment_*`, `fragments_total`, `peak_count`, `frip`, `peak_genome_coverage`; a key is left out when its file has no row for that sample). Peak file per demuxed sample: `MACS2_QC/<name>.filtered.BAM_peaks.qc.txt` if it exists, else `MACS2/<name>...` (RELACS runs keep it in `MACS2/`). At library level BRB (`ET._relacsLibrary`) sends the same field names as every other library, so a yearly aggregate needs no per-sample rows: `fragments_total` (sum, exact), `dupped_reads` (pooled: the samples' rates weighted by their flagstat `total_passed`, exact), `mapped_reads` (mean weighted by `total_passed`), `fragment_q1`, `fragment_median`, `fragment_q3`, `fragment_p10`, `fragment_p90`, `insert_size` and `frip` (mean weighted by the samples' `fragments_total`). The weighted means approximate the library value (a mean of medians is not a median); on the backfill, the median of the samples and the weighted mean differ by about 1 % for half of the libraries and up to about 15 % at worst for the fragment values. `peak_count` and `peak_genome_coverage` are not sent at library level because the samples' peak sets overlap; they stay per demuxed sample. Parkour stores whatever BRB sends in `flowcell.sequences` (`SequencesStatisticsViewSet.upload` has no field whitelist), so no Parkour change is needed. restats records the per-sample values as `demuxed_samples/<name>/<field>` (a flat key of restats' sqlite, not a Parkour field) and writes them back nested. restats computes the same library-level values with the same weights as `ET._relacsLibrary` (the weighted means are not rounded to ints).
- Number types: restats sends the count and length fields as ints, like BRB (`reads_pf_sequenced`, `insert_size`, `fragment_q1`, `fragment_median`, `fragment_q3`, `fragment_p10`, `fragment_p90`, `fragments_total`, `peak_count`). Every other field is a float on both sides. The RELACS library-level weighted means are floats.
- `restats.py` does not store CONFLICT rows (a field with several distinct values, such as Hi-C lanes). BRB sends one of them.
- Hi-C: the `_bs10kb` row of a sample wins, else the first `multiqc_hicexplorer` row.
- Several stats files per sample: none exist (0 of 19,437 samples checked on rapidus and longus2, 2026-11-18).
- CONFLICT rows (a key with several distinct parsed values, 1,858 lines in the last run) come from different runs or pipelines for `mapped_reads`, `dupped_reads`, `fragment_*`, `insert_size`. Parkour holds one of the candidates, sometimes the lower and sometimes the higher, so no min or max rule fits. They are skipped and reported, not stored.

## Lane and micro-C fields

| Field | Protocol | Type | Source file and rule |
|---|---|---|---|
| `polony_density` | AVITI | text | `RunParameters.json` `AdvancedSettings.PolonyDensity`, as given |
| `pmg_shift` | AVITI | num | `RunParameters.json` top-level `ShiftPMGBy`, else `AdvancedSettings.ShiftPmgBy` |
| `custom_recipe` | AVITI | text | `RunParameters.json` `AdvancedSettings.CustomRecipeName`, `.rec` suffix stripped |
| `occupancy_score` | AVITI | num | `RunParameters.json` `AdvancedSettings.OccupancyScore` (almost never present) |
| `sequencer_side` | AVITI | text | `RunParameters.json` `Side`, `SideA`/`SideB` reduced to `A`/`B` |
| `lane_loading_format` | AVITI | text | `RunManifest.csv` `[SAMPLES]` Lane column: any `1+2` gives `1 pool`; both `1` and `2` present gives `2 pools`; otherwise `1 pool`; no lane rows gives nothing |
| `gb_yield` | AVITI | num | `<outBaseDir>/<lane>/RunStats.json` lane `TotalYield`, rounded to 2 decimals |
| `phix_alignment_rate` | AVITI | num | `<aviti-raw-root>/<instrument>/<run>/AvitiRunStats.json` `LaneStats[i].Reads[0].PhiXAlignmentRate` (percent, read 1), 2 decimals. `LaneStats[].Lane` is 0 in production runs, so list order is the lane order (checked against 45 dual-lane runs); filled-in `Lane` values are used as given. An unreadable entry costs only its lane |
| `run_outcome` | AVITI | text | `<aviti-raw-root>/<instrument>/<run>/RunUploaded.json` `outcome` (`OutcomeCompleted`, `OutcomeStopped`, `OutcomeFailed`), copied to every lane; no file or no value gives nothing |
| `lane_loading_format` | Illumina | text | `RunParameters.xml` `WorkflowType`: `NovaSeqXp` gives `XP`, `NovaSeqStandard` gives `Standard`, any other value is kept raw |
| `percent_occupied` | Illumina | num | interop summary `% Occupied`, read 1, 2 decimals |
| `gb_yield` | Illumina | num | interop `Projected Yield G`, read 1, 2 decimals |
| `phix_alignment_rate` | Illumina | num | interop `% Aligned` x 100, read 1, 2 decimals |
| `percent_pf` | Illumina | num | interop `% Pf`, read 1, 2 decimals |
| `mapped_reads` | micro-C | num | `Analysis_*/<micro-C dir>/pairs/<sample>.pairs.dedup.stats`: 100 x `total_mapped` / `total` |
| `dupped_reads` | micro-C | num | same file: 100 x `total_dups` / `total_mapped` |

Text fields are compared by string equality, never parsed as numbers. Sqlite stores them as TEXT (REAL affinity keeps `220` as a number, so `restats_report.py` compares both sides as text). A text field with no stored value is `MISSING`; a stored value that differs is `WRONG`; equal text is `MATCH`. Numeric fields keep the size bands above.

micro-C: the sample is the R1 fastqc basename minus `_R1_fastqc.zip`, mapped to the barcode the same way as the other pipelines. A library whose `pairs/<sample>.pairs.dedup.stats` is absent gets no keys (detected by file presence, as for Hi-C). A file missing `total`, `total_mapped` or `total_dups` is logged and those keys are omitted. A zero denominator also omits the field (BRB sends NaN, which is left out of the payload).

Parity: lane fields mirror dissectBCL `fakeNews.pushParkour` (`parseAvitiRunParameters`, `parseAvitiLoadingFormat`, `parseAvitiPhixByLane`, `parseAvitiRunOutcome`, `parseIlluminaRunParameters`, and the AVITI/Illumina branches). micro-C mirrors BRB `ET.py` `makePairs` and `pairsStats`. Both are read, not imported. The AVITI instrument run folder is `--aviti-raw-root` (default `/dont_touch_this/short_runs/ElementBiosciences`) plus the instrument id and the run name without `_lanes_N`.

The wrong share is `(ZERO + WRONG_* + WRONG) / (ZERO + WRONG_* + WRONG + MATCH)`. Text mismatches count in the numerator like any other WRONG.

## What `validate` records
Besides `mismatches` and `matches`, every `validate` run writes:
- `scan_runs`: host, `--source` label, `--since`, deployment URL, the four roots, number of dirs, time. One row per invocation.
- `scanned`: every flowcell dir considered, its flowcell id, run date and status (`parsed`, `lane stats failed`, `library stats failed`, `skipped`) plus the error text. `lane stats failed` still has sequence rows; only lane (matrix) rows are missing.

`origin` is `validate` for rows recorded by the script and `reconstructed` for rows listed afterwards. The current `restats_backfill.sqlite` has `validate` rows only (full rerun of 2026-11-17).

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

New keys, all protocols with the DNA pipeline (ChIP, CUT&Tag, CUT&RUN, ATAC): `fragment_q1`, `fragment_median`, `fragment_q3`, `fragment_p10`, `fragment_p90`, `fragments_total`. Peak keys (`peak_count`, `frip`, `peak_genome_coverage`): ATAC, ChIP and CUT&Tag at library level, RELACS per demuxed sample. Details: `atac_plan.md`.

## Sources
| Source | Host | Scope | Command arguments |
|---|---|---|---|
| `old` | rapidus | `/data/manke/repository/processed_flowcells/*/*/` (2004 dirs, 2018 to mid 2024) | the dirs as positional arguments |
| `since2024` | rapidus | NovaSeq6000 and Aviti roots, runs from 2024-01-01 | `--since 2024-01-01` |
| `longus2` | longus2 | `/scratch/INBOX/sequencing_data2` (146 run dirs, 107 flowcells), flowcells processed while rapidus was offline | `--illumina-root /scratch/INBOX/sequencing_data2 --raw-root /dont_touch_this/short_runs/Illumina/NovaSeq6000 --aviti-root /scratch/INBOX/sequencing_data --group-root /data --since 2024-01-01` |

Every run: `restats.py validate --url https://parkour-dev.ie-freiburg.mpg.de --user <prod user> --cert /etc/pki/tls/certs/ca-bundle.crt --db <tmp>/<source>.sqlite <args>`, using `/localenv/pipegrp/anaconda/miniconda3/bin/python`.

## How it was run (2026-11-17, full rerun with the fixed code)
1. `restats.py` piped over ssh stdin into a `mktemp -d /tmp/restats_bf.*` directory on the host. The directory is deleted on exit; nothing else on rapidus or longus2 is touched.
2. Credentials read on rapidus (or passed through stdin to longus2), exported as `PARKOUR_PASSWORD`.
3. The finished sqlite goes back to this machine as base64 on stdout.
4. Merge with `misc/restats_merge.py` into a fresh file (first source wins on the UNIQUE key `(flowcell_id, kind, key, field)`, across `mismatches` and `matches`). Priority: `rapidus-2024+`, `longus2-inbox`, `processed_flowcells`. All three runs use `--url dev` (GET only).
5. Result copied to `misc/restats_backfill.sqlite` (12 MB; now larger with `scanned` rows). It is gitignored like `misc/restats.sqlite`; it lives on this machine only, regenerate with the steps above.

## Results
| Source | Mismatch rows | Match rows | Flowcells | Run dates | Notes |
|---|---|---|---|---|---|
| `rapidus-2024+` (404 dirs) | 30,053 | 42,906 | 288 | 2024-07-02 to 2026-11-11 | 32 sequence lines not in Parkour dev; 1,239 CONFLICT lines; 249 lane-stats failures; 4,628 empty `.duplicate.txt` skipped |
| `longus2-inbox` (208 dirs, 62 Aviti) | 12,006 | 22,081 | 104 | 2025-03-03 to 2026-06-25 | 20 sequence lines not in Parkour dev; 418 CONFLICT lines; 85 lane-stats failures |
| `processed_flowcells` (2,004 dirs) | 47,970 | 52,581 | 719 | 2018-04-09 to 2024-06-28 | 177 sequence lines not in Parkour dev; 201 CONFLICT lines; 1,910 lane-stats failures (interop files gone) |
| merged (`misc/restats_backfill.sqlite`) | 79,729 | 103,613 | 705 with mismatches, 845 with matches | 2018-04-09 to 2026-11-11 | 79,599 sequence rows, 130 matrix rows, no key in both tables |

New-key rows in the merged file: `fragment_median` 8,382, `fragment_q1` 8,381, `fragment_q3` 8,379, `fragment_p10` 8,380, `fragment_p90` 8,364, `fragments_total` 5,463, `peak_count` 1,050, `frip` 1,057, `peak_genome_coverage` 1,098. `insert_size` has 2,054 rows.

The merge priority only matters where sources overlap a flowcell. The merged file has no key in both tables.

## Known quirks
- CONFLICT rows: a barcode with two different values across run dirs of the same flowcell is skipped, not guessed. Example: `HLCH3DRX7 26L002823 mapped_reads [55.66, 55.68]`.
- `lane stats failed` lines for old runs: the Illumina interop files are gone. Lane (matrix) rows are missing for those flowcells. Sequence rows are unaffected.
- `not in Parkour (no sequence stats stored)`: flowcell has no entry on dev; nothing to compare, nothing to push.

## Next
- Compare numbers now on production with the values that would be pushed. Production is read-only for this: GET only.
- Review rows in the sqlite, mark `"update"`, then push to parkour-dev only, after confirmation.
- `push` fills empty values only. A row whose Parkour value is already stored is skipped with a `SKIP` line. Pass `--overwrite` to replace stored values, for example a number from a partial run that the file now contradicts. Without `--apply` nothing is posted either way.
