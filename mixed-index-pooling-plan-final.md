# Plan: Mixed single/dual-index pooling + Hamming-distance guardrail

## Question 1: Can S (single-index) and D (dual-index) samples/libraries share a pool?

**Yes, technically supported by both platforms' sample-sheet formats, but not free.**

### Current repo behavior
`backend/index_generator/index_generator.py:311-323` (`IndexGenerator.validate_index_types`)
hard-blocks today:
```python
is_dual = [x.is_dual for x in index_types]
if len(set(is_dual)) != 1:
    raise ValueError("Mixed single/dual indices not allowed.")
self.mode = "dual" if is_dual[0] else "single"
```
This runs at **pool creation** via `IndexGeneratorViewSet.generate_indices`
(`backend/index_generator/views.py:281`). The resulting single global
`self.mode` string then gates ~6 further call sites inside
`IndexGenerator`/`IndexRegistry` that decide i5 lookup/blanking
per *batch*, not per record.

Separately, `IndexGeneratorViewSet.save_pool` (`views.py:301-379`,
final persist action) does **not** call `IndexGenerator`/`validate_index_types`
at all — it persists already-chosen indices and checks `is_dual`
**per-record** there (`views.py:334-367`). It is already mixed-S/D-safe
server-side.

Frontend `indexGeneratorView.vue` has its own independent gate,
`validatePoolCompatibility()` (line 1734, called from both the
generate flow at line 1732 and the save flow at line 1883), which
also hard-blocks any pool containing rows with differing
`indexTypeMeta(...).is_dual` — this blocks manual mixed-pool saves even though the
backend `save_pool` path would accept them.

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
Caveat: DRAGEN's **default barcode-collision check is "combined"**
(both index reads concatenated) — a same-lane collision between a
single-index row and a dual-index row's Index1 is only flagged if
*both* fall within tolerance on the compared portion. The per-lane
opt-in `BarcodeMismatchesIndex2` knob exists because the combined check
alone can miss a collision that a per-index check would catch. Net:
DRAGEN supports mixed rows mechanically, but the demux-collision
safety net is weaker for the mixed case than for uniform dual-index.

