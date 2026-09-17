# Task 4 report — demo-deploy.yml

## Files changed
- Created `.github/workflows/demo-deploy.yml`
- Appended `backend/fixtures_snapshot.dump` to `.gitignore`

## Corrections made against the brief's draft

1. **Requirements path**: brief guessed `backend/requirements.txt`. Actual repo
   layout (confirmed in `backend.Dockerfile`'s `pk2_base` stage, line
   `RUN ... uv pip install -r requirements/${PyVersion}/base.txt`, and
   `backend/requirements/<pyver>/{base,demo,dev,testing}.txt` on disk) is
   `backend/requirements/3.12/base.txt`. Pinned to 3.12 (the Dockerfile's own
   `ARG PyVersion=3.12` default / `FROM python:3.12-bookworm`), matching what
   `pk2_demo` actually ships. Installed with `uv pip install --system` (no
   `working-directory: backend`, since the path already includes `backend/`)
   and added `uv pip install --system setuptools wheel` first — `django.yml`'s
   matrix job does this too (`ModuleNotFoundError` workaround for `pkg_resources`
   on newer Python).

2. **Checkout/setup-python/setup-uv actions**: pinned to the exact SHAs
   `django.yml` uses (`actions/checkout@3d3c42e...` v7.0.1,
   `actions/setup-python@5fda3b9...` v7.0.0, `astral-sh/setup-uv@20cfd1b...`
   v10.0.1) instead of the brief's unpinned `@v4`/`@v5`/`@v8`, for consistency
   with this repo's existing pinning convention. Also added
   `persist-credentials: false` on checkout, matching `django.yml`.

