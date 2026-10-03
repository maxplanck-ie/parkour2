# Plan: Mixed single/dual-index pooling + Hamming-distance guardrail

**Status: Phase 1 MVP + Phase 2 wave 1 implemented and committed** (branch
`idxgen`, commit `e9b38135`). This file consolidates the original design doc,
the Opus review, and the user's answers to its open questions (previously
split across `plan.md`/`fragen.md`/`extra.md` — merged here per request,
originals removed). **This file is intentionally kept uncommitted.**

## Implementation status at a glance

| # | Task | Tier | Status |
|---|---|---|---|
| 1 | `hamming_distance(a, b)` helper | Haiku | ✅ Done — `backend/common/utils.py`, doctested |
| 2 | Floor semantics decision + `MIN_HAMMING_DISTANCE` constant | Sonnet | ✅ Done — `views.py:79`, per-read (not concatenated), see Q-E resolution below |
| 3 | 10 mechanical `self.mode`→`is_dual` swaps | Haiku | ✅ Done — `index_generator.py` |
| 4 | Drop `mode` param from `IndexRegistry` | Haiku | ✅ Done — ctor + 8 test call sites |
| 5 | Remove mixed-index block from `validate_index_types` | Sonnet | ❌ **Not done, by design** — `generate_indices` (auto-pick) still blocks mixed types; only `save_pool` (manual/TDD path) was relaxed, per user's D answer below ("relax save_pool first") |
| 6 | Delete `test_mixed_single_dual_indices` | Haiku | ❌ Not done — correct, since task 5 didn't happen; this test still accurately pins `generate_indices`' current 400 behavior |
| 7 | i5 split/merge redesign (sample-pk-keyed) | Sonnet | ⏳ Not started — blocked on task 5; needed only once `generate_indices` itself goes mixed-aware |
| 8 | Hard Hamming filter in `find_index`/`find_pair` | Sonnet | ⏳ Not started — blocked on 2, 7 |
| 9 | `iterations` request param | Sonnet | ⏳ Not started — blocked on 8, needs cap decision (Q-C below) |
| 10 | Best-of-N outer loop | Sonnet | ⏳ Not started — blocked on 9 |
| 11 | Post-hoc advisory in `save_pool` | Sonnet | ✅ Done — `compute_index_warnings()`, `views.py:82-106,410-414` |
| 12 | Surface advisory in frontend | Sonnet | ✅ Done — `indexGeneratorView.vue:notifyIndexWarnings` displays toast on close indices with `compared_length` |
| 13 | Narrow frontend `validatePoolCompatibility` gate | Sonnet | ✅ Done — `is_dual` clause removed, read-length clause kept, `indexGeneratorView.vue` |
| 14 | Backfill read-length guard server-side | Sonnet | ✅ Done — `views.py:save_pool` raises 400 on mismatched `read_length_id` across records |
| 15 | CHANGELOG entry | Haiku | ✅ Done — `CHANGELOG.md` under `Unreleased` |
| 16 | `compared_length` in warning schema | Haiku | ✅ Done — `utils.py:hamming_distance` returns `(dist, min_len)`, schema persisted on `Pool.index_warnings` |

**What shipped (Phase 1 MVP):** mixed single+dual pools can now be **manually
saved** via `save_pool` (frontend gate narrowed, backend already safe). On
save, `compute_index_warnings()` scores every pair of records in the pool
per-read (i7 vs i7, i5 vs i5, scored separately — never concatenated),
flags any pair closer than `MIN_HAMMING_DISTANCE=3`, and persists the result
on `pool.index_warnings` (new JSONField), returned in the response as
`{"success": true, "warnings": {...}}`.

**What's explicitly deferred:** `generate_indices` (auto-pick) still hard-blocks
mixed index types — staff must manually assign indices for a mixed pool today.
Making auto-pick mixed-aware (tasks 5, 7-10) is Phase 2, not started.

---

## Question 1: Can S (single-index) and D (dual-index) samples/libraries share a pool?

**Yes, technically supported by both platforms' sample-sheet formats, but not free.**

### Current repo behavior (as of before this session's changes)
`backend/index_generator/index_generator.py:311-323` (`IndexGenerator.validate_index_types`)
hard-blocked:
```python
is_dual = [x.is_dual for x in index_types]
if len(set(is_dual)) != 1:
    raise ValueError("Mixed single/dual indices not allowed.")
self.mode = "dual" if is_dual[0] else "single"
```
This runs at **pool creation** via `IndexGeneratorViewSet.generate_indices`
(`backend/index_generator/views.py:281`). **This block is still active** —
task 5 (removing it) was intentionally not done this round; see Q-D below.

