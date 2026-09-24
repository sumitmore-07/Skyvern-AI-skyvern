# Competitor Price Comparison with Skyvern

Point an AI agent at several shop websites, and get back one table showing who sells each product cheapest.

No page-specific code is needed. Every shop has a different layout, and the same plain-English instruction works on all of them. Prices are read from what a person would see on the page.

## What you get

An HTML report like this (from the included demo shops):

| Product | TechMart | GadgetHub | ValueDepot | Best deal |
|---|---|---|---|---|
| Wireless Mouse | 24.99 | **22.49** | 26.00 | GadgetHub |
| Mechanical Keyboard | 79.00 | 84.99 | **74.50** | ValueDepot |
| Laptop Stand | 32.00 | ~~29.50~~ out of stock | **27.99** | ValueDepot |

- The cheapest **available** offer is highlighted. Out-of-stock items are ignored.
- Prices that look wrong are flagged **unverified** for a human to check, instead of being trusted blindly.
- If a shop can't be read, it shows as "n/a" and the rest of the report still works.

## How it works

1. The script opens each shop in a real browser (Chromium, via Playwright).
2. [Skyvern](https://github.com/Skyvern-AI/skyvern) sends a screenshot of the page to a vision LLM (Google Gemini) and asks for each product's price and stock status.
3. Plain Python then checks the results: missing values, and prices far from the median across shops, are flagged.
4. The cheapest verified in-stock offer per product is picked and written to an HTML report.

```
data/products.yaml + data/sites.yaml
        |
   run_task.py  ->  tasks/price_lookup.py  ->  Skyvern (in-process) -> Gemini
        |                                              |
   compare.py (validate + cheapest)  <-----------------+
        |
   report.py + templates/report.html  ->  output/price_report_<time>.html
```

Adding a shop or product means editing a YAML file, not writing code.

## Setup (Windows 11, PowerShell)

Requires Python **3.11 to 3.13** (Skyvern 1.0.48 does not support 3.14) and a free [Google AI Studio](https://aistudio.google.com/) API key.

```powershell
py -3.12 -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
copy .env.example .env      # then put your real key in .env
```

Your `.env` needs:

```
GEMINI_API_KEY=your-key
ENABLE_GEMINI=true
LLM_KEY=GEMINI_3.5_FLASH_LITE
```

`.env` is gitignored. Never commit it.

**About `LLM_KEY`:** Google retires Gemini models over time. As of 2026-09-24, `GEMINI_2.5_FLASH` and `GEMINI_2.5_FLASH_LITE` return 404 for new keys, while `GEMINI_3.5_FLASH_LITE` works. If you see a 404 or "not found" from Google, list the models your key can use and pick a matching name from Skyvern's registry (`skyvern/forge/sdk/api/llm/config_registry.py` in the installed package).

## Run

```powershell
python run_task.py compare
```

A visible Chromium window opens (set `BROWSER_TYPE` in `.env` to change that). A run of 3 shops takes about a minute and makes 3 Gemini calls. Open the generated file in `output/`.

Tests (no LLM calls, no network):

```powershell
python -m pytest -q
```

## Project layout

| Path | Purpose |
|---|---|
| `run_task.py` | Entry point; serves the demo shops, runs each shop, writes the report |
| `tasks/price_lookup.py` | The one generic Skyvern extraction; the shop URL is just a parameter |
| `compare.py` | Validation and cheapest-offer logic (pure Python, unit-tested) |
| `schemas.py` | Pydantic models for results |
| `report.py`, `templates/report.html` | HTML report |
| `demo_shops/` | Three self-written fake shops with different layouts (table, cards, list) |
| `data/` | Products and shop URLs |
| `config.py` | Loads `.env` before Skyvern is imported |

## Design decisions worth knowing

- **`page.extract`, not the agent loop.** Skyvern's `run_task` is built for click-and-navigate work. On a read-only page it finished in one step without returning any data, and took about 45 seconds per step. `page.extract` is a single LLM call that returned correct data in about 7 seconds.
- **Runs in-process.** `Skyvern.local(use_in_memory_db=True)` needs no Skyvern server, no Skyvern API key and no database.
- **Own demo shops, not real sites.** Many real shops forbid scraping and use bot protection. Fake shops are legal to automate, and because the true prices are known, accuracy can be checked. All 18 prices in the first run matched.
- **Skyvern blocks `localhost` by default** as an SSRF safeguard. `config.py` allows only `localhost`, so the local demo shops work.

## Limitations

- **Tested only on the three demo shops:** small, clean pages with 6 products each. Real shops are harder and may block automation. Check a site's terms of service before pointing this at it.
- **AI reads can be wrong.** The sanity checks catch some errors, but not all. Treat the report as a fast first pass, not as a source of truth.
- **Free-tier limits.** Runs are sequential to stay within Gemini's rate limits, and available models change.
- **No login, checkout or booking.** This tool only reads public prices.

## License

Not yet specified.