3. **`flyctl deploy` flags**: brief's draft used
   `--remote-only=false --push`, flagged in its own notes as unverified. Checked
   the installed `flyctl v0.4.104 --help`: `--remote-only` is the default
   (remote builder); to build on the GitHub runner (satisfying the "Docker
   build happens on the GitHub runner, not the Fly VM" constraint) the correct
   flag is `--local-only`, combined with `--push` to push the locally-built
   image to Fly's registry. Also added `--ha=false .` to mirror the existing
   `make fly-deploy` target (`flyctl deploy --config misc/fly.toml --ha=false .`)
   for consistency — the trailing `.` sets the build context to the repo root,
   which is required since `misc/fly.toml`'s `[build] dockerfile = '../backend.Dockerfile'`
   is resolved relative to the config file's directory while `pk2_demo`'s
   `COPY backend/fixtures_snapshot.dump /app/fixtures_snapshot.dump` needs the
   context rooted at the repo root, same as CI's dump file location. Dropped
   the redundant `--build-arg VITE_GOATCOUNTER_URL=...` from the CLI call since
   `misc/fly.toml`'s `[build.args]` already bakes that in.

4. **`--exclude-table-data` table list**: verified against
   `backend/common/management/commands/reset_demo.py`'s comment (`flush()`'s
   post_migrate signal recreates django_content_type/auth_permission...`) and
   Task 1's spec cross-reference (`django_content_type`, `auth_permission`,
   `django_migrations`, `django_session`). Brief's draft already used the
   exact same four table names — no change needed.

5. **`DJANGO_SETTINGS_MODULE`/`DATABASE_URL`/`SECRET_KEY` for the migrate +
   fixture-dump step**: confirmed these match `django.yml`'s own
   `Verify migrations`/`Validate templates` steps, which use the identical
   three env vars against `config.settings.prod` with a `postgres://` DSN and
   a placeholder `SECRET_KEY`. Kept as the brief drafted (`config.settings.prod`,
   not `.demo`).

6. **Postgres service container**: kept as the brief drafted
   (`postgres:18`, `parkour`/`parkour`/`parkour` user/password/db, port 5432,
   `pg_isready` healthcheck) — this differs slightly from `django.yml`'s own
   service (which uses `postgres:latest` + a `secrets.POSTGRES_PASSWORD`/dynamic
   port), but matches `misc/fly.toml`'s comment pinning postgres-client-18 to
   the demo's real Postgres version, and needs fixed credentials/port since
   this workflow (unlike `django.yml`) also shells out to `pg_dump` directly
   with hard-coded `--host=localhost --username=parkour --dbname=parkour`.

7. Added `if: github.repository == 'maxplanck-ie/parkour2'` guard, matching
   the pattern used by every job in `django.yml`, so this doesn't fire on
   forks.

## Verification performed
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/demo-deploy.yml'))"` — passed, no exception.
- `actionlint` — not installed on this machine (`which actionlint` found nothing); skipped, YAML-syntax check above is the only validation performed.
- Did NOT run the workflow, dispatch it, create a Fly token, or touch the live `parkour-demo` app, per task instructions. Step 6 of the brief (manual first run) is explicitly left for the user, as it touches shared infra and requires their confirmation.

## Follow-up needed from the user (out of scope here)
- `FLY_API_TOKEN` GitHub Actions secret must still be created
  (`flyctl tokens create deploy -a parkour-demo`) before this workflow can run
  for real — flagged in the brief, not created here.
- Manual `workflow_dispatch` dry run (brief's Step 6) requires explicit
  confirmation before running, per this workspace's production-safety rules.

## Fix round (review: 2 Critical + 3 Important)

1. **Critical — `pg_dump`/server version mismatch**: added a step
   "Install postgresql-client-18 (PGDG apt repo)" before the dump step,
   mirroring `backend.Dockerfile`'s `pk2_base` apt.postgresql.org
   key/repo/install sequence (installs `postgresql-client-18` from PGDG
   since ubuntu-latest's own apt repo doesn't carry it), so the `pg_dump`
   client now matches the `postgres:18` service container.

2. **Critical — missing `--build-arg VITE_GOATCOUNTER_URL=...`**: restored
   `--build-arg VITE_GOATCOUNTER_URL=https://pk2demo.stats.omics.dev/count`
   on the `flyctl deploy` command, per the plan's Global Constraints ledger
   ruling (progress.md, "Global Constraints vs Task 4") requiring it passed
   directly to the build rather than relying solely on `fly.toml`'s
   `[build.args]`. Left `[build.args]` in `misc/fly.toml` as-is
   (redundant but harmless).

3. **Important — unpinned `superfly/flyctl-actions/setup-flyctl@master`**:
   resolved `master`'s current SHA
   (`git ls-remote https://github.com/superfly/flyctl-actions master` ->
   `ed8efb33836e8b2096c7fd3ba1c8afe303ebbff1`, which also matches tags
   `1.6`/`v1`) and pinned to
   `superfly/flyctl-actions/setup-flyctl@ed8efb33836e8b2096c7fd3ba1c8afe303ebbff1 # v1.6`,
   consistent with every other action pin in this workflow.

4. **Important — no check that the dump isn't empty**: appended
   `test -s backend/fixtures_snapshot.dump || (echo "::error::fixtures_snapshot.dump is empty" && exit 1)`
   to the dump step, failing the job immediately on a 0-byte/truncated dump
   instead of silently deploying an empty demo.

5. **Important — FK-ordering risk with `--data-only` + no
   `--disable-triggers`**: not fixed with `--disable-triggers` (needs
   superuser, likely unavailable on Neon). Instead added a comment above
   the dump step documenting the risk and the existing mitigation. Verified
   the mitigation claim against `backend/common/management/commands/reset_demo.py`:
   its `pg_restore` call uses `--data-only --single-transaction` (no
   `--disable-triggers`), and this project's models rely on Postgres's
   default `DEFERRABLE INITIALLY DEFERRED` FK constraint behavior, so FK
   checks are deferred to `COMMIT` time within that single transaction —
   this is the actual mitigation already in place, not a gap. Flagged in
   the comment that this should still be verified end-to-end during the
   plan's manual dry-run step (Testing section / brief Step 6).

### Re-verification
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/demo-deploy.yml'))"` — passed.
- Confirmed only `.github/workflows/demo-deploy.yml` (plus this report) changed in the fix commit; no dump file or other stray files added.
