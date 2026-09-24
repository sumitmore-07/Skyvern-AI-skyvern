"""One generic Skyvern task: read prices for a product list from any shop page. No per-site code."""
import structlog

import config  # noqa: F401  (must load .env before skyvern is imported)
from schemas import PriceResult

logger = structlog.get_logger()

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Product name exactly as shown on the page"},
                    "price": {"type": ["number", "null"], "description": "Numeric price, no currency symbol"},
                    "currency": {"type": ["string", "null"], "description": "ISO code such as USD"},
                    "in_stock": {"type": ["boolean", "null"], "description": "False if out of stock or sold out"},
                },
                "required": ["name", "price", "currency", "in_stock"],
            },
        }
    },
    "required": ["products"],
}


def build_prompt(products: list[str]) -> str:
    listing = "\n".join(f"- {p}" for p in products)
    return (
        "This page is an online shop. For each product below, read its price and whether it is in stock. "
        "Only report what is visible on the page. If a product is not listed, omit it. "
        "Do not click anything that adds to a cart or navigates away.\n\n" + listing
    )


def parse_output(shop: str, products: list[str], output: object) -> list[PriceResult]:
    """Turn Skyvern's raw output into PriceResult rows; products it did not return are marked failed."""
    rows = output.get("products", []) if isinstance(output, dict) else []
    by_name = {str(r.get("name", "")).strip().lower(): r for r in rows if isinstance(r, dict)}
    results: list[PriceResult] = []
    for product in products:
        row = by_name.get(product.lower())
        if row is None:
            results.append(PriceResult(product=product, shop=shop, status="failed", note="not returned"))
            continue
        try:
            price = float(row["price"]) if row.get("price") is not None else None
        except (TypeError, ValueError):
            price = None
        results.append(
            PriceResult(
                product=product,
                shop=shop,
                price=price,
                currency=row.get("currency"),
                in_stock=row.get("in_stock"),
            )
        )
    return results


async def lookup_shop(page, shop: str, url: str, products: list[str]) -> list[PriceResult]:
    """Open one shop page and extract prices with a single Skyvern extract call.

    Uses page.extract (one LLM call on the page) rather than run_task: the agent loop is built for
    click-and-navigate work, and on a read-only page it finished without extracting anything.
    Failures become 'failed' rows, not exceptions, so one bad shop cannot abort the comparison.
    """
    try:
        await page.goto(url)
        output = await page.extract(prompt=build_prompt(products), schema=EXTRACTION_SCHEMA)
    except Exception as e:  # noqa: BLE001 - one bad shop must not abort the whole comparison
        logger.error("shop_lookup_failed", shop=shop, error=str(e))
        return [PriceResult(product=p, shop=shop, status="failed", note=str(e)[:200]) for p in products]

    logger.info("shop_lookup_done", shop=shop)
    return parse_output(shop, products, output)