Separately, `IndexGeneratorViewSet.save_pool` (now `views.py:332`, formerly
301-379) does **not** call `IndexGenerator`/`validate_index_types` at all —
it persists already-chosen indices and checks `is_dual` **per-record**. It
was already mixed-S/D-safe server-side, confirmed by this session's
implementation and its 64-test-green full-suite run.

Frontend `indexGeneratorView.vue` had its own independent gate,
`validatePoolCompatibility()`, which hard-blocked any pool containing rows
with differing `is_dual` — **this is now narrowed** (task 13, done): the
`is_dual` clause is removed from both the generate-flow and save-flow call
sites, read-length clause is untouched.

### DRAGEN bcl-convert (Illumina, v4.1+)
Per-sample `OverrideCycles` in **Sample Sheet v2**'s `[BCLConvert_Data]`
section lets each row mask its own Index 2 cycles (`I8` vs `N8`), so
single- and dual-index rows legitimately coexist in one sample sheet/lane.
Confirmed in docs' own example
(https://help.dragen.illumina.com/dragen-v4.4/product-guide/dragen-v4.4/bcl-conversion):
```
Sample_ID,index,index2,OverrideCycles
21599,ATAGAGGC,TATAGCCT,Y151;I8;I8;Y151        <- dual
21600,ACGTACGT,na,Y151;I8;N8;Y151              <- index2 masked as skip
```
Caveat: DRAGEN's **default barcode-collision check is "combined"** (both
index reads concatenated) — a same-lane collision between a single-index
row and a dual-index row's Index1 is only flagged if *both* fall within
tolerance on the compared portion.

### bases2fastq (Element AVITI)
Docs (https://docs.elembio.io/docs/run-manifest/samples/#index-collision)
confirm per-sample `Index1`/`Index2` columns are independent per row — a row
can leave `Index2` empty (single-index) while another carries a full `Index2`
(dual-index). Mismatch tolerance is set **per-lane**, not per-sample:
`Settings[].I1MismatchThreshold` / `I2MismatchThreshold` (0-2, default 1 each).

**AVITI sample-sheet export is already mixed-safe** — `flowcell/views.py:479-490`
emits blank `Index2` for single-index records already. Actual AVITI gap: no
`[SETTINGS]` section at all, so mismatch thresholds are never written. The
real "not yet capable" gap is Illumina-only: the v1 `[Data]` branch
(`flowcell/views.py:460-475`) has a fixed 11-column header, no
`OverrideCycles` support — **out of scope for this plan**, flagged as its
own follow-up.

### Evidence from production runs (rapidus, `pipegrp@rapidus`)
Checked `/dont_touch_this/short_runs/ElementBiosciences/{AV261103,AV251009}/`.
**No production run has ever mixed single- and dual-index samples in the same
lane.** One run (`20260915_AV261103_2605694029`) had a single-index lane
(6bp Index1, project `4044_Carrozzo_Oudelaar`) but it was alone in its lane,
not mixed with the dual-index lane in the same run.
`I1MismatchThreshold`/`I2MismatchThreshold` confirmed 1/1 per-lane across all
checked runs — flat per-lane regardless of index type present.

**Implication:** today staff lane-separate S+D groups by default. This plan
*enables* mixing in one pool (with guardrails), doesn't force it.

### Verdict
Allow at the data-model level, but surface a warning rather than silent
success — mixing has real downstream demux-tolerance cost. Sample-sheet
export limitations for Illumina mixed pools are flagged as separate,
out-of-scope follow-up work (see Non-goals).

---

## Question 2: Hamming-distance guardrail — worth adding?

**Yes.** Both platforms' docs already publish the exact relationship:

| Mismatch threshold (per-index) | Min required pairwise Hamming distance |
|---|---|
| 0 | ≥ 1 |
| 1 | ≥ 3 |
| 2 | ≥ 5 |

Formula: `min_distance ≥ 2×N + 1` for N allowed mismatches. Matches AVITI's
live default (1 mismatch) confirmed on rapidus above, hence
`MIN_HAMMING_DISTANCE = 3` as implemented (`views.py:79`).

**Implementation: stdlib only, no scipy.** `hamming_distance(a, b)` in
`backend/common/utils.py` — `zip`-truncating equal-length count, docstring
states the truncation rule. For AVITI's unequal-length case (single-index
6bp vs dual-index 8bp, seen in production), comparison is over the
overlapping prefix only — this matches how the sequencer itself scores it
(can only compare cycles both indices share). See Q-F resolution below for
the one refinement identified post-implementation (transparency about
partial-length comparisons).

