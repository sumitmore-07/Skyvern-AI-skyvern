# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal learning/portfolio project that **uses Skyvern as a pip dependency** (LLM + vision browser automation). It is NOT a fork or clone of upstream Skyvern: never copy upstream source in, and never modify Skyvern's own repo. Despite the repo name, it holds only the owner's own scripts.

## Use case

Competitor price comparison, aimed at non-technical business owners. Skyvern reads prices and stock for a product list from several shops with different page layouts, one generic prompt, no per-site code. Results are validated, then rendered as an HTML report (cheapest available shop per product, out-of-stock ignored, suspect prices flagged as unverified). No flight search/booking, and no logins or payments, ever.

Targets are three self-written static shops in `demo_shops/` (table, card and list layouts, same 6 products, some out of stock), served automatically on ports 9001-9003 by `run_task.py`. Ground-truth prices are in the HTML, so accuracy can be checked. Real sites are an optional later stretch (books.toscrape.com and scrapeme.live allow scraping; webscraper.io/test-sites disallows product-detail pages in robots.txt).

## Commands

Run from the repo root with `venv\Scripts\python.exe` (or the activated venv):
- `python run_task.py compare` — full run: 3 shops, 3 Gemini calls, opens a visible Chromium window, writes `output/price_report_<timestamp>.html`
- `python -m pytest -q` — logic tests only (no LLM calls); single test: `python -m pytest tests/test_compare.py::test_outlier_price_is_flagged`
- `pip install -r requirements.txt` then `playwright install chromium` (one-time setup)

## Architecture

`run_task.py` starts the demo shop servers, starts Skyvern in-process (`Skyvern.local(use_in_memory_db=True)`: no Skyvern server, no Skyvern API key, no Postgres, no `skyvern quickstart`), launches one local browser and loops over `data/sites.yaml`. For each shop, `tasks/price_lookup.py` does `page.goto(url)` then `page.extract(prompt, schema)` and turns the output into `PriceResult` rows (`schemas.py`); a shop that errors becomes `failed` rows instead of aborting. `compare.py` (pure Python, no Skyvern imports) marks suspect rows `unverified` (missing price/currency/stock, or a price more than 3x away from the median across shops) and picks the cheapest verified in-stock offer. `report.py` + `templates/report.html` render the HTML. Inputs are `data/products.yaml` and `data/sites.yaml`; adding a shop means editing YAML.

Non-obvious constraints:
- `config.py` must be imported before `skyvern`: Skyvern reads settings at import time, so `.env` is loaded (and `ALLOWED_HOSTS='["localhost"]'` set) there first.
- Use `page.extract`, not `run_task`, for reading data. In testing, `run_task` (agent loop) completed in one step with `output=None` on a read-only page, and took ~45s per step; `extract` returned correct data in ~7s.
- Skyvern blocks `localhost` by default (SSRF guard: "The host in your url is blocked"); the `ALLOWED_HOSTS` env var is what lets the demo shops work. Passing it via `Skyvern.local(settings=...)` only worked for `run_task`, not for the `extract`/`goto` path.
- Runs are sequential on purpose (free-tier rate limits).

## Environment

- Windows 11; PowerShell/Git Bash. Local venv is `venv/` (gitignored), Python 3.12.2. Skyvern 1.0.48 requires Python `>=3.11,<3.14`; 3.14 is unsupported and 3.11 is not installed on this machine.
- `requirements.txt` pins `skyvern[local]==1.0.48`. The extras are `local` (SQLite) and `server` (Postgres); there is no `all` extra.
- `.env` (owner-written, gitignored; never read, print or ask for its values) needs: `GEMINI_API_KEY`, `ENABLE_GEMINI=true`, `LLM_KEY`, optionally `MAX_STEPS_PER_RUN`, `BROWSER_TYPE=chromium-headful` (visible browser). `.env.example` has the same names with placeholders.
- `LLM_KEY` must be a name in Skyvern's registry (`skyvern/forge/sdk/api/llm/config_registry.py`) AND still served by Google. As of 2026-09-24, `GEMINI_2.5_FLASH` and `GEMINI_2.5_FLASH_LITE` return 404 ("no longer available to new users"); `GEMINI_3.5_FLASH_LITE` works. Other models returned transient 503s. If a model 404s, list what the key can use via `GET https://generativelanguage.googleapis.com/v1beta/models` and test with one tiny `generateContent` call.
- Skyvern log output is very verbose and prints request bodies to stderr; filter it (e.g. `Select-String "shop_lookup_|Report:"`) instead of dumping it.

## Working rules from the owner

- Do not assume. If a requirement, name or choice is unclear, ask before acting.
- Do not create files, folders or dependencies beyond what has been agreed.
- Say what you are doing during long commands; run slow ones in the background. Live runs use free-tier quota, so avoid needless repeat runs.
- Licence for this repo is not yet chosen (MIT was suggested, unconfirmed); no `LICENSE` file exists. Skyvern's licence is unverified (believed AGPL-3.0); the package metadata did not state it.
