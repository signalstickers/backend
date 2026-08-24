# AGENTS.md — signalstickers-back

Backend for signalstickers.org: a moderation tool where third parties propose Signal sticker packs via the API, reviewers approve/refuse/escalate via Django Admin, and approved packs are served to the public front-end.

## Package Manager

- Use **pipenv**: `pipenv install --dev` (or `make venv`)

## Commands

| Task                          | Command            |
| ----------------------------- | ------------------ |
| Test (enforces ≥70% coverage) | `pipenv run test`  |
| Lint (pylint + black + isort) | `pipenv run lint`  |
| Bandit security scan          | `pipenv run sec`   |
| All of the above              | `pipenv run check` |
| Auto-fix formatting           | `make fix`         |
| Any python command            | Use the venv       |

## External References

| Need                          | File                |
| ----------------------------- | ------------------- |
| Public API contract           | `doc/public_api.md` |
| Deploy configs (nginx/apache) | `deploy_scripts/`   |

## Architecture

- **`core/`** — all domain models, admin, services, management commands. `api/` migrations are state-only relocations; Django state lives in `core`.
- **`api/`** — API v1 (DRF), mounted at `/v1/`.
- **`api_v2/`** — half-baked, not ready. **Do not touch it.**
- **`signalstickers/signalstickers/`** — project package (settings, urls). `manage.py` selects settings via `ENV_TYPE` (`prod` → `settings.prod`, else `settings.dev`).
- No Celery/Redis/task queue. Periodic jobs are management commands driven by cron.

## Key Conventions

- Create packs with `Pack.objects.new()` (validates against Signal, creates tags). Never `Pack.objects.create()`.
- All domain models live in `core/models/`.
- Auth is minimal: raw `X-Auth-Token` header (no DRF auth classes) or a bot-prevention challenge.
- `remove_empty_values()` in `api/utils.py` strips `''/False/None/[]/{}` before serialization.
- Pack stats are a JSONField `{YYYY_MM: int}` on `Pack`, incremented by `/v1/ping/`.
- Tests patch `core.models.pack.get_pack_from_signal` (fakes in `signalstickers/tests_common.py`) to avoid real Signal calls.
- Don't run docker commands yourself (ask the user). Don't install pip packages unless asked.

## Settings

- `settings/dev.py` — `DEBUG=True`, Postgres `django/django@127.0.0.1:5432`, console email, `AI_REVIEW_API_KEY="api-key-for-dev"`.
- `settings/prod.py` — git-ignored; copy from `prod.py.dist`. Adds `CLOUDFLARE_CONF`, `EMAIL_FROM`, `NTFY_*`.