### bases2fastq (Element AVITI)
Docs (https://docs.elembio.io/docs/run-manifest/samples/#index-collision)
confirm per-sample `Index1`/`Index2` columns are independent per row — a row
can leave `Index2` empty (single-index) while another carries a full `Index2`
(dual-index). Mismatch tolerance is set **per-lane**, not per-sample:
`Settings[].I1MismatchThreshold` / `I2MismatchThreshold` (0-2, default 1 each).
Because the threshold is lane-global, a single-index row's I1-only match and a
dual-index row's I1+I2 match are scored under the *same* per-lane budget — there
is no independent per-record demux pass. This is AVITI's counterpart of DRAGEN's
combined-check caveat: mixing S+D in one lane narrows the effective collision
margin for the pool as a whole.

### Evidence from production runs (rapidus, `pipegrp@rapidus`)
Checked `/dont_touch_this/short_runs/ElementBiosciences/{AV261103,AV251009}/` —
all `RunManifest.csv`/`RunManifest.json` under both AVITI instruments.

**No production run has ever mixed single- and dual-index samples in the same lane.**
Scanned all AVITI `RunManifest.csv` since 2026-08-01 for empty-`Index2` rows
(single-index signature): only one run matched, `20260915_AV261103_2605694029`. In
that run:
- Lane 1: two dual-index projects (`4058_Fakhraeighazvini_Oudelaar`, `4061_Cao_Oudelaar`),
  both 8bp/8bp, mixed *with each other* fine but not with any single-index sample.
- Lane 2: one single-index project (`4044_Carrozzo_Oudelaar`), 6bp Index1 only,
  **alone in its lane** — no dual-index rows sharing it.

Two most-recent dual-index runs (`20260922_AV261103_2605514357` 8bp/8bp,
`20260922_AV261103_2605440090` 10bp/10bp): both single-flowcell, per-lane
`I1MismatchThreshold`/`I2MismatchThreshold` = 1/1 uniformly — confirms mismatch
tolerance is flat per-lane regardless of index type present, consistent with docs.

**Implication:** Staff have avoided S+D mixing in practice (by lane-separating them),
which matches the docs' caveat — this is *de facto* institutional evidence the
combined-tolerance risk is real enough that nobody has tested it in production yet.
Supports shipping the relaxation as **opt-in with a visible warning**, not silent default.

### Verdict
Allow at the data-model level (loosen `validate_index_types`), but:
1. Surface a warning, not silent success — mixing has real downstream demux-tolerance
   cost (see DRAGEN/bases2fastq caveats above), and zero production runs have
   exercised this path yet.
2. Downstream sample-sheet export is **not yet capable** of emitting what DRAGEN/bases2fastq
   need for a mixed pool (no v2 `OverrideCycles` column, no dual-manifest generation).
   That's separate, larger work — relaxing the pool-creation check flags this follow-up,
   don't ship a config that silently produces wrong sample sheets.

## Question 2: Hamming-distance guardrail — worth adding?

**Yes.** Both platforms' docs already publish the exact relationship, we're not
inventing a heuristic:

| Mismatch threshold (per-index) | Min required pairwise Hamming distance |
|---|---|
| 0 | ≥ 1 |
| 1 | ≥ 3 |
| 2 | ≥ 5 |

(https://docs.elembio.io/docs/run-manifest/samples/#index-collision;
DRAGEN's `BarcodeMismatchesIndex1`/`BarcodeMismatchesIndex2`, same 0-2 range,
default 1 each — matches live defaults confirmed on rapidus above.)
Formula: `min_distance ≥ 2×N + 1` for N allowed mismatches.

### Implementation: stdlib only, no scipy
Raw equal-length integer count:
```python
def hamming_distance(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))
```
For AVITI's unequal-length case (single-index 6bp vs dual-index 8bp, seen in
production above): compare only overlapping prefix (`zip` truncates to shorter).
This matches how the per-lane check scores it — sequencer can only compare cycles
both indices share. Document this inline as the "reconciling different lengths"
note — same shared-tolerance caveat from Question 1, not separate mechanism.

## Chosen scope (Option A) vs. rejected alternative (Option B)

**Option A (recommended):** Relax only the already-per-record-correct `save_pool`
manual path + its frontend gate; leave `generate_indices`'/`IndexGenerator.generate()`
restricted to homogeneous (all-S or all-D) batches. Add Hamming-collision advisory
to the `save_pool`/pooling-membership paths only.
- Size: ~50-80 lines net (relax 2 checks, add 1 stdlib helper, wire warnings into
  2 response payloads, 1 frontend banner).
- Risk: low — touches only code paths already proven per-record-safe server-side;
  auto-generate's fragile `self.mode` threading is untouched.

**Option B (rejected for this pass):** Rewire `IndexGenerator.generate()` and
`IndexRegistry` to track dual/single per-record instead of one global `self.mode`,
enabling auto-generate to mix S+D in one batch.
- Size: ~250 lines across ~6 call sites, non-trivial ordering invariants in the
  picking loop.
- Risk: high, sibling-test breakage likely; no production evidence (see rapidus
  scan above) that staff need *auto-generation* of mixed pools today — every
  production instance of separate S/D groups was lane-separated (two homogeneous
  pools already).
- Verdict: defer. If staff later request one-click mixed auto-generation, revisit
  as its own PR with its own test plan.

## Non-goals
- No new dependency (stdlib `hamming_distance` only).
- No implementation yet — this is the design plan requested before code changes.
  Once approved, the diff needs its own PR review, Django tests (mixed-pool:
  shared i7 S+D collision, below-threshold Hamming distance, length-mismatched
  indices), CHANGELOG entry, and smoke test running `save_pool` against
  fixture mixed-type pool.
- No change to `generate_indices` homogeneous-only constraint (Option B, explicitly
  deferred above).
- No dual-manifest / v2 `OverrideCycles` sample-sheet export work (flagged as
  separate follow-up in Question 1's Verdict).