---

## Question 3: Use per-record `is_dual` awareness during generation itself, not just post-hoc warning?

**Still the design, not yet implemented (Phase 2, task 8).** `find_index`
(index_generator.py:570-605) and `find_pair` (630-676) already thread the
full-batch-so-far picks into every candidate evaluation and already select
by best `avg_score` (color-balance) — same infrastructure a Hamming-distance
objective needs.

**Design — two-phase select, reuses existing score-and-pick pattern:**
1. For each shuffled candidate: `min(hamming_distance(candidate, x) for x in indices_in_result)`.
2. Hard-filter candidates meeting `MIN_HAMMING_DISTANCE` first; among
   survivors, existing `avg_score` color-balance breaks ties. Lexicographic,
   not a blended weight — avoids inventing a combined-scoring formula.
3. If no candidate meets the floor (small/custom index sets), fall back to
   today's unfiltered pool rather than failing generation — tag the pick so
   the post-hoc warning still fires.

**Cost note (corrected from original estimate):** "`MAX_ATTEMPTS` already
retries on failure" (original Question 3 cost claim) is **false** — the
`generate()` loop (420-455) only retries the duplicate-`all_pairs` condition.
`ValueError("Index not found.")`, `ValueError('Could not generate
indices...')`, and `IndexError` from `find_pairs_fixed` all propagate
straight out as a 400, uncovered by that retry. A hard Hamming filter makes
these more likely to fire. Task 8 must account for this, not lean on the
existing retry as free insurance.

---

## Question 4: User-facing controls — opt-in flag, iteration depth, parallel multiplier?

**Still the design (Phase 2, tasks 9-10), not yet implemented. Single param,
threshold-triggered — not two separate flags.** Confirmed correct by user's
A answer below (no change from original design).

One optional request param, `iterations: int | None`, on `generate_indices`.

- **`MAX_ATTEMPTS` (30) is always a floor, never lowered** — effective
  attempts = `max(iterations or MAX_ATTEMPTS, MAX_ATTEMPTS)`.
- **`iterations` omitted or `<= MAX_ATTEMPTS`:** today's exact first-success
  loop, unchanged — no floor filter, no extra Hamming computation, zero
  regression risk.
- **`iterations > MAX_ATTEMPTS`:** switches on both things together — the
  Question-3 floor filter activates in `find_index`/`find_pair`, *and* the
  outer loop becomes best-of-N: track best min-pairwise-distance seen,
  early-exit once every pair clears the floor, else return best-seen after
  `iterations` attempts.

This makes "request more search depth" and "get Hamming-aware picking" the
same action — no way to ask for one without the other, removing the bug
class where raising iteration count silently does nothing.

**Parallel "multiplier" (N workers × M/N iterations): rejected for v1,
measured why.** `multiprocessing.Pool` spawn+teardown overhead (~29ms,
benchmarked on this VM) exceeds 5000 sequential toy iterations (~12ms).
2-vCPU VM caps real parallelism at 2 workers regardless of request count.
`IndexRegistry` already caches indices in-memory per `index_type` at init —
attempts aren't DB-bound, nothing to amortize across workers. **Crossover
condition to revisit:** if per-attempt wall time is ever measured above
~50ms, parallel multi-start becomes worth it; revisit the Django task-queue
non-goal at the same time (synchronous endpoint shouldn't block that long
either way).

---

## Index hopping vs. sequencing-error collisions — a distinction this plan must state explicitly

**This guardrail protects against one failure mode, not the other — document
which, so the feature isn't mis-communicated internally as "hopping
protection."**

- **Hamming distance / mismatch-tolerance guards against sequencing-error
  misassignment**: a read's index is mis-called during sequencing (base-call
  error), and distance-based tolerance decides whether the mis-called
  sequence still correctly matches its true sample or ambiguously/wrongly
  matches a different sample's index. This is exactly what
  `compute_index_warnings()` and the planned hard filter address.
