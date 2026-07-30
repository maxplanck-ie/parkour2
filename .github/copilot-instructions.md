# Instructions

## Principles

- **KISS**: simplest solution meet requirements.
- Small, focused changes; skip speculative refactors.
- No new dependencies unless explicit ask.
- Requirements/patterns unclear? Ask up to 3 clarifying questions, don't guess.

## Architecture

- **Backend**: Django + Django REST Framework (DRF).
- **Frontend**: Vue 3 with Vite.
- Reuse existing utilities/components before new ones.
- Business logic out of views (backend) and UI components (frontend).

## Frontend UI — non-negotiable rules

Prevent recurring regressions. No deviate without explicit ask.

### Tables MUST use Tabulator

- Tabulator library (`tabulator-tables`) only approved table impl.
  Never hand-roll `<table>`/`<tr>`/`<td>` markup, never new grid
  library (ag-grid, DataTables, PrimeVue tables, etc.) for new tables.
- Render tables through existing wrapper components — don't instantiate Tabulator
  directly, don't duplicate their logic:
  - `frontend/src/components/TabulatorTableLite.vue` — optimized for large record sets.
  - `frontend/src/components/TabulatorTableFull.vue` — full-featured tables.
- Configure table via wrapper's `columnDefs`, `rowData`, `tableOptions` props.
  Column definitions belong in relevant `frontend/src/constants/*Consts.js` file,
  follow existing patterns there. No inline ad-hoc column configs in views.
- Reference: `views/librariesAndSamplesView.vue`,
  `views/poolingView.vue`, `views/requestEditorView.vue`, `views/runStatisticsView.vue`.

### Preserve existing styling (DRY)

- No new styling systems, ad-hoc inline `style="..."`, hard-coded
  colors/fonts/spacing. Reuse what exists.
- Styling sources, preference order:
  1. Existing Bootstrap 5 classes (project depends on `bootstrap` 5.x).
  2. Shared CSS variables/rules in `frontend/src/assets/css/css_base.css` and
     `css_main.css` (e.g. `var(--app-font-family)`). Add variable there rather than
     repeat literal value.
  3. Existing component-scoped styles — extend patterns already in component.
- Tabulator tables use Bootstrap 5 theme
  (`tabulator-tables/dist/css/tabulator_bootstrap5.min.css`) plus shared overrides
  already in wrapper components. Match those; never restyle table inline.
- Before new CSS, search existing class/variable that already does
  job, reuse it. New text/elements inherit surrounding look and feel.

## Changelog

- `CHANGELOG.md` uses date-based versioning (`yy.mm.dd`) for releases, but do NOT add
  date when recording change. Every change (bug fix, feature, refactor with
  user-visible/behavioral impact) MUST add bullet under `Unreleased` heading
  at top of file. Create `Unreleased` heading if missing.
- Dates added manually, only at release time, by renaming `Unreleased` to
  `yy.mm.dd` release date. Never add or guess date yourself.
- Keep entries terse, specific (what changed, why matters), match
  style of existing entries — no filler.

## Commands

- Run backend tests: Makefile rule `djtest`.
- Run frontend tests: Makefile rule `playwright`.
- Build frontend: Makefile rule `reload-ux`.
- Command fails w/ permission error (e.g. built output files owned by root) → app likely inside Docker. Run command inside appropriate container instead `parkour2-django` for backend or `parkour2-vite` for frontend.

## Security

- Never log secrets/sensitive data.
- Validate, sanitize all user input.
- Use Django ORM; skip raw SQL unless strictly necessary.
- Follow least-privilege, safe-default patterns.

## Python / Django / DRF (`**/*.py`)

- Use DRF serializers for input validation, response shaping.
- Business logic out of views; place in service modules/helpers consistent w/ existing codebase.
- Use Django ORM; skip raw SQL unless necessary, clearly justified.
- Follow existing naming, module, package conventions in repo.
- Add/adjust tests for behaviour changes; run with `python manage.py test --parallel`.
- Type hints where they improve clarity; skip overly generic abstractions.

## Vue.js frontend (`**/*.vue`, `**/*.ts`, `**/*.js`)

- Use Vue 3 Composition API; stay consistent w/ existing patterns in repo.
- Prefer `<script setup lang="ts">` for new components; props/emits explicitly typed.
- Keep components focused; extract shared logic into composables/utilities only when clearly reduces duplication.
- Use project's existing API client/wrappers; no new networking patterns.
- Use Pinia for cross-component state (not every local interaction); don't mutate props; follow established store patterns.
- Use `computed`/`watch` intentionally; skip broad/deep watchers unless justified.
- Handle loading, empty, success, error states explicitly in UI flows.
- Favor accessible, semantic HTML, keyboard-friendly patterns.
- Rebuild frontend with `npm run build`. If running under `parkour2-vite` Docker container, prefer Makefile rule `reload-ux` instead.