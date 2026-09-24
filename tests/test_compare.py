import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from compare import build_comparison, validate  # noqa: E402
from schemas import PriceResult  # noqa: E402


def r(shop: str, price: float | None, in_stock: bool | None = True, currency: str | None = "USD") -> PriceResult:
    return PriceResult(product="Mouse", shop=shop, price=price, currency=currency, in_stock=in_stock)


def test_cheapest_ignores_out_of_stock():
    results = validate([r("A", 10.0), r("B", 5.0, in_stock=False), r("C", 8.0)])
    row = build_comparison(["Mouse"], results)[0]
    assert (row.cheapest_shop, row.cheapest_price) == ("C", 8.0)


def test_missing_price_is_unverified_and_excluded():
    results = validate([r("A", None), r("B", 9.0)])
    assert results[0].status == "unverified"
    assert build_comparison(["Mouse"], results)[0].cheapest_shop == "B"


def test_outlier_price_is_flagged():
    results = validate([r("A", 10.0), r("B", 11.0), r("C", 1000.0)])
    assert results[2].status == "unverified"
    assert build_comparison(["Mouse"], results)[0].cheapest_shop == "A"


def test_no_valid_offer_gives_no_cheapest():
    row = build_comparison(["Mouse"], validate([r("A", 5.0, in_stock=False)]))[0]
    assert row.cheapest_shop is None