- **Index hopping is a different, physical failure mode**: a library
  molecule itself acquires the wrong index during pooled amplification/
  cluster generation (not a sequencing read-out error). Hamming distance
  between indices **does not detect or prevent this** — what prevents it is
  using **unique dual indices (UDI)**, i.e. never reusing the same i7 or i5
  value across different samples in a pool, so a hopped read's barcode
  combination doesn't match any valid sample pairing and can be filtered at
  the demux/analysis stage.
- **Platform-dependent severity**: patterned flow cells (e.g. Illumina
  NextSeq 2000) are the primary context where hopping is a real concern —
  UDI is strongly preferred there. AVITI's chemistry (RCA/polony-based, not
  bridge-amplification-on-patterned-surface) has negligible documented
  hopping risk per Element's own materials, making single-indexing more
  defensible on that platform specifically than it would be on a patterned
  Illumina flow cell.

**Implication for this plan:** nothing above changes the Hamming-distance
guardrail design — it's still correct and worth having. It changes what the
guardrail should be *described as* to staff: a sequencing-error/collision
safety net, not hopping protection. If hopping protection is ever wanted as
a feature, it requires a UDI-uniqueness check (no i7/i5 value reused within
a pool), a materially different check from pairwise distance — **not in
scope here, flagged as a possible separate follow-up.**

---

## Chosen scope: per-record dual-aware rewire (Phase 2 wave 1 — done; wave 2 — not started)

**Option A** = small/safe: relax `save_pool` manual-entry path only; leave
`generate_indices` homogeneous-only. **Option B** = full rewire: both become
per-record dual-aware.

