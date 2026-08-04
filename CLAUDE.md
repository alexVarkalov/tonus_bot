# CLAUDE.md — tonus-bot

Personal single-user Telegram bot for tracking mood and productivity.
Architecture and conventions inherited from language-assistant (Cursor guide), adapted for Claude Code and for single-user scale.

Place this file at the root of the `tonus-bot/` repository. Claude Code picks it up automatically at the start of a session.

---

## Differences from language-assistant (reference bot)

- **No `i18n.py`** — single user, single language (English). Strings live in `strings.py`, flat constants, no locale keys.
- **No access-control layer** — instead of `is_allowed` / `ADMIN_USER_IDS`, a single `ALLOWED_USER_ID` in config; handlers silently ignore updates from any other `user_id`.
- **No streaks or penalties for missed check-ins** — the scheduler checks for a missing check-in and sends one reminder, nothing more.
- Everything else — layout, layers, ORM patterns, testing, deployment — follows the reference 1:1.

---

## Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.14+ |
| Package manager | uv (`uv sync`, `uv run`, lockfile committed) |
| Bot framework | python-telegram-bot v22+, `job-queue` extra |
| HTTP client | httpx, single `AsyncClient` in `bot_data`, closed in `post_shutdown` |
| Database | PostgreSQL + SQLAlchemy ORM, sync engine wrapped with `asyncio.to_thread` |
| DB driver | `psycopg` (not `psycopg[binary]` — required for ARM/Raspberry Pi) |
| Lint/format | Ruff: `E`, `F`, `I`, `B`, `UP`, line-length 120 |
| Tests | pytest + pytest-asyncio |
| Hooks | pre-commit: ruff check --fix, ruff format, pytest |
| LLM | Anthropic SDK, `claude-sonnet-4-6`, weekly analysis only |

Database — the existing PostgreSQL instance on the Pi (already running), a separate `tonus` database within that instance, separate role. Do not share tables with the vocabulary bot.

---

## Project layout

```
tonus-bot/
├── CLAUDE.md
├── pyproject.toml
├── uv.lock
├── .env
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
├── tonus_bot/
│   ├── __init__.py
│   ├── __main__.py          # entry point: dotenv, logging, Application bootstrap
│   ├── config.py            # frozen Settings dataclass from env
│   ├── db.py                # Database facade, mixes in store classes
│   ├── strings.py           # flat English strings, no i18n
│   ├── handlers/
│   │   ├── __init__.py      # register_handlers()
│   │   ├── common.py        # access guard, formatting helpers
│   │   ├── checkin.py       # /checkin conversation
│   │   ├── stats.py         # /stats, /week
│   │   └── settings.py      # /settings
│   ├── services/
│   │   ├── __init__.py
│   │   ├── checkin_service.py    # validation, resolving which date a check-in belongs to
│   │   ├── analysis_service.py   # Claude API, weekly analysis
│   │   ├── trends.py             # pure logic: averages, trend arrows
│   │   ├── gadgetbridge.py       # read-only access to sleep/steps
│   │   └── reminder_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── checkin_repository.py
│   │   ├── insight_repository.py
│   │   └── settings_repository.py
│   └── persistence/
│       ├── __init__.py
│       ├── models.py        # CheckinRecord, WeeklyInsightRecord, UserSettingsRecord
│       ├── types.py         # Checkin, WeeklyInsight, UserSettings (frozen dataclass)
│       ├── utils.py         # to_checkin(), utc_now()
│       ├── checkin_store.py
│       ├── insight_store.py
│       └── settings_store.py
└── tests/
    ├── helpers.py
    ├── persistence/fakes.py
    ├── handlers/
    ├── services/
    └── repositories/
```

### Naming

- Package: `tonus_bot`.
- CLI script: `tonus-bot` → `tonus_bot.__main__:main`.
- ORM: `CheckinRecord`, `WeeklyInsightRecord`, `UserSettingsRecord` — `Record` suffix.
- Domain: `Checkin`, `WeeklyInsight`, `UserSettings` — frozen dataclasses in `persistence/types.py`.
- Stores: `CheckinStore`, `InsightStore`, `SettingsStore` — mixins with `_sync` helpers.
- Repositories: `CheckinRepository` — domain-oriented methods (`save_checkin`, `get_week`), not SQL-oriented.
- Services: `CheckinService`, `AnalysisService` — validation and orchestration, no `telegram` imports.
- Handlers: `cmd_checkin`, `on_mood_callback`, `on_productivity_callback` — thin, delegate to services.

