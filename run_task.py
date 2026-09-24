"""Usage: python run_task.py compare"""
import argparse
import asyncio
import functools
import http.server
import threading
from urllib.parse import urlparse

import structlog
import yaml

import config

logger = structlog.get_logger()


def start_demo_shops(sites: list[dict]) -> list[http.server.ThreadingHTTPServer]:
    """Serve demo_shops/shop_a,b,c on the ports named in sites.yaml (only for localhost URLs)."""
    servers = []
    local = [s for s in sites if urlparse(s["url"]).hostname in ("localhost", "127.0.0.1")]
    for folder, site in zip(sorted(p for p in config.DEMO_SHOPS_DIR.iterdir() if p.is_dir()), local):
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(folder))
        handler.log_message = lambda *a, **k: None  # type: ignore[attr-defined]
        server = http.server.ThreadingHTTPServer(("127.0.0.1", urlparse(site["url"]).port), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
    return servers


async def compare() -> None:
    config.require_env("GEMINI_API_KEY", "ENABLE_GEMINI", "LLM_KEY")
    from skyvern import Skyvern  # imported after config so .env is loaded first

    import compare as compare_logic
    from report import render_report
    from tasks.price_lookup import lookup_shop

    products = yaml.safe_load(config.PRODUCTS_FILE.read_text(encoding="utf-8"))["products"]
    sites = yaml.safe_load(config.SITES_FILE.read_text(encoding="utf-8"))["sites"]

    servers = start_demo_shops(sites)
    skyvern = Skyvern.local(use_in_memory_db=True)
    browser = None
    try:
        browser = await skyvern.launch_local_browser(headless=False)
        page = await browser.get_working_page()
        results = []
        for site in sites:  # sequential on purpose: free-tier rate limits
            results += await lookup_shop(page, site["name"], site["url"], products)
    finally:
        if browser is not None:
            await browser.close()
        await skyvern.aclose()
        for s in servers:
            s.shutdown()

    rows = compare_logic.build_comparison(products, compare_logic.validate(results))
    path = render_report(rows, [s["name"] for s in sites], config.OUTPUT_DIR)
    logger.info("report_written", path=str(path))
    print(f"Report: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["compare"])
    args = parser.parse_args()
    if args.command == "compare":
        asyncio.run(compare())


if __name__ == "__main__":
    main()
