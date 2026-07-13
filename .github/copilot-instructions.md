# Copilot Chat Instructions

These instructions apply to **Copilot Chat** in VS Code for this repository.
Path-specific rules live in `.github/instructions/` and are applied automatically
based on the file you are editing (see [GitHub docs](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)).

## Principles

- **KISS**: prefer the simplest solution that meets the requirements.
- Prefer small, focused changes; avoid speculative refactors.
- Do not introduce new dependencies unless explicitly requested.
- If requirements or existing patterns are unclear, ask up to 3 clarifying questions instead of guessing.

## Architecture

- **Backend**: Django + Django REST Framework (DRF).
- **Frontend**: Vue 3 with Vite.
- Reuse existing utilities and components before creating new ones.
- Keep business logic out of views (backend) and out of UI components (frontend).

## Frontend UI — non-negotiable rules

These prevent recurring regressions. Do not deviate without an explicit request.

### Tables MUST use Tabulator

- The Tabulator library (`tabulator-tables`) is the ONLY approved table implementation.
  Never hand-roll `<table>`/`<tr>`/`<td>` markup, and never introduce another grid
  library (ag-grid, DataTables, PrimeVue tables, etc.) for new tables.
- Render tables through the existing wrapper components — do not instantiate Tabulator
  directly and do not duplicate their logic:
  - `frontend/src/components/TabulatorTableLite.vue` — optimized for large record sets.
  - `frontend/src/components/TabulatorTableFull.vue` — full-featured tables.
- Configure a table via the wrapper's `columnDefs`, `rowData`, and `tableOptions` props.
  Column definitions belong in the relevant `frontend/src/constants/*Consts.js` file,
  following the existing patterns there. Do not inline ad-hoc column configs in views.
- See existing usages for reference: `views/librariesAndSamplesView.vue`,
  `views/poolingView.vue`, `views/requestEditorView.vue`, `views/runStatisticsView.vue`.

### Preserve existing styling (DRY)

- Do NOT introduce new styling systems, ad-hoc inline `style="..."`, or hard-coded
  colors/fonts/spacing. Reuse what already exists.
- Styling sources, in order of preference:
  1. Existing Bootstrap 5 classes (the project depends on `bootstrap` 5.x).
  2. Shared CSS variables and rules in `frontend/src/assets/css/css_base.css` and
     `css_main.css` (e.g. `var(--app-font-family)`). Add a variable there rather than
     repeating a literal value.
  3. Existing component-scoped styles — extend the patterns already in the component.
- Tabulator tables use the Bootstrap 5 theme
  (`tabulator-tables/dist/css/tabulator_bootstrap5.min.css`) plus the shared overrides
  already defined in the wrapper components. Match those; never restyle a table inline.
- Before adding any new CSS, search for an existing class or variable that already does
  the job and reuse it. New text/elements must inherit the surrounding look and feel.

## Commands

- Run backend tests using Makefile rule: `djtest`.
- Run frontend tests using Makefile rule: `playwright`.
- Build frontend using Makefile rule: `reload-ux`.
- If a command fails with a permission error (e.g. built output files are owned by root), the app is likely running inside Docker. Run the command inside the appropriate container instead `parkour2-django` for backend or `parkour2-vite` for frontend.

## Security

- Never log secrets or sensitive data.
- Validate and sanitize all user input.
- Use Django ORM; avoid raw SQL unless strictly necessary.
- Follow least-privilege and safe-default patterns.
