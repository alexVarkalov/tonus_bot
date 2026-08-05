# tonus-bot

Personal single-user Telegram bot for tracking daily mood and productivity, with optional
Gadgetbridge sleep/steps enrichment and a weekly Claude-generated analysis.

Architecture and conventions are documented in [`CLAUDE.md`](./CLAUDE.md).

## Commands

- `/checkin` — rate today's (or, in the early-morning window, yesterday's) mood and productivity
  1-7, with an optional note.
- `/stats` — last 7 days, with mood/productivity trend arrows vs. the previous 7 days.
- `/week` — averages for the current calendar week.
- `/settings` — view or change reminder hour, timezone, and whether reminders are on.
  - `/settings hour <0-23>`
  - `/settings timezone <IANA timezone>`
  - `/settings reminders on|off`

Every hour the bot checks whether it's the configured reminder hour and there's no check-in yet
for today; if so, it sends one reminder. Every Sunday evening it pulls the last two weeks of
check-ins and asks Claude for a short pattern analysis.

## Environment variables

See [`.env.example`](./.env.example) for the full list with comments:

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | yes | Token from @BotFather |
| `ALLOWED_USER_ID` | yes | Telegram `user_id` of the single allowed user |
| `DATABASE_URL` | yes | `postgresql+psycopg://user:password@host:5432/tonus` |
| `ANTHROPIC_API_KEY` | yes | Used only for the weekly analysis job |
| `GADGETBRIDGE_DB_PATH` | no | Path to Gadgetbridge's SQLite export; omit to skip enrichment |
| `DEFAULT_TIMEZONE` | no | Default IANA timezone for a new settings row (default `Europe/Warsaw`) |
| `CHECKIN_REMINDER_HOUR` | no | Default reminder hour, 0-23 (default `21`) |

## Local run

```bash
uv sync --extra dev
cp .env.example .env   # fill in BOT_TOKEN, ALLOWED_USER_ID, DATABASE_URL, ANTHROPIC_API_KEY

# CREATE DATABASE tonus; on your Postgres instance first, then:
uv run tonus-bot
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run pre-commit install   # runs ruff + pytest on every commit
```

## Deployment on Raspberry Pi

Runs as its own systemd unit, independent from any other bot on the same Pi:

```bash
git clone <this repo> tonus-bot && cd tonus-bot
uv venv .venv --python 3.14
uv sync --frozen
cp .env.example .env   # fill in real values
```

`/etc/systemd/system/tonus-bot.service`:

```ini
[Unit]
Description=tonus-bot
After=postgresql.service network-online.target
Wants=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/tonus-bot
EnvironmentFile=/home/pi/tonus-bot/.env
ExecStart=/home/pi/tonus-bot/.venv/bin/tonus-bot
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Run as an unprivileged user (`User=`), not root.

On the existing PostgreSQL instance, create a separate database and role — don't reuse another
bot's role:

```sql
CREATE DATABASE tonus;
CREATE ROLE tonus_bot WITH LOGIN PASSWORD '...';
GRANT ALL PRIVILEGES ON DATABASE tonus TO tonus_bot;
```

Logs: `journalctl -u tonus-bot -f`

Update flow: `git pull && uv sync --frozen && systemctl restart tonus-bot`
