"""Validation and comparison logic. Pure Python, no Skyvern imports, so it is unit-testable."""
from statistics import median

from schemas import ComparisonRow, PriceResult

OUTLIER_FACTOR = 3.0  # a price this many times above/below the median of the others is suspect


def validate(results: list[PriceResult]) -> list[PriceResult]:
    """Mark results that fail basic sanity checks as 'unverified'. Never trusts model output blindly."""
    for r in results:
        if r.status == "failed":
            continue
        if r.price is None or r.price <= 0:
            r.status, r.note = "unverified", "missing or non-positive price"
        elif not r.currency:
            r.status, r.note = "unverified", "missing currency"
        elif r.in_stock is None:
            r.status, r.note = "unverified", "stock status unclear"

    by_product: dict[str, list[PriceResult]] = {}
    for r in results:
        if r.status == "ok":
            by_product.setdefault(r.product, []).append(r)
    for group in by_product.values():
        if len(group) < 3:
            continue  # too few data points to call anything an outlier
        mid = median(r.price for r in group if r.price)  # median is robust to a single bad value
        for r in group:
            if r.price and (r.price > mid * OUTLIER_FACTOR or r.price < mid / OUTLIER_FACTOR):
                r.status, r.note = "unverified", f"price far from median across shops ({mid:.2f})"
    return results


def build_comparison(products: list[str], results: list[PriceResult]) -> list[ComparisonRow]:
    """Group results per product and pick the cheapest verified, in-stock offer."""
    rows: list[ComparisonRow] = []
    for product in products:
        group = [r for r in results if r.product == product]
        candidates = [r for r in group if r.status == "ok" and r.in_stock and r.price]
        best = min(candidates, key=lambda r: r.price) if candidates else None  # type: ignore[arg-type,return-value]
        rows.append(
            ComparisonRow(
                product=product,
                results=group,
                cheapest_shop=best.shop if best else None,
                cheapest_price=best.price if best else None,
            )
        )
    return rows
