# Instructions

## Principles

- **KISS**: simplest solution meet requirements.
- Small, focused changes; skip speculative refactors.
- No new dependencies unless explicit ask.
- Requirements/patterns unclear? Ask up to 3 clarifying questions, don't guess.
- New write/edit UI (inline editing, save/confirm flows hitting an API): confirm
  the write path is actually in scope before building it. Read-only display first;
  add editing only once product intent is explicit — building then discarding an
  editor is wasted work.

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

### Icons: FontAwesome + Scarlab Duotone Line only

- Two approved icon sources, no others (no new icon packs/libraries):
  1. **FontAwesome** (`@fortawesome/*`, registered via `library.add` in `main.js`)
     for small inline/action icons — via `<font-awesome-icon icon="fa-solid fa-..." />`.
  2. **SVG files** in `frontend/src/assets/icons/`, sourced from the
     [Scarlab Duotone Line](https://www.svgrepo.com/collection/scarlab-duotone-line-vectors/)
     collection on SVGRepo, for header/action/export-style icons — imported as
     ES modules (e.g. `import iconFoo from "../assets/icons/foo.svg"`), not inlined.
- Before adding a new icon, check `frontend/src/assets/icons/` and the registered
  FontAwesome set in `main.js` for one that already fits.
- When adding a new SVG (e.g. a header icon for a new view), pick one from the
  Scarlab Duotone Line collection and adjust its colors/sizing/styles to match
  the existing icons of the same kind (e.g. other `header_*` icons) rather than
  using it as-is. Follow the existing filename convention: `header_*`, `action_*`,
  `export_*`, `alert_*`.

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

## Vite dev vs prod: two different servers, not just a port

- Prod (`start-prod`) runs `vite build` then serves the static `dist/`
  output on `:5173`. Dev (`start-dev`) runs the live Vite dev server with
  HMR on `:5174`. These are different serving mechanisms, not
  interchangeable — never run the raw Vite dev server (HMR) as a
  production deployment. It serves unminified per-module source over
  dev-only routes (`/@fs/`, `/@id/`, `/src/*`) that assume a trusted
  local machine, has a history of path-traversal/arbitrary-file-read
  CVEs when exposed publicly, and its HMR WebSocket isn't subject to the
  app's normal auth/CSRF handling.
- `misc/nginx-server.conf` is one file, shared by nginx across prod,
  `parkour-test`, and `parkour-dev` (all three domains, one `server`
  block). Its tracked value in git is the **prod** port; `make set-dev`
  locally `sed`s it to the dev port (`hardreset-nginx-server-dev`) —
  that edit is meant to stay local/uncommitted on dev hosts, never
  pushed. **After every `git pull` on a dev/test host, re-run
  `make set-dev`** (or at minimum `make hardreset-nginx-server-dev`) —
  `git pull` silently reverts the port back to prod's value if a local
  override isn't reapplied. A stale Docker single-file bind mount can
  mask this for a long time (nginx keeps serving old cached content
  until the container is restarted), so the failure can surface much
  later than the `git pull` that caused it. Symptom: nginx 502s to the
  vite upstream, or (if the stale mount happened to still match) it
  works until the next restart.

## Vue router needs an explicit index route

- `frontend/src/router/appRoutes.js`'s top-level `/` route has children
  for every page but no `path: ""` entry — without one, visiting the
  bare path renders `AppShell` (header/nav) but leaves
  `<router-view>` (`.app-shell-content`) empty, since no child route
  matches. This looks like a "blank page" but only the content area is
  blank; the nav bar renders fine. Fixed via a
  `{ path: "", redirect: "/libraries_and_samples" }` first child. Any
  future top-level route section added under `/` should keep this in
  mind if it also needs a bare-path landing page.

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
- Date formatting/validation: use `frontend/src/utilities/dateUtils.js`
  (`formatDateForInput`, `formatDisplayDate`, `isValidDate`) instead of hand-rolled
  `new Date()`/`toLocaleDateString` calls.
- Rebuild frontend with `npm run build`. If running under `parkour2-vite` Docker container, prefer Makefile rule `reload-ux` instead.

### Modals/popups/dialogs

- Reuse `focusFirstElement`/`trapFocus` from `frontend/src/utilities/utilityFunctions.js`
  for any new modal, popup, or dialog — don't hand-roll focus logic per component.
- Every dialog needs: `role="dialog"`, `aria-modal`, `aria-labelledby` pointing at
  its heading, focus moved in on open, Tab-trapped focus, Escape to close,
  click-outside to close, and focus restored to the opener on close.
  Reference: `CostsPanel.vue`, `invoicingView.vue` (export popup, columns dialog).

### Async fetches triggered by user-changeable filters

- Date/month pickers, search boxes, or any input that can re-fire a request
  before the previous one resolves need a stale-response guard (incrementing
  request-id checked before applying the response, or an `AbortController`).
  Without it, a slow earlier request can overwrite a newer one's data.
  Reference: `invoicingView.vue` `getInvoicing()` (`invoicingRequestId`).

### Tabulator: derive "displayed/exported rows" from the table, not a reimplementation

- When exporting or otherwise acting on "what the user currently sees" in a
  Tabulator table, read the table's own filtered state
  (`table.getRows("active")` / `table.getData("active")`) instead of
  re-filtering `rowData` by hand — a hand-rolled filter drifts from Tabulator's
  actual active filters (search + per-column) and silently exports the wrong rows.