---

## Architecture rules

4 layers, dependencies flow downward only:

```
handlers  →  services  →  repositories  →  persistence (stores + ORM)
                ↓
          config, strings, external APIs (analysis_service.py, gadgetbridge.py)
```

### Handlers

- Early-return on missing `effective_user` / `effective_message` / `callback_query`.
- Check `update.effective_user.id == settings.allowed_user_id` at the top of every handler — on mismatch, just `return`, no reply (so the bot doesn't confirm its own existence to strangers).
- Strings only from `strings.py`, never hardcoded in handlers.
- No business logic or SQL in handlers — call services instead.
- Register all handlers centrally in `handlers/__init__.py::register_handlers()`.

### Services

- Business logic: validating the 1-7 range, resolving "which day is being rated" accounting for timezone and the midnight boundary, assembling the JSON payload for the Claude API.
- Receive repositories and `Settings` via constructor.
- Invalid input → `ValueError`; the handler translates it into a user-facing message.
- **No** `telegram` imports.
- No `settings_service` — `/settings`'s only logic is trivial validation (IANA timezone via `ZoneInfo`, hour clamped 0-23), so `handlers/settings.py` calls `SettingsRepository` directly. Same level of triviality as `cmd_languages` validating language codes inline in the reference bot.

### Repositories

- Thin async facades over `Database`.
- One repository per aggregate: check-ins, insights, settings.

### Persistence

- `models.py` — `DeclarativeBase`, tables, `UniqueConstraint(user_id, date)` on `checkins`.
- `types.py` — frozen dataclasses.
- Store mixins: sync logic in `_method_sync`, public `async def` wraps it with `asyncio.to_thread`.
- `db.py::init()` — `create_all()` + additive migrations (`ADD COLUMN IF NOT EXISTS`); Alembic is unnecessary at this scale.

---

## Database schema

```sql
CREATE TABLE checkins (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    date DATE NOT NULL,
    mood SMALLINT NOT NULL CHECK (mood BETWEEN 1 AND 7),
    productivity SMALLINT NOT NULL CHECK (productivity BETWEEN 1 AND 7),
    note TEXT,
    tags JSONB,
    sleep_hours REAL,
    steps INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, date)
);

CREATE TABLE weekly_insights (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    week_start DATE NOT NULL,
    insight_text TEXT NOT NULL,
    raw_stats JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_settings (
    user_id BIGINT PRIMARY KEY,
    checkin_hour SMALLINT NOT NULL DEFAULT 21,
    timezone TEXT NOT NULL DEFAULT 'Europe/Warsaw',
    reminders_enabled BOOLEAN NOT NULL DEFAULT true
);
```

A repeat `/checkin` for an existing date is `ON CONFLICT (user_id, date) DO UPDATE`, not an error.

---

## Configuration (config.py)

```python
@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    anthropic_api_key: str
    allowed_user_id: int
    gadgetbridge_db_path: str | None
    default_timezone: str
    checkin_reminder_hour: int

    @classmethod
    def from_env(cls) -> Settings:
        token = os.environ.get("BOT_TOKEN", "").strip()
        if not token:
            raise ValueError("BOT_TOKEN is required")
        allowed_user_id_raw = os.environ.get("ALLOWED_USER_ID", "").strip()
        if not allowed_user_id_raw:
            raise ValueError("ALLOWED_USER_ID is required")
        # database_url, anthropic_api_key — same pattern, ValueError if empty
        return cls(
            bot_token=token,
            database_url=os.environ["DATABASE_URL"],
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
            allowed_user_id=int(allowed_user_id_raw),
            gadgetbridge_db_path=os.environ.get("GADGETBRIDGE_DB_PATH") or None,
            default_timezone=os.environ.get("DEFAULT_TIMEZONE", "Europe/Warsaw"),
            checkin_reminder_hour=max(0, min(23, int(os.environ.get("CHECKIN_REMINDER_HOUR", "21")))),
        )
```

`.env` is loaded by a minimal inline loader in `__main__.py`, as in the reference — no `python-dotenv`, does not override already-set `os.environ` values.

---

## Bootstrap (`__main__.py`)

1. `_load_dotenv_if_present()`
2. `logging.basicConfig(...)`, `httpx` → WARNING
3. `Settings.from_env()`, exit code 2 on `ValueError`
4. Build `Application` with `.post_init()` / `.post_shutdown()`
5. In `bot_data`: `settings`, `db`, `http_client`, `settings_repository`, `anthropic_client`, `checkin_service`, `analysis_service`
6. `register_handlers(application)`
7. `application.run_polling(allowed_updates=Update.ALL_TYPES)`

### post_init

```python
async def _post_init(application: Application) -> None:
    db = application.bot_data["db"]
    await db.init()
    application.bot_data["http_client"] = httpx.AsyncClient()
    application.job_queue.scheduler.configure(timezone="UTC")

    settings = application.bot_data["settings"]
    checkin_repo = CheckinRepository(db)
    insight_repo = InsightRepository(db)
    application.bot_data["settings_repository"] = SettingsRepository(db)
    application.bot_data["anthropic_client"] = AsyncAnthropic(api_key=settings.anthropic_api_key)
    application.bot_data["checkin_service"] = CheckinService(checkin_repo)
    application.bot_data["analysis_service"] = AnalysisService(
        settings, application.bot_data["anthropic_client"], checkin_repo, insight_repo
    )

    application.job_queue.run_repeating(reminder_job, interval=3600, first=10, name="checkin_reminder")
    application.job_queue.run_repeating(
        weekly_analysis_job,
        interval=604800,
        first=_seconds_until_sunday_evening(settings.default_timezone),
        name="weekly_analysis",
    )
```

`reminder_job` lives in `handlers/checkin.py` and `weekly_analysis_job` in `handlers/stats.py` — both imported into `__main__.py` via `from tonus_bot.handlers import register_handlers, reminder_job, weekly_analysis_job`, the same pattern the reference bot uses for `due_poll`. `_seconds_until_sunday_evening(timezone)` computes seconds until the next Sunday 20:00 in that timezone.

No standalone `apscheduler` dependency needed — PTB's `job-queue` extra pulls it in itself, accessed via `application.job_queue`.

---

## Scheduler and day boundaries

- Hourly `reminder_job`: if the current local hour for the user equals `checkin_hour` and there's no check-in for today — send one reminder, don't repeat until the next day.
- `checkin_service` resolves the "check-in date" from the user's local time, not server UTC: if it's currently between 00:00 and, say, 04:00 local time — default to offering yesterday's date, with a button to switch to today.
- `weekly_analysis_job` — Sunday evening in local time, pulls 14 days, calls `analysis_service`.

---

## Gadgetbridge (services/gadgetbridge.py)

A separate SQLite database (not Postgres), read-only, path from `GADGETBRIDGE_DB_PATH`. Table schema depends on the app version — before implementing, open the actual database (`sqlite3 <path> ".schema"`) and check against it; don't rely on the schema described in the Gadgetbridge project's README, it lags behind. If the file is unavailable — `sleep_hours`/`steps` stay `None`, the check-in still saves. This is optional enrichment, not a blocking dependency, so it should not be a required constructor argument on `CheckinService` — call it optionally after the check-in is saved.

The current implementation guesses at common table/column names (`MI_BAND_ACTIVITY_SAMPLE`, `RAW_KIND`, `STEPS`, ...) because no real export was available to inspect during initial scaffolding. Verify it against your actual `GADGETBRIDGE_DB_PATH` file before trusting it, and adjust `_CANDIDATE_TABLES`/`_SLEEP_KINDS` in `gadgetbridge.py` to match — it fails safe (returns no enrichment) if the schema doesn't match, so nothing breaks in the meantime.

---

## External APIs (services/analysis_service.py)

- Anthropic SDK, key from `Settings`, not read directly from `os.environ`.
- A single `AsyncAnthropic` client, passed in as a parameter, not created per call.
- System prompt: patterns only, tied to concrete numbers, 3-5 sentences, no generic advice.
- API errors → `ValueError` with a clear message; the handler decides what to show the user.

---

## Testing

| Layer | Approach |
|-------|----------|
| `config.py` | `monkeypatch.setenv/delenv`, test validation and defaults |
| `persistence/*Store` | `FakeSession` + `FakeSessionFactory`, test `_sync` methods directly |
| `repositories/` | mock `Database` |
| `services/` | mock repositories; `trends.py` and check-in date resolution are pure unit tests, no mocks |
| `handlers/` | `AsyncMock` for services, `SimpleNamespace` instead of `Update`/`Context` |

Test names: `test_<function>_<scenario>`. Test files mirror the source layout.

When a mocked service mixes sync and async methods (e.g. `CheckinService.resolve_checkin_date` and `validate_rating` are sync, `save_checkin` is async), construct the mock as `AsyncMock(spec=CheckinService)` — a plain `AsyncMock()` makes every attribute async, so the sync calls return unawaited coroutines instead of values.

### pre-commit

```yaml
- ruff-check (--fix)
- ruff-format
- pytest (always_run: true, uv run --extra dev pytest)
```

---

## pyproject.toml

```toml
[project]
name = "tonus-bot"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "python-telegram-bot[job-queue]>=22.0,<23",
    "httpx>=0.27,<1",
    "sqlalchemy",
    "psycopg",
    "anthropic",
]

[project.optional-dependencies]
dev = ["pre-commit", "pytest", "pytest-asyncio", "ruff"]

[project.scripts]
tonus-bot = "tonus_bot.__main__:main"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py314"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

---

## Deployment on Raspberry Pi

- Separate systemd unit from the vocabulary bot: `tonus-bot.service`, `EnvironmentFile=.env`, `Restart=always`, `After=postgresql.service`.
- Separate venv: `uv venv .venv --python 3.14 && uv sync --frozen`.
- Separate role and database on the existing PostgreSQL instance: `CREATE DATABASE tonus; CREATE ROLE tonus_bot ...` — don't reuse the vocabulary bot's role.
- Logs: `journalctl -u tonus-bot -f`.
- Update flow: `git pull && uv sync --frozen && systemctl restart tonus-bot`.

---

## Rules for Claude Code working in this repo

1. Minimal diff, don't touch unrelated code.
2. Build order for a new feature: persistence → repository → service → handler.
3. Never import `telegram` in `services/` or `persistence/`.
4. Never put SQL in `handlers/` or `services/`.
5. Don't commit unless explicitly asked; never commit `.env`.
6. Don't add abstractions for hypothetical multi-user support — this bot is single-user by deliberate design, not an oversight to be fixed later.
7. Comments only for non-obvious business rules (e.g. the midnight-boundary logic for resolving a check-in's date).

---

## Project start checklist

- [ ] Scaffold from the layout above
- [ ] `pyproject.toml` + `uv lock` + dev extras
- [ ] `Settings.from_env()` with validation of required vars
- [ ] Inline `.env` loader in `__main__.py`
- [ ] `Database` + `CheckinStore` (upsert on `user_id, date`)
- [ ] `register_handlers()` with `/checkin` and the `ALLOWED_USER_ID` access guard
- [ ] `strings.py`
- [ ] `.gitignore`, `.pre-commit-config.yaml`
- [ ] `tests/helpers.py`, `tests/persistence/fakes.py`
- [ ] `README.md`: env vars, local run, deploy steps
- [ ] `CREATE DATABASE tonus` + separate role on the Pi

---

## Anti-patterns

| Don't | Do instead |
|-------|------------|
| Global `Database()` singleton | Inject via `application.bot_data` |
| Raw SQL in handlers | Repository → store |
| `python-dotenv` for one file | Inline loader in `__main__.py` |
| `psycopg[binary]` on ARM Pi | Plain `psycopg` |
| i18n layer for a single language | `strings.py` |
| Access-control layer for a single user | `ALLOWED_USER_ID` in config |
| Async SQLAlchemy | Sync ORM + `asyncio.to_thread` |
| Standalone `apscheduler` dependency | PTB's `job-queue` extra |
| Streaks / penalties for missed check-ins | One reminder, no pressure |
