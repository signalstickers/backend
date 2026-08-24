# AGENTS.md — signalstickers-back

## Overview

Backend for [signalstickers.org](https://signalstickers.org), a directory of Signal (messaging app) sticker packs. The app is a **moderation tool**: third parties propose packs via the API, reviewers (via Django Admin) approve/refuse/escalate them, and approved packs are served to the public front-end.

## Tech Stack

- **Python 3.11**, **Django 5.2**, **Django REST Framework 3.17**
- **PostgreSQL** (via `psycopg2-binary`)
- **Pillow** for image handling
- **signalstickers-client** — async client to fetch/validate packs from Signal's servers
- **httpx / anyio** — async HTTP (pack fetching, ntfy notifications)
- **ntfy** — push notifications to reviewers (fire-and-forget via `ThreadPoolExecutor`)
- No Celery, no Redis, no task queue. Periodic jobs are management commands driven by cron.

## Directory Structure

```
signalstickers-back/
├── Makefile                  # venv / lint / sec / test / check / fix
├── Pipfile / requirements.txt
├── docker-compose.yml        # postgres (5432) + adminer (9988)
├── deploy_scripts/           # nginx + apache deploy configs
├── doc/public_api.md         # public API documentation
└── signalstickers/           # Django project root
    ├── manage.py             # selects settings by ENV_TYPE; enforces ≥70% coverage on test
    ├── manage.py
    ├── signalstickers/       # project package
    │   ├── settings/
    │   │   ├── common.py     # shared settings (apps, middleware, templates)
    │   │   ├── dev.py        # DEBUG=True, Postgres @ 127.0.0.1:5432, console email
    │   │   └── prod.py       # git-ignored; copy from prod.py.dist
    │   ├── urls.py           # root URLconf
    │   ├── wsgi.py / asgi.py
    │   └── tests_common.py   # TestPack / TestSticker fakes (patch get_pack_from_signal)
    ├── core/                 # domain models, admin, services, commands
    │   ├── models/           # all domain models (see below)
    │   ├── admin/            # ModelAdmins (PackAdmin is the main moderation UI)
    │   ├── adminsite.py      # CustomAdmin: extra views (stats, trigger_actions)
    │   ├── services.py       # business logic (bot-check, CDN, email, ntfy)
    │   ├── utils.py          # Signal client wrapper, animation detection, date helpers
    │   ├── notifications.py  # ntfy fire-and-forget via ThreadPoolExecutor
    │   ├── context_processors.py  # admin_navbar: pending counts for admin templates
    │   ├── feeds/            # RSS + Atom feeds of new packs
    │   ├── management/commands/   # 7 management commands (see below)
    │   ├── migrations/       # 0001–0012
    │   ├── templates/admin/  # admin templates (stats, pack change form, AI review)
    │   └── tests.py
    └── api/                  # API v1 (DRF) — the public API
        ├── views/            # 8 class-based views
        ├── serializers/      # 8 DRF serializers
        ├── urls.py           # mounted at /v1/
        ├── utils.py          # remove_empty_values()
        ├── migrations/       # 0001–0004 (state-only relocations to core)
        └── tests.py
```

## Models (all in `core/models/`)

| Model                       | DB Table                 | Purpose                                                                                                                                                                                                                                                                                                                   |
| --------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`Pack`**                  | `packs`                  | Core entity. `pack_id` (32-char lowercase alnum, unique), `pack_key` (64-char), `title`, `author`, `id_cover`, `source`, `nsfw`, `original`, `editorschoice`, `tags` (M2M→Tag), `animated`/`animated_detected`/`animated_mode`, `stats` (JSONField `{YYYY_MM: views}`), `status`, `status_comments`, `submitter_comments` |
| **`Tag`**                   | `tags`                   | `name` (unique, lowercased on save)                                                                                                                                                                                                                                                                                       |
| **`Report`**                | `reports`                | User report on a pack. FK→Pack (PROTECT), `content`, `status` (TO_PROCESS/AGREED/DISAGREED)                                                                                                                                                                                                                               |
| **`ApiKey`**                | `apikeys`                | `key` (UUID PK), `name`. Authenticates third-party contribution clients via `X-Auth-Token`                                                                                                                                                                                                                                |
| **`ContributionRequest`**   | `contributionrequests`   | Bot-prevention challenge. UUID PK, `client_ip`, FK→BotPreventionQuestion, `request_date`. Expires after 1h (cleanup at 2h)                                                                                                                                                                                                |
| **`BotPreventionQuestion`** | `botpreventionquestions` | `question`, `answer` (alphanumeric-validated)                                                                                                                                                                                                                                                                             |
| **`AIReview`**              | `ai_reviews`             | OneToOne→Pack. `status` (ACCEPT/REFUSE), `review_comment`, `tags_match`, `nsfw`, `confidence` (0–1), `alert`                                                                                                                                                                                                              |
| **`SiteStat`**              | `sitestats`              | `month` (YYYY_MM), `visits`                                                                                                                                                                                                                                                                                               |
| **`AdminPermissions`**      | — (managed=False)        | Custom permissions: `view_stats_page`, `invalidate_cloudflare`                                                                                                                                                                                                                                                            |
| **`AdminAction`**           | — (managed=False)        | `caches_dirty()` helper for Cloudflare cache staleness                                                                                                                                                                                                                                                                    |

### Enums

- **`PackStatus`**: `ONLINE`, `IN_REVIEW`, `REFUSED`, `ESCALATED`
- **`PackAnimatedMode`**: `AUTO`, `FORCE_ANIMATED`, `FORCE_STILL`
- **`ReportStatus`**: `TO_PROCESS`, `AGREED`, `DISAGREED`
- **`AIReviewStatus`**: `ACCEPT`, `REFUSE`

### PackManager (custom manager on `Pack`)

Key query methods: `onlines()`, `in_review()`, `in_review_with_tags()`, `escalated()`, `most_popular_for_month(month, nbr)`, `most_viewed_packs(nbr)`, `total_packviews()`, `total_packviews_for_month(month)`.

**`PackManager.new()`** is the canonical factory: validates pack_id/pack_key format, fetches the pack from Signal (via `get_pack_from_signal`), computes title/author/cover/animation, creates tags atomically. Always use `new()` instead of `create()`.

### Pack lifecycle

```
new pack (API or admin) → IN_REVIEW → approve() → ONLINE
                                         → refuse()  → REFUSED
                                         → escalate  → ESCALATED
```

`Pack.clean()` is called by `new()` and validates against Signal's servers.

## API v1 Endpoints (DRF, mounted at `/v1/`)

| URL                        | Method | View                      | Auth                                         | Purpose                                                                                                                                                                                    |
| -------------------------- | ------ | ------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/v1/packs/`               | GET    | `PacksView`               | none                                         | List all ONLINE packs (newest first). Response: `{meta, manifest}`. Furry packs expose only the `furry` tag                                                                                |
| `/v1/ping/`                | POST   | `StatsPingView`           | none                                         | Increment visit stats. `target=home` → SiteStat; `target=<pack_id>` → pack `stats[YYYY_MM]`. Form-encoded                                                                                  |
| `/v1/packs/status/`        | POST   | `StatusView`              | none                                         | Look up pack by `pack_id`+`pack_key`, return status + refusal comments. 404 if unknown                                                                                                     |
| `/v1/report/`              | PUT    | `ReportView`              | bot-check                                    | Create a `Report`. Requires valid `contribution_id`/`contribution_answer`. Sends HIGH-priority ntfy                                                                                        |
| `/v1/contribute/`          | PUT    | `ContributionView`        | API key **or** bot-check                     | Propose a new pack (→ IN_REVIEW). With `X-Auth-Token` (validated against `ApiKey`): appends `(via <name>)` to source. Without: requires valid contribution request. Sends email + LOW ntfy |
| `/v1/admin/toreview/`      | GET    | `InReviewPacksView`       | `X-Auth-Token == settings.AI_REVIEW_API_KEY` | List IN_REVIEW packs. Optional `?only_noaireview` filters to packs without AIReview                                                                                                        |
| `/v1/admin/aireview/`      | PUT    | `AIReviewView`            | `X-Auth-Token == settings.AI_REVIEW_API_KEY` | Upsert an `AIReview` for a pack                                                                                                                                                            |
| `/v1/contributionrequest/` | POST   | `ContributionRequestView` | none                                         | Create a bot-prevention challenge. Returns `contribution_id` + `contribution_question`                                                                                                     |

Ignore API v2 for now. It's half-baked, and not ready. Completely ignore it.

### Auth pattern

No DRF auth classes or JWT. Two mechanisms:

1. **`X-Auth-Token` header** checked against the `ApiKey` table (for `/v1/contribute/`) or against the static `settings.AI_REVIEW_API_KEY` (for admin endpoints)
2. **Bot-prevention challenge**: client POSTs to `/v1/contributionrequest/` to get a question, then submits the answer with the contribution/report

### Bot-prevention flow

1. Client → `POST /v1/contributionrequest/` → gets `contribution_id` + `contribution_question`
2. Client → `PUT /v1/contribute/` or `PUT /v1/report/` with `contribution_id` + `contribution_answer`
3. Server validates: CR exists, matches client IP, <1h old, answer matches (alphanumeric-normalized). Deletes CR on success.

## Services (`core/services.py`)

- `new_contribution_request(client_ip)` — create a CR with a random question
- `check_contribution_request(id, answer, ip)` — validate CR (exists, IP match, <1h, answer match); deletes on success
- `check_api_key(key)` — look up `ApiKey` by UUID
- `clear_contribution_requests()` — delete expired CRs (>2h)
- `invalidate_cdn()` — POST to Cloudflare purge_cache API
- `send_email_on_pack_propose(pack)` — email users in group `email_notification_on_propose`

## Utilities (`core/utils.py`)

- `get_pack_from_signal(pack_id, pack_key)` — sync wrapper around async `signalstickers_client.StickersClient` via `anyio`
- `detect_animated_pack(pack)` — byte-magic detection of APNG/GIF/animated-WebP; rejects animated WebP
- `get_current_ym_date()` / `get_last_month_ym_date()` — return `YYYY_MM` strings
- `is_url(value)` — URL validation

## Notifications (`core/notifications.py`)

`notify(topic, message, priority)` — fire-and-forget ntfy HTTP POST via a bounded `ThreadPoolExecutor` (8 workers). No-op if `NTFY_SERVER_URL` is empty. `NotificationPriority` enum: `LOW`, `HIGH`.
2 ntfy topics: 'signalstickers-admin' for administration-related stuff, and 'signalstickers-packs' for pack-related stuff.

## Admin Site

Custom `CustomAdmin` site (`core/adminsite.py`) with extra views:

- `admin/trigger_actions/` — POST `action=cloudflareclear` to invalidate Cloudflare CDN (requires `core.invalidate_cloudflare` perm)
- `admin/stats/` — analytics dashboard: visits by month, most popular packs, most-viewed all-time (requires `core.view_stats_page`)
- Successful admin login fires `notify()` (ntfy to `signalstickers-admin`)

`PackAdmin` is the main moderation UI with:

- Bulk review session workflow (approve/refuse/escalate + "continue to next pack")
- Escalating a pack fires `notify()` directly (immediate HIGH ntfy), only on the transition to ESCALATED
- AI-review hint fields
- Read-only computed fields
- Non-superusers cannot edit `pack_id`/`pack_key`

Other ModelAdmins: `AIReviewAdmin`, `ApiKeyAdmin`, `BotPreventionQuestionAdmin`, `ContributionRequestAdmin` (read-only), `LogEntryAdmin` (custom, read-only), `ReportAdmin`, `TagAdmin`.

## Management Commands (`core/management/commands/`)

| Command                       | Purpose                                                                                       |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| `import_from_yml`             | Import packs from legacy Signal stickers YAML format (validates via Signal, skips duplicates) |
| `clean_packs_tags`            | Split malformed `#a #b` tags into separate tags                                               |
| `clear_contribution_requests` | Delete expired CRs (cron)                                                                     |
| `export_packs_img`            | Export all sticker images to `/tmp/export_sst/`                                               |
| `import_stats_from_logfile`   | Import pack/site stats from Apache access log (destructive, requires confirmation)            |
| `invalidate_cloudflare`       | Purge Cloudflare cache                                                                        |

## Feeds

- `/feed/rss/` — RSS feed of last 10 ONLINE packs
- `/feed/atom/` — Atom feed of last 10 ONLINE packs

## Settings

- `settings/common.py` — shared: apps, middleware, templates, i18n, static
- `settings/dev.py` — `DEBUG=True`, `CORS_ALLOW_ALL_ORIGINS=True`, Postgres `django/django@127.0.0.1:5432`, console email, `AI_REVIEW_API_KEY="api-key-for-dev"`, `HEADER_IP="REMOTE_ADDR"`
- `settings/prod.py` — git-ignored. Adds `CLOUDFLARE_CONF`, `EMAIL_FROM`, `NTFY_SERVER_URL`/`NTFY_AUTH_TOKEN`, proxy `HEADER_IP`

`manage.py` selects settings by `ENV_TYPE` env var: `prod` → `settings.prod`, otherwise `settings.dev`.

## Development

- Run tests: `pipenv run test`
- Run lint: `pipenv run lint`
- Run bandit: `pipenv run sec`

Don't use docker yourself (ask the user). Don't install pip packages unless asked.

## Testing

- `api/tests.py` — DRF API tests: contribution flow, pack listing, bot-prevention, status, ping, in-review, AI review
- `core/tests.py` — model tests (Pack creation/validation/animation), utils (animated detection), management commands, AI review, notifications
- `signalstickers/tests_common.py` — `TestPack`/`TestSticker` fakes. Tests patch `core.models.pack.get_pack_from_signal` to avoid real Signal calls
- Coverage is **enforced at ≥70%** by `manage.py` during `test` (use 'pipenv run test')

## Key Conventions

- **All domain models live in `core`**. The `api` app's migrations (0001–0004) are `SeparateDatabaseAndState` relocations — the tables exist but Django state is in `core`
- **Use `Pack.objects.new()`** to create packs (validates against Signal, creates tags). Never use `Pack.objects.create()` directly
- **No background-job framework** — periodic tasks are management commands for cron
- **Auth is minimal** — raw `X-Auth-Token` header, no DRF auth classes
- **`remove_empty_values()`** in `api/utils.py` recursively strips `''/False/None/[]/{}` from dicts/lists before serialization
- **Pack stats** are stored as a JSONField `{YYYY_MM: int}` on the Pack model; `stats[YYYY_MM]` is incremented by `/v1/ping/`
