# SNKRSMonitor
Lightweight Nike SNKRS monitor that polls the Nike product feed, tracks changes to product details and per-size stock levels, and sends real-time Discord webhook notifications.

## How it works

Each polling interval the monitor:
1. Fetches products from Nike's `product_feed/threads/v3` API using configurable filters
2. Upserts products and SKUs into a local SQLite database — rows are only updated when data actually changes
3. For any product or SKU that changed this cycle, sends (or edits) a Discord embed with full product details and stock levels

Discord message IDs are persisted in the database so subsequent changes edit the existing message rather than posting a new one.

## Setup

Requires Python 3.13+ and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
cp .env.example .env  # then fill in your values
uv run main.py
```

## Configuration

All configuration is via a `.env` file:

| Variable | Description |
|---|---|
| `COUNTRY_CODE` | Nike marketplace country code (e.g. `US`) |
| `LANGUAGE` | Language code (e.g. `en`) |
| `CHANNEL_ID` | Nike channel ID (e.g. `010794e5-35fe-4e32-aaff-cd2c74f89d61` for SNKRS) |
| `UPCOMING` | Include upcoming releases (`true`/`false`) |
| `EXCLUSIVE_ACCESS` | Include exclusive access products (`true`/`false`) |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications |
| `POLLING_INTERVAL_SECONDS` | Seconds between each poll |
| `DB_PATH` | Path to the SQLite database file (e.g. `snkrs.db`) |

## Discord embed

Each product notification includes:
- Price, release date (Discord timestamp), and style/color SKU
- Status, release method, cart limit, and exclusive access flag
- Per-size stock levels (HIGH / MEDIUM / LOW / OOS) across two columns
- Quick links to StockX, GOAT, and eBay searches for the SKU

## Logs

- `INFO` and above → stdout
- `WARNING` and above → `app.log`