**What actually shipped this round is a hybrid, not pure Option A or B:**
`save_pool` is relaxed (matches Option A's save-path piece). The mechanical
`self.mode`→`is_dual` plumbing cleanup (10 call sites + `IndexRegistry`
constructor) is done — it was prerequisite groundwork regardless of which
option wins, since `self.mode` was redundant state even for Option A's
scope. `generate_indices`'s actual hard-block (task 5) is **not** removed
yet — full Option B isn't live. This matches the user's D answer below:
relax `save_pool` first via TDD, no backend gates needed initially,
auto-pick mixed-awareness comes later.

**Remaining scope for full Option B (Phase 2 wave 2):** the i5 split/merge
redesign (task 7) is the one genuinely complex remaining piece.
`find_indices` (index_generator.py:543-568) returns results **re-sorted** by
`(index_type, cast_index_number(number))`, not input order. The original
plan's "split sublists, merge back at the correct position" design **cannot
work** — a positional zip against two independently-resorted lists of
different lengths has no valid alignment. **Needs a sample-pk-keyed
association** (e.g. `dict[sample.pk] -> index_dict`) instead of a positional
merge. This was caught by Opus review, not discovered during Phase 1
implementation — still unresolved, still blocks task 7.

---

## Resolved: user's answers to the original open questions (A-G)

### A. Hamming floor filter: default-on or gated behind `iterations`?
**Confirmed: gated, per Question 4's design above — no contradiction to
resolve.** Floor filter and best-of-N both activate only when
`iterations > MAX_ATTEMPTS`; at or below, behavior is byte-identical to
today. This was the design the plan already had in Question 4; the earlier
apparent Q3/Q4 contradiction is resolved by treating Q3 as describing the
*mechanism* and Q4 as describing *when it's switched on* — not two
competing designs.

### B. Warning schema and persistence
**Confirmed: persist as JSON on `Pool`** (done — `Pool.index_warnings`
JSONField, `views.py:410-414`). Two points where the implementation
deliberately differs from the original ask, both intentional:

- **Keyed by record `pk`, not barcode identifier.** Keying by barcode would
  actively break the feature: two near-duplicate barcodes colliding as dict
  keys could clobber each other in the warnings structure — exactly the
  case this feature exists to catch. PK is the correct key.
- **No severity field — only `distance` (int) and `index_read`
  (`"i7"`/`"i5"`).** Distance is already ordinal (lower = worse); inventing
  a categorical severity (e.g. "low"/"high") on top would be an unrequested
  scoring formula with no platform-published thresholds to ground it in,
  same trap Question 3 deliberately avoided for candidate selection. If a
  severity tier is wanted later, it should be computed by the *consumer*
  (frontend or a future report) from `distance`, not baked into the stored
  schema.
Current schema, exact, as implemented (`views.py:82-106`):
```python
{
    "<sample_or_library_pk>": {
        "<other_pk>": {
            "distance": int,
            "compared_length": int,
            "index_read": "i7" | "i5",
        }
    },
    ...  # symmetric: both directions present
}
```
Only pairs with `distance < MIN_HAMMING_DISTANCE` appear. If both i7 and i5
collide for the same pair, only the worse (lower-distance) read is reported.
Key always present in the response (`{"success": true, "warnings": {}}` on a
clean pool), per the "stable schema" requirement from the original review.

**Frontend display is still not implemented** (task 12) — warnings are
computed, persisted, and returned, but no UI surfaces them yet.

### C. `iterations` upper bound
User: max ~10k in mind, open to 3k if timeout risk; task queue explicitly
out of scope for now. **No gunicorn `--timeout` override found in this repo**
(checked Dockerfile, docker-compose, entrypoint scripts) — Django's gunicorn
default is 30s; nginx `proxy_read_timeout` is looser (120s per
`misc/nginx-server.conf`), not the binding constraint. **Decision: cap at
3000** for the initial implementation (task 9) — conservative relative to
the 30s default, revisit upward only after measuring actual per-attempt wall
time in this codebase (ties to Question 4's ~50ms crossover note). Not yet
implemented.

### D. Scope ordering: relax `save_pool` first
User: no backend gates needed initially (nice-to-have later); confirms
`save_pool`-first via TDD. **This is exactly what Phase 1 MVP did** — task
11 (save_pool warnings) shipped; task 5 (`generate_indices` relaxation) was
deliberately deferred to Phase 2. Matches the user's explicit preference,
not an oversight.

### E. Which index read does the floor measure?
**Confirmed and implemented: per-read, separately** (i7 vs i7, i5 vs i5 —
`views.py:94` `for read in ("i7", "i5")`), never concatenated. Matches the
user's E answer exactly.

### F. Should mixing be blocked when index lengths differ (e.g. single
shorter than dual)? — user asked this back, unresolved until now.

**Proposed resolution: no hard block on length mismatch.** The
truncated-prefix Hamming comparison already matches real per-cycle demux
behavior — a sequencer literally cannot compare cycles that don't exist on
the shorter index, so truncation isn't a shortcut, it's the physically
correct comparison. Blocking mixed-length pools outright would forbid
exactly the production-realistic case (AVITI 6bp single vs 8bp dual, seen in
real rapidus data under Question 1 above).

**What *is* missing, and should be fixed:** the current warning schema gives
no signal that a comparison was truncated — a `distance: 2` on a full 8bp-vs-8bp
pair and a `distance: 2` on a truncated 6bp-vs-8bp pair look identical in the
response, but the second one compared fewer cycles and is a weaker signal.
**New task (Phase 2, unscheduled number — call it task 16):** add a
`compared_length` field to each warning entry
(`{"distance": int, "index_read": "i7"|"i5", "compared_length": int}`), so
staff can see when a check was partial. Small, additive, no schema-breaking
change to existing keys — should land whenever task 12 (frontend display) is
tackled, so the UI can show "(partial, Nbp compared)" inline.

### G. Test fixture shape
**Confirmed: tube-only**, matches what Phase 1 subagents actually used.
Plate-format coverage stays on the roadmap, not required for current tasks.

---

## Remaining task breakdown (Phase 2, not started)

Tier rubric: **Sonnet** = touches control flow, changes a public request
contract, requires reasoning about edge cases/ordering, or has ambiguity.
**Haiku** = pure mechanical, unambiguous target, zero design decisions.

| # | Task | Files/Functions | Depends on | Tier | Acceptance check |
|---|---|---|---|---|---|
| 5 | Remove mixed-index block from `validate_index_types`; keep read-length check | `index_generator.py:validate_index_types` (~311-327) | — | **Sonnet** | New test: single-index type + dual-index type, same read length → `generate_indices` returns 200 |
| 6 | Delete `test_mixed_single_dual_indices` (pins the 400 this removes) | `tests.py` (search current line, moved since last count) | 5 | **Haiku** | Test gone; suite green |
| 7 | **Redesign i5 association for mixed batches** — sample-pk-keyed dict, not positional merge | `index_generator.py:generate()` (~417-468), `find_indices` (~543-568) | 5 | **Sonnet**, highest-risk, ship alone | Fixture: 2 single-index + 2 dual-index tube samples in one call → every record's `index_i5` non-empty iff `index_type.is_dual`, belongs to that record's own index type; dual-only/single-only tests byte-identical |
| 8 | Hard Hamming filter in `find_index`/`find_pair`, using `MIN_HAMMING_DISTANCE` (already defined, `views.py:79` — move to shared location both views.py and index_generator.py can import) | `index_generator.py:find_index` (~570-604), `find_pair` (~630-673) | 2 (done), 7 | **Sonnet** | Hand-built set where exactly one candidate clears distance 3 → chosen even over better color-balance score; separate test: no candidate clears → generation succeeds, pick flagged |
| 9 | `iterations` param: explicit `int()` coercion with clear `ValueError`, cap at 3000 (Q-C resolved above) | `views.py:generate_indices`, `index_generator.py:__init__` | 8 | **Sonnet** | `iterations="abc"` → 400 named message; `iterations=5` → still 30 attempts; `iterations=5000` → 400; omitted → byte-identical to today |
| 10 | Best-of-N outer loop when `iterations > MAX_ATTEMPTS` | `index_generator.py:generate()` | 9 | **Sonnet** | Deterministic-seed test: `iterations=200` on a pool where first-success misses floor → returns strictly higher min pairwise distance than `iterations` omitted |
| 12 | Surface advisory in frontend (warnings already computed/persisted) | `indexGeneratorView.vue` save-response handler; `poolingView.vue` if Pool-detail display wanted | 11 (done) | **Sonnet** | Save colliding pool in browser → warning visible, no reload needed |
| 14 | Backfill read-length guard in `save_pool` (frontend-only today, bypassable via direct POST) | `views.py:save_pool` | — | **Sonnet** | Direct POST to `save_pool` with differing read lengths → 400 |
| 15 | CHANGELOG entry under `Unreleased` | `parkour2/CHANGELOG.md` | all above | **Haiku** | Entry matches existing one-paragraph-per-bullet style, references commit `e9b38135` + follow-up commits |
| 16 | `compared_length` field on warning entries (Q-F resolution above) | `backend/common/utils.py` (hamming_distance or a wrapper), `views.py:compute_index_warnings` | 11 (done) | **Haiku** — additive field, schema already has the shape, no new design | Truncated pair (6bp vs 8bp) → `compared_length: 6`; equal-length pair → `compared_length` == full index length |

**Dependency order:** 5 → {6, 7}; 7 → 8 → 9 → 10; 12 depends only on already-done
11; 14 independent; 16 depends only on already-done 11; 15 last.

**Model assignment summary:** 3 Haiku tasks (6, 15, 16 — mechanical),
6 Sonnet tasks (5, 7, 8, 9, 10, 12, 14 — control flow, i5 redesign, request
contract, or UI work). Task 7 stays highest-risk, ship alone.

---

## Non-goals (unchanged)
- No new dependency (stdlib `hamming_distance` only) — confirmed in shipped code.
- No dual-manifest / v2 `OverrideCycles` sample-sheet export work (Illumina-only
  gap, confirmed real in Opus review; AVITI already handles mixed rows).
- No parallel/multiprocess search workers, no `multiplier` param — measured
  and rejected at today's scale (Question 4). Revisit only past the
  ~50ms/attempt crossover.
- No Django task queue (celery/rq) — none installed today. `generate_indices`
  stays synchronous; `iterations` cap (3000, Q-C) keeps it inside normal
  request-timeout budgets without needing one.
- No UDI-uniqueness / index-hopping protection (see dedicated section above)
  — materially different check from pairwise distance, not in scope here.
- No per-pool configurable `MIN_HAMMING_DISTANCE` override — hardcoded to
  platform default (1 mismatch → distance 3); revisit if a platform's live
  default ever diverges from what's confirmed on rapidus.
- Opus review's broader architecture ideas from `extra.md` (vendor index
  catalogs, pluggable platform-profile configs, FASTQ-based post-run
  confusion-matrix analysis, pluggable Illumina/AVITI exporters) are
  aspirational roadmap items, not part of this plan's scope — noted here so
  they aren't lost, not expanded into tasks.

## Opus review reference
Full read-only review transcript: `agent://BottomFly`. Verified 10/10 cited
call-site line numbers exact; found the two design-breaking issues
documented inline above (Q3/Q4 apparent contradiction, i5 positional-merge
impossibility) plus the corrected facts folded into their relevant sections
above (self.mode count, AVITI export already mixed-safe, retry-loop coverage
gap, frontend gate scope, pinned test needing deletion).
